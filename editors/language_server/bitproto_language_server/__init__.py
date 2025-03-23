"""
A simple bitproto language server script (stdio based).

Reference:
 - Repo: https://github.com/hit9/bitproto
 - Docs: https://bitproto.readthedocs.io

Requirements:
  - bitproto >= 1.2.0
  - pygls~=2.0.0 (a2)

Currently Supports:
  - Goto Definition
  - Hover to show comments.
  - Completion for Enum/Message/Constant definitions.
  - Diagnostic (Simple)
  - DocumentSymbol (tree)
  - Find References

Currently Un-Supported, but may in plan:
  - Inlay Hint
  - Formatting

"""

import os
import logging
import argparse
from typing import Callable, Optional, List, Dict, cast
from collections import defaultdict
from dataclasses import dataclass, field

from pygls.lsp.server import LanguageServer
from lsprotocol import types
from bitproto.parser import parse, parse_string
from bitproto.errors import ParserError
from bitproto._ast import (
    Proto,
    Definition,
    Node,
    Scope,
    Reference,
    Message,
    Enum,
    Constant,
    IntegerConstant,
    StringConstant,
    BooleanConstant,
    MessageField,
    EnumField,
)
from pygls.workspace import TextDocument


@dataclass
class ProtoInfo:
    proto: Proto

    # Indexing lineno to definitions.
    # lineno (starting from 1) => definitions on this line
    definition_line_index: Dict[int, List[Definition]] = field(
        default_factory=lambda: defaultdict(list)
    )

    # Indexing lineno to references.
    # lineno (starting from 1) => list of references
    reference_line_index: Dict[int, List[Reference]] = field(
        default_factory=lambda: defaultdict(list)
    )

    # The filepath this proto imported (recursively)
    imported_proto_paths: List[str] = field(default_factory=list)


def _bp_to_pygls_k(n: int) -> int:
    """
    bitproto's lineno and col are starting from 1.
    while pygls's are starting from 0.
    Converts given bitproto's lineno/col to pygls's.
    """
    return n - 1 if n > 0 else 0


def _pygls_to_bp_k(n: int) -> int:
    """
    bitproto's lineno and col are starting from 1.
    while pygls's are starting from 0.
    Converts given pygls's lineno/col to bitproto's.
    """
    return n + 1


def _bp_node_to_pygls_location(d: Node) -> types.Location:
    """
    Converts given definition's location to pygls's location.
    """

    lineno = _bp_to_pygls_k(d.lineno)
    col_start = _bp_to_pygls_k(d.token_col_start)
    col_end = _bp_to_pygls_k(d.token_col_end)
    start = types.Position(lineno, col_start)
    end = types.Position(lineno, col_end)
    uri = "file://" + d.filepath
    return types.Location(uri=uri, range=types.Range(start=start, end=end))


def _bp_definition_to_pygls_range(d: Definition) -> types.Range:
    if isinstance(d, Scope):
        return types.Range(
            start=types.Position(
                line=_bp_to_pygls_k(d.scope_start_lineno),
                character=_bp_to_pygls_k(d.scope_start_col),
            ),
            end=types.Position(
                line=_bp_to_pygls_k(d.scope_end_lineno),
                character=_bp_to_pygls_k(d.scope_end_col),
            ),
        )
    return types.Range(
        start=types.Position(
            line=_bp_to_pygls_k(d.lineno),
            character=_bp_to_pygls_k(d.token_col_start),
        ),
        end=types.Position(
            line=_bp_to_pygls_k(d.lineno),
            character=_bp_to_pygls_k(d.token_col_end),
        ),
    )


class BitprotoLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # uri => proto
        # where uri starts from "file://"
        self.index = {}
        self.diagnostics_versions = {}

    def _traverse_scope(self, scope: Scope, cb: Callable):
        """
        Traverse the given scope and descendant scopes recursively.
        Call given `cb` on all walked definitions.
        """
        cb(scope)  # pre order
        for member in scope.members.values():
            if isinstance(member, Scope):
                self._traverse_scope(member, cb)
            else:
                cb(member)

    def _add_to_definition_line_index(
        self, d: Definition, definition_line_index: Dict[int, List[Definition]]
    ):
        """Add given definition `d` to given `definition_line_index` map."""
        definition_line_index[d.lineno].append(d)

    def _push_diagnostics(self, doc_uri: str, e: Optional[ParserError] = None):
        """Push an error diagnostics or empty diagnostics list"""

        self.diagnostics_versions.setdefault(doc_uri, 0)
        self.diagnostics_versions[doc_uri] += 1

        diagnostics = []

        if e:
            position = types.Position(_bp_to_pygls_k(e.lineno), 0)
            diagnostics = [
                types.Diagnostic(
                    message=str(e),
                    range=types.Range(start=position, end=position),
                    source="bitproto",
                )
            ]
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=doc_uri,
                diagnostics=diagnostics,
                version=self.diagnostics_versions.get(doc_uri, 0),
            )
        )

    def parse(
        self,
        doc: TextDocument,
        use_parse_string: bool = False,
        file_source: str = "",
        raise_on_parsing_error: bool = False,
        enable_diagnostics: bool = True,
    ):
        """
        Parse given document to bitproto.

        :param doc: Current editing document.
        :param use_parse_string:
           Setting to `True` means to parse from given string `file_source` instead of
           parsing from filepath `doc.uri`.
        """

        # Converts `file://` started uri to normalized filepath.
        uri = doc.uri
        if uri.startswith("file://"):
            uri = uri[7:]

        # Parse proto.
        proto: Optional[Proto] = None

        try:
            if use_parse_string and file_source:
                proto = parse_string(file_source, filepath=uri)
            else:
                proto = parse(uri)

            if enable_diagnostics:
                self._push_diagnostics(doc.uri, None)
        except Exception as e:
            if raise_on_parsing_error:
                raise e
            else:
                if enable_diagnostics and isinstance(e, ParserError):
                    self._push_diagnostics(doc.uri, e)
                return

        # Line Number => Definitions map.
        definition_line_index: Dict[int, List[Definition]] = defaultdict(list)
        self._traverse_scope(
            proto,
            lambda d: self._add_to_definition_line_index(d, definition_line_index),
        )

        # Line Number => References map.
        reference_line_index: Dict[int, List[Reference]] = defaultdict(list)
        for ref in proto.references:
            reference_line_index[ref.lineno].append(ref)

        # Collects imported protos recursively.
        imported_proto_paths: list[str] = []

        def __collect_child_proto_path(d: Definition):
            if isinstance(d, Proto):
                imported_proto_paths.append(d.filepath)

        self._traverse_scope(proto, __collect_child_proto_path)

        # Url => ProtoInfo
        self.index[doc.uri] = ProtoInfo(
            proto=proto,
            definition_line_index=definition_line_index,
            reference_line_index=reference_line_index,
            imported_proto_paths=imported_proto_paths,
        )

    def _build_scope_stack_by_position_helper(
        self, scope: Scope, lineno: int, col: int, scope_stack: List[Scope]
    ) -> None:
        """
        Collects `scope_stack` starting from current `scope` recursively.
        """
        if (
            (scope.scope_start_lineno, scope.scope_start_col)
            <= (lineno, col)
            <= (scope.scope_end_lineno, scope.scope_end_col)
        ):
            # this location is inside this scope
            scope_stack.append(scope)

            # Lets dfs down to the child scopes.
            for member in scope.members.values():
                if isinstance(member, Scope) and not isinstance(member, Proto):
                    # We don't care the imported proto.
                    self._build_scope_stack_by_position_helper(
                        member, lineno, col, scope_stack
                    )

    def find_scope_stack_by_position(
        self, doc_uri: str, lineno: int, col: int
    ) -> Optional[List[Scope]]:
        """
        Find current position (lineno, col)'s scope_stack.
        Returns None if given doc_uri is unknown.
        """
        if doc_uri not in self.index:
            return None

        proto_info = self.index[doc_uri]

        scope_stack: List[Scope] = []

        self._build_scope_stack_by_position_helper(
            proto_info.proto, lineno, col, scope_stack
        )

        return scope_stack

    def find_members_by_scope_stack(
        self, scope_stack: List[Scope], dotted_identifier: str
    ) -> Optional[Definition]:
        """Find names in given scope_stack.
        This works very similar to the parser's internal method `_lookup_referenced_member`.
        """
        names = dotted_identifier.split(".")
        for scope in scope_stack[::-1]:
            d = scope.get_member(*names)
            if d is not None:
                return d
        return None

    def find_definition_by_position(
        self, doc_uri: str, lineno: int, col: int, word: str, current_line: str
    ) -> Optional[Definition]:
        """
        Find a bitproto definition in given document at location (lineno, col).

        :param doc_uri: The doc's "file://" uri to handle, we use it to find which proto to search.
        :param lineno, col, word: the word with its location (lineno, col).
        """

        if doc_uri not in self.index:
            return None

        proto_info = self.index[doc_uri]

        # Find current scope.
        scope_stack = self.find_scope_stack_by_position(doc_uri, lineno, col)

        dotted_identifier = _util_find_dotted_identifier_backward(
            current_line, col + len(word)
        )
        if dotted_identifier.endswith("."):
            dotted_identifier = dotted_identifier[:-1]  # remove the "."

        # Find existing references at first.
        references = proto_info.reference_line_index.get(lineno, [])
        for ref in references:
            if ref.referenced_definition is None:
                # Only checks the references that positions match
                continue

            if col >= ref.token_col_start and col <= ref.token_col_end:
                ref_token_words = ref.token.split(".")
                if word == ref.token or ref_token_words[-1] == word:
                    # exactly this reference
                    return ref.referenced_definition

                # Maybe the word is part of a dotted_identifier.
                # e.g. `A.B.C`
                if dotted_identifier and scope_stack:
                    # find the referenced definition
                    d = self.find_members_by_scope_stack(scope_stack, dotted_identifier)
                    if d:
                        return d

                # The final approach maybe not accurate,we have to guess by matching word and name.
                for i, token_word in enumerate(ref_token_words[:-1]):
                    if word == token_word:
                        try:
                            # why i+1: the current proto it self may be the root scope
                            return ref.referenced_definition.scope_stack[i + 1]
                        except Exception:
                            pass

        # Maybe the current dotted_identifier is still not parsable
        if scope_stack and dotted_identifier:
            d = self.find_members_by_scope_stack(scope_stack, dotted_identifier)
            if d:
                return d

        # Find the definition itself.
        definitions = proto_info.definition_line_index.get(lineno, [])
        for d1 in definitions:
            if col >= d1.token_col_start and col <= d1.token_col_end:
                if word in d1.token:
                    return d1
        return None


