"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindEnum,
                                     BlockBindMessage, BlockComposition,
                                     BlockConditional, BlockDeferable,
                                     BlockWrapper)
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


class BlockAlias(Block[F]):  # TODO
    pass


class BlockEnumProcessorBody(BlockBindEnum[F]):
    @override(Block)
    def render(self) -> None:
        descriptor = self.formatter.format_bp_enum_descriptor(self.d)
        self.push(f"struct BpEnumDescriptor descriptor = {descriptor};")
        self.push("BpEndecodeEnum(&descriptor, ctx, data);")


class BlockEnumProcessor(BlockBindEnum[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockEnumProcessorBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        processor_name = self.formatter.format_bp_enum_processor_name(self.d)
        signature = f"void {processor_name}(void *data, struct BpProcessorContext *ctx)"
        self.push(f"{signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockEnumProcessorList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockEnumProcessor(d)
            for _, d in self.bound.enums(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockInclude(),
            BlockEnumProcessorList(),
        ]


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
