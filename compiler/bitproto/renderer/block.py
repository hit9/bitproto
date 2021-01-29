"""
bitproto.renderer.block
~~~~~~~~~~~~~~~~~~~~~~~

Block class base.

    Block
      |- BlockBindDefinition
      |    |- BlockBindAlias
      |    |- BlockBindConstant
      |    |- BlockBindEnum
      |    |- BlockBindEnumField
      |    |- BlockBindMessage
      |    |- BlockBindMessageField
      |    |- BlockBindProto
      |- BlockDeferable
      |- BlockComposition
      |- BlockWrapper
      |- BlockConditional
"""

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generic, Iterator, List, Optional
from typing import Type as T
from typing import TypeVar, Union, cast

from bitproto._ast import (
    Alias,
    BoundDefinition,
    Comment,
    Constant,
    D,
    Definition,
    Enum,
    EnumField,
    Message,
    MessageField,
    Proto,
)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import F, Formatter
from bitproto.utils import (
    cached_property,
    final,
    overridable,
    override,
    snake_case,
    upper_case,
)

#############
# Block base
#############


@dataclass
class BlockRenderContext(Generic[F]):
    """Context for block's render()."""

    formatter: F
    bound: Proto
    optimization_mode_filter_messages: Optional[List[str]] = None


class Block(Generic[F]):
    """Block maintains formatted strings to render.

    :param indent: Number of characters to indent for this block.
    """

    def __init__(self, indent: int = 0) -> None:
        self.indent = indent
        self._strings: List[str] = []
        self._ctx: Optional[BlockRenderContext[F]] = None

    ####
    # Renderer implementation level api
    ####

    @abstractmethod
    def render(self) -> None:
        """Render processor for this block."""
        raise NotImplementedError

    @overridable
    def separator(self) -> str:
        """Separator to join managed strings, defaults to '\n'."""
        return "\n"

    @property
    def formatter(self) -> F:
        """Returns the formatter of current block."""
        return self._get_ctx_or_raise().formatter

    @property
    def bound(self) -> Proto:
        """Returns the bound proto of current block."""
        return self._get_ctx_or_raise().bound

    @final
    def push_string(self, s: str, separator: str = " ") -> None:
        """Append an inline string `s` onto current string.

        :param separator: The separator between current string with given `s`,
           defaults to " ".
        """
        self._strings[-1] = separator.join([self._strings[-1], s])

    @final
    def push(self, line: str, indent: Optional[int] = None) -> None:
        """Append a line of string.

        :param line: A line of string (without ending newline character).
        :param indent: Number of indent characters to insert at the head of given line,
           defaults to this block's indent.
        """
        indent = self.indent if indent is None else indent
        if indent > 0:
            line = indent * self.formatter.indent_character() + line
        self._strings.append(line)

    @final
    def push_empty_line(self) -> None:
        """Append an empty line."""
        self.push("")

    @final
    def push_comment(
        self, comment: Union[Comment, str], indent: Optional[int] = None
    ) -> None:
        """Push a line of comment.

        :param comment: A line of comment or str.
        """
        self.push(self.formatter.format_comment(str(comment)), indent=indent)

    @final
    def push_docstring(
        self, *comments: Union[Comment, str], indent: Optional[int] = None
    ) -> None:
        """Push one or more lines of comment as docstring.
        Dose nothing if given comments is empty.

        :param comments: List of comment or str.
        """
        if not comments:
            return

        strings = [i.content() if isinstance(i, Comment) else i for i in comments]
        for string in self.formatter.format_docstring(*strings):
            self.push(string, indent=indent)

    ####
    # Framework-level api
    ####

    @final
    def _get_ctx_or_raise(self) -> BlockRenderContext[F]:
        """Returns current render context, raise if None."""
        assert self._ctx is not None, InternalError("block._ctx not set")
        return self._ctx

    @final
    @contextmanager
    def _maintain_ctx(self, ctx: BlockRenderContext[F]) -> Iterator[None]:
        """Maintain given ctx as current block's render context."""
        try:
            self._ctx = ctx
            yield
        finally:
            self._ctx = None

    @final
    def __str__(self) -> str:
        """Returns the joined managed strings with separator."""
        return self.separator().join(self._strings)

    @final
    def _is_empty(self) -> bool:
        """Returns True if this block is empty."""
        return len(self._strings) == 0

    @final
    def _clear(self) -> None:
        """Clears internal managed strings."""
        self._strings = []

    @final
    def _collect(self) -> str:
        """Clear and returns the joined string."""
        s = str(self)
        self._clear()
        return s

    @final
    def _push_from_block(self, b: "Block") -> None:
        """Push strings onto this block from given block `b`."""
        if not b._is_empty():
            self.push(b._collect(), indent=0)

    @final
    def _render_with_ctx(self, ctx: BlockRenderContext) -> None:
        """Call this block's render() processor with given render context `ctx`."""
        with self._maintain_ctx(ctx):
            self.render()

    @final
    def _render_from_block(
        self, b: "Block[F]", ctx: Optional[BlockRenderContext[F]] = None
    ) -> None:
        """Render given block `b` with given render context `ctx`,
        and push its strings onto this block.
        Uses the render context of current block by default.
        """
        ctx = ctx or self._get_ctx_or_raise()
        b._render_with_ctx(ctx)
        self._push_from_block(b)

    @final
    def _defer_from_block(
        self, b: "BlockDeferable[F]", ctx: Optional[BlockRenderContext[F]] = None
    ) -> None:
        """Call defer() on given block `b` with given render context `ctx`,
        and push its strings onto this block.
        Uses the render context of current block by default.
        """
        ctx = ctx or self._get_ctx_or_raise()
        b._defer_with_ctx(ctx)
        self._push_from_block(b)


