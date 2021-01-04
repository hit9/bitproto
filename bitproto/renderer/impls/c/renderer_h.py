"""
Renderer for C header file.
"""

from typing import Any, List, cast

from bitproto._ast import Array, Proto
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override, snake_case, upper_case


class BlockIncludeGuard(Block):
    def render_proto_doc(self) -> None:
        for comment in self.bound.comment_block:
            self.push("// {0}".format(comment.content()))

    def format_proto_macro_name(self) -> str:
        proto_name = snake_case(self.bound.name).upper()
        return f"__BITPROTO__{proto_name}_H__"

    def render_declaration_begin(self) -> None:
        macro_name = self.format_proto_macro_name()
        self.push(f"#ifndef  {macro_name}")
        self.push(f"#define  {macro_name} 1")

    def render_declaration_end(self) -> None:
        self.push(f"#endif")

    @override(Block)
    def render(self) -> None:
        self.render_proto_doc()
        self.render_declaration_begin()

    @override(Block)
    def defer(self) -> None:
        self.render_declaration_end()


class BlockIncludeGeneralHeaders(Block):
    @override(Block)
    def render(self) -> None:
        self.push("#include <inttypes.h>")
        self.push("#include <stdbool.h>")
        self.push("#include <stdint.h>")
        self.push("#include <stdio.h>")


class BlockExternCPlusPlus(Block):
    @override(Block)
    def render(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push('extern "C" {')
        self.push("#endif")

    @override(Block)
    def defer(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push("}")
        self.push("#endif")


class BlockIncludeChildProtoHeader(BlockDefinition):
    @override(Block)
    def render(self) -> None:
        self.push(self.formatter.format_import_statement(self.as_proto))


class BlockGeneralMacroDefines(Block):
    @override(Block)
    def render(self) -> None:
        self.push('#define btoa(x) ((x) ? "true" : "false")')


class BlockConstant(BlockDefinition):
    def render_constant_define(self) -> None:
        name = self.formatter.format_constant_name(self.as_constant)
        value = self.formatter.format_value(self.as_constant.value)
        self.push(f"#define {name} {value}")

    @override(Block)
    def render(self) -> None:
        self.push_docstring()
        self.render_constant_define()


class BlockAlias(BlockDefinition):
    def render_alias_typedef_to_array(self) -> None:
        array_type = cast(Array, self.as_alias.type)
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
        self.push_location_doc()

    @override(Block)
    def render(self) -> None:
        self.push_docstring()
        self.render_alias_typedef()


class BlockEnumField(BlockDefinition):
    def render_define_macro(self) -> None:
        field = self.as_enum_field
        name = self.formatter.format_enum_field_name(field)
        value = self.formatter.format_int_value(field.value)
        self.push(f"#define {name} {value}")

    @override(Block)
    def render(self) -> None:
        self.push_docstring()
        self.render_define_macro()


class BlockEnumBase(BlockDefinition):
    @property
    def enum_name(self) -> str:
        return self.formatter.format_enum_name(self.as_enum)


class BlockEnumFieldList(BlockEnumBase, BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [BlockEnumField(field) for field in self.as_enum.fields()]


class BlockEnum(BlockEnumBase, BlockWrapper):
    @override(BlockWrapper)
    def before(self) -> None:
        self.push_docstring()
        self.render_enum_typedef()

    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumFieldList(self.as_message)

    def render_enum_typedef(self) -> None:
        name = self.enum_name
        uint_type = self.formatter.format_uint_type(self.as_enum.type)
        self.push(f"typedef {uint_type} {name};")
        self.push_location_doc()


class BlockMessageField(BlockDefinition):
    def render_field_declaration_array(self) -> None:
        field_type = self.as_message_field.type
        field_name = self.as_message_field.name
        array_type = cast(Array, field_type)
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
        self.push_location_doc()

    @override(Block)
    def render(self) -> None:
        self.push_docstring()
        self.render_field_declaration()


class BlockMessageBase(BlockDefinition):
    @property
    def struct_name(self) -> str:
        return self.formatter.format_message_name(self.as_message)


class BlockMessageLengthMacro(BlockMessageBase):
    @override(BlockDefinition)
    def render(self) -> None:
        message = self.as_message
        struct_name: str = self.struct_name
        struct_name_upper = upper_case(snake_case(struct_name))
        comment = self.formatter.format_comment(
            f"Number of bytes to encode struct {struct_name}"
        )
        self.push(comment)
        nbytes = message.nbytes()
        macro_string = f"#define BYTES_LENGTH_{struct_name_upper} {nbytes}"
        self.push(macro_string)


class BlockMessageFieldList(BlockMessageBase, BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockMessageField(field, indent=4)
            for field in self.as_message.sorted_fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageStruct(BlockMessageBase, BlockWrapper):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockMessageFieldList(self.definition, name=self.definition_name)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_docstring()
        struct_name: str = self.struct_name
        self.push(f"struct {struct_name} {{")
        self.push_location_doc()

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")
        option_name = "c.struct_packing_alignment"
        alignment = self.bound.get_option_as_int_or_raise(option_name)
        if alignment > 0:
            self.push_string(f"__attribute__((packed, aligned({alignment})))")
        self.push_string(";", separator="")


class BlockMessageEncoderFunctionDeclaration(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        struct_name: str = self.struct_name
        comment = self.formatter.format_docstring(
            f"Encode struct {struct_name} to given buffer s"
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Encode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)


class BlockMessageDecoderFunctionDeclaration(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        struct_name: str = self.struct_name
        comment = self.formatter.format_docstring(
            f"Decode struct {struct_name} from given buffer s"
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Decode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)


class BlockMessageJsonFormatterFunctionDeclaration(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        enabled = self.bound.get_option_as_bool_or_raise(
            "c.enable_render_json_formatter"
        )
        if not enabled:
            return
        struct_name: str = self.struct_name
        comment = self.formatter.format_docstring(
            f"Format struct {struct_name} to a json format string."
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Json{struct_name}({struct_type} *m, char *s);"
        self.push(declaration)


class BlockMessage(BlockDefinition, BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockMessageLengthMacro(self.as_message),
            BlockMessageStruct(self.as_message),
            BlockMessageEncoderFunctionDeclaration(self.as_message),
            BlockMessageDecoderFunctionDeclaration(self.as_message),
            BlockMessageJsonFormatterFunctionDeclaration(self.as_message),
        ]


class BlockImportList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockIncludeChildProtoHeader(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]


class BlockConstantList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockConstant(constant, name=name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]


class BlockAliasList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockAlias(alias, name=name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]


class BlockEnumList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockEnum(enum, name=name)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]


class BlockMessageList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockMessage(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]


class BlockList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockAheadNotice(),
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


class RendererCHeader(Renderer):
    """Renderer for C language (header)."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".h"

    @override(Renderer)
    def formatter(self) -> Formatter:
        return CFormatter()

    @override(Renderer)
    def block(self) -> Block:
        return BlockList()
