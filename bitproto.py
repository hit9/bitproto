"""
bitproto
~~~~~~~~

Bit level data interchange format.

:copyright: (c) 2020 by Chao Wang <hit9@icloud.com>
"""


from contextlib import contextmanager
from dataclasses import dataclass, field as dataclass_field
from collections import OrderedDict
from typing import (
    TypeVar,
    Tuple,
    Union,
    Optional,
    Dict,
    Type as T,
    List,
    Iterator,
)

from ply import lex, yacc
from ply.lex import LexToken
from ply.yacc import YaccProduction as P, LRParser as PlyParser

__version__ = "0.1.0"
__repository__ = "https://github.com/hit9/bitproto"

###
# Errors
###


@dataclass
class Error(Exception):
    """Some error occurred during bitproto handling."""

    description: str = ""

    def __post_init__(self) -> None:
        if not self.description:
            self.description = self.format_default_description()

    def format_default_description(self) -> str:
        return self.__doc__ or ""

    def __str__(self) -> str:
        return self.description


@dataclass
class InternalError(Error):
    f"""Some internal error occurred in bitproto,
    please open an issue at {__repository__}"""


@dataclass
class ParserError(Error):
    """Some error occurred during bitproto parsing."""

    message: str = ""
    filepath: str = ""
    token: str = ""
    lineno: int = 0

    def format_default_description(self) -> str:
        message = self.message or self.__doc__
        return f"{self.filepath}:L{self.lineno}:{self.token}: {message}"


@dataclass
class LexerError(ParserError):
    """Some token error occurred during bitproto lexing."""


@dataclass
class GrammarError(ParserError):
    """Some grammar error occurred during bitproto grammar parsing."""


@dataclass
class InvalidUintCap(LexerError):
    """Invalid bits capacity for a uint type."""


@dataclass
class InvalidIntCap(LexerError):
    """Invalid bits capacity for a int type, only 8,16,32,64 are supported."""


@dataclass
class UnsupportedArrayType(LexerError):
    """Unsupported type to construct an array type."""


@dataclass
class InvalidEscapingChar(LexerError):
    """Unsupported escaping character."""


@dataclass
class CalculationExpressionError(GrammarError):
    """Some error occurred during calculation expression parsing."""


@dataclass
class InvalidArrayCap(GrammarError):
    """Invalid array capacity."""


###
# AST
###


@dataclass
class Node:

    token: str = ""
    lineno: int = 0
    position: int = 0
    filepath: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        pass


@dataclass
class Newline(Node):
    def __str__(self) -> str:
        return self.token


@dataclass
class Comment(Node):
    def content(self) -> str:
        """Returns the stripped content of this comment, without the starting slashes."""
        return self.token[2:].strip()

    def __str__(self) -> str:
        return self.content()


@dataclass
class Importer(Node):
    pass


@dataclass
class Definition(Node):
    scope_stack: Tuple["Scope", ...] = tuple()
    breadth: int = 0
    comment_block: Tuple[Comment, ...] = tuple()

    def docstring(self) -> str:
        """Returns the comment block in string format."""
        return "\n".join(str(c) for c in self.comment_block)


@dataclass
class Option(Definition):

    value: Union[str, int, bool, None] = None


@dataclass
class IntegerOption(Option):
    value: int = 0


@dataclass
class BooleanOption(Option):
    value: bool = False


@dataclass
class StringOption(Option):
    value: str = ""


@dataclass
class Constant(Definition):
    value: Union[str, int, bool, None] = None

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Constant):
            return False
        return self.value == o.value

    def __ne__(self, o: object) -> bool:
        return not (self == o)

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class IntegerConstant(Constant):
    value: int = 0

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, IntegerConstant):
            return False
        return self.value == o.value

    def __int__(self) -> int:
        return self.value


@dataclass
class BooleanConstant(Constant):
    value: bool = False

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, BooleanConstant):
            return False
        return self.value == o.value


@dataclass
class StringConstant(Constant):
    value: str = ""

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, StringConstant):
            return False
        return self.value == o.value


@dataclass
class Scope(Definition):
    members: OrderedDict[str, Definition] = dataclass_field(default_factory=OrderedDict)


@dataclass
class Template(Scope):
    name: str = ""
    lang: str = ""
    content: str = ""


@dataclass
class Type(Node):
    def nbits(self) -> int:
        raise NotImplementedError

    def nbytes(self) -> int:
        nbits = self.nbits()
        if nbits % 8 == 0:
            return int(nbits / 8)
        return int(nbits / 8) + 1


