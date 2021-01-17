"""
Renderer for C header file.
"""

from typing import Any, List, Optional

from bitproto._ast import (Alias, Array, BoundDefinition, Constant, Enum,
                           Message, Proto)
from bitproto.errors import InternalError
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindAlias,
                                     BlockBindConstant, BlockBindEnum,
                                     BlockBindEnumField, BlockBindMessage,
                                     BlockBindMessageField, BlockBindProto,
                                     BlockComposition, BlockDeferable,
                                     BlockWrapper)
from bitproto.renderer.impls.c.formatter import CFormatter as F
from bitproto.renderer.renderer import Renderer
from bitproto.utils import (cached_property, cast_or_raise, override,
                            snake_case, upper_case)


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
        self.push(f"#ifndef  {macro_name}")
        self.push(f"#define  {macro_name} 1")

    @override(BlockDeferable)
    def defer(self) -> None:
        self.push(f"#endif")


class BlockIncludeGeneralHeaders(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("#include <inttypes.h>")
        self.push("#include <stdbool.h>")
        self.push("#include <stddef.h>")
        self.push("#include <stdint.h>")


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


class BlockAlias(BlockBindAlias[F]):
    def render_alias_typedef_to_array(self) -> None:
        self.push(f"typedef {self.aliased_type};")

    def render_alias_typedef_to_common(self) -> None:
        self.push(f"typedef {self.aliased_type} {self.alias_name};")

    def render_alias_typedef(self) -> None:
        if isinstance(self.d.type, Array):
            self.render_alias_typedef_to_array()
        else:
            self.render_alias_typedef_to_common()

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_alias_typedef()


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


class BlockEnum(BlockBindEnum[F], BlockWrapper[F]):
    @override(BlockWrapper[F])
    def before(self) -> None:
        self.push_definition_comments()
        self.render_enum_typedef()

    @override(BlockWrapper[F])
    def wraps(self) -> Block:
        return BlockEnumFieldList(self.d)

    def render_enum_typedef(self) -> None:
        self.push(f"typedef {self.enum_uint_type} {self.enum_name};")


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

    def is_enabled(self) -> bool:
        option_name = "c.enable_render_json_formatter"
        return self.bound.get_option_as_bool_or_raise(option_name)


class BlockMessageJsonFormatterFunctionDeclaration(BlockMessageJsonFormatterBase):
    @override(Block)
    def render(self) -> None:
        if not self.is_enabled():
            return
        self.push_comment(self.function_comment)
        self.push(f"{self.function_signature};")


class BlockMessage(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageLengthMacro(self.d),
            BlockMessageStruct(self.d),
            BlockMessageEncoderFunctionDeclaration(self.d),
            BlockMessageDecoderFunctionDeclaration(self.d),
            BlockMessageJsonFormatterFunctionDeclaration(self.d),
        ]


class BlockImportList(BlockComposition[F]):
    @override(BlockComposition[F])
    def blocks(self) -> List[Block[F]]:
        return [
            BlockIncludeChildProtoHeader(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition[F])
    def separator(self) -> str:
        return "\n"


class BlockBoundDefinitionList(BlockComposition[F]):
    @override(BlockComposition[F])
    def blocks(self) -> List[Block[F]]:
        b: List[Block[F]] = []
        for _, d in self.bound.filter(
            BoundDefinition, recursive=True, bound=self.bound
        ):
            block = self.dispatch(d)
            if block:
                b.append(block)
        return b

    def dispatch(self, d: BoundDefinition) -> Optional[Block[F]]:
        if isinstance(d, Alias):
            return BlockAlias(d)
        if isinstance(d, Constant):
            return BlockConstant(d)
        if isinstance(d, Enum):
            return BlockEnum(d)
        if isinstance(d, Message):
            return BlockMessage(d)
        return None


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockProtoDocstring(self.bound),
            BlockIncludeGuard(),
            BlockIncludeGeneralHeaders(),
            BlockExternCPlusPlus(),
            BlockImportList(),
            BlockBoundDefinitionList(),
        ]


class RendererCHeader(Renderer[F]):
    """Renderer for C language (header)."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".h"

    @override(Renderer)
    def formatter(self) -> F:
        return F()

    @override(Renderer)
    def block(self) -> Block[F]:
        return BlockList()
