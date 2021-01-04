"""
Renderer for Go.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.go.formatter import GoFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override

Renderer_ = Renderer[GoFormatter]
Block_ = Block[GoFormatter]
BlockComposition_ = BlockComposition[GoFormatter]
BlockWrapper_ = BlockWrapper[GoFormatter]
BlockDefinition_ = BlockDefinition[GoFormatter]


class RendererGo(Renderer_):
    """Renderer for Go language."""

    @override(Renderer_)
    def file_extension(self) -> str:
        return ".go"

    @override(Renderer_)
    def formatter(self) -> GoFormatter:
        return GoFormatter()

    @override(Renderer_)
    def block(self) -> Block_:
        pass  # TODO
