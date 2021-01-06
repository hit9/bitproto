"""
Renderer for C file.
"""

from typing import List

from bitproto.renderer.block import BlockAheadNotice
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.impls.c.renderer_h import (
    Block_, BlockComposition_, BlockConditional_, BlockDefinition_,
    BlockMessageBase, BlockMessageDecoderBase, BlockMessageEncoderBase,
    BlockMessageJsonFormatterBase, BlockWrapper_, Renderer_, RendererCHeader)
from bitproto.utils import override


class BlockInclude(Block_):
    @override(Block_)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "{header_filename}"')


class BlockMessageEncoderBody(BlockMessageEncoderBase):
    @override(Block_)
    def render(self) -> None:
        pass  # TODO


class BlockMessageEncoder(BlockMessageEncoderBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockMessageEncoderBody(self.as_message, indent=4)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")


class BlockMessageDecoderBody(BlockMessageDecoderBase):
    @override(Block_)
    def render(self) -> None:
        pass  # TODO


class BlockMessageDecoder(BlockMessageDecoderBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockMessageDecoderBody(self.as_message, indent=4)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")


class BlockMessageJsonFormatterBody(BlockMessageJsonFormatterBase):
    @override(Block_)
    def render(self) -> None:
        pass  # TODO


class BlockMessageJsonFormatterWrapper(BlockMessageJsonFormatterBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockMessageJsonFormatterBody(self.as_message, indent=4)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")


class BlockMessageJsonFormatter(BlockMessageJsonFormatterBase, BlockConditional_):
    @override(BlockConditional_)
    def condition(self) -> bool:
        return self.is_enabled()

    @override(BlockConditional_)
    def block(self) -> Block_:
        return BlockMessageJsonFormatterWrapper(self.as_message)


class BlockMessageFunctionList(BlockMessageBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageEncoder(self.as_message),
            BlockMessageDecoder(self.as_message),
            BlockMessageJsonFormatter(self.as_message),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n\n"


class BlockFunctionList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageFunctionList(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n\n"


class BlockList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [BlockAheadNotice(), BlockInclude(), BlockFunctionList()]


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
