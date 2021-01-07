"""
Renderer for C header file.
"""

from typing import Any, List

from bitproto._ast import Array, Proto
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindAlias,
                                     BlockBindConstant, BlockBindEnum,
                                     BlockBindEnumField, BlockBindMessage,
                                     BlockBindMessageField, BlockBindProto,
                                     BlockComposition, BlockConditional,
                                     BlockDeferable, BlockWrapper)
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
        self.push("#include <stdint.h>")
        self.push("#include <stdio.h>")


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


class BlockGeneralMacroDefines(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push('#define btoa(x) ((x) ? "true" : "false")')


class BlockConstant(BlockBindConstant[F]):
    def render_constant_define(self) -> None:
        self.push(f"#define {self.constant_name} {self.constant_value}")

    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_constant_define()


class BlockAlias(BlockBindAlias[F]):
    def render_alias_typedef_to_array(self) -> None:
        array_type = cast_or_raise(Array, self.d.type)
        aliased_type = self.formatter.format_type(array_type.element_type)
        name = self.formatter.format_alias_name(self.d)
        capacity = array_type.cap
        self.push(f"typedef {aliased_type} {name}[{capacity}];")

    def render_alias_typedef_to_common(self) -> None:
        aliased_type = self.formatter.format_type(self.d.type)
        name = self.formatter.format_alias_name(self.d)
        self.push(f"typedef {aliased_type} {name};")

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
        array_type = cast_or_raise(Array, self.d.type)
        field_name = self.d.name
        field_definition = self.formatter.format_array_type(array_type, field_name)
        self.push(f"{field_definition};")

    def render_field_declaration_common(self) -> None:
        field_type = self.d.type
        field_name = self.d.name
        type_string = self.formatter.format_type(field_type)
        self.push(f"{type_string} {field_name};")

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


class BlockConstantList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockConstant(constant, name=name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockAliasList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAlias(alias, name=name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockEnum(enum, name=name)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]


class BlockMessageList(BlockComposition[F]):
    @override(BlockComposition[F])
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessage(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]


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
            BlockGeneralMacroDefines(),
            BlockAliasList(),
            BlockConstantList(),
            BlockEnumList(),
            BlockMessageList(),
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
