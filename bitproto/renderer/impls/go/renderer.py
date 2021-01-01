"""
Renderer for Go.
"""

from typing import List

from bitproto.renderer.block import Block
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.renderer import Renderer
from bitproto.renderer.impls.go.formatter import GoFormatter


class RendererGo(Renderer):
    """Renderer for Go language."""

    def file_extension(self) -> str:
        return ".go"

    def formatter(self) -> Formatter:
        return GoFormatter()

    def blocks(self) -> List[Block]:
        pass  # TODO
