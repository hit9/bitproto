"""
bitproto.renderer.block
~~~~~~~~~~~~~~~~~~~~~~~

Block class base.


   Block
     |- BlockDefinition
     |- BlockDeferable
     |- BlockComposition
     |- BlockWrapper
"""

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generic, Iterator, List, Optional
from typing import Type as T
from typing import Union, cast

from bitproto._ast import (Alias, Comment, Constant, D, Definition, Enum,
                           EnumField, Message, MessageField, Proto)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import F, Formatter
from bitproto.utils import final, overridable, override


@dataclass
class BlockRenderContext(Generic[F]):
    """Context for block's render()."""

    formatter: F
    bound: Proto


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


class BlockDefinition(Block[F]):
    """Block that bind a definition.

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
    def push_definition_comments(self, indent: Optional[int] = None):
        """Format the comment_block of this definition as lines of comments,
        and push them.
        """
        for comment in self.definition.comment_block:
            comment_string = comment.content()
            self.push_comment(comment, indent)

    @final
    def push_definition_docstring(self, indent: Optional[int] = None) -> None:
        """Format the comment_block of this definition as lines of docstring,
        and push them.
        """
        self.push_docstring(*self.definition.comment_block, indent=indent)


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


class BlockWrapper(Block[F]):
    """Wraps on a block as a block."""

    @final
    @override(Block)
    def render(self) -> None:
        self.before()
        block = self.wraps()
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
