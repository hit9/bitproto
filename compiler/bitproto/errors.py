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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Optional
from typing import Type as T
from typing import TypeVar

from bitproto.utils import Color, colored, overridable, override, write_stderr

if TYPE_CHECKING:
    from bitproto._ast import Node

_B = TypeVar("_B", bound="_TokenBound")


@dataclass
class Base:
    description: str = ""

    def __post_init__(self) -> None:
        if not self.description:
            self.description = self.format_default_description()

    @overridable
    def format_default_description(self) -> str:
        return self.__doc__ or ""

    @overridable
    def _message_prefix(self) -> str:
        pass

    def __str__(self) -> str:
        description = self.description
        prefix = self._message_prefix()
        return "\n".join(map(lambda l: prefix + " " + l, description.splitlines()))

    def colored(self) -> str:
        return str(self)


@dataclass
class Error(Base, Exception):
    """Some error occurred during bitproto handling."""

    def colored(self) -> str:
        return colored(super(Error, self).__str__(), Color.RED)

    @override(Base)
    def _message_prefix(self) -> str:
        return "error: "


@dataclass
class Warning(Base):
    """Warning continues processing and leaves a message."""

    @override(Base)
    def _message_prefix(self) -> str:
        return "warning: "

    def colored(self) -> str:
        return colored(super(Warning, self).__str__(), Color.YELLOW)


def warning(w: Optional["Warning"] = None) -> None:
    """Logs a warning to stderr."""
    if not w:
        return
    write_stderr(w.colored())


@dataclass
class InternalError(Error):
    """Some internal error occurred in bitproto."""


@dataclass
class _TokenBound(Base):
    message: str = ""
    filepath: str = ""
    token: str = ""
    lineno: int = 0

    @override(Base)
    def format_default_description(self) -> str:
        message = self.message or self.__doc__
        if self.filepath:
            return f"{self.filepath}:L{self.lineno} {self.token} => {message}"
        return f"L{self.lineno} {self.token} => {message}"

    @classmethod
    def from_token(
        cls: T[_B],
        token: "Node",
        **kwds: Any,
    ) -> _B:
        return cls(
            filepath=token.filepath, token=token.token, lineno=token.lineno, **kwds
        )


@dataclass
class UserError(Error):
    """User error."""


class NoLanguageArgument(UserError):
    """No language specific."""


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
    """Invalid array capacity, should between (0, 65536)."""


@dataclass
class DuplicatedDefinition(GrammarError):
    """Duplicated definition."""


@dataclass
class DuplicatedImport(GrammarError):
    """Duplicated import."""


@dataclass
class ReferencedConstantNotDefined(GrammarError):
    """Referenced constant not defined."""


@dataclass
class ReferencedNotConstant(GrammarError):
    """Referenced not a constant."""


@dataclass
class ReferencedTypeNotDefined(GrammarError):
    """Referenced type not defined."""


@dataclass
class ReferencedNotType(GrammarError):
    """Referenced not a type."""


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
    """Invalid type to alias."""


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
class MessageSizeOverflows(GrammarError):
    """Message size overflows constraint, should < 65535 bits (about 8kb)."""


@dataclass
class AliasInMessageUnsupported(GrammarError):
    """Unsupported to declare alias type inside message."""


@dataclass
class ConstInMessageUnsupported(GrammarError):
    """Unsupported to declare constant inside message."""


@dataclass
class ImportInMessageUnsupported(GrammarError):
    """Unsupported to import proto inside message."""


@dataclass
class UnsupportedToDeclareProtoNameOutofProtoScope(GrammarError):
    """Cannot declare proto name out of global scope."""


@dataclass
class StatementInMessageUnsupported(GrammarError):
    """Unsupported statement inside message."""


@dataclass
class AliasInEnumUnsupported(GrammarError):
    """Unsupported to declare alias type inside enum."""


@dataclass
class ConstInEnumUnsupported(GrammarError):
    """Unsupported to declare constant inside enum."""


@dataclass
class ImportInEnumUnsupported(GrammarError):
    """Unsupported to import proto inside enum."""


@dataclass
class OptionInEnumUnsupported(GrammarError):
    """Unsupported to declare option inside enum."""


@dataclass
class EnumInEnumUnsupported(GrammarError):
    """Unsupported to declare enum inside enum."""


@dataclass
class MessageInEnumUnsupported(GrammarError):
    """Unsupported to declare message inside enum."""


@dataclass
class MessageFieldInEnumUnsupported(GrammarError):
    """Unsupported to declare message field inside enum."""


@dataclass
class ProtoNameUndefined(GrammarError):
    """Proto name undefined."""


@dataclass
class ExtensibleGrammarFoundInTraditionalMode(GrammarError):
    """Extensible-type grammar found while enforcing traditional mode parsing."""


@dataclass
class LanguageNotSupportOptimizationMode(RendererError):
    """Language doesn't support optimization mode."""

    lang: str = ""

    @override(Base)
    def format_default_description(self) -> str:
        message: str
        if self.lang:
            message = f"Optimization mode for language {self.lang} isn't supported."
        else:
            message = self.__doc__ or ""
        return message


@dataclass
class LintWarning(_TokenBound, Warning):
    """Some warning occurred during bitproto linting."""

    suggestion: Optional[str] = None

    @override(Base)
    def format_default_description(self) -> str:
        description: str = super(LintWarning, self).format_default_description()
        if self.suggestion:
            description = description + " suggestion => " + self.suggestion
        return description


@dataclass
class IndentWarning(LintWarning):
    """Indent warning."""


@dataclass
class EnumNameNotPascal(LintWarning):
    """Enum name not pascal case."""


@dataclass
class EnumHasNoFieldValue0(LintWarning):
    """Enum has no field with value 0."""


@dataclass
class EnumFieldNameNotUpper(LintWarning):
    """Enum field name not upper case."""


@dataclass
class MessageNameNotPascal(LintWarning):
    """Message name not pascal case."""


@dataclass
class MessageFieldNameNotSnake(LintWarning):
    """Message field name not snake case."""


@dataclass
class ConstantNameNotUpper(LintWarning):
    """Constant name not upper case."""


@dataclass
class AliasNameNotPascal(LintWarning):
    """Alias name not pascal case."""
