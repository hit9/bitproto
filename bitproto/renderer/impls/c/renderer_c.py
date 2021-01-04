"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.impls.c.renderer_h import RendererCHeader
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override


class BlockInclude(Block):
    @override(Block)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "{header_filename}"')


class BlockMessageEncoder(BlockDefinition):
    @override(Block)
    def render(self) -> None:
        pass


class BlockList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [BlockAheadNotice(), BlockInclude()]


class RendererC(Renderer):
    """Renderer for C language (c file)."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".c"

    @override(Renderer)
    def formatter(self) -> Formatter:
        return CFormatter()

    @override(Renderer)
    def block(self) -> Block:
        return BlockList()