server = BitprotoLanguageServer("bitproto-language-server", "v1")


def is_valid_identifier_char(char: str):
    return char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_."


def _util_find_dotted_identifier_backward(current_line: str, col: int):
    """Find the `dotted_identifier` around current col.
    Where `col` starting from `1`.
    e.g.
        '    base.BaseMessage'
                     ^
        => 'base.Base'
    """
    # Search backward for the first non [A-Za-z0-9_\.] character
    # (e.g. whitespaces, `=`, newlines etc)
    stack = []
    k = min(col - 1, len(current_line) - 1)
    while k >= 0:
        if not is_valid_identifier_char(current_line[k]):
            break
        stack.append(current_line[k])
        k -= 1
    stack.reverse()
    return "".join(stack)


def _goto_definition(
    ls: BitprotoLanguageServer, doc: TextDocument, position: types.Position
) -> Optional[types.Location]:
    """
    Helper function handles all `GotoXXX` features.
    In bitproto, there's no `Declaration`, `TypeDefinition` concepts,
    so we map all `GotoXXX` features to `GotoDefinition`.
    """
    word = doc.word_at_position(position)
    current_line = doc.lines[position.line]
    current_line = current_line.rstrip("\n")
    lineno = _pygls_to_bp_k(position.line)
    col = _pygls_to_bp_k(position.character)
    d = ls.find_definition_by_position(doc.uri, lineno, col, word, current_line)
    if not d:
        return None
    return _bp_node_to_pygls_location(d)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: BitprotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """On document open."""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: BitprotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """On document changed (buffer changes)."""
    doc = ls.workspace.get_text_document(params.text_document.uri)

    ls.parse(doc, use_parse_string=True, file_source=doc.source)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: BitprotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """On document saved to disk."""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)

    # We have to refresh all ancestor bitprotos that may include the current one.
    filepath = doc.uri[7:] if doc.uri.startswith("file://") else doc.uri
    refreshed_uris = set()
    for doc_uri, proto_info in ls.index.items():
        if doc_uri in refreshed_uris:
            continue
        for child_proto_path in proto_info.imported_proto_paths:
            print(child_proto_path, filepath)
            if os.path.samefile(child_proto_path, filepath):
                # refresh this proto
                doc = ls.workspace.get_text_document(doc_uri)
                ls.parse(doc, enable_diagnostics=False)
                refreshed_uris.add(doc_uri)
                break


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(ls: BitprotoLanguageServer, params: types.TypeDefinitionParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return _goto_definition(ls, doc, params.position)


@server.feature(types.TEXT_DOCUMENT_DECLARATION)
def goto_declaration(ls: BitprotoLanguageServer, params: types.DeclarationParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return _goto_definition(ls, doc, params.position)


@server.feature(types.TEXT_DOCUMENT_TYPE_DEFINITION)
def goto_type_definition(
    ls: BitprotoLanguageServer, params: types.TypeDefinitionParams
):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return _goto_definition(ls, doc, params.position)


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def find_references(ls: BitprotoLanguageServer, params: types.ReferenceParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    if doc.uri not in ls.index:
        return

    # Firstly, find current definition.
    current_line = doc.lines[params.position.line]
    current_line = current_line.rstrip("\n")
    lineno = _pygls_to_bp_k(params.position.line)
    col = _pygls_to_bp_k(params.position.character)
    word = doc.word_at_position(params.position)
    d = ls.find_definition_by_position(doc.uri, lineno, col, word, current_line)
    if not d:
        return None

    # current file path
    current_file_path = doc.uri
    if current_file_path.startswith("file://"):
        current_file_path = current_file_path[7:]

    results = []

    # Then find its reference
    for uri, proto_info in ls.index.items():
        should_check_current_proto = False

        if uri == doc.uri:  # Current proto
            should_check_current_proto = True

        for child_proto_path in proto_info.imported_proto_paths:
            if os.path.samefile(child_proto_path, current_file_path):
                # this proto may reference current_file.
                should_check_current_proto = True
                break

        if not should_check_current_proto:
            continue

        for ref in proto_info.proto.references:
            d1 = ref.referenced_definition
            if d1 is d:
                results.append(ref)
            else:
                if (
                    d1.name == d.name
                    and d1.filepath == d.filepath
                    and d1.lineno == d.lineno
                    and d1.token_col_start == d.token_col_start
                ):
                    results.append(ref)

    # transform to location
    return [_bp_node_to_pygls_location(ref) for ref in results]


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: BitprotoLanguageServer, params: types.HoverParams):
    """
    Hover to show the definition's comment block.
    """

    doc = ls.workspace.get_text_document(params.text_document.uri)
    word = doc.word_at_position(params.position)
    current_line = doc.lines[params.position.line]
    current_line = current_line.rstrip("\n")
    lineno = _pygls_to_bp_k(params.position.line)
    col = _pygls_to_bp_k(params.position.character)
    d = ls.find_definition_by_position(doc.uri, lineno, col, word, current_line)
    if not d:
        return None

    contents = [c.content() for c in d.comment_block]

    if isinstance(d, Constant):
        contents.append("\n\n---\n\n Value: {0}".format(d.value))
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value="\n\n".join(contents),
            )
        )

    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.PlainText,
            value="\n\n".join(contents),
        )
    )


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION, types.CompletionOptions(trigger_characters=["."])
)
def completions(ls: BitprotoLanguageServer, params: types.CompletionParams):
    items = []

    doc = server.workspace.get_text_document(params.text_document.uri)

    if doc.uri not in ls.index:
        return

    current_line = doc.lines[params.position.line]
    current_line = current_line.rstrip("\n")

    lineno = _pygls_to_bp_k(params.position.line)
    col = _pygls_to_bp_k(params.position.character)

    dotted_identifier = _util_find_dotted_identifier_backward(current_line, col)
    if dotted_identifier.endswith("."):
        # trim the last dot
        dotted_identifier = dotted_identifier[:-1]

    scope_stack = ls.find_scope_stack_by_position(doc.uri, lineno, col)
    if not scope_stack:
        return None

    d = ls.find_members_by_scope_stack(scope_stack, dotted_identifier)
    if not d:
        return None

    if not isinstance(d, Scope):
        return None

    scope = cast(Scope, d)
    items = [
        types.CompletionItem(label=member_name)
        for member_name, member in scope.members.items()
        if isinstance(member, (Proto, Message, Enum, Constant))
    ]
    return types.CompletionList(is_incomplete=False, items=items)


