"""
Renderer for C header file.
"""

from typing import Any, List, Optional

from bitproto._ast import Alias, Array, BoundDefinition, Constant, Enum, Message, Proto
from bitproto.errors import InternalError
from bitproto.renderer.block import (
    Block,
    BlockAheadNotice,
    BlockBindAlias,
    BlockBindConstant,
    BlockBindEnum,
    BlockBindEnumField,
    BlockBindMessage,
    BlockBindMessageField,
    BlockBindProto,
    BlockBoundDefinitionDispatcher,
    BlockComposition,
    BlockDeferable,
    BlockWrapper,
)
from bitproto.renderer.impls.c.formatter import CFormatter as F
from bitproto.renderer.renderer import Renderer
from bitproto.utils import (
    cached_property,
    cast_or_raise,
    override,
    snake_case,
    upper_case,
)


class BlockProtoDocstring(BlockBindProto[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()


class BlockIncludeGuard(BlockDeferable[F]):
    def format_proto_macro_name(self) -> str:
        proto_name = snake_case(self.bound.name).upper()
        return f"__BITPROTO__{proto_name}_H__"

    @override(Block)
    def render(self) -> None:
        macro_name = self.format_proto_macro_name()
        self.push(f"#ifndef {macro_name}")
        self.push(f"#define {macro_name} 1")

    @override(BlockDeferable)
    def defer(self) -> None:
        self.push(f"#endif")


class BlockIncludeGeneralHeaders(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("#include <inttypes.h>")
        self.push("#include <stddef.h>")
        self.push("#include <stdint.h>")
        self.push("#ifndef __cplusplus")
        self.push("#include <stdbool.h>")
        self.push("#endif")


class BlockIncludeHeaders(BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockIncludeGeneralHeaders()

    @override(BlockWrapper)
    def after(self) -> None:
        self.push_empty_line()
        self.push('#include "bitproto.h"')


class BlockExternCPlusPlus(BlockDeferable[F]):
    @override(Block)
    def render(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push('extern "C" {')
        self.push("#endif")

    @override(BlockDeferable)
    def defer(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push("}")
        self.push("#endif")


class BlockIncludeChildProtoHeader(BlockBindProto[F]):
    @override(Block)
    def render(self) -> None:
        self.push(self.formatter.format_import_statement(self.d))


class BlockConstant(BlockBindConstant[F]):
    def render_constant_define(self) -> None:
        self.push(f"#define {self.constant_name} {self.constant_value}")

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_constant_define()


class BlockAliasProcessorBase(BlockBindAlias[F]):
    @cached_property
    def function_name(self) -> str:
        return self.formatter.format_bp_alias_processor_name(self.d)

    @cached_property
    def function_signature(self) -> str:
        return f"void {self.function_name}(void *data, struct BpProcessorContext *ctx)"


class BlockAliasProcessorDeclaration(BlockAliasProcessorBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.function_signature};")


class BlockAliasJsonFormatterBase(BlockBindAlias[F]):
    @cached_property
    def function_name(self) -> str:
        return self.formatter.format_bp_alias_json_formatter_name(self.d)

    @cached_property
    def function_signature(self) -> str:
        return f"void {self.function_name}(void *data, struct BpJsonFormatContext *ctx)"


class BlockAliasJsonFormatterDeclaration(BlockAliasJsonFormatterBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.function_signature};")


class BlockAliasDef(BlockBindAlias[F]):
    def render_alias_typedef_to_array(self) -> None:
        self.push(f"typedef {self.aliased_type};")

    def render_alias_typedef_to_common(self) -> None:
        self.push(f"typedef {self.aliased_type} {self.alias_name};")

    def render_alias_typedef(self) -> None:
        if isinstance(self.d.type, Array):
            self.render_alias_typedef_to_array()
        else:
            self.render_alias_typedef_to_common()
        self.push_typing_hint_inline_comment()

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_alias_typedef()


class BlockAliasFunctionDeclarationsForInternal(BlockBindAlias[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAliasProcessorDeclaration(self.d),
            BlockAliasJsonFormatterDeclaration(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumField(BlockBindEnumField[F]):
    def render_define_macro(self) -> None:
        self.push(f"#define {self.enum_field_name} {self.enum_field_value}")

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_define_macro()


class BlockEnumFieldList(BlockBindEnum[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockEnumField(field) for field in self.d.fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumDef(BlockBindEnum[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"typedef {self.enum_uint_type} {self.enum_name};")
        self.push_typing_hint_inline_comment()


class BlockEnumDefs(BlockBindEnum[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockEnumDef(self.d),
            BlockEnumFieldList(self.d),
        ]


class BlockMessageField(BlockBindMessageField[F]):
    def render_field_declaration_array(self) -> None:
        self.push(f"{self.message_field_type};")

    def render_field_declaration_common(self) -> None:
        self.push(f"{self.message_field_type} {self.message_field_name};")

    def render_field_declaration(self) -> None:
        if isinstance(self.d.type, Array):
            self.render_field_declaration_array()
        else:
            self.render_field_declaration_common()

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_field_declaration()
        self.push_typing_hint_inline_comment()


class BlockMessageLengthMacro(BlockBindMessage[F]):
    @override(Block)
    def render(self) -> None:
        self.push_comment(f"Number of bytes to encode struct {self.message_name}")
        self.push(f"#define {self.message_size_constant_name} {self.message_nbytes}")


class BlockMessageFieldList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockMessageField(field, indent=4) for field in self.d.sorted_fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageStruct(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockMessageFieldList(self.d, name=self.name)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_definition_comments()
        self.push(f"struct {self.message_name} {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")
        option_name = "c.struct_packing_alignment"
        alignment = self.bound.get_option_as_int_or_raise(option_name)
        if alignment > 0:
            self.push_string(f"__attribute__((packed, aligned({alignment})))")
        self.push_string(";", separator="")


class BlockMessageEncoderBase(BlockBindMessage[F]):
    @cached_property
    def function_name(self) -> str:
        return f"Encode{self.message_name}"

    @cached_property
    def function_comment(self) -> str:
        return f"Encode struct {self.message_name} to given buffer s."

    @cached_property
    def function_signature(self) -> str:
        return f"int {self.function_name}({self.message_type} *m, unsigned char *s)"


class BlockMessageEncoderFunctionDeclaration(BlockMessageEncoderBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature};")


class BlockMessageDecoderBase(BlockBindMessage[F]):
    @cached_property
    def function_name(self) -> str:
        return f"Decode{self.message_name}"

    @cached_property
    def function_comment(self) -> str:
        return f"Decode struct {self.message_name} from given buffer s."

    @cached_property
    def function_signature(self) -> str:
        return f"int {self.function_name}({self.message_type} *m, unsigned char *s)"


class BlockMessageDecoderFunctionDeclaration(BlockMessageDecoderBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature};")


class BlockMessageBpJsonFormatterBase(BlockBindMessage[F]):
    @cached_property
    def function_name(self) -> str:
        return self.formatter.format_bp_message_json_formatter_name(self.d)

    @cached_property
    def function_signature(self) -> str:
        return f"void {self.function_name}(void *data, struct BpJsonFormatContext *ctx)"


class BlockMessageBpJsonFormatterDeclaration(BlockMessageBpJsonFormatterBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.function_signature};")


class BlockMessageJsonFormatterBase(BlockBindMessage[F]):
    @cached_property
    def function_name(self) -> str:
        return f"Json{self.message_name}"

    @cached_property
    def function_comment(self) -> str:
        return f"Format struct {self.message_name} to a json format string."

    @cached_property
    def function_signature(self) -> str:
        return f"int {self.function_name}({self.message_type} *m, char *s)"


class BlockMessageJsonFormatterFunctionDeclaration(BlockMessageJsonFormatterBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature};")


class BlockMessageFieldDescriptorsIniterBase(BlockBindMessage[F]):
    @cached_property
    def function_name(self) -> str:
        return self.formatter.format_bp_message_field_descriptor_initer(self.d)

    @cached_property
    def function_signature(self) -> str:
        return f"void {self.function_name}({self.message_type} *m, struct BpMessageFieldDescriptor *fds)"


class BlockMessageProcessorBase(BlockBindMessage[F]):
    @cached_property
    def function_name(self) -> str:
        return self.formatter.format_bp_message_processor_name(self.d)

    @cached_property
    def function_signature(self) -> str:
        return f"void {self.function_name}(void *data, struct BpProcessorContext *ctx)"


class BlockMessageProcessorDeclaration(BlockMessageProcessorBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.function_signature};")


class BlockMessageFunctionDeclarationsForUser(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageEncoderFunctionDeclaration(self.d),
            BlockMessageDecoderFunctionDeclaration(self.d),
            BlockMessageJsonFormatterFunctionDeclaration(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageFunctionDeclarationsForInternal(
    BlockBindMessage[F], BlockComposition[F]
):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageProcessorDeclaration(self.d),
            BlockMessageBpJsonFormatterDeclaration(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageDef(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageLengthMacro(self.d),
            BlockMessageStruct(self.d),
        ]


class BlockImportList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockIncludeChildProtoHeader(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockDefineMacroOpMode(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("#define BITPROTO_OPTIMIZATION_MODE 1")


class BlockDataStructuresList(BlockBoundDefinitionDispatcher[F]):
    @override(BlockBoundDefinitionDispatcher)
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Alias):
            return BlockAliasDef(d)
        if isinstance(d, Constant):
            return BlockConstant(d)
        if isinstance(d, Enum):
            return BlockEnumDefs(d)
        if isinstance(d, Message):
            return BlockMessageDef(d)
        return None


class BlockFunctionDeclarationsForUserList(BlockBoundDefinitionDispatcher[F]):
    @override(BlockBoundDefinitionDispatcher)
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Message):
            return BlockMessageFunctionDeclarationsForUser(d)
        return None


class BlockFunctionDeclarationsForInternalList(BlockBoundDefinitionDispatcher[F]):
    @override(BlockBoundDefinitionDispatcher)
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Alias):
            return BlockAliasFunctionDeclarationsForInternal(d)
        if isinstance(d, Message):
            return BlockMessageFunctionDeclarationsForInternal(d)
        return None


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockProtoDocstring(self.bound),
            BlockIncludeGuard(),
            BlockIncludeHeaders(),
            BlockExternCPlusPlus(),
            BlockImportList(),
            BlockDataStructuresList(),
            BlockFunctionDeclarationsForUserList(),
            BlockFunctionDeclarationsForInternalList(),
        ]


class BlockMessageFunctionDeclarationsForUserOpMode(
    BlockBindMessage[F], BlockComposition[F]
):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageEncoderFunctionDeclaration(self.d),
            BlockMessageDecoderFunctionDeclaration(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockFunctionDeclarationsForUserListOpMode(BlockBoundDefinitionDispatcher[F]):
    @override(BlockBoundDefinitionDispatcher)
    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Message):
            filter_messages = self._get_ctx_or_raise().optimization_mode_filter_messages
            if filter_messages:
                if d.name not in filter_messages:
                    return None
            return BlockMessageFunctionDeclarationsForUserOpMode(d)
        return None


class BlockListOpMode(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockProtoDocstring(self.bound),
            BlockIncludeGuard(),
            BlockIncludeGeneralHeaders(),
            BlockExternCPlusPlus(),
            BlockImportList(),
            BlockDefineMacroOpMode(),
            BlockDataStructuresList(),
            BlockFunctionDeclarationsForUserListOpMode(),
        ]


class RendererCHeader(Renderer[F]):
    """Renderer for C language (header)."""

    @override(Renderer)
    def language_name(self) -> str:
        return "c"

    @override(Renderer)
    def file_extension(self) -> str:
        return ".h"

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
