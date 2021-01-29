"""
Renderer for C file.
"""

from typing import List, Optional

from bitproto._ast import (
    Alias,
    Array,
    BoundDefinition,
    Definition,
    Enum,
    Message,
    MessageField,
)
from bitproto.renderer.block import (
    Block,
    BlockAheadNotice,
    BlockBindAlias,
    BlockBindEnum,
    BlockBindMessage,
    BlockBindMessageField,
    BlockBoundDefinitionDispatcher,
    BlockComposition,
    BlockConditional,
    BlockDeferable,
    BlockWrapper,
)
from bitproto.renderer.impls.c.formatter import CFormatter as F
from bitproto.renderer.impls.c.renderer_h import (
    BlockAliasJsonFormatterBase,
    BlockAliasProcessorBase,
    BlockMessageBpJsonFormatterBase,
    BlockMessageDecoderBase,
    BlockMessageEncoderBase,
    BlockMessageFieldDescriptorsIniterBase,
    BlockMessageJsonFormatterBase,
    BlockMessageProcessorBase,
    RendererCHeader,
)
from bitproto.renderer.renderer import Renderer
from bitproto.utils import cached_property, cast_or_raise, override


class BlockInclude(Block[F]):
    @override(Block)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "bitproto.h"')
        self.push(f'#include "{header_filename}"')


class BlockArrayBpFunctionBase(Block[F]):
    def __init__(self, t: Array, d: Definition, indent: int = 0) -> None:
        super().__init__(indent)
        self.t = t
        self.d = d

    @cached_property
    def array_descriptor(self) -> str:
        return self.formatter.format_bp_array_descriptor(self.t)


class BlockArrayProcessorBody(BlockArrayBpFunctionBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"struct BpArrayDescriptor descriptor = {self.array_descriptor};")
        self.push("BpEndecodeArray(&descriptor, ctx, data);")


class BlockArrayProcessor(BlockArrayBpFunctionBase, BlockWrapper[F]):
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


class BlockArrayJsonFormatterBody(BlockArrayBpFunctionBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"struct BpArrayDescriptor descriptor = {self.array_descriptor};")
        self.push("BpJsonFormatArray(&descriptor, ctx, data);")


