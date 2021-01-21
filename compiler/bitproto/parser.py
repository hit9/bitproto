"""
bitproto.parser
~~~~~~~~~~~~~~~

Grammar parser for bitproto.
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Iterator, List, Optional, Tuple
from typing import Type as T
from typing import cast

from ply import yacc  # type: ignore
from ply.lex import LexToken  # type: ignore
from ply.yacc import LRParser as PlyParser  # type: ignore
from ply.yacc import YaccProduction as P  # type: ignore

from bitproto._ast import (Alias, Array, BooleanConstant, Comment, Constant,
                           Definition, Enum, EnumField, IntegerConstant,
                           Message, MessageField, Option, Proto, Scope,
                           StringConstant, Type)
from bitproto.errors import (AliasInEnumUnsupported, AliasInMessageUnsupported,
                             CalculationExpressionError,
                             ConstInEnumUnsupported, ConstInMessageUnsupported,
                             CyclicImport, DuplicatedDefinition,
                             DuplicatedImport, EnumInEnumUnsupported,
                             GrammarError, ImportInEnumUnsupported,
                             ImportInMessageUnsupported, InternalError,
                             InvalidArrayCap, MessageFieldInEnumUnsupported,
                             MessageInEnumUnsupported, OptionInEnumUnsupported,
                             ProtoNameUndefined, ReferencedConstantNotDefined,
                             ReferencedNotConstant, ReferencedNotType,
                             ReferencedTypeNotDefined,
                             StatementInMessageUnsupported,
                             UnsupportedToDeclareProtoNameOutofProtoScope)
from bitproto.lexer import Lexer
from bitproto.utils import cast_or_raise, write_stderr


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

    def __init__(
        self,
        scope_stack: Optional[List[Scope]] = None,
        filepath_stack: Optional[List[str]] = None,
        comment_block: Optional[List[Comment]] = None,
    ) -> None:
        self.lexer: Lexer = Lexer(filepath_stack=filepath_stack)
        self.parser: PlyParser = yacc.yacc(
            module=self, start="start", debug=False, write_tables=False
        )
        self.scope_stack: List[Scope] = scope_stack or []
        self.filepath_stack: List[str] = filepath_stack or []
        self.comment_block: List[Comment] = comment_block or []
        self.scope_stack_init_length: int = len(self.scope_stack)
        self.last_newline_pos: int = 0

    def push_scope(self, scope: Scope) -> None:
        self.scope_stack.append(scope)

    def pop_scope(self) -> Scope:
        return self.scope_stack.pop()

    def current_scope(self) -> Scope:
        assert self.scope_stack, InternalError("Empty scope_stack")
        return self.scope_stack[-1]

    def current_proto(self) -> Proto:
        index = self.scope_stack_init_length
        assert index < len(self.scope_stack), InternalError("Determining current_proto")
        return cast(Proto, self.scope_stack[index])

    def current_scope_stack(self) -> Tuple[Scope, ...]:
        return tuple(self.scope_stack)

    def scope_stack_in_current_proto(self) -> Tuple[Scope, ...]:
        start = self.scope_stack_init_length
        return tuple(self.scope_stack[start:])

    def clear_comment_block(self) -> None:
        self.comment_block = []

    def push_comment(self, comment: Comment) -> None:
        self.comment_block.append(comment)

    def collect_comment_block(self) -> Tuple[Comment, ...]:
        comment_block = tuple(self.comment_block)
        self.clear_comment_block()
        return comment_block

    def current_filepath(self) -> str:
        assert self.filepath_stack, InternalError("Empty filepath_stack")
        return self.filepath_stack[-1]

    def push_filepath(self, filepath: str) -> None:
        self.filepath_stack.append(filepath)

    def pop_filepath(self) -> str:
        return self.filepath_stack.pop()

    def set_last_newline_pos(self, pos: int) -> None:
        self.last_newline_pos = pos

    def current_indent(self, p: P, i: int = 1) -> int:
        lexpos = p.lexpos(i)
        indent = lexpos - self.last_newline_pos - 1
        if indent < 0:
            return -1
        return indent

    @contextmanager
    def maintain_filepath(self, filepath: str) -> Iterator[str]:
        try:
            self.push_filepath(filepath)
            yield filepath
        finally:
            self.pop_filepath()

    def parse_string(self, s: str, filepath: str = "") -> Proto:
        """Parse a bitproto from given string `s`.
        :param filepath: The filepath information if exist.
        """
        with self.lexer.maintain_filepath(filepath):
            with self.maintain_filepath(filepath):
                return self.parser.parse(s)

    def parse(self, filepath: str) -> Proto:
        """Parse a bitproto from given file."""
        with open(filepath) as f:
            return self.parse_string(f.read(), filepath=filepath)

    def parse_child(self, filepath: str) -> Proto:
        """Parse a child bitproto from given file.
        Child parsing references current parser's internal states.
        """
        return Parser(
            scope_stack=self.scope_stack,
            filepath_stack=self.filepath_stack,
            comment_block=self.comment_block,
        ).parse(filepath)

    def util_parse_sequence(self, p: P) -> None:
        if len(p) == 3:
            p[0] = [p[1]] + p[2]
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 1:
            p[0] = []

    def copy_p_tracking(self, p: P, from_: int = 1, to: int = 0) -> None:
        """Don't know why P's tracking info (lexpos and lineno) sometimes missing.
        Particular in recursion grammar situation. We have to copy it manually.

        Add this function in a p_xxx function when:
            1. the p[0] is gona to be used in another parsing target.
            2. and the tracking information is gona to be used there.
        """
        p.set_lexpos(to, p.lexpos(from_))
        p.set_lineno(to, p.lineno(from_))

    def p_optional_semicolon(self, p: P) -> None:
        """optional_semicolon : ';'
                              |"""
        p[0] = None

    def p_start(self, p: P) -> None:
        """start : open_global_scope global_scope close_global_scope"""
        p[0] = p[2]

    def p_open_global_scope(self, p: P) -> None:
        """open_global_scope : """
        proto = Proto(
            filepath=self.current_filepath(),
            _bound=None,
            scope_stack=self.current_scope_stack(),
        )
        self.push_scope(proto)

    def p_close_global_scope(self, p: P) -> None:
        """close_global_scope :"""
        scope = self.pop_scope()
        proto = cast_or_raise(Proto, scope)
        if not proto.name:
            raise ProtoNameUndefined(filepath=self.current_filepath())
        proto.freeze()

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
        scope = self.current_scope()
        if isinstance(scope, Proto):
            proto = cast(Proto, self.current_scope())
            proto.set_name(p[2])
            proto.set_comment_block(self.collect_comment_block())
        else:
            raise UnsupportedToDeclareProtoNameOutofProtoScope(
                lineno=p.lineno(1), filepath=self.current_filepath()
            )

    def p_comment(self, p: P) -> None:
        """comment : COMMENT NEWLINE"""
        comment = p[1]
        self.push_comment(comment)
        self.set_last_newline_pos(p.lexpos(2))

    def p_newline(self, p: P) -> None:
        """newline : NEWLINE"""
        self.clear_comment_block()
        self.set_last_newline_pos(p.lexpos(1))

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
        for filepath_ in self.filepath_stack:
            if os.path.samefile(filepath, filepath_):
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

        # Check if this filepath already parsed by current proto.
        for _, proto in self.current_proto().protos(recursive=False):
            if os.path.samefile(proto.filepath, filepath):
                raise DuplicatedImport(
                    filepath=self.current_filepath(), token=filepath, lineno=p.lineno(1)
                )

        # Parse.
        p[0] = child = self.parse_child(filepath)
        name = child.name
        if len(p) == 5:  # Importing as `name`
            name = p[2]

        # Check if import (as) name already taken.
        if name in self.current_proto().members:
            raise DuplicatedDefinition(
                message="imported proto name already used",
                token=name,
                lineno=p.lineno(1),
                filepath=self.current_filepath(),
            )

        # Push to current scope
        self.current_scope().push_member(child, name)

    def p_option(self, p: P) -> None:
        """option : OPTION dotted_identifier '=' option_value optional_semicolon"""
        name, value = p[2], p[4]
        p[0] = option = Option.from_value(
            value=value,
            name=name,
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
            indent=self.current_indent(p),
            _bound=self.current_proto(),
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
        """alias : TYPE IDENTIFIER '=' type optional_semicolon
                 | TYPEDEF type IDENTIFIER optional_semicolon"""

        if len(p) == 6:
            name, type, lineno, token = p[2], p[4], p.lineno(2), p[2]
        else:
            name, type, lineno, token = p[3], p[2], p.lineno(3), p[3]
            write_stderr(
                f"syntax warning: keyword typedef deprecated, suggestion: type {name} = ..."
            )

        p[0] = alias = Alias(
            name=name,
            type=type,
            filepath=self.current_filepath(),
            lineno=lineno,
            token=token,
            indent=self.current_indent(p),
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
            _bound=self.current_proto(),
        )
        self.current_scope().push_member(alias)

    def p_const(self, p: P) -> None:
        """const : CONST IDENTIFIER '=' const_value optional_semicolon"""

        name, value = p[2], p[4]

        constant_cls: Optional[T[Constant]] = None

        if isinstance(value, Constant):
            constant_ = cast(Constant, value)
            # Unwrap if value is a referenced constant.
            value = constant_.unwrap()

        p[0] = constant = Constant.from_value(
            value=value,
            name=name,
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
            indent=self.current_indent(p),
            _bound=self.current_proto(),
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
        referenced = p[1]
        if isinstance(referenced, IntegerConstant):
            integer_constant = cast(IntegerConstant, referenced)
            p[0] = integer_constant.unwrap()
        else:
            raise CalculationExpressionError(
                message="Non integer constant referenced to use in calculation expression.",
                filepath=self.current_filepath(),
                token=p[1].name,
                lineno=p.lineno(1),
            )

    def _lookup_referenced_member(self, identifier: str) -> Optional[Definition]:
        """Lookup referenced defintion member in current bitproto.
          * When `identifier` contains dots: lookup from its bitproto.
          * Otherwise, lookup from the scope stack reversively (in current proto).
        """
        names = identifier.split(".")

        for scope in self.scope_stack_in_current_proto()[::-1]:
            # Lookup in scopes bound to current proto reversively.
            d = scope.get_member(*names)
            if d is not None:
                return d
        return None

    def p_constant_reference(self, p: P) -> None:
        """constant_reference : dotted_identifier"""
        d = self._lookup_referenced_member(p[1])
        if d is None:
            raise ReferencedConstantNotDefined(
                message="referenced constant {0} not defined".format(p[1]),
                filepath=self.current_filepath(),
                token=p[1],
                lineno=p.lineno(1),
            )
        if not isinstance(d, Constant):
            raise ReferencedNotConstant(
                message="referenced defintion is not a constant",
                filepath=self.current_filepath(),
                token=p[1],
                lineno=p.lineno(1),
            )

        p[0] = d
        self.copy_p_tracking(p)

    def p_type(self, p: P) -> None:
        """type : single_type
                | array_type"""
        p[0] = p[1]
        self.copy_p_tracking(p)

    def p_single_type(self, p: P) -> None:
        """single_type : base_type
                       | type_reference"""
        p[0] = p[1]
        self.copy_p_tracking(p)

    def p_base_type(self, p: P) -> None:
        """base_type : BOOL_TYPE
                     | UINT_TYPE
                     | INT_TYPE
                     | BYTE_TYPE"""
        p[0] = p[1]
        self.copy_p_tracking(p)

    def p_type_reference(self, p: P) -> None:
        """type_reference : dotted_identifier"""
        d = self._lookup_referenced_member(p[1])
        if d is None:
            raise ReferencedTypeNotDefined(
                message="referenced type {0} not defined".format(p[1]),
                filepath=self.current_filepath(),
                token=p[1],
                lineno=p.lineno(1),
            )
        if not isinstance(d, Type):
            raise ReferencedNotType(
                message="referenced defintion is not a type",
                filepath=self.current_filepath(),
                token=p[1],
                lineno=p.lineno(1),
            )
        p[0] = d
        self.copy_p_tracking(p)

    def p_optional_extensible_flag(self, p: P) -> None:
        """optional_extensible_flag : "'"
                                    |"""
        p[0] = len(p) == 2

    def p_array_type(self, p: P) -> None:
        """array_type : single_type '[' array_capacity ']' optional_extensible_flag"""
        p[0] = Array(
            element_type=p[1],
            cap=p[3],
            extensible=p[5],
            token="{0}[{1}]".format(p[1], p[3]),
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
        )
        self.copy_p_tracking(p)

    def p_array_capacity(self, p: P) -> None:
        """array_capacity : INT_LITERAL
                          | constant_reference_for_array_capacity"""
        p[0] = p[1]

    def p_constant_reference_for_array_capacity(self, p: P) -> None:
        """constant_reference_for_array_capacity : constant_reference"""
        referenced = p[1]
        if isinstance(referenced, IntegerConstant):
            integer_constant = cast(IntegerConstant, referenced)
            p[0] = integer_constant.unwrap()  # Using int format
        else:
            raise InvalidArrayCap(
                message="Non integer constant referenced to use as array capacity.",
                filepath=self.current_filepath(),
                token=p[1].name,
                lineno=p.lineno(1),
            )

    def p_enum(self, p: P) -> None:
        """enum : open_enum_scope enum_scope close_enum_scope"""
        p[0] = enum = p[2]
        self.current_scope().push_member(enum)
        self.copy_p_tracking(p)

    def p_open_enum_scope(self, p: P) -> None:
        """open_enum_scope : ENUM IDENTIFIER optional_extensible_flag ':' UINT_TYPE '{'"""
        enum = Enum(
            name=p[2],
            type=p[5],
            extensible=p[3],
            token=p[2],
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
            indent=self.current_indent(p),
            comment_block=self.collect_comment_block(),
            scope_stack=self.current_scope_stack(),
            _bound=self.current_proto(),
        )
        self.push_scope(enum)

    def p_enum_scope(self, p: P) -> None:
        """enum_scope : enum_items"""
        p[0] = scope = self.current_scope()

    def p_close_enum_scope(self, p: P) -> None:
        """close_enum_scope : '}'"""
        self.pop_scope().freeze()

    def p_enum_items(self, p: P) -> None:
        """enum_items : enum_item enum_items
                      | enum_item
                      |"""
        self.util_parse_sequence(p)

    def p_enum_item(self, p: P) -> None:
        """enum_item : enum_field
                     | enum_item_unsupported
                     | comment
                     | newline"""
        p[0] = p[1]

    def p_enum_item_unsupported(self, p: P) -> None:
        """enum_item_unsupported : alias
                                 | const
                                 | proto
                                 | import
                                 | option
                                 | enum
                                 | message
                                 | message_field"""
        if isinstance(p[1], Alias):
            raise AliasInEnumUnsupported.from_token(token=p[1])
        if isinstance(p[1], Constant):
            raise ConstInEnumUnsupported.from_token(token=p[1])
        if isinstance(p[1], Proto):
            raise ImportInEnumUnsupported.from_token(token=p[1])
        if isinstance(p[1], Option):
            raise OptionInEnumUnsupported.from_token(token=p[1])
        if isinstance(p[1], Enum):
            raise EnumInEnumUnsupported.from_token(token=p[1])
        if isinstance(p[1], Message):
            raise MessageInEnumUnsupported.from_token(token=p[1])
        if isinstance(p[1], MessageField):
            raise MessageFieldInEnumUnsupported.from_token(token=p[1])
        raise StatementInMessageUnsupported(
            lineno=p.lineno(1), filepath=self.current_filepath()
        )

    def p_enum_field(self, p: P) -> None:
        """enum_field : IDENTIFIER '=' INT_LITERAL optional_semicolon"""
        name = p[1]
        value = p[3]
        field = EnumField(
            name=name,
            value=value,
            token=p[1],
            lineno=p.lineno(1),
            indent=self.current_indent(p),
            filepath=self.current_filepath(),
            scope_stack=self.current_scope_stack(),
            comment_block=self.collect_comment_block(),
            _bound=self.current_proto(),
        )
        self.current_scope().push_member(field)

    def p_message(self, p: P) -> None:
        """message : open_message_scope message_scope close_message_scope"""
        p[0] = message = p[2]
        self.current_scope().push_member(message)
        self.copy_p_tracking(p)

    def p_open_message_scope(self, p: P) -> None:
        """open_message_scope : MESSAGE IDENTIFIER optional_extensible_flag '{'"""
        message = Message(
            name=p[2],
            extensible=p[3],
            token=p[2],
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
            indent=self.current_indent(p),
            comment_block=self.collect_comment_block(),
            scope_stack=self.current_scope_stack(),
            _bound=self.current_proto(),
        )
        self.push_scope(message)

    def p_close_message_scope(self, p: P) -> None:
        """close_message_scope : '}'"""
        self.pop_scope().freeze()

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
                        | message_item_unsupported
                        | comment
                        | newline"""
        p[0] = p[1]

    def p_message_item_unsupported(self, p: P) -> None:
        """message_item_unsupported : alias
                                    | const
                                    | proto
                                    | import"""
        if isinstance(p[1], Alias):
            raise AliasInMessageUnsupported.from_token(token=p[1])
        if isinstance(p[1], Constant):
            raise ConstInMessageUnsupported.from_token(token=p[1])
        if isinstance(p[1], Proto):
            raise ImportInMessageUnsupported.from_token(token=p[0])
        raise StatementInMessageUnsupported(
            lineno=p.lineno(1), filepath=self.current_filepath()
        )

    def p_message_field(self, p: P) -> None:
        """message_field : type IDENTIFIER '=' INT_LITERAL optional_semicolon"""
        name = p[2]
        type = p[1]
        field_number = p[4]
        p[0] = message_field = MessageField(
            name=name,
            type=type,
            number=field_number,
            token=p[2],
            lineno=p.lineno(2),
            filepath=self.current_filepath(),
            comment_block=self.collect_comment_block(),
            indent=self.current_indent(p),
            scope_stack=self.current_scope_stack(),
            _bound=self.current_proto(),
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

    def p_dotted_identifier(self, p: P) -> None:
        """dotted_identifier : IDENTIFIER '.' dotted_identifier
                             | IDENTIFIER"""

        self.copy_p_tracking(p)
        if len(p) == 4:
            p[0] = ".".join([p[1], p[3]])
        elif len(p) == 2:
            p[0] = p[1]

    def p_error(self, p: P) -> None:
        filepath = self.current_filepath()
        if p is None:
            raise GrammarError(message="Grammar error at eof.", filepath=filepath)
        if isinstance(p, LexToken):
            raise GrammarError(filepath=filepath, token=str(p.value), lineno=p.lineno)
        if len(p) > 1:
            raise GrammarError(filepath=filepath, token=p.value(1), lineno=p.lineno(1))
        raise GrammarError()


def parse(filepath: str) -> Proto:
    """Parse a bitproto from given filepath."""
    return Parser().parse(filepath)
