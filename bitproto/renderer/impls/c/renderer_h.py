"""
Renderer for C header file.
"""

from typing import Any, List, cast

from bitproto._ast import Array, Proto
from bitproto.renderer.block import Block, BlockAheadNotice, BlockDefinition
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.c.formatter import CFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override, snake_case


class BlockIncludeGuard(Block):
    def __init__(self, proto: Proto) -> None:
        super(BlockIncludeGuard, self).__init__()
        self.proto = proto

    def render_proto_doc(self) -> None:
        for comment in self.proto.comment_block:
            self.push("// {0}".format(comment.content()))

    def format_proto_macro_name(self) -> str:
        proto_name = snake_case(self.proto.name).upper()
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
        self.render_doc()
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
        self.render_doc()
        self.render_alias_typedef()


class BlockEnumField(BlockDefinition):
    def render_define_macro(self) -> None:
        field = self.as_enum_field
        name = self.formatter.format_enum_field_name(field)
        value = self.formatter.format_int_value(field.value)
        self.push(f"#define {name} {value}")

    @override(Block)
    def render(self) -> None:
        self.render_doc()
        self.render_define_macro()


class BlockEnum(BlockDefinition):
    def render_enum_typedef(self) -> None:
        name = self.formatter.format_enum_name(self.as_enum)
        uint_type = self.formatter.format_uint_type(self.as_enum.type)
        self.push(f"typedef {uint_type} {name};")
        self.push_location_doc()

    def render_enum_fields(self) -> None:
        for field in self.as_enum.fields():
            block = BlockEnumField(field, formatter=self.formatter)
            block.render()
            self.push(block.collect())

    @override(Block)
    def render(self) -> None:
        self.render_doc()
        self.render_enum_typedef()
        self.render_enum_fields()


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
        self.render_doc()
        self.render_field_declaration()


class BlockMessage(BlockDefinition):
    def __init__(self, proto: Proto, *args: Any, **kwds: Any) -> None:
        super(BlockMessage, self).__init__(*args, **kwds)
        self.proto = proto

    @property
    def struct_name(self) -> str:
        return self.formatter.format_message_name(self.as_message)

    def render_message_length_macro(self) -> None:
        message = self.as_message
        struct_name: str = self.struct_name
        struct_name_upper = snake_case(struct_name).upper()
        comment = self.formatter.format_comment(
            f"Number of bytes to encode struct {struct_name}"
        )
        self.push(comment)
        nbytes = message.nbytes()
        macro_string = f"#define BYTES_LENGTH_{struct_name_upper} {nbytes}"
        self.push(macro_string)

    def render_message_struct_fields(self) -> None:
        for field in self.as_message.sorted_fields():
            block = BlockMessageField(field, formatter=self.formatter, ident=4)
            block.render()
            self.push(block.collect())

    def render_message_struct(self) -> None:
        struct_name: str = self.struct_name

        self.push(f"struct {struct_name} {{")
        self.push_location_doc()
        self.render_message_struct_fields()
        self.push("}")

        alignment = self.proto.get_option_as_int_or_raise("c.struct_packing_alignment")
        if alignment > 0:
            self.push_string(f"__attribute__((packed, aligned({alignment})))")
        self.push_string(";")

    def render_encoder_function_declaration(self) -> None:
        struct_name: str = self.struct_name
        comment = self.formatter.format_docstring(
            f"Encode struct {struct_name} to given buffer s"
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Encode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)

    def render_decoder_function_declaration(self) -> None:
        struct_name: str = self.struct_name
        comment = self.formatter.format_docstring(
            f"Decode struct {struct_name} from given buffer s"
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Decode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)

    def render_json_formatter_function_declaration(self) -> None:
        enabled = self.proto.get_option_as_bool_or_raise(
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

    @override(Block)
    def render(self) -> None:
        self.render_message_length_macro()
        self.push_empty_line()
        self.render_doc()
        self.render_message_struct()
        self.push_empty_line()
        self.render_encoder_function_declaration()
        self.push_empty_line()
        self.render_decoder_function_declaration()
        self.push_empty_line()
        self.render_json_formatter_function_declaration()


class RendererCHeader(Renderer):
    """Renderer for C language (header)."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".h"

    @override(Renderer)
    def formatter(self) -> Formatter:
        return CFormatter()

    @override(Renderer)
    def blocks(self) -> List[Block]:
        blocks = [
            BlockAheadNotice(),
            BlockIncludeGuard(self.proto),
            BlockIncludeGeneralHeaders(),
            BlockExternCPlusPlus(),
        ]
        # Imports
        for name, proto in self.proto.protos(recursive=False):
            blocks.append(BlockIncludeChildProtoHeader(proto, name=name))

        blocks.append(BlockGeneralMacroDefines())

        # Constants
        for name, constant in self.proto.constants(recursive=True, bound=self.proto):
            blocks.append(BlockConstant(constant, name=name))
        # Alias
        for name, alias in self.proto.aliases(recursive=True, bound=self.proto):
            blocks.append(BlockAlias(alias, name=name))
        # Enum
        for name, enum in self.proto.enums(recursive=True, bound=self.proto):
            blocks.append(BlockEnum(enum, name=name))
        # Message
        for name, message in self.proto.messages(recursive=True, bound=self.proto):
            blocks.append(BlockMessage(self.proto, message, name=name))

        return blocks