class BlockArrayJsonFormatter(BlockArrayBpFunctionBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockArrayJsonFormatterBody(self.t, self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        json_formatter_name = self.formatter.format_bp_array_json_formatter_name(
            self.t, self.d
        )
        signature = (
            f"void {json_formatter_name}(void *data, struct BpJsonFormatContext *ctx)"
        )
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


class BlockArrayJsonFormatterForAlias(BlockBindAlias[F], BlockConditional[F]):
    @override(BlockConditional)
    def condition(self) -> bool:
        return isinstance(self.d.type, Array)

    @override(BlockConditional)
    def block(self) -> Block[F]:
        array_type = cast_or_raise(Array, self.d.type)
        return BlockArrayJsonFormatter(array_type, self.d)


class BlockAliasProcessorBody(BlockBindAlias[F]):
    @override(Block)
    def render(self) -> None:
        descriptor = self.formatter.format_bp_alias_descriptor(self.d)
        self.push(f"struct BpAliasDescriptor descriptor = {descriptor};")
        self.push("BpEndecodeAlias(&descriptor, ctx, data);")


class BlockAliasProcessor(BlockAliasProcessorBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockAliasProcessorBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockAliasFunctions(BlockBindAlias[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockArrayProcessorForAlias(self.d),
            BlockArrayJsonFormatterForAlias(self.d),
            BlockAliasProcessor(self.d),
            BlockAliasJsonFormatter(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockAliasJsonFormatterBody(BlockBindAlias[F]):
    @override(Block)
    def render(self) -> None:
        descriptor = self.formatter.format_bp_alias_descriptor(self.d)
        self.push(f"struct BpAliasDescriptor descriptor = {descriptor};")
        self.push("BpJsonFormatAlias(&descriptor, ctx, data);")


class BlockAliasJsonFormatter(BlockAliasJsonFormatterBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockAliasJsonFormatterBody(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


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


class BlockArrayJsonFormatterForMessageField(
    BlockBindMessageField[F], BlockConditional[F]
):
    @override(BlockConditional)
    def condition(self) -> bool:
        return isinstance(self.d.type, Array)

    @override(BlockConditional)
    def block(self) -> Block[F]:
        array_type = cast_or_raise(Array, self.d.type)
        return BlockArrayJsonFormatter(array_type, self.d)


class BlockArrayJsonFormatterForMessageFieldList(
    BlockBindMessage[F], BlockComposition[F]
):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockArrayJsonFormatterForMessageField(d) for d in self.d.sorted_fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockMessageProcessorFieldItem(BlockBindMessageField[F]):
    def __init__(
        self, d: MessageField, name: Optional[str] = None, indent: int = 0, i: int = 0
    ) -> None:
        super().__init__(d, name, indent)
        self.i: int = i

    @override(Block)
    def render(self) -> None:
        bp_type = self.formatter.format_bp_type(self.d.type, self.d)
        index = self.formatter.format_int_value(self.i)
        name = self.formatter.format_str_value(self.d.name)
        self.push(f"fds[{index}] =")
        self.push_string("BpMessageFieldDescriptor(")
        self.push_string(f"(void *)&(m->{self.message_field_name})", separator="")
        self.push_string(f"{bp_type}", separator=", ")
        self.push_string(f"{name}", separator=", ")
        self.push_string(");", separator="")


class BlockMessageProcessorFieldList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageProcessorFieldItem(d, indent=self.indent, i=i)
            for i, d in enumerate(self.d.sorted_fields())
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageFieldDescriptorsIniter(
    BlockMessageFieldDescriptorsIniterBase, BlockWrapper[F]
):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageProcessorFieldList(self.d, indent=self.indent + 4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageDescriptorBuild(BlockMessageFieldDescriptorsIniterBase):
    @override(Block)
    def render(self) -> None:
        nfields = self.formatter.format_int_value(self.d.nfields())
        bp_type = self.formatter.format_bp_message_descriptor(self.d)
        initer = self.formatter.format_bp_message_field_descriptor_initer(self.d)

        self.push(f"{self.message_type} *m = ({self.message_type} *)(data);")
        self.push(f"struct BpMessageFieldDescriptor field_descriptors[{nfields}];")
        self.push(f"{initer}(m, field_descriptors);")
        self.push(f"struct BpMessageDescriptor descriptor = {bp_type};")


class BlockMessageProcessor(BlockMessageProcessorBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageDescriptorBuild(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("BpEndecodeMessage(&descriptor, ctx, data);", indent=4)
        self.push("}")


class BlockMessageBpJsonFormatter(BlockMessageBpJsonFormatterBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageDescriptorBuild(self.d, indent=4)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"{self.function_signature} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("BpJsonFormatMessage(&descriptor, ctx, data);", indent=4)
        self.push("}")


class BlockMessageEncoder(BlockMessageEncoderBase):
    @override(Block)
    def render(self) -> None:
        processor_name = self.formatter.format_bp_message_processor_name(self.d)
        self.push(f"{self.function_signature} {{")
        self.push(
            "struct BpProcessorContext ctx = BpProcessorContext(true, s);", indent=4
        )
        self.push(f"{processor_name}((void *)m, &ctx);", indent=4)
        self.push("return 0;", indent=4)
        self.push("}")


class BlockMessageDecoder(BlockMessageDecoderBase):
    @override(Block)
    def render(self) -> None:
        processor_name = self.formatter.format_bp_message_processor_name(self.d)
        self.push(f"{self.function_signature} {{")
        self.push(
            "struct BpProcessorContext ctx = BpProcessorContext(false, s);", indent=4
        )
        self.push(f"{processor_name}((void *)m, &ctx);", indent=4)
        self.push("return 0;", indent=4)
        self.push("}")


class BlockMessageJsonFormatter(BlockMessageJsonFormatterBase):
    @override(Block)
    def render(self) -> None:
        json_formatter_name = self.formatter.format_bp_message_json_formatter_name(
            self.d
        )
        self.push(f"{self.function_signature} {{")
        self.push("struct BpJsonFormatContext ctx = BpJsonFormatContext(s);", indent=4)
        self.push(f"{json_formatter_name}((void *)m, &ctx);", indent=4)
        self.push("return ctx.n;", indent=4)
        self.push("}")


class BlockMessageFunctions(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockArrayProcessorForMessageFieldList(self.d),
            BlockArrayJsonFormatterForMessageFieldList(self.d),
            BlockMessageFieldDescriptorsIniter(self.d),
            BlockMessageProcessor(self.d),
            BlockMessageBpJsonFormatter(self.d),
            BlockMessageEncoder(self.d),
            BlockMessageDecoder(self.d),
            BlockMessageJsonFormatter(self.d),
        ]


class BlockBoundDefinitionList(BlockBoundDefinitionDispatcher[F]):
    @override(BlockBoundDefinitionDispatcher)
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Alias):
            return BlockAliasFunctions(d)
        if isinstance(d, Message):
            return BlockMessageFunctions(d)
        return None


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockInclude(),
            BlockBoundDefinitionList(),
        ]


class BlockIncludeOpMode(Block[F]):
    @override(Block)
    def render(self) -> None:
        header_filename = self.formatter.format_out_filename(self.bound, extension=".h")
        self.push(f'#include "{header_filename}"')


class BlockMessageEncoderOpMode(BlockMessageEncoderBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.function_signature} {{")
        l = self.formatter.format_op_mode_encode_message(self.d)
        for line in l:
            self.push(line, indent=4)
        self.push("return 0;", indent=4)
        self.push("}")


class BlockMessageDecoderOpMode(BlockMessageDecoderBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.function_signature} {{")
        l = self.formatter.format_op_mode_decode_message(self.d)
        for line in l:
            self.push(line, indent=4)
        self.push("return 0;", indent=4)
        self.push("}")


class BlockMessageFunctionsOpMode(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageEncoderOpMode(self.d),
            BlockMessageDecoderOpMode(self.d),
        ]


class BlockBoundDefinitionListOpMode(BlockBoundDefinitionDispatcher[F]):
    @override(BlockBoundDefinitionDispatcher)
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Message):
            render_ctx = self._get_ctx_or_raise()
            filter_messages = render_ctx.optimization_mode_filter_messages
            if filter_messages:
                if d.name not in filter_messages:
                    return None
            return BlockMessageFunctionsOpMode(d)
        return None


class BlockListOpMode(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockIncludeOpMode(),
            BlockBoundDefinitionListOpMode(),
        ]


class RendererC(Renderer[F]):
    """Renderer for C language (c file)."""

    @override(Renderer)
    def language_name(self) -> str:
        return "c"

    @override(Renderer)
    def file_extension(self) -> str:
        return ".c"

    @override(Renderer)
    def support_optimization(self) -> bool:
        return True

    @override(Renderer)
    def formatter(self) -> F:
        return F()

    @override(Renderer)
    def block(self) -> Block[F]:
        if self.optimization_mode:
            return BlockListOpMode()
        return BlockList()