@final
class BlockAheadNotice(Block):
    """Block to render a comment of bitproto notice."""

    def render(self) -> None:
        """Renders a line of comment of generation notice."""
        notice = "Code generated by bitproto. DO NOT EDIT."
        notice_comment = self.formatter.format_comment(notice)
        self.push(notice_comment)


#############
# Block that bind a definition ast.
#############


@dataclass
class BlockBindDefinitionBase(Generic[D]):
    """Base class of BlockBindDefinition.

    :param d: The associated definition instance.
    :param name: The name of associated definition, defaults to `d.name`.
    """

    d: D
    name: Optional[str] = None


class BlockBindDefinition(Block[F], BlockBindDefinitionBase[D]):
    """Block that bind a definition."""

    def __init__(
        self,
        d: D,
        name: Optional[str] = None,
        indent: int = 0,
    ) -> None:
        BlockBindDefinitionBase.__init__(self, d, name=name)
        Block.__init__(self, indent=indent)

    @final
    def push_definition_comments(self, indent: Optional[int] = None):
        """Format the comment_block of this definition as lines of comments,
        and push them.
        """
        for comment in self.d.comment_block:
            comment_string = comment.content()
            self.push_comment(comment, indent)

    @final
    def push_definition_docstring(self, indent: Optional[int] = None) -> None:
        """Format the comment_block of this definition as lines of docstring,
        and push them.
        """
        self.push_docstring(*self.d.comment_block, indent=indent)

    @final
    def push_typing_hint_inline_comment(self) -> None:
        """Push an inline comment to hint the original defined bitproto type."""
        comment = self.formatter.format_comment(f"{self.nbits()}bit")
        self.push_string(comment)

    @overridable
    def nbits(self) -> int:
        """Returns the number of bits this definition occupy."""
        return 0


class BlockBindAlias(BlockBindDefinition[F, Alias]):
    """Implements BlockBindDefinition for Alias."""

    @override(BlockBindDefinition)
    def nbits(self) -> int:
        return self.d.nbits()

    @cached_property
    def alias_name(self) -> str:
        """Returns the formatted name of this alias."""
        return self.formatter.format_alias_name(self.d)

    @cached_property
    def aliased_type(self) -> str:
        """Returns the formatted representation of the type it aliased to."""
        return self.formatter.format_type(self.d.type, name=self.alias_name)


class BlockBindConstant(BlockBindDefinition[F, Constant]):
    """Implements BlockBindDefinition for Constant."""

    @cached_property
    def constant_name(self) -> str:
        """Returns the formatted name of this constant."""
        return self.formatter.format_constant_name(self.d)

    @cached_property
    def constant_value(self) -> str:
        """Returns the formatted value of this constant."""
        return self.formatter.format_value(self.d.value)

    @cached_property
    def constant_value_type(self) -> str:
        """Returns the formatted representation of this constant's value."""
        return self.formatter.format_constant_type(self.d)


class BlockBindEnum(BlockBindDefinition[F, Enum]):
    """Implements BlockBindDefinition for Enum."""

    @override(BlockBindDefinition)
    def nbits(self) -> int:
        return self.d.nbits()

    @cached_property
    def enum_name(self) -> str:
        """Returns the formatted name of this enum."""
        return self.formatter.format_enum_name(self.d)

    @cached_property
    def enum_uint_type(self) -> str:
        """Returns the formatted uint type representation of this enum."""
        return self.formatter.format_uint_type(self.d.type)


