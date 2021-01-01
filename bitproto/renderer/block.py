"""
bitproto.renderer.block
~~~~~~~~~~~~~~~~~~~~~~~

Block class base.
"""

import abc
from typing import cast, List, Optional

from bitproto._ast import (
    Alias,
    Constant,
    Definition,
    Enum,
    EnumField,
    Message,
    MessageField,
    Proto,
)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import Formatter


class Block:
    """Renderer block."""

    def __init__(self, formatter: Optional[Formatter] = None, ident: int = 0) -> None:
        self.strings: List[str] = []
        self._formatter: Optional[Formatter] = formatter
        self.ident = ident

    @property
    def formatter(self) -> Formatter:
        assert self._formatter is not None, InternalError("block._formatter not set")
        return self._formatter

    def set_formatter(self, formatter: Formatter) -> None:
        self._formatter = formatter

    def __str__(self) -> str:
        return "\n".join(self.strings)

    def push_string(self, s: str, separator: str = " ") -> None:
        """Append a string onto current string."""
        self.strings[-1] = separator.join([self.strings[-1], s])

    def push(self, line: str, ident: Optional[int] = None) -> None:
        """Append a line of string."""
        ident = self.ident if ident is None else ident
        if ident > 0:
            line = ident * self.formatter.ident_character() + line
        self.strings.append(line)

    def push_empty_line(self) -> None:
        self.push("")

    def clear(self) -> None:
        self.strings = []

    def collect(self) -> str:
        s = str(self)
        self.clear()
        return s

    @abc.abstractmethod
    def render(self) -> None:
        """Render processor for this block, invoked by Renderer.render()."""
        raise NotImplementedError

    def defer(self) -> None:
        """Defer render processor for this block. invoked by Renderer.render().
        Optional overrided.
        """
        raise NotImplementedError


class BitprotoDeclarationBlock(Block):
    """Block to render bitproto header declaration."""

    def render(self) -> None:
        declaration = self.formatter.BITPROTO_DECLARATION
        self.push(self.formatter.format_comment(declaration))


class BlockForDefinition(Block):
    """Block for definition."""

    def __init__(
        self,
        definition: Definition,
        name: Optional[str] = None,
        formatter: Optional[Formatter] = None,
        ident: int = 0,
    ) -> None:
        super(BlockForDefinition, self).__init__(formatter=formatter, ident=ident)

        self.definition = definition
        self.definition_name: str = name or definition.name

    @property
    def as_constant(self) -> Constant:
        return cast(Constant, self.definition)

    @property
    def as_alias(self) -> Alias:
        return cast(Alias, self.definition)

    @property
    def as_enum(self) -> Enum:
        return cast(Enum, self.definition)

    @property
    def as_enum_field(self) -> EnumField:
        return cast(EnumField, self.definition)

    @property
    def as_message(self) -> Message:
        return cast(Message, self.definition)

    @property
    def as_message_field(self) -> MessageField:
        return cast(MessageField, self.definition)

    @property
    def as_proto(self) -> Proto:
        return cast(Proto, self.definition)

    def render_doc(self) -> None:
        for comment in self.definition.comment_block:
            self.push(self.formatter.format_comment(comment.content()))

    def push_location_doc(self) -> None:
        """Push current definition source location as an inline-comment to current line."""
        location_string = self.formatter.format_token_location(self.definition)
        self.push_string(self.formatter.format_comment(location_string), separator=" ")
