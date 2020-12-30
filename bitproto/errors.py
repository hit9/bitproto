"""
bitproto.errors
~~~~~~~~~~~~~~~

Errors.

    Base
      |- Error
      |    |- InternalError
      |    |- ParserError
      |    |    |- LexerError
      |    |    |- GrammarError
      |    |- RendererError
      |- Warning
      |    |- LintWarning
"""

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from typing import Type as T
from typing import TypeVar, ClassVar, Optional

if TYPE_CHECKING:
    from bitproto._ast import Node

_B = TypeVar("_B", bound="_TokenBound")


@dataclass
class Base:
    description: str = ""

    def __post_init__(self) -> None:
        if not self.description:
            self.description = self.format_default_description()

    def format_default_description(self) -> str:
        return self.__doc__ or ""

    def _message_prefix(self) -> str:
        return "( error )"

    def __str__(self) -> str:
        description = self.description
        prefix = self._message_prefix()
        return "\n".join(map(lambda l: prefix + " " + l, description.splitlines()))


@dataclass
class Error(Base, Exception):
    """Some error occurred during bitproto handling."""


@dataclass
class Warning(Base):
    """Warning continues processing and leaves a message."""

    def _message_prefix(self) -> str:
        return "( warning )"


def warning(
    warning: Optional["Warning"] = None, suggestion: Optional[str] = None
) -> None:
    """Logs a warning to stderr."""
    if not warning:
        return
    message = str(warning)
    if suggestion:
        message = f"{message} suggestion => {suggestion}"
    sys.stderr.write(message + "\n")


@dataclass
class InternalError(Error):
    """Some internal error occurred in bitproto."""


@dataclass
class _TokenBound(Base):
    message: str = ""
    filepath: str = ""
    token: str = ""
    lineno: int = 0

    def format_default_description(self) -> str:
        message = self.message or self.__doc__
        if self.filepath:
            return f"{self.filepath}:L{self.lineno} {self.token} => {message}"
        return f"L{self.lineno} {self.token} => {message}"

    @classmethod
    def from_token(cls: T[_B], token: "Node", **kwds: Any,) -> _B:
        return cls(
            filepath=token.filepath, token=token.token, lineno=token.lineno, **kwds
        )


@dataclass
class ParserError(Error, _TokenBound):
    """Some error occurred during bitproto parsing."""


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


@dataclass
class UnsupportedOption(GrammarError):
    """Unsupported option."""


@dataclass
class InvalidOptionValue(GrammarError):
    """Invalid option value."""


@dataclass
class LintWarning(Warning, _TokenBound):
    """Some warning occurred during bitproto linting."""


@dataclass
class EnumNameNotPascal(LintWarning):
    """Enum name not pascal case."""
