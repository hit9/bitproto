"""
Renderer for C header file.
"""

from typing import Any, List

from bitproto._ast import Array, Proto
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import (cached_property, cast_or_raise, override,
                            snake_case, upper_case)

Renderer_ = Renderer[CFormatter]
Block_ = Block[CFormatter]
BlockComposition_ = BlockComposition[CFormatter]
BlockWrapper_ = BlockWrapper[CFormatter]
BlockDefinition_ = BlockDefinition[CFormatter]


class BlockProtoDocstring(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()


class BlockIncludeGuard(Block_):
    def format_proto_macro_name(self) -> str:
        proto_name = snake_case(self.bound.name).upper()
        return f"__BITPROTO__{proto_name}_H__"

    @override(Block_)
    def render(self) -> None:
        macro_name = self.format_proto_macro_name()
        self.push(f"#ifndef  {macro_name}")
        self.push(f"#define  {macro_name} 1")

    @override(Block_)
    def defer(self) -> None:
        self.push(f"#endif")


class BlockIncludeGeneralHeaders(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("#include <inttypes.h>")
        self.push("#include <stdbool.h>")
        self.push("#include <stdint.h>")
        self.push("#include <stdio.h>")


class BlockExternCPlusPlus(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push('extern "C" {')
        self.push("#endif")

    @override(Block_)
    def defer(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push("}")
        self.push("#endif")


class BlockIncludeChildProtoHeader(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        self.push(self.formatter.format_import_statement(self.as_proto))


class BlockGeneralMacroDefines(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push('#define btoa(x) ((x) ? "true" : "false")')


class BlockConstant(BlockDefinition_):
    def render_constant_define(self) -> None:
        name = self.formatter.format_constant_name(self.as_constant)
        value = self.formatter.format_value(self.as_constant.value)
        self.push(f"#define {name} {value}")

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_constant_define()


class BlockAlias(BlockDefinition_):
    def render_alias_typedef_to_array(self) -> None:
        array_type = cast_or_raise(Array, self.as_alias.type)
        aliased_type = self.formatter.format_type(array_type.element_type)
        name = self.formatter.format_alias_name(self.as_alias)
        capacity = array_type.cap
        self.push(f"typedef {aliased_type} {name}[{capacity}];")

    def render_alias_typedef_to_common(self) -> None:
        aliased_type = self.formatter.format_type(self.as_alias.type)
        name = self.formatter.format_alias_name(self.as_alias)
        self.push(f"typedef {aliased_type} {name};")

    def render_alias_typedef(self) -> None:
        if isinstance(self.as_alias.type, Array):
            self.render_alias_typedef_to_array()
        else:
            self.render_alias_typedef_to_common()

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_alias_typedef()


class BlockEnumField(BlockDefinition_):
    def render_define_macro(self) -> None:
        field = self.as_enum_field
        name = self.formatter.format_enum_field_name(field)
        value = self.formatter.format_int_value(field.value)
        self.push(f"#define {name} {value}")

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_define_macro()


class BlockEnumBase(BlockDefinition_):
    @cached_property
    def enum_name(self) -> str:
        return self.formatter.format_enum_name(self.as_enum)


class BlockEnumFieldList(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [BlockEnumField(field) for field in self.as_enum.fields()]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnum(BlockEnumBase, BlockWrapper_):
    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_definition_comments()
        self.render_enum_typedef()

    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockEnumFieldList(self.as_enum)

    def render_enum_typedef(self) -> None:
        name: str = self.enum_name
        uint_type = self.formatter.format_uint_type(self.as_enum.type)
        self.push(f"typedef {uint_type} {name};")


class BlockMessageField(BlockDefinition_):
    def render_field_declaration_array(self) -> None:
        array_type = cast_or_raise(Array, self.as_message_field.type)
        field_name = self.as_message_field.name
        field_definition = self.formatter.format_array_type(array_type, field_name)
        self.push(f"{field_definition};")

    def render_field_declaration_common(self) -> None:
        field_type = self.as_message_field.type
        field_name = self.as_message_field.name
        type_string = self.formatter.format_type(field_type)
        self.push(f"{type_string} {field_name};")

    def render_field_declaration(self) -> None:
        if isinstance(self.as_message_field.type, Array):
            self.render_field_declaration_array()
        else:
            self.render_field_declaration_common()

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.render_field_declaration()


class BlockMessageBase(BlockDefinition_):
    @cached_property
    def struct_name(self) -> str:
        return self.formatter.format_message_name(self.as_message)


class BlockMessageLengthMacro(BlockMessageBase):
    @override(BlockDefinition_)
    def render(self) -> None:
        message = self.as_message
        struct_name: str = self.struct_name
        struct_name_upper = upper_case(snake_case(struct_name))
        self.push_comment(f"Number of bytes to encode struct {struct_name}")
        nbytes = message.nbytes()
        macro_string = f"#define BYTES_LENGTH_{struct_name_upper} {nbytes}"
        self.push(macro_string)


class BlockMessageFieldList(BlockMessageBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageField(field, indent=4)
            for field in self.as_message.sorted_fields()
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockMessageStruct(BlockMessageBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockMessageFieldList(self.definition, name=self.definition_name)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_definition_comments()
        struct_name: str = self.struct_name
        self.push(f"struct {struct_name} {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")
        option_name = "c.struct_packing_alignment"
        alignment = self.bound.get_option_as_int_or_raise(option_name)
        if alignment > 0:
            self.push_string(f"__attribute__((packed, aligned({alignment})))")
        self.push_string(";", separator="")


class BlockMessageEncoderFunctionDeclaration(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        struct_name: str = self.struct_name
        self.push_comment(f"Encode struct {struct_name} to given buffer s")
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Encode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)


class BlockMessageDecoderFunctionDeclaration(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        struct_name: str = self.struct_name
        self.push_comment(f"Decode struct {struct_name} from given buffer s")
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Decode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)


class BlockMessageJsonFormatterFunctionDeclaration(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        enabled = self.bound.get_option_as_bool_or_raise(
            "c.enable_render_json_formatter"
        )
        if not enabled:
            return
        struct_name: str = self.struct_name
        self.push_comment(f"Format struct {struct_name} to a json format string.")
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Json{struct_name}({struct_type} *m, char *s);"
        self.push(declaration)


class BlockMessage(BlockDefinition_, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageLengthMacro(self.as_message),
            BlockMessageStruct(self.as_message),
            BlockMessageEncoderFunctionDeclaration(self.as_message),
            BlockMessageDecoderFunctionDeclaration(self.as_message),
            BlockMessageJsonFormatterFunctionDeclaration(self.as_message),
        ]


class BlockImportList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockIncludeChildProtoHeader(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockConstantList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockConstant(constant, name=name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockAliasList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockAlias(alias, name=name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnumList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockEnum(enum, name=name)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]


class BlockMessageList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessage(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]


class BlockList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
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


class RendererCHeader(Renderer_):
    """Renderer for C language (header)."""

    @override(Renderer_)
    def file_extension(self) -> str:
        return ".h"

    @override(Renderer_)
    def formatter(self) -> CFormatter:
        return CFormatter()

    @override(Renderer_)
    def block(self) -> Block_:
        return BlockList()
