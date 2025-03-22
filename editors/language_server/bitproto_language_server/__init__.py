"""
A simple bitproto language server script (stdio based).

Reference: https://github.com/hit9/bitproto
"""

import logging
import string
import argparse
from typing import Callable, Optional
from collections import defaultdict
from dataclasses import dataclass, field

from pygls.lsp.server import LanguageServer
from lsprotocol import types
from bitproto.parser import parse
from bitproto._ast import Proto, Definition, Scope, Reference
from pygls.workspace import TextDocument


@dataclass
class ProtoInfo:
    proto: Proto

    # lineno (starting from 0) => definitions on this line
    definition_line_index: dict[int, list[Definition]] = field(
        default_factory=lambda: defaultdict(list)
    )

    reference_line_index: dict[int, list[Reference]] = field(
        default_factory=lambda: defaultdict(list)
    )


def _bp_to_pygls_k(n: int) -> int:
    return n - 1 if n > 0 else 0


def _pygls_to_bp_k(n: int) -> int:
    return n + 1


def _bp_definition_to_pygls_location(d: Definition) -> types.Location:
    lineno = _bp_to_pygls_k(d.lineno)
    col_start = _bp_to_pygls_k(d.token_col_start)
    col_end = _bp_to_pygls_k(d.token_col_end)
    start = types.Position(lineno, col_start)
    end = types.Position(lineno, col_end)
    uri = "file://" + d.filepath
    return types.Location(uri=uri, range=types.Range(start=start, end=end))


class BitprotoLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = {}  # uri => proto

    def _traverse_scope(self, scope: Scope, cb: Callable):
        cb(scope)
        for member in scope.members.values():
            if isinstance(member, Scope):
                self._traverse_scope(member, cb)
            else:
                cb(member)

    def _add_to_definition_line_index(
        self, d: Definition, definition_line_index: dict[int, Definition]
    ):
        # pygls uses lineno starts from 0.
        lineno = _bp_to_pygls_k(d.lineno)
        definition_line_index[lineno].append(d)

    def parse(self, doc: TextDocument):
        uri = doc.uri
        if uri.startswith("file://"):
            uri = uri[7:]

        proto = parse(uri)

        # Line Number => Definitions map.
        definition_line_index: dict[int, list[Definition]] = defaultdict(list)
        self._traverse_scope(
            proto,
            lambda d: self._add_to_definition_line_index(d, definition_line_index),
        )

        # Line Number => References map.
        reference_line_index: dict[int, list[Definition]] = defaultdict(list)

        for ref in proto.references:
            lineno = _bp_to_pygls_k(ref.lineno)
            reference_line_index[lineno].append(ref)

        # Url => ProtoInfo
        self.index[doc.uri] = ProtoInfo(
            proto=proto,
            definition_line_index=definition_line_index,
            reference_line_index=reference_line_index,
        )

    def find_definition_by_position(
        self, doc_uri: str, lineno: int, col: int, word: str
    ) -> Optional[Definition]:
        if doc_uri not in self.index:
            return None

        # pygls uses col starting from 0
        col = _pygls_to_bp_k(col)

        proto_info = self.index[doc_uri]

        # Find references at first.
        references = proto_info.reference_line_index.get(lineno, [])
        for ref in references:
            if ref.referenced_definition is not None:
                if col >= ref.token_col_start and col <= ref.token_col_end:
                    ref_token_words = ref.token.split(".")
                    if word == ref.token or ref_token_words[-1] == word:
                        # exactly this reference
                        return ref.referenced_definition

                    # have to guess which scope parent?
                    for i, w in enumerate(ref_token_words[:-1]):
                        if word == w:
                            try:
                                # why i+1: the current proto it self may be the root scope
                                return ref.referenced_definition.scope_stack[i + 1]
                            except:
                                pass

        # Find the definition itself.
        definitions = proto_info.definition_line_index.get(lineno, [])
        for d in definitions:
            if col >= d.token_col_start and col <= d.token_col_end:
                if word in d.token:
                    return d
        return None


server = BitprotoLanguageServer("bitproto-language-server", "v1")


def _goto_definition(
    ls: BitprotoLanguageServer, doc: TextDocument, position: types.Position
) -> Optional[types.Location]:
    word = doc.word_at_position(position)
    d = ls.find_definition_by_position(doc.uri, position.line, position.character, word)
    if not d:
        return None
    return _bp_definition_to_pygls_location(d)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: BitprotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is opened"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: BitprotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is changed"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


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
    pass


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: BitprotoLanguageServer, params: types.HoverParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    word = doc.word_at_position(params.position)
    d = ls.find_definition_by_position(
        doc.uri, params.position.line, params.position.character, word
    )
    if not d:
        return None
    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.PlainText,
            value="\n\n".join([c.content() for c in d.comment_block]),
        )
    )


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION, types.CompletionOptions(trigger_characters=["."])
)
def completions(ls: BitprotoLanguageServer, params: types.CompletionParams):
    items = []
    doc = server.workspace.get_text_document(params.text_document.uri)
    current_line = doc.lines[params.position.line].strip()
    # TODO how to get the dotted_identifier here?
    dotted_identifier = ""
    proto_info = ls.index.get(doc.uri, None)
    if word and proto_info:
        proto = proto_info.proto
        # TODO:
        # When `identifier` contains dots: lookup from its bitproto.
        # Otherwise, lookup from the scope stack reversively (in current proto).
        items = [
            types.CompletionItem(label="world"),
            types.CompletionItem(label="friend"),
        ]
    return types.CompletionList(is_incomplete=False, items=items)


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
        version="1.0.0",
    )
    args_parser.parse_args()
    server.start_io()
