"""
bitproto.parser
~~~~~~~~~~~~~~~

Grammar parser for bitproto.
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass, field as dataclass_field
from typing import List, Tuple, Iterator, Optional, Type as T

from ply import yacc
from ply.lex import LexToken
from ply.yacc import YaccProduction as P, LRParser as PlyParser

from bitproto.ast import (
    Alias,
    Array,
    Comment,
    Definition,
    Enum,
    EnumField,
    Constant,
    BooleanConstant,
    IntegerConstant,
    StringConstant,
    Message,
    MessageField,
    Type,
    Option,
    Scope,
    Proto,
)
from bitproto.errors import (
    InternalError,
    CalculationExpressionError,
    InvalidArrayCap,
    GrammarError,
    ReferencedConstantNotDefined,
    ReferencedTypeNotDefined,
    CyclicImport,
)
from bitproto.lexer import Lexer, LexerHandle


@dataclass
class ParserHandle:
    """Parsing context holder."""

    filepath: str = ""
    scope_stack: List[Scope] = dataclass_field(default_factory=list)
    comment_block: List[Comment] = dataclass_field(default_factory=list)

    def push_scope(self, scope: Scope) -> None:
        self.scope_stack.append(scope)

    def pop_scope(self) -> Scope:
        return self.scope_stack.pop()

    def current_scope(self) -> Scope:
        assert len(self.scope_stack) > 0, InternalError("Empty scope_stack")
        return self.scope_stack[-1]

    def scope_stack_tuple(self) -> Tuple[Scope, ...]:
        return tuple(self.scope_stack)

    def current_proto(self) -> Proto:
        assert len(self.scope_stack) > 0, InternalError("Empty scope_stack")
        assert isinstance(self.scope_stack[0], Proto), InternalError(
            "scope_stack[0] not a Proto instance"
        )
        return self.scope_stack[0]

    def push_comment(self, comment: Comment) -> None:
        self.comment_block.append(comment)

    def clear_comment_block(self) -> None:
        block = self.comment_block[:]
        self.comment_block = []

    def collect_comment_block(self) -> Tuple[Comment, ...]:
        comment_block = tuple(self.comment_block)
        self.clear_comment_block()
        return comment_block


class Parser:
    """Parser for bitproto.

        >>> parser = Parser()
        >>> parser.parse("path/to/example.bitproto")
        <bitproto example>

    """

    tokens: Tuple[str, ...] = Lexer.tokens
    # precedence for math operators
    precedence: Tuple[Tuple[str, str, str], ...] = (
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE"),
    )

    def __init__(self, debug: bool = False, write_tables: bool = False) -> None:
        self.handle_stack: List[ParserHandle] = []
        self.lexer: Lexer = Lexer()
        self.parser: PlyParser = yacc.yacc(
            module=self, start="start", debug=debug, write_tables=write_tables
        )

    def push_handle(self, handle: ParserHandle) -> None:
        self.handle_stack.append(handle)

    def pop_handle(self) -> ParserHandle:
        return self.handle_stack.pop()

    def current_handle(self) -> ParserHandle:
        assert len(self.handle_stack) > 0, InternalError(
            "ParserHandle is None during parsing"
        )
        return self.handle_stack[-1]

    def push_scope(self, scope: Scope) -> None:
        self.current_handle().push_scope(scope)

    def pop_scope(self) -> Scope:
        return self.current_handle().pop_scope()

    def current_scope(self) -> Scope:
        handle = self.current_handle()
        return handle.current_scope()

    def current_proto(self) -> Proto:
        handle = self.current_handle()
        return handle.current_proto()

    def current_scope_stack(self) -> Tuple[Scope, ...]:
        handle = self.current_handle()
        return handle.scope_stack_tuple()

    def collect_comment_block(self) -> Tuple[Comment, ...]:
        handle = self.current_handle()
        return handle.collect_comment_block()

    def clear_comment_block(self) -> None:
        handle = self.current_handle()
        return handle.clear_comment_block()

    def push_comment(self, comment: Comment) -> None:
        handle = self.current_handle()
        handle.push_comment(comment)

    def current_filepath(self) -> str:
        handle = self.current_handle()
        return handle.filepath

    @contextmanager
    def maintain_handle(self, handle: ParserHandle) -> Iterator[ParserHandle]:
        try:
            self.push_handle(handle)
            yield handle
        finally:
            self.pop_handle()

    def parse_string(self, s: str, filepath: str = "") -> Proto:
        """Parse a bitproto from given string `s`.
        :param filepath: The filepath information if exist.
        """
        with self.lexer.maintain_handle(LexerHandle(filepath=filepath)):
            with self.maintain_handle(ParserHandle(filepath=filepath)):
                return self.parser.parse(s)

    def parse(self, filepath: str) -> Proto:
        """Parse a bitproto from given file."""
        with open(filepath) as f:
            return self.parse_string(f.read(), filepath=filepath)

    def util_parse_sequence(self, p: P) -> None:
        if len(p) == 3:
            p[0] = [p[1]] + p[2]
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 1:
            p[0] = []

    def p_optional_semicolon(self, p: P) -> None:
        """optional_semicolon : ';'
                              |"""
        p[0] = None

    def p_start(self, p: P) -> None:
        """start : open_global_scope global_scope close_global_scope"""
        p[0] = p[2]

    def p_open_global_scope(self, p: P) -> None:
        """open_global_scope : """
        proto = Proto(filepath=self.current_filepath())
        self.push_scope(proto)

    def p_close_global_scope(self, p: P) -> None:
        """close_global_scope :"""
        self.pop_scope()

    def p_global_scope(self, p: P) -> None:
        """global_scope : global_scope_definitions"""
        p[0] = scope = self.current_scope()

    def p_global_scope_definitions(self, p: P) -> None:
        """global_scope_definitions : global_scope_definition_unit global_scope_definitions
                                    | global_scope_definition_unit
                                    |"""
        self.util_parse_sequence(p)

    def p_global_scope_definition_unit(self, p: P) -> None:
        """global_scope_definition_unit : import
                                        | option
                                        | alias
                                        | const
                                        | enum
                                        | message
                                        | proto
                                        | comment
                                        | newline"""
        p[0] = p[1]

    def p_proto(self, p: P) -> None:
        """proto : PROTO IDENTIFIER optional_semicolon"""
        proto = self.current_proto()
        proto.set_name(p[2])
        proto.set_comment_block(self.collect_comment_block())

    def p_comment(self, p: P) -> None:
        """comment : COMMENT NEWLINE"""
        self.push_comment(p[1])

    def p_newline(self, p: P) -> None:
        """newline : NEWLINE"""
        self.clear_comment_block()

    def _get_child_filepath(self, importing_path: str) -> str:
        """Gets the filepath for the importing path.
        If the `importing_path` is an absolute path, using it directly.
        Otherwise, use it as a relative path to current parsing file.
        """
        if os.path.isabs(importing_path):
            return importing_path
        base_filepath = self.current_filepath()
        if base_filepath:  # We are parsing a file
            current_proto_dir = os.path.dirname(base_filepath)
        else:
            # We are parsing from a string, using cwd instead.
            current_proto_dir = os.getcwd()
        return os.path.join(current_proto_dir, importing_path)

    def _check_parsing_file(self, filepath: str) -> bool:
        """Checks if given filepath existing in parsing stack.
        """
        for handle in self.handle_stack:
            if os.path.samefile(handle.filepath, filepath):
                return True
        return False

    def p_import(self, p: P) -> None:
        """import : IMPORT STRING_LITERAL optional_semicolon
                  | IMPORT IDENTIFIER STRING_LITERAL optional_semicolon"""
        # Get filepath to import.
        importing_path = p[len(p) - 2]
        filepath = self._get_child_filepath(importing_path)
        # Check if this filepath already in parsing.
        if self._check_parsing_file(filepath):
            raise CyclicImport(
                message=f"cyclic importing {filepath}",
                filepath=self.current_filepath(),
                token=importing_path,
                lineno=p.lineno(2),
            )
        # Parse.
        child = Parser().parse(filepath)
        name = child.name
        if len(p) == 5:  # Importing as `name`
            name = p[2]
        # Push to current scope
        self.current_scope().push_member(child, name)

    def p_option(self, p: P) -> None:
        """option : OPTION IDENTIFIER '=' option_value optional_semicolon"""
        name, value = p[2], p[4]
        option = Option(
            name=name,
            value=value,
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
            filepath=self.current_filepath(),
            lineno=p.lineno(2),
            token=p[2],
        )
        self.current_scope().push_member(option)

    def p_option_value(self, p: P) -> None:
        """option_value : boolean_literal
                        | integer_literal
                        | string_literal"""
        p[0] = p[1]

    def p_alias(self, p: P) -> None:
        """alias : TYPE IDENTIFIER '=' type optional_semicolon"""
        name, type = p[2], p[4]
        alias = Alias(
            name=name,
            type=type,
            filepath=self.current_filepath(),
            lineno=p.lineno(2),
            token=p[2],
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
        )
        self.current_scope().push_member(alias)

    def p_const(self, p: P) -> None:
        """const : CONST IDENTIFIER '=' const_value optional_semicolon"""

        name, value = p[2], p[4]

        constant_cls: Optional[T[Constant]] = None

        if value is True or value is False or isinstance(value, BooleanConstant):
            # Avoid isinstance(True, int)
            constant_cls = BooleanConstant
            value = bool(value)
        elif isinstance(value, (int, IntegerConstant)):
            constant_cls = IntegerConstant
            value = int(value)
        elif isinstance(value, (str, StringConstant)):
            constant_cls = StringConstant
            value = str(value)
        else:
            raise InternalError("No constant_cls to use")

        constant = constant_cls(
            name=name,
            value=value,
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
            filepath=self.current_filepath(),
            token=p[2],
            lineno=p.lineno(2),
        )
        self.current_scope().push_member(constant)

    def p_const_value(self, p: P) -> None:
        """const_value : boolean_literal
                       | string_literal
                       | constant_reference
                       | calculation_expression
                       """
        p[0] = p[1]

    def p_calculation_expression(self, p: P) -> None:
        """calculation_expression : calculation_expression_plus
                                  | calculation_expression_minus
                                  | calculation_expression_times
                                  | calculation_expression_divide
                                  | calculation_expression_group
                                  | integer_literal
                                  | constant_reference_for_calculation"""
        p[0] = p[1]

    def p_calculation_expression_plus(self, p: P) -> None:
        """calculation_expression_plus : calculation_expression PLUS calculation_expression"""
        p[0] = p[1] + p[3]

    def p_calculation_expression_minus(self, p: P) -> None:
        """calculation_expression_minus : calculation_expression MINUS calculation_expression"""
        p[0] = p[1] - p[3]

    def p_calculation_expression_times(self, p: P) -> None:
        """calculation_expression_times : calculation_expression TIMES calculation_expression"""
        p[0] = p[1] * p[3]

    def p_calculation_expression_divide(self, p: P) -> None:
        """calculation_expression_divide : calculation_expression DIVIDE calculation_expression"""
        # NOTE: Both sides are integers and we output an integer too.
        p[0] = int(p[1] // p[3])

    def p_calculation_expression_group(self, p: P) -> None:
        """calculation_expression_group : '(' calculation_expression ')'"""
        p[0] = p[2]

    def p_constant_reference_for_calculation(self, p: P) -> None:
        """constant_reference_for_calculation : constant_reference"""
        if not isinstance(p[1], IntegerConstant):
            raise CalculationExpressionError(
                message="Non integer constant referenced to use in calculation expression.",
                filepath=self.current_filepath(),
                token=p[1].name,
                lineno=p.lineno(1),
            )
        p[0] = int(p[1])  # Using int format

    def _lookup_referenced_member(self, identifier: str) -> Optional[Definition]:
        """Lookup referenced defintion member in current bitproto.
          * When `identifier` contains dots: lookup from the root bitproto.
          * Otherwise, lookup from the scope stack reversively.
        """
        names = identifier.split(".")
        if len(names) > 1:  # Contains dots
            proto = self.current_proto()
            return proto.get_member(*names)
        else:  # No dot.
            for scope in self.current_scope_stack()[::-1]:
                d = scope.get_member(identifier)
                if d is not None:
                    return d
            return None

    def p_constant_reference(self, p: P) -> None:
        """constant_reference : IDENTIFIER"""
        d = self._lookup_referenced_member(p[1])
        if d and isinstance(d, Constant):
            p[0] = d
        else:
            raise ReferencedConstantNotDefined(
                message="referenced constant {0} not defined".format(p[1]),
                filepath=self.current_filepath(),
                token=p[1],
                lineno=p.lineno(1),
            )

    def p_type(self, p: P) -> None:
        """type : single_type
                | array_type"""
        p[0] = p[1]

    def p_single_type(self, p: P) -> None:
        """single_type : base_type
                       | type_reference"""
        p[0] = p[1]

    def p_base_type(self, p: P) -> None:
        """base_type : BOOL_TYPE
                     | UINT_TYPE
                     | INT_TYPE
                     | BYTE_TYPE"""
        p[0] = p[1]

    def p_type_reference(self, p: P) -> None:
        """type_reference : IDENTIFIER"""
        d = self._lookup_referenced_member(p[1])
        if d and isinstance(d, Type):
            p[0] = d
        else:
            raise ReferencedTypeNotDefined(
                message="referenced type {0} not defined".format(p[1]),
                filepath=self.current_filepath(),
                token=p[1],
                lineno=p.lineno(1),
            )

    def p_optional_extensible_flag(self, p: P) -> None:
        """optional_extensible_flag : "'"
                                    |"""
        p[0] = len(p) == 2

    def p_array_type(self, p: P) -> None:
        """array_type : single_type '[' array_capacity ']' optional_extensible_flag"""
        p[0] = Array(
            type=p[1],
            cap=p[3],
            extensible=p[5],
            token="{0}[{1}]".format(p[1], p[3]),
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
        )

    def p_array_capacity(self, p: P) -> None:
        """array_capacity : INT_LITERAL
                          | constant_reference_for_array_capacity"""
        p[0] = p[1]

    def p_constant_reference_for_array_capacity(self, p: P) -> None:
        """constant_reference_for_array_capacity : constant_reference"""
        if not isinstance(p[1], IntegerConstant):
            raise InvalidArrayCap(
                message="Non integer constant referenced to use as array capacity.",
                filepath=self.current_filepath(),
                token=p[1].name,
                lineno=p.lineno(1),
            )
        p[0] = int(p[1])  # Using int format

    def p_enum(self, p: P) -> None:
        """enum : open_enum_scope enum_scope close_enum_scope"""
        enum = p[2]
        self.current_scope().push_member(enum)

    def p_open_enum_scope(self, p: P) -> None:
        """open_enum_scope : ENUM IDENTIFIER optional_extensible_flag ':' UINT_TYPE '{'"""
        enum = Enum(
            name=p[2],
            type=p[5],
            extensible=p[3],
            token=p[2],
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
            comment_block=self.collect_comment_block(),
            scope_stack=self.current_scope_stack(),
        )
        self.push_scope(enum)

    def p_enum_scope(self, p: P) -> None:
        """enum_scope : enum_items"""
        p[0] = scope = self.current_scope()

    def p_close_enum_scope(self, p: P) -> None:
        """close_enum_scope : '}'"""
        self.pop_scope()

    def p_enum_items(self, p: P) -> None:
        """enum_items : enum_item enum_items
                      | enum_item
                      |"""
        self.util_parse_sequence(p)

    def p_enum_item(self, p: P) -> None:
        """enum_item : option
                     | enum_field
                     | comment
                     | newline"""
        p[0] = p[1]

    def p_enum_field(self, p: P) -> None:
        """enum_field : IDENTIFIER '=' INT_LITERAL optional_semicolon"""
        name = p[1]
        value = p[3]
        field = EnumField(
            name=name,
            value=value,
            token=p[1],
            lineno=p.lineno(1),
            filepath=self.current_filepath(),
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
        )
        self.current_scope().push_member(field)

    def p_message(self, p: P) -> None:
        """message : open_message_scope message_scope close_message_scope"""
        message = p[2]
        self.current_scope().push_member(message)

    def p_open_message_scope(self, p: P) -> None:
        """open_message_scope : MESSAGE IDENTIFIER optional_extensible_flag '{'"""
        message = Message(
            name=p[2],
            extensible=p[3],
            token=p[2],
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
            comment_block=self.collect_comment_block(),
            scope_stack=self.current_scope_stack(),
        )
        self.push_scope(message)

    def p_close_message_scope(self, p: P) -> None:
        """close_message_scope : '}'"""
        self.pop_scope()

    def p_message_scope(self, p: P) -> None:
        """message_scope : message_items"""
        p[0] = scope = self.current_scope()

    def p_message_items(self, p: P) -> None:
        """message_items : message_item message_items
                         | message_item
                         |"""
        self.util_parse_sequence(p)

    def p_message_item(self, p: P) -> None:
        """message_item : option
                        | enum
                        | message_field
                        | message
                        | comment
                        | newline"""
        p[0] = p[1]

    def p_message_field(self, p: P) -> None:
        """message_field : type IDENTIFIER '=' INT_LITERAL optional_semicolon"""
        name = p[2]
        type = p[1]
        field_number = p[4]
        message_field = MessageField(
            name=name,
            type=type,
            number=field_number,
            token=p[2],
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
            comment_block=self.collect_comment_block(),
            scope_stack=self.current_scope_stack(),
        )
        self.current_scope().push_member(message_field)

    def p_boolean_literal(self, p: P) -> None:
        """boolean_literal : BOOL_LITERAL"""
        p[0] = p[1]

    def p_integer_literal(self, p: P) -> None:
        """integer_literal : INT_LITERAL
                           | HEX_LITERAL"""
        p[0] = p[1]

    def p_string_literal(self, p: P) -> None:
        """string_literal : STRING_LITERAL"""
        p[0] = p[1]

    def p_error(self, p: P) -> None:
        handle = self.current_handle()
        if p is None:
            raise GrammarError(
                message="Grammar error at eof.", filepath=handle.filepath
            )
        if isinstance(p, LexToken):
            raise GrammarError(
                filepath=handle.filepath, token=str(p.value), lineno=p.lineno
            )
        if len(p) <= 1:
            raise GrammarError()
        else:
            raise GrammarError(
                filepath=handle.filepath, token=p.value(1), lineno=p.lineno(1)
            )


def parse(filepath: str) -> Proto:
    """Parse a bitproto from given filepath."""
    return Parser().parse(filepath)