def __determine_symbol_kind(d: Definition) -> types.SymbolKind:
    if isinstance(d, Message):
        return types.SymbolKind.Struct
    elif isinstance(d, Enum):
        return types.SymbolKind.Enum
    elif isinstance(d, Constant):
        if isinstance(d, IntegerConstant):
            return types.SymbolKind.Number
        if isinstance(d, StringConstant):
            return types.SymbolKind.String
        if isinstance(d, BooleanConstant):
            return types.SymbolKind.Boolean
        return types.SymbolKind.Constant
    elif isinstance(d, Proto):
        return types.SymbolKind.Module
    elif isinstance(d, EnumField):
        return types.SymbolKind.EnumMember
    elif isinstance(d, MessageField):
        return types.SymbolKind.Field
    return types.SymbolKind.Object


def _dfs_symbol_collect(definition: Definition) -> types.DocumentSymbol:
    children: List[types.DocumentSymbol] = []

    if isinstance(definition, Scope):
        scope = cast(Scope, definition)
        for member in scope.members.values():
            children.append(_dfs_symbol_collect(member))

    range_ = _bp_definition_to_pygls_range(definition)
    return types.DocumentSymbol(
        name=definition.name,
        kind=__determine_symbol_kind(definition),
        range=range_,
        children=children,
        selection_range=range_,
    )


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: BitprotoLanguageServer, params: types.DocumentSymbolParams):
    doc = server.workspace.get_text_document(params.text_document.uri)
    if doc.uri not in ls.index:
        return
    proto_info = ls.index[doc.uri]
    return [_dfs_symbol_collect(proto_info.proto)]


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    args_parser = argparse.ArgumentParser(
        description="bitproto-language-server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    args_parser.add_argument(
        "-v",
        "--version",
        dest="version",
        action="version",
        help="show version",
        version="1.2.0",
    )
    args_parser.parse_args()
    server.start_io()