class BlockBindEnumField(BlockBindDefinition[F, EnumField]):
    """Implements the BlockBindDefinition for EnumField."""

    @override(BlockBindDefinition)
    def nbits(self) -> int:
        return self.d.enum.nbits()

    @cached_property
    def enum_field_name(self) -> str:
        """Returns the formatted name of this enum field."""
        return self.formatter.format_enum_field_name(self.d)

    @cached_property
    def enum_field_value(self) -> str:
        """Returns the formatted value of this enum field."""
        return self.formatter.format_int_value(self.d.value)

    @cached_property
    def enum_field_type(self) -> str:
        """Returns the formatted representation of the enum field type, aka the enum type."""
        return self.formatter.format_enum_type(self.d.enum)


class BlockBindMessage(BlockBindDefinition[F, Message]):
    """Implements the BlockBindDefinition for Message."""

    @override(BlockBindDefinition)
    def nbits(self) -> int:
        return self.d.nbits()

    @cached_property
    def message_name(self) -> str:
        """Returns the formatted name of this message."""
        return self.formatter.format_message_name(self.d)

    @cached_property
    def message_type(self) -> str:
        """Returns the formatted representation of this message type."""
        return self.formatter.format_message_type(self.d)

    @cached_property
    def message_nbytes(self) -> str:
        """Returns the formatted representation of the number of bytes of this message."""
        return self.formatter.format_int_value(self.d.nbytes())

    @overridable
    @cached_property
    def message_size_constant_name(self) -> str:
        """Return the formatted name of the message size constant."""
        return f"BYTES_LENGTH_" + upper_case(snake_case(self.message_name))


class BlockBindMessageField(BlockBindDefinition[F, MessageField]):
    """Implements the BlockBindDefinition for MessageField."""

    @override(BlockBindDefinition)
    def nbits(self) -> int:
        return self.d.type.nbits()

    @cached_property
    def message_field_name(self) -> str:
        return self.formatter.format_message_field_name(self.d)

    @cached_property
    def message_field_type(self) -> str:
        """Returns the formatted field type representation of this field."""
        return self.formatter.format_type(self.d.type, name=self.message_field_name)


class BlockBindProto(BlockBindDefinition[F, Proto]):
    """Implements the BlockBindDefinition for Proto."""


#############
# Block that defines a defer().
#############


class BlockDeferable(Block[F]):
    """Block with a defer method defined."""

    @abstractmethod
    def defer(self) -> None:
        """Defer is a hook function, invoked by BlockComposition's render().
        Called reversively over the order of the composition of blocks.
        """
        raise NotImplementedError

    def _defer_with_ctx(self, ctx: BlockRenderContext) -> None:
        """Call this block's defer() processor with given ctx."""
        with self._maintain_ctx(ctx):
            self.defer()


#############
# Block that join a list of blocks.
#############


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
            self._render_from_block(block)

        for block in blocks[::-1]:
            if isinstance(block, BlockDeferable):
                self._defer_from_block(block)

    @abstractmethod
    def blocks(self) -> List[Block[F]]:
        """Returns the blocks to join."""
        raise NotImplementedError


#############
# Block that wraps a block.
#############


class BlockWrapper(Block[F]):
    """Wraps on a block as a block."""

    @final
    @override(Block)
    def render(self) -> None:
        self.before()
        block = self.wraps()
        if block:
            self._render_from_block(block)
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


#############
# Block that works if condition satisfied
#############


class BlockConditional(Block[F]):
    """Block that render conditional."""

    @abstractmethod
    def condition(self) -> bool:
        """Render if this condition returns True."""
        raise NotImplementedError

    @abstractmethod
    def block(self) -> Block[F]:
        """Returns the target block."""
        raise NotImplementedError

    @final
    @override(Block)
    def render(self) -> None:
        if self.condition():
            block = self.block()
            self._render_from_block(block)


#############
# Block that render simple empty lines.
#############


class BlockEmptyLine(Block[F]):
    """Block that renders simple empty line."""

    @final
    @override(Block)
    def render(self) -> None:
        self.push_empty_line()


###########
# Block that dispatches BoundDefinition.
###########


class BlockBoundDefinitionDispatcher(BlockComposition[F]):
    """Block that dispatch BoundDefinition in current processing proto to specific block
    and composite them into a BlockComposition.
    """

    @final
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        b: List[Block[F]] = []
        for _, d in self.bound.filter(
            BoundDefinition, recursive=True, bound=self.bound
        ):
            block = self.dispatch(d)
            if block:
                b.append(block)
        return b

    @abstractmethod
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        """Returns a specific block instance by given bound definition d."""
        raise NotImplementedError
