"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import Block, BlockForDefinition, BitprotoDeclarationBlock
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.renderer import Renderer
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.impls.c.renderer_h import RendererCHeader


class IncludeHeaderFile(Block):
    def __init__(self, header_filename: str) -> None:
        super(IncludeHeaderFile, self).__init__()
        self.header_filename = header_filename

    def render(self) -> None:
        self.push(f'#include "{self.header_filename}"')


class MessageEncoderBlock(BlockForDefinition):
    def render(self) -> None:
        pass


class RendererC(Renderer):
    """Renderer for C language (c file)."""

    def file_extension(self) -> str:
        return ".c"

    def formatter(self) -> Formatter:
        return CFormatter()

    def blocks(self) -> List[Block]:
        header_filename = RendererCHeader(self.proto, self.outdir).out_filename
        return [BitprotoDeclarationBlock(), IncludeHeaderFile(header_filename)]
