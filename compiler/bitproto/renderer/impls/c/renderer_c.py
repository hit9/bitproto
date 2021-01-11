"""
Renderer for C file.
"""

from typing import List

from bitproto._ast import Array, Definition
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindAlias,
                                     BlockBindEnum, BlockBindMessage,
                                     BlockBindMessageField, BlockComposition,
                                     BlockConditional, BlockDeferable,
                                     BlockWrapper)
from bitproto.renderer.impls.c.formatter import CFormatter as F
from bitproto.renderer.impls.c.renderer_h import (
    BlockMessageDecoderBase, BlockMessageEncoderBase,
    BlockMessageJsonFormatterBase, RendererCHeader)
from bitproto.renderer.renderer import Renderer
from bitproto.utils import cast_or_raise, override


class BlockInclude(Block[F]):
    @override(Block)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "bitproto.h"')
        self.push(f'#include "{header_filename}"')


class BlockArrayProcessorBase(Block[F]):
    def __init__(self, t: Array, d: Definition, indent: int = 0) -> None:
        super().__init__(indent)
        self.t = t
        self.d = d


class BlockArrayProcessorBody(BlockArrayProcessorBase):
    @override(Block)
    def render(self) -> None:
        descriptor = self.formatter.format_bp_array_descriptor(self.t)
        self.push(f"struct BpArrayDescriptor descriptor = {descriptor};")
        self.push("BpEndecodeArray(&descriptor, ctx, data);")


class BlockArrayProcessor(BlockArrayProcessorBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockArrayProcessorBody(self.t, self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        processor_name = self.formatter.format_bp_array_processor_name(self.t, self.d)
        signature = f"void {processor_name}(void *data, struct BpProcessorContext *ctx)"
        self.push(f"{signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockArrayProcessorForAlias(BlockBindAlias[F], BlockConditional[F]):
    @override(BlockConditional)
    def condition(self) -> bool:
        return isinstance(self.d.type, Array)

    @override(BlockConditional)
    def block(self) -> Block[F]:
        array_type = cast_or_raise(Array, self.d.type)
        return BlockArrayProcessor(array_type, self.d)


class BlockAliasProcessorBody(BlockBindAlias[F]):
    @override(Block)
    def render(self) -> None:
        descriptor = self.formatter.format_bp_alias_descriptor(self.d)
        self.push(f"struct BpAliasDescriptor descriptor = {descriptor};")
        self.push("BpEndecodeAlias(&descriptor, ctx, data);")


class BlockAliasProcessor(BlockBindAlias[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockAliasProcessorBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        processor_name = self.formatter.format_bp_alias_processor_name(self.d)
        signature = f"void {processor_name}(void *data, struct BpProcessorContext *ctx)"
        self.push(f"{signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockAliasProcessor_(BlockBindAlias[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockArrayProcessorForAlias(self.d), BlockAliasProcessor(self.d)]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockAliasProcessorList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAliasProcessor_(d)
            for _, d in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n\n"


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


class BlockArrayProcessorForMessageField(BlockBindMessageField[F], BlockConditional[F]):
    @override(BlockConditional)
    def condition(self) -> bool:
        return isinstance(self.d.type, Array)

    @override(BlockConditional)
    def block(self) -> Block[F]:
        array_type = cast_or_raise(Array, self.d.type)
        return BlockArrayProcessor(array_type, self.d)


class BlockArrayProcessorForMessageFieldList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockArrayProcessorForMessageField(d) for d in self.d.sorted_fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockMessageProcessorFieldItem(BlockBindMessageField[F]):
    @override(Block)
    def render(self) -> None:
        bp_type = self.formatter.format_bp_type(self.d.type, self.d)
        self.push("{")
        self.push_string(f"(void *)&(m->{self.message_field_name})")
        self.push_string(f"{bp_type}", separator=", ")
        self.push_string("},")


class BlockMessageProcessorFieldList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageProcessorFieldItem(d, indent=self.indent)
            for d in self.d.sorted_fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageProcessorBody(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageProcessorFieldList(self.d, indent=self.indent + 4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"{self.message_type} *m = ({self.message_type} *)(data);")
        self.push("struct BpMessageFieldDescriptor field_descriptors[] = {")

    @override(BlockWrapper)
    def after(self) -> None:
        bp_type = self.formatter.format_bp_message_descriptor(self.d)
        self.push("};")
        self.push(f"struct BpMessageDescriptor descriptor = {bp_type};")
        self.push("BpEndecodeMessage(&descriptor, ctx, data);")


class BlockMessageProcessor(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageProcessorBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        processor_name = self.formatter.format_bp_message_processor_name(self.d)
        signature = f"void {processor_name}(void *data, struct BpProcessorContext *ctx)"
        self.push(f"{signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageEncoder(BlockMessageEncoderBase):
    @override(Block)
    def render(self) -> None:
        processor_name = self.formatter.format_bp_message_processor_name(self.d)
        self.push(f"{self.function_signature} {{")
        self.push("struct BpProcessorContext ctx = BpContext(true, s);", indent=4)
        self.push(f"{processor_name}((void *)m, &ctx);", indent=4)
        self.push("return 0;", indent=4)
        self.push("}")


class BlockMessageDecoder(BlockMessageDecoderBase):
    @override(Block)
    def render(self) -> None:
        processor_name = self.formatter.format_bp_message_processor_name(self.d)
        self.push(f"{self.function_signature} {{")
        self.push("struct BpProcessorContext ctx = BpContext(false, s);", indent=4)
        self.push(f"{processor_name}((void *)m, &ctx);", indent=4)
        self.push("return 0;", indent=4)
        self.push("}")


class BlockMessageFunctions(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockArrayProcessorForMessageFieldList(self.d),
            BlockMessageProcessor(self.d),
            BlockMessageEncoder(self.d),
            BlockMessageDecoder(self.d),
        ]


class BlockMessageFunctionsList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageFunctions(d)
            for _, d in self.bound.messages(recursive=True, bound=self.bound)
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
            BlockAliasProcessorList(),
            BlockMessageFunctionsList(),
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
