"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindMessage,
                                     BlockComposition, BlockConditional,
                                     BlockDeferable, BlockWrapper)
from bitproto.renderer.impls.c.formatter import CFormatter as F
from bitproto.renderer.impls.c.renderer_h import (
    BlockMessageDecoderBase, BlockMessageEncoderBase,
    BlockMessageJsonFormatterBase, RendererCHeader)
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override


class BlockInclude(Block[F]):
    @override(Block)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "{header_filename}"')


class BlockMessageEncoderBody(BlockMessageEncoderBase):
    @override(Block)
    def render(self) -> None:
        pass  # TODO


class BlockMessageEncoder(BlockMessageEncoderBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockMessageEncoderBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageDecoderBody(BlockMessageDecoderBase):
    @override(Block)
    def render(self) -> None:
        pass  # TODO


class BlockMessageDecoder(BlockMessageDecoderBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockMessageDecoderBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageJsonFormatterBody(BlockMessageJsonFormatterBase):
    @override(Block)
    def render(self) -> None:
        pass  # TODO


class BlockMessageJsonFormatterWrapper(BlockMessageJsonFormatterBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockMessageJsonFormatterBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageJsonFormatter(BlockMessageJsonFormatterBase, BlockConditional[F]):
    @override(BlockConditional)
    def condition(self) -> bool:
        return self.is_enabled()

    @override(BlockConditional)
    def block(self) -> Block:
        return BlockMessageJsonFormatterWrapper(self.d)


class BlockMessageFunctionList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageEncoder(self.d),
            BlockMessageDecoder(self.d),
            BlockMessageJsonFormatter(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


class BlockFunctionList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageFunctionList(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockAheadNotice(), BlockInclude(), BlockFunctionList()]


class RendererC(Renderer[F]):
    """Renderer for C language (c file)."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".c"

    @override(Renderer)
    def formatter(self) -> F:
        return F()

    @override(Renderer)
    def block(self) -> Block[F]:
        return BlockList()
