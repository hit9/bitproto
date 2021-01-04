"""
bitproto.renderer.block
~~~~~~~~~~~~~~~~~~~~~~~

Block class base.
"""

from abc import abstractmethod
from typing import Generic, List, Optional
from typing import Type as T

from bitproto._ast import (Alias, Constant, D, Definition, Enum, EnumField,
                           Message, MessageField, Proto)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import F, Formatter
from bitproto.utils import final, overridable, override


class Block(Generic[F]):
    """Block is a collection of rendered strings.

    :param indent: Number of characters to indent for this block.
    """

    def __init__(self, indent: int = 0) -> None:
        self.strings: List[str] = []
        self.indent = indent

        self._bound: Optional[Proto] = None
        self._formatter: Optional[F] = None

    @property
    def formatter(self) -> F:
        assert self._formatter is not None, InternalError("block._formatter not set")
        return self._formatter

    @final
    def set_formatter(self, formatter: F) -> None:
        self._formatter = formatter

    @property
    def bound(self) -> Proto:
        assert self._bound is not None, InternalError("block._bound not set")
        return self._bound

    @final
    def set_bound(self, bound: Proto) -> None:
        self._bound = bound

    @final
    def __str__(self) -> str:
        """Returns the joined managed strings with separator."""
        return self.separator().join(self.strings)

    @final
    def is_empty(self) -> bool:
        """Returns if this block is empty."""
        return len(self.strings) == 0

    @final
    def push_string(self, s: str, separator: str = " ") -> None:
        """Append a in-line string `s` onto current string.
        :param separator: The separator between current string with given `s`.
        """
        self.strings[-1] = separator.join([self.strings[-1], s])

    @final
    def push(self, line: str, indent: Optional[int] = None) -> None:
        """Append a line of string.
        :param line: A line of string (without ending newline character).
        :param indent: The number of characters to indent this line, defaults to this
           block's indent.
        """
        indent = self.indent if indent is None else indent
        if indent > 0:
            line = indent * self.formatter.indent_character() + line
        self.strings.append(line)

    @final
    def push_empty_line(self) -> None:
        """Append an empty line."""
        self.push("")

    @final
    def clear(self) -> None:
        self.strings = []

    @final
    def collect(self) -> str:
        """Clear and returns the joined string."""
        s = str(self)
        self.clear()
        return s

    @final
    def push_from_block(self, b: "Block") -> None:
        """Push from another block."""
        if not b.is_empty():
            self.push(b.collect(), indent=0)

    @abstractmethod
    def render(self) -> None:
        """Render processor for this block, invoked by Renderer.render()."""
        raise NotImplementedError

    @overridable
    def defer(self) -> None:
        """Defer render processor for this block. invoked by BlockComposition.render().
        Optional overrided.
        """
        raise NotImplementedError

    @overridable
    def separator(self) -> str:
        """Separator to join managed strings, defaults to '\n'."""
        return "\n"


@final
class BlockAheadNotice(Block):
    """Block to render a comment of bitproto notice."""

    def render(self) -> None:
        notice = self.formatter.AHEAD_NOTICE
        notice_comment = self.formatter.format_comment(notice)
        self.push(notice_comment)


class BlockDefinition(Block[F]):
    """Block for a definition.

    :param definition: The associated definition.
    :param name: The name of associated definition, defaults to `definition.name`.
    :param indent: Argument inherits from super class Block.
    """

    def __init__(
        self, definition: Definition, name: Optional[str] = None, indent: int = 0,
    ) -> None:
        super(BlockDefinition, self).__init__(indent=indent)

        self.definition = definition
        self.definition_name: str = name or definition.name

    def as_t(self, t: T[D]) -> D:
        """Safe cast internal definition to given definition type `t`."""
        if isinstance(self.definition, t):
            return self.definition
        raise InternalError(f"can't cast {self.definition} to type {t}")

    @property
    def as_constant(self) -> Constant:
        """Returns the definition as a Constant."""
        return self.as_t(Constant)

    @property
    def as_alias(self) -> Alias:
        """Returns the definition as an Alias."""
        return self.as_t(Alias)

    @property
    def as_enum(self) -> Enum:
        """Returns the definition as an Enum."""
        return self.as_t(Enum)

    @property
    def as_enum_field(self) -> EnumField:
        """Returns the definition as a EnumField."""
        return self.as_t(EnumField)

    @property
    def as_message(self) -> Message:
        """Returns the definition as a Message."""
        return self.as_t(Message)

    @property
    def as_message_field(self) -> MessageField:
        """Returns the definition as a MessageField."""
        return self.as_t(MessageField)

    @property
    def as_proto(self) -> Proto:
        """Returns the definition as a Proto."""
        return self.as_t(Proto)

    @final
    def push_docstring(
        self, as_comment: bool = False, indent: Optional[int] = None
    ) -> None:
        """Format the comment_block of this definition, and push them."""
        indent = self.indent if indent is None else indent

        fmt = self.formatter.format_docstring
        if as_comment:
            fmt = self.formatter.format_comment

        for comment in self.definition.comment_block:
            comment_string = comment.content()
            formatted_comment = fmt(comment_string)
            self.push(formatted_comment, indent)

    @final
    def push_location_doc(self) -> None:
        """Push current definition source location as an inline-comment to current line."""
        location_string = self.formatter.format_token_location(self.definition)
        inline_comment = self.formatter.format_comment(location_string)
        self.push_string(inline_comment, separator=" ")


class BlockComposition(Block[F]):
    """Composition of a list of blocks as a block."""

    @overridable
    @override(Block)
    def separator(self) -> str:
        """Overrides upper method `separator()`, for separator between blocks,
        defaults to '\n\n'.
        """
        return "\n\n"

    @final
    @override(Block)
    def render(self) -> None:
        """Overrides upper method `render()`.
        It will firstly call each block's render method.
        And then call defer method reversively.
        """
        blocks = self.blocks()
        for block in blocks:
            block.set_formatter(self.formatter)
            block.set_bound(self.bound)
            block.render()
            self.push_from_block(block)

        for block in blocks[::-1]:
            try:
                block.defer()
            except NotImplementedError:
                pass
            else:
                self.push_from_block(block)

    @abstractmethod
    def blocks(self) -> List[Block[F]]:
        """Returns the blocks to join."""
        raise NotImplementedError


class BlockWrapper(Block[F]):
    """Wraps on a block as a block."""

    @final
    @override(Block)
    def render(self) -> None:
        self.before()

        block = self.wraps()
        block.set_formatter(self.formatter)
        block.set_bound(self.bound)
        block.render()
        self.push_from_block(block)

        self.after()

    @abstractmethod
    def wraps(self) -> Block[F]:
        """Returns the wrapped block instance."""
        raise NotImplementedError

    @overridable
    def before(self) -> None:
        """Hook function invoked before render."""
        pass

    @overridable
    def after(self) -> None:
        """Hook function invoked after render."""
        pass
