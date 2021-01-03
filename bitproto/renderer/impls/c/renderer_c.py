"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import Block, BlockAheadNotice, BlockDefinition
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.impls.c.renderer_h import RendererCHeader
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override


class BlockInclude(Block):
    def __init__(self, header_filename: str) -> None:
        super(BlockInclude, self).__init__()
        self.header_filename = header_filename

    @override(Block)
    def render(self) -> None:
        self.push(f'#include "{self.header_filename}"')


class BlockMessageEncoder(BlockDefinition):
    @override(Block)
    def render(self) -> None:
        pass


class RendererC(Renderer):
    """Renderer for C language (c file)."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".c"

    @override(Renderer)
    def formatter(self) -> Formatter:
        return CFormatter()

    @override(Renderer)
    def blocks(self) -> List[Block]:
        header_filename = self.format_out_filename(extension=".h")
        return [BlockAheadNotice(), BlockInclude(header_filename)]
