"""
bitproto.errors
~~~~~~~~~~~~~~~

Errors.
"""

from dataclasses import dataclass

from typing import TypeVar, Type as T, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bitproto.ast import Node

T_ParserError = TypeVar("T_ParserError", bound="ParserError")


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
    """Some internal error occurred in bitproto."""


@dataclass
class ParserError(Error):
    """Some error occurred during bitproto parsing."""

    message: str = ""
    filepath: str = ""
    token: str = ""
    lineno: int = 0

    def format_default_description(self) -> str:
        message = self.message or self.__doc__
        if self.filepath:
            return f"{self.filepath}:L{self.lineno}: {self.token} => {message}"
        return f"L{self.lineno}: {self.token} => {message}"

    @classmethod
    def from_token(cls: T[T_ParserError], token: "Node", **kwds: Any,) -> T_ParserError:
        return cls(
            filepath=token.filepath, token=token.token, lineno=token.lineno, **kwds
        )


@dataclass
class LexerError(ParserError):
    """Some token error occurred during bitproto lexing."""


@dataclass
class GrammarError(ParserError):
    """Some grammar error occurred during bitproto grammar parsing."""


@dataclass
class RendererError(Error):
    """Some renderer error occurred during bitproto rendering."""


@dataclass
class InvalidUintCap(LexerError):
    """Invalid bits capacity for a uint type, should between [1, 64]"""


@dataclass
class InvalidIntCap(LexerError):
    """Invalid bits capacity for a int type, should be one of 8,16,32,64."""


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
    """Invalid array capacity, should between (0, 1024)."""


@dataclass
class DuplicatedDefinition(GrammarError):
    """Duplicated definition."""


@dataclass
class ReferencedConstantNotDefined(GrammarError):
    """Referenced constant not defined."""


@dataclass
class ReferencedTypeNotDefined(GrammarError):
    """Referenced type not defined."""


@dataclass
class InvalidEnumFieldValue(GrammarError):
    """Invalid enum field, should >=0."""


@dataclass
class EnumFieldValueOverflow(GrammarError):
    """Enum field value overflows type constraint."""


@dataclass
class DuplicatedEnumFieldValue(GrammarError):
    """Duplicated enum field value."""


@dataclass
class CyclicImport(GrammarError):
    """Cyclic proto import."""


@dataclass
class InvalidAliasedType(GrammarError):
    """Invalid type to alias, only bool,byte,uint,int and array of them can be aliased."""


@dataclass
class InvalidMessageFieldNumber(GrammarError):
    """Invalid message field number, should between [1, 255]."""


@dataclass
class DuplicatedMessageFieldNumber(GrammarError):
    """Duplicated message field number."""


@dataclass
class UnsupportedLanguageToRender(RendererError):
    """Unsupported language to render."""
