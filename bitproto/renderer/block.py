"""
bitproto.renderer.block
~~~~~~~~~~~~~~~~~~~~~~~

Block class base.
"""

from abc import abstractmethod
from typing import List, Optional, cast

from bitproto._ast import (Alias, Constant, Definition, Enum, EnumField,
                           Message, MessageField, Proto)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import Formatter
from bitproto.utils import final


class Block:
    """Block is a collection of rendered strings.

    :param formatter: The formatter for target language.
    :param ident: Number of characters to indent for this block.
    :param separator: Separator to join managed strings, defaults to "\n".
    """

    def __init__(
        self,
        formatter: Optional[Formatter] = None,
        ident: int = 0,
        separator: str = "\n",
    ) -> None:
        self.strings: List[str] = []
        self._formatter: Optional[Formatter] = formatter
        self.ident = ident
        self.separator = separator

    @property
    def formatter(self) -> Formatter:
        assert self._formatter is not None, InternalError("block._formatter not set")
        return self._formatter

    def set_formatter(self, formatter: Formatter) -> None:
        self._formatter = formatter

    def __str__(self) -> str:
        """Returns the joined managed strings with separator."""
        return self.separator.join(self.strings)

    def push_string(self, s: str, separator: str = " ") -> None:
        """Append a in-line string `s` onto current string.
        :param separator: The separator between current string with given `s`.
        """
        self.strings[-1] = separator.join([self.strings[-1], s])

    def push(self, line: str, ident: Optional[int] = None) -> None:
        """Append a line of string.
        :param line: A line of string (without ending newline character).
        :param indent: The number of characters to indent this line, defaults to this
           block's ident.
        """
        ident = self.ident if ident is None else ident
        if ident > 0:
            line = ident * self.formatter.indent_character() + line
        self.strings.append(line)

    def push_empty_line(self) -> None:
        """Append an empty line."""
        self.push("")

    def clear(self) -> None:
        self.strings = []

    def collect(self) -> str:
        """Clear and returns the joined string."""
        s = str(self)
        self.clear()
        return s

    @abstractmethod
    def render(self) -> None:
        """Render processor for this block, invoked by Renderer.render()."""
        raise NotImplementedError

    def defer(self) -> None:
        """Defer render processor for this block. invoked by Renderer.render().
        Optional overrided.
        """
        raise NotImplementedError


@final
class BlockAheadNotice(Block):
    """Block to render a comment of bitproto notice."""

    def render(self) -> None:
        notice = self.formatter.AHEAD_NOTICE
        notice_comment = self.formatter.format_comment(notice)
        self.push(notice_comment)


class BlockForDefinition(Block):
    """Block for a definition.

    :param definition: The associated definition.
    :param name: The name of associated definition, defaults to `definition.name`.
    :param formatter: Argument inherits from super class Block.
    :param indent: Argument inherits from super class Block.
    """

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
        """Returns the definition as a Constant."""
        return cast(Constant, self.definition)

    @property
    def as_alias(self) -> Alias:
        """Returns the definition as an Alias."""
        return cast(Alias, self.definition)

    @property
    def as_enum(self) -> Enum:
        """Returns the definition as an Enum."""
        return cast(Enum, self.definition)

    @property
    def as_enum_field(self) -> EnumField:
        """Returns the definition as a EnumField."""
        return cast(EnumField, self.definition)

    @property
    def as_message(self) -> Message:
        """Returns the definition as a Message."""
        return cast(Message, self.definition)

    @property
    def as_message_field(self) -> MessageField:
        """Returns the definition as a MessageField."""
        return cast(MessageField, self.definition)

    @property
    def as_proto(self) -> Proto:
        """Returns the definition as a Proto."""
        return cast(Proto, self.definition)

    def render_doc(self) -> None:
        """Format the comment_block of this definition, and push them."""
        for comment in self.definition.comment_block:
            comment_string = comment.content()
            formatted_comment = self.formatter.format_comment(comment_string)
            self.push(formatted_comment)

    def push_location_doc(self) -> None:
        """Push current definition source location as an inline-comment to current line."""
        location_string = self.formatter.format_token_location(self.definition)
        inline_comment = self.formatter.format_comment(location_string)
        self.push_string(inline_comment, separator=" ")
