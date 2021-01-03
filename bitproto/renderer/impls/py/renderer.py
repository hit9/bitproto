"""
Renderer for Python.
"""
from typing import List

from bitproto.renderer.block import Block, BlockAheadNotice
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.py.formatter import PyFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override


class BlockGeneralImports(Block):
    @override(Block)
    def render(self) -> None:
        self.push("import json")


class BlockGeneralGlobalFunctions(Block):
    @override(Block)
    def render(self) -> None:
        pass


class RendererPy(Renderer):
    """Renderer for Python language."""

    def file_extension(self) -> str:
        return ".py"

    def formatter(self) -> Formatter:
        return PyFormatter()

    def blocks(self) -> List[Block]:
        return [
            BlockAheadNotice(),
            BlockGeneralImports(),
            BlockGeneralGlobalFunctions(),
        ]
