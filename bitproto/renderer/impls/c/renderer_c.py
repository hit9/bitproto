"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.impls.c.renderer_h import RendererCHeader
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override

Renderer_ = Renderer[CFormatter]
Block_ = Block[CFormatter]
BlockComposition_ = BlockComposition[CFormatter]
BlockWrapper_ = BlockWrapper[CFormatter]
BlockDefinition_ = BlockDefinition[CFormatter]


class BlockInclude(Block_):
    @override(Block_)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "{header_filename}"')


class BlockMessageEncoder(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        pass


class BlockList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [BlockAheadNotice(), BlockInclude()]


class RendererC(Renderer_):
    """Renderer for C language (c file)."""

    @override(Renderer_)
    def file_extension(self) -> str:
        return ".c"

    @override(Renderer_)
    def formatter(self) -> CFormatter:
        return CFormatter()

    @override(Renderer_)
    def block(self) -> Block_:
        return BlockList()