@dataclass
class Bool(Type):
    def nbits(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "bool"


@dataclass
class Byte(Type):
    def nbits(self) -> int:
        return 8

    def __repr__(self) -> str:
        return "byte"


@dataclass
class Uint(Type):
    cap: int = 0

    def validate(self) -> None:
        if self.cap <= 0 or self.cap > 64:
            raise InvalidUintCap(
                filepath=self.filepath, token=self.token, lineno=self.lineno
            )

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "uint{0}".format(self.cap)


@dataclass
class Int(Type):
    cap: int = 0

    def validate(self) -> None:
        if self.cap not in (8, 16, 32, 64):
            raise InvalidIntCap(
                filepath=self.filepath, token=self.token, lineno=self.lineno
            )

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "int{0}".format(self.cap)


@dataclass
class Array(Type):
    type: Optional[Type] = None
    cap: int = 0

    @property
    def supported_types(self) -> Tuple[T[Type], ...]:
        return (Bool, Byte, Int, Uint, Enum, Message, Alias)

    def validate(self) -> None:
        if self.type is None:
            raise InternalError(description="No type to construct an array type")
        if not isinstance(self.type, self.supported_types):
            raise UnsupportedArrayType(
                filepath=self.filepath, token=self.token, lineno=self.lineno
            )

    def nbits(self) -> int:
        if self.type is None:
            return 0
        return self.cap * self.type.nbits()


@dataclass
class Alias(Type):
    pass


@dataclass
class Field(Definition):
    pass


@dataclass
class EnumField(Field):
    pass


@dataclass
class Enum(Type, Scope):
    pass


@dataclass
class MessageFiled(Field):
    pass


@dataclass
class Message(Type, Scope):
    pass


@dataclass
class Proto(Type, Scope):
    name: str = ""

    def set_name(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<bitproto (name={self.name})>"


class Lexer:
    """Lexer for bitproto.

        >>> lexer = Lexer()
        >>> lexer.input("uint3 field")
        >>> lexer.token()
        LexToken(UINT_TYPE, uint3, 1, 0)

    """

    # Ignore whitespaces.
    t_ignore: str = " \t\r"

    # Literal symbols
    literals: str = ":;{}[]()=\\."

    # Reversed keywords
    keywords: Tuple[str, ...] = (
        "proto",
        "import",
        "option",
        "type",
        "const",
        "enum",
        "message",
        "template",
        "render",
    )
    keywords_tokens = tuple(map(lambda keyword: keyword.upper(), keywords))

    # Tokens
    tokens: Tuple[str, ...] = (
        # Misc
        "NEWLINE",
        "COMMENT",
        # Template
        "TEMPLATELINE",
        # Operators
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        # Types
        "BOOL_TYPE",
        "UINT_TYPE",
        "INT_TYPE",
        "BYTE_TYPE",
        # Literals
        "HEX_LITERAL",
        "INT_LITERAL",
        "BOOL_LITERAL",
        "STRING_LITERAL",
        # IDENTIFIER
        "IDENTIFIER",
    ) + keywords_tokens

    # Supported escaping characters in strings.
    escaping_chars: Dict[str, str] = {
        "t": "\t",
        "r": "\r",
        "n": "\n",
        "\\": "\\",
        "'": "'",
        '"': '"',
    }

    # Expression operators.
    t_PLUS: str = r"\+"
    t_MINUS: str = r"-"
    t_TIMES: str = r"\*"
    t_DIVIDE: str = r"/"

    def __init__(self) -> None:
        self.lexer = lex.lex(object=self)
        self.filepath: str = ""

    def set_filepath(self, filepath: str) -> str:
        self.filepath = filepath
        return self.filepath

    def clear_filepath(self) -> None:
        self.filepath = ""

    @contextmanager
    def maintain_filepath(self, filepath: str) -> Iterator[str]:
        try:
            yield self.set_filepath(filepath)
        finally:
            self.clear_filepath()

    def token(self) -> Optional[LexToken]:
        """Returns the next token lexed.
        Returns `None` if no token is lexed."""
        return self.lexer.token()

    def input(self, s: str) -> None:
        """Inputs a string to this lexer."""
        self.lexer.input(s)

    def t_error(self, t: LexToken) -> None:
        raise LexerError(
            message="Invalid token",
            filepath=self.filepath,
            token=t.value[0],
            lineno=t.lexer.lineno,
        )

    def t_newline(self, t: LexToken) -> LexToken:
        r"\n"
        t.lexer.lineno += 1
        t.type = "NEWLINE"
        t.value = Newline(
            token=t.value, lineno=t.lineno, position=t.lexpos, filepath=self.filepath
        )
        return t

    def t_COMMENT(self, t: LexToken) -> LexToken:
        r"\/\/[^\n]*"
        t.value = Comment(
            token=t.value, position=t.lexpos, lineno=t.lineno, filepath=self.filepath
        )
        return t

    def t_TEMPLATELINE(self, t: LexToken) -> LexToken:
        r"\\[^\n]*"
        t.value = t.value[1:]
        return t

    def t_BOOL_TYPE(self, t: LexToken) -> LexToken:
        r"\bbool\b"
        t.value = Bool(
            token=t.value, position=t.lexpos, lineno=t.lineno, filepath=self.filepath
        )
        return t

    def t_UINT_TYPE(self, t: LexToken) -> LexToken:
        r"\buint[0-9]+\b"
        cap: int = int(t.value[4:])  # uint{n}
        t.value = Uint(
            cap=cap,
            token=t.value,
            position=t.lexpos,
            lineno=t.lineno,
            filepath=self.filepath,
        )
        return t

    def t_INT_TYPE(self, t: LexToken) -> LexToken:
        r"\bint[0-9]+\b"
        # Why use the regexp `int[0-9]+` instead of `int(8|16|32|64)`?
        # We want the unsupported cases like `int0`, `int3` to raise an error instead of
        # lexing into identifiers.
        cap: int = int(t.value[3:])
        t.value = Int(
            cap=cap,
            token=t.value,
            position=t.lexpos,
            lineno=t.lineno,
            filepath=self.filepath,
        )
        return t

    def t_BYTE_TYPE(self, t: LexToken) -> LexToken:
        r"\bbyte\b"
        t.value = Byte(
            token=t.value, position=t.lexpos, lineno=t.lineno, filepath=self.filepath
        )
        return t

    def t_HEX_LITERAL(self, t: LexToken) -> LexToken:
        r"0x[0-9a-fA-F]+"
        t.value = int(t.value, 16)
        return t

    def t_INT_LITERAL(self, t: LexToken) -> LexToken:
        r"[0-9]+"
        # NOTE: Currently only non-negative integers are supported.
        # FIXME Negative integers?
        t.value = int(t.value)
        return t

    def t_BOOL_LITERAL(self, t: LexToken) -> LexToken:
        r"\b(true|false|yes|no)\b"
        t.value = t.value in ("true", "yes")
        return t

    def t_IDENTIFIER(self, t: LexToken) -> LexToken:
        r"\b[a-zA-Z_]([a-zA-Z_0-9])*\b"
        # This rule may match a keyword.
        if t.value in Lexer.keywords:
            # Converts the matched token to the keyword type
            t.type = t.value.upper()
            return t
        return t

    def t_STRING_LITERAL(self, t: LexToken) -> LexToken:
        r"\"([^\\\n]|(\\.))*?\""
        s: str = t.value[1:-1]

        # Escaping.
        i: int = 0
        val: str = ""
        while i < len(s):
            if s[i] == "\\":  # A single slash '\'
                i += 1
                if s[i] in Lexer.escaping_chars:
                    val += Lexer.escaping_chars[s[i]]
                else:
                    raise InvalidEscapingChar(
                        token=t.value, filepath=self.filepath, lineno=t.lexer.lineno
                    )
            else:
                val += s[i]
            i += 1
        t.value = val
        return t


###
# Parser
###


@dataclass
class ParserHandle:
    """Parsing context holder."""

    filepath: str
    breadth: int = 0  # Current walking breadth in the current scope.
    scope_stack: List[Scope] = dataclass_field(default_factory=list)
    comment_block: List[Comment] = dataclass_field(default_factory=list)

    def breadth_up(self) -> int:
        self.breadth += 1
        return self.breadth

    def breadth_down(self) -> int:
        self.breadth -= 1
        return self.breadth

    def push_scope(self, scope: Scope) -> Scope:
        self.scope_stack.append(scope)
        return scope

    def pop_scope(self) -> Scope:
        return self.scope_stack.pop()

    def current_scope(self) -> Scope:
        return self.scope_stack[-1]

    def scope_stack_tuple(self) -> Tuple[Scope, ...]:
        return tuple(self.scope_stack)

    def current_proto(self) -> Proto:
        assert isinstance(self.scope_stack[0], Proto), InternalError(
            "First scope in stack not a Proto instance"
        )
        return self.scope_stack[0]

    def push_comment(self, comment: Comment) -> Comment:
        self.comment_block.append(comment)
        return comment

    def clear_comment_block(self) -> Tuple[Comment, ...]:
        block = self.comment_block[:]
        self.comment_block = []
        return tuple(block)


class Parser:
    """Parser for bitproto.

        >>> parser = Parser()
        >>> parser.parse("path/to/example.bitproto")
        <bitproto (name="example")>

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
            module=self, debug=debug, write_tables=write_tables
        )

    def push_handle(self, handle: ParserHandle) -> ParserHandle:
        self.handle_stack.append(handle)
        return handle

    def pop_handle(self) -> ParserHandle:
        return self.handle_stack.pop()

    def current_handle(self) -> Optional[ParserHandle]:
        if len(self.handle_stack) > 0:
            return self.handle_stack[-1]
        return None

    def current_handle_or_raise(self) -> ParserHandle:
        """Gets not `None` handle during the parsing."""
        handle = self.current_handle()
        assert handle, InternalError("ParserHandle is None during parsing")
        return handle

    @contextmanager
    def maintain_handle(self, handle: ParserHandle) -> Iterator[ParserHandle]:
        try:
            yield self.push_handle(handle)
        finally:
            self.pop_handle()

    def parse_string(self, s: str, filepath: str = "") -> Proto:
        """Parse a bitproto from given string `s`.
        :param filepath: The filepath information if exist.
        """
        with self.lexer.maintain_filepath(filepath):
            with self.maintain_handle(ParserHandle(filepath)):
                return self.parser.parse(s)

    def parse(self, filepath: str) -> Proto:
        """Parse a bitproto from given file."""
        with open(filepath) as f:
            return self.parse_string(f.read())

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
        p[0] = p[1]

    def p_open_global_scope(self, p: P) -> None:
        """open_global_scope :"""
        handle = self.current_handle_or_raise()
        handle.breadth_up()
        scope = Proto(
            filepath=handle.filepath,
            breadth=handle.breadth,
            scope_stack=handle.scope_stack_tuple(),
        )
        handle.push_scope(scope)
        handle.breadth_down()
        p[0] = scope

    def p_close_global_scope(self, p: P) -> None:
        """close_global_scope :"""
        handle = self.current_handle_or_raise()
        handle.pop_scope()
        # FIXME: proto.validate?

    def p_global_scope(self, p: P) -> None:
        """global_scope : proto_namer global_scope_definitions"""

    def p_proto_namer(self, p: P) -> None:
        """proto_namer : PROTO IDENTIFIER optional_semicolon"""
        p[0] = proto_name = p[2]
        handle = self.current_handle_or_raise()
        proto = handle.current_proto()
        proto.set_name(proto_name)

    def p_global_scope_definitions(self, p: P) -> None:
        """global_scope_definitions : global_scope_definition_unit global_scope_definitions
                                    | global_scope_definition_unit
                                    |"""
        self.util_parse_sequence(p)

    def p_global_scope_definition_unit(self, p: P) -> None:
        """global_scope_definition_unit : importer
                                        | option
                                        | alias
                                        | const
                                        | template
                                        | enum
                                        | message
                                        | comment
                                        | newline"""
        p[0] = p[1]

    def p_comment(self, p: P) -> None:
        """comment : COMMENT NEWLINE"""
        p[0] = self.current_handle_or_raise().push_comment(p[1])

    def p_newline(self, p: P) -> None:
        """newline : NEWLINE"""
        p[0] = p[1]
        self.current_handle_or_raise().clear_comment_block()  # FIXME: why clear?

    def p_importer(self, p: P) -> None:
        """importer : IMPORT STRING_LITERAL optional_semicolon
                    | IMPORT IDENTIFIER STRING_LITERAL optional_semicolon"""
        pass  # TODO

    def p_option(self, p: P) -> None:
        """option : OPTION IDENTIFIER '=' option_value optional_semicolon"""
        pass

    def p_option_value(self, p: P) -> None:
        """option_value : boolean_literal
                        | integer_literal
                        | string_literal"""
        p[0] = p[1]

    def p_alias(self, p: P) -> None:
        """alias : TYPE IDENTIFIER '=' type optional_semicolon"""
        pass

    def p_const(self, p: P) -> None:
        """const : CONST IDENTIFIER '=' const_value optional_semicolon"""
        pass

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
                filepath=self.current_handle_or_raise().filepath,
                token=p[1].name,
                lineno=p.lineno(1),
            )
        # Using int format version of this IntegerConstant.
        p[0] = int(p[1])

    def p_constant_reference_for_array_capacity(self, p: P) -> None:
        """constant_reference_for_array_capacity : constant_reference"""
        if not isinstance(p[1], IntegerConstant):
            raise InvalidArrayCap(
                message="Non integer constant referenced to use as array capacity.",
                filepath=self.current_handle_or_raise().filepath,
                token=p[1].name,
                lineno=p.lineno(1),
            )
        # Using int format version of this IntegerConstant.
        p[0] = int(p[1])

    def p_constant_reference(self, p: P) -> None:
        """constant_reference : IDENTIFIER"""
        # TODO

    def p_type(self, p: P) -> None:
        """type : single_type
                | array_type"""
        p[0] = p[1]

    def p_single_type(self, p: P) -> None:
        """single_type : base_type
                       | type_reference"""

    def p_base_type(self, p: P) -> None:
        """base_type : BOOL_TYPE
                     | UINT_TYPE
                     | INT_TYPE
                     | BYTE_TYPE"""
        p[0] = p[1]

    def p_type_reference(self, p: P) -> None:
        """type_reference : type_reference '.' type_reference
                          | IDENTIFIER"""
        if len(p) == 4:
            p[0] = p[1].get_member(p[3])  # FIXME
        else:
            pass  # FIXME

    def p_array_type(self, p: P) -> None:
        """array_type : '[' array_capacity ']' single_type"""
        pass

    def p_array_capacity(self, p: P) -> None:
        """array_capacity : INTCONSTANT
                          | constant_reference_for_array_capacity
                          | message_field_reference_for_array_capacity"""
        p[0] = p[1]

    def p_message_field_reference_for_array_capacity(self, p: P) -> None:
        """message_field_reference_for_array_capacity : IDENTIFIER"""
        pass

    def p_template(self, p: P) -> None:
        """template : TEMPLATE IDENTIFIER  open_template_scope template_items close_template_scope"""
        pass

    def p_open_template_scope(self, p: P) -> None:
        """open_template_scope : '{'"""
        pass

    def p_close_template_scope(self, p: P) -> None:
        """close_template_scope : '}'"""
        pass

    def p_template_items(self, p: P) -> None:
        """template_items : template_item template_items
                          | template_item
                          |"""
        self.util_parse_sequence(p)

    def p_template_item(self, p: P) -> None:
        """template_item : option
                         | template_line
                         | comment
                         | newline
                         """
        p[0] = p[1]

    def p_template_line(self, p: P) -> None:
        """template_line : TEMPLATELINE"""
        p[0] = p[1]  # FIXME: template.Push
        pass

    def p_enum(self, p: P) -> None:
        """enum : open_enum_scope enum_items close_enum_scope"""
        pass

    def p_open_enum_scope(self, p: P) -> None:
        """open_enum_scope : ENUM IDENTIFIER '{'"""
        pass

    def p_close_enum_scope(self, p: P) -> None:
        """close_enum_scope : '}'"""
        pass

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
        """enum_field : IDENTIFIER '=' INTCONSTANT optional_semicolon"""
        pass

    def p_message(self, p: P) -> None:
        """message : open_message_scope message_items close_message_scope"""
        pass

    def p_open_message_scope(self, p: P) -> None:
        """open_message_scope : MESSAGE IDENTIFIER '{'"""
        pass

    def p_close_message_scope(self, p: P) -> None:
        """close_message_scope : '}'"""
        pass

    def p_message_items(self, p: P) -> None:
        """message_items : message_item message_items
                         | message_item
                         |"""
        self.util_parse_sequence(p)

    def p_message_item(self, p: P) -> None:
        """message_item : option
                        | message_field
                        | comment
                        | newline"""
        p[0] = p[1]

    def p_message_field(self, p: P) -> None:
        """message_field : message_field_number ':' IDENTIFIER type optional_semicolon"""
        pass

    def p_message_field_number(self, p: P) -> None:
        """message_field_number : INTCONSTANT"""
        p[0] = p[1]

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
        handle = self.current_handle_or_raise()
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
