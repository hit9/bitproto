"""
Renderer for Python.
"""
from typing import List

from bitproto.renderer.block import Block, BlockAheadNotice, BlockComposition
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.py.formatter import PyFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override


class BlockGeneralImports(Block):
    @override(Block)
    def render(self) -> None:
        self.push("import json")


class BlockGeneralFunctionInt8(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int8(i: int) -> int:")
        self.push("if i < 128:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 256", indent=4)


class BlockGeneralFunctionInt16(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int16(i: int) -> int:")
        self.push("if i < 32768:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 65536", indent=4)


class BlockGeneralFunctionInt32(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int32(i: int) -> int:")
        self.push("if i < 2147483648:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 4294967296", indent=4)


class BlockGeneralFunctionInt64(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int64(i: int) -> int:")
        self.push("if i < 9223372036854775808:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 18446744073709551616", indent=4)


class BlockGeneralGlobalFunctions(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockGeneralFunctionInt8(),
            BlockGeneralFunctionInt16(),
            BlockGeneralFunctionInt32(),
            BlockGeneralFunctionInt64(),
        ]


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
