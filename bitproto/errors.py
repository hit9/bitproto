"""
bitproto.errors
~~~~~~~~~~~~~~~

Errors.
"""

from dataclasses import dataclass


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
class InvalidEnumField(GrammarError):
    """Invalid enum field."""


@dataclass
class EnumFieldValueOverflow(GrammarError):
    """Enum field value overflows type constraint."""


@dataclass
class DuplicatedEnumFieldValue(GrammarError):
    """Duplicated enum field value."""
