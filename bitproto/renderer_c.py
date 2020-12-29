"""
bitproto.renderer_c
~~~~~~~~~~~~~~~~~~~~

Renderer for C.
"""

import os
from typing import List, Optional, cast

from bitproto.ast import Alias, Array, Constant, EnumField, Int, Message, Proto, Uint
from bitproto.errors import InternalError
from bitproto.renderer import (
    BITPROTO_DECLARATION,
    Block,
    BlockForDefinition,
    Formatter,
    Renderer,
)
from bitproto.utils import snake_case, write_file


class CFormatter(Formatter):
    def ident_character(self) -> str:
        return " "

    def support_import(self) -> bool:
        return False

    def delimer_cross_proto(self) -> str:
        return ""

    def delimer_inner_proto(self) -> str:
        return "_"

    def format_comment(self, content: str) -> str:
        return f"// {content}"

    def format_bool_literal(self, value: bool) -> str:
        if value:
            return "true"
        return "false"

    def format_str_literal(self, value: str) -> str:
        return '"{0}"'.format(value)

    def format_int_literal(self, value: int) -> str:
        return "{0}".format(value)

    def format_constant_name(self, v: Constant) -> str:
        """Overrides super method to use upper case."""
        return super(CFormatter, self).format_constant_name(v).upper()

    def format_enum_field_name(self, f: EnumField) -> str:
        """Overrides super method to use upper case (of snake_case)."""
        name = super(CFormatter, self).format_enum_field_name(f)
        return snake_case(name).upper()

    def format_bool_type(self) -> str:
        return "bool"

    def format_byte_type(self) -> str:
        return "unsigned char"

    def format_uint_type(self, t: Uint) -> str:
        return "uint{0}_t".format(self.nbits_from_integer_type(t))

    def format_int_type(self, t: Int) -> str:
        return "int{0}_t".format(self.nbits_from_integer_type(t))

    def format_array_type(self, t: Array, name: Optional[str] = None) -> str:
        assert name is not None, InternalError("format_array_type got name=None")
        return "{type} {name}[{capacity}]".format(
            type=self.format_type(t.type), name=name, capacity=t.cap
        )

    def format_message_type(self, t: Message) -> str:
        return "struct {0}".format(self.format_message_name(t))

    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        return '#include "{0}_bp.h"'.format(t.name)


class BitprotoDeclaration(Block):
    def render(self) -> None:
        self.push(self.formatter.format_comment(BITPROTO_DECLARATION))


class IncludeHeaderFile(Block):
    def __init__(self, header_filename: str) -> None:
        super(IncludeHeaderFile, self).__init__()
        self.header_filename = header_filename

    def render(self) -> None:
        self.push(f'#include "{self.header_filename}"')


class RendererC(Renderer):
    """Renderer for C language (c file)."""

    def file_extension(self) -> str:
        return ".c"

    def formatter(self) -> Formatter:
        return CFormatter()

    def blocks(self) -> List[Block]:
        header_filename = RendererCHeader(self.proto, self.outdir).out_filename
        return [BitprotoDeclaration(), IncludeHeaderFile(header_filename)]


class HeaderDeclaration(Block):
    def __init__(self, proto: Proto) -> None:
        super(HeaderDeclaration, self).__init__()
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

    def render(self) -> None:
        self.render_proto_doc()
        self.render_declaration_begin()

    def defer(self) -> None:
        self.render_declaration_end()


class HeaderIncludes(Block):
    def render(self) -> None:
        self.push("#include <inttypes.h>")
        self.push("#include <stdbool.h>")
        self.push("#include <stdint.h>")
        self.push("#include <stdio.h>")


class HeaderIncludeGuard(Block):
    def render(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push('extern "C"')
        self.push("#endif")

    def defer(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push("}")
        self.push("#endif")


class HeaderImportBlock(BlockForDefinition):
    def render(self) -> None:
        self.push(self.formatter.format_import_statement(self.as_proto))


class HeaderBuiltinMacroDefines(Block):
    def render(self) -> None:
        self.push('#define btoa(x) ((x) ? "true" : "false")')


class ConstantBlock(BlockForDefinition):
    def render_constant_define(self) -> None:
        name = self.formatter.format_constant_name(self.as_constant)
        value = self.formatter.format_literal(self.as_constant.value)
        self.push(f"#define {name} {value}")

    def render(self) -> None:
        self.render_doc()
        self.render_constant_define()


class AliasBlock(BlockForDefinition):
    def render_alias_typedef_to_array(self) -> None:
        array_type = cast(Array, self.as_alias.type)
        aliased_type = self.formatter.format_type(array_type.type)
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

    def render(self) -> None:
        self.render_doc()
        self.render_alias_typedef()


class EnumFieldBlock(BlockForDefinition):
    def render_define_macro(self) -> None:
        field = self.as_enum_field
        name = self.formatter.format_enum_field_name(field)
        value = self.formatter.format_int_literal(field.value)
        self.push(f"#define {name} {value}")

    def render(self) -> None:
        self.render_doc()
        self.render_define_macro()


class EnumBlock(BlockForDefinition):
    def render_enum_typedef(self) -> None:
        name = self.formatter.format_enum_name(self.as_enum)
        uint_type = self.formatter.format_uint_type(self.as_enum.type)
        self.push(f"typedef {uint_type} {name};")
        self.push_location_doc()

    def render_enum_fields(self) -> None:
        for field in self.as_enum.fields:
            block = EnumFieldBlock(field, formatter=self.formatter)
            block.render()
            self.push(block.collect())

    def render(self) -> None:
        self.render_doc()
        self.render_enum_typedef()
        self.render_enum_fields()


class MessageFieldBlock(BlockForDefinition):
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

    def render(self) -> None:
        self.render_doc()
        self.render_field_declaration()


class MessageBlock(BlockForDefinition):
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
        for field in self.as_message.fields:
            block = MessageFieldBlock(field, formatter=self.formatter, ident=4)
            block.render()
            self.push(block.collect())

    def render_message_struct(self) -> None:
        struct_name: str = self.struct_name
        self.push(f"struct {struct_name} {{")
        self.push_location_doc()
        self.render_message_struct_fields()
        self.push("};")
        # TODO: __attribute__((packed, aligned(1)));

    def render_encoder_function_declaration(self) -> None:
        struct_name: str = self.struct_name
        comment = self.formatter.format_comment(
            f"Encode struct {struct_name} to given buffer s"
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Encode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)

    def render_decoder_function_declaration(self) -> None:
        struct_name: str = self.struct_name
        comment = self.formatter.format_comment(
            f"Decode struct {struct_name} from given buffer s"
        )
        self.push(comment)
        struct_type = self.formatter.format_message_type(self.as_message)
        declaration = f"int Decode{struct_name}({struct_type} *m, unsigned char *s);"
        self.push(declaration)

    def render(self) -> None:
        self.render_message_length_macro()
        self.push_empty_line()
        self.render_doc()
        self.render_message_struct()
        self.push_empty_line()
        self.render_encoder_function_declaration()
        self.push_empty_line()
        self.render_decoder_function_declaration()
        # TODO: render json formatter


class RendererCHeader(Renderer):
    """Renderer for C language (header)."""

    def file_extension(self) -> str:
        return ".h"

    def formatter(self) -> Formatter:
        return CFormatter()

    def blocks(self) -> List[Block]:
        blocks = [
            BitprotoDeclaration(),
            HeaderDeclaration(self.proto),
            HeaderIncludes(),
        ]
        # Imports
        for name, proto in self.proto.protos(recursive=False):
            blocks.append(HeaderImportBlock(proto, name=name))

        blocks.extend(
            [HeaderIncludeGuard(), HeaderBuiltinMacroDefines(),]
        )
        # Constants
        for name, constant in self.proto.constants(recursive=True, bound=self.proto):
            blocks.append(ConstantBlock(constant, name=name))
        # Alias
        for name, alias in self.proto.aliases(recursive=True, bound=self.proto):
            blocks.append(AliasBlock(alias, name=name))
        # Enum
        for name, enum in self.proto.enums(recursive=True, bound=self.proto):
            blocks.append(EnumBlock(enum, name=name))
        # Message
        for name, message in self.proto.messages(recursive=True, bound=self.proto):
            blocks.append(MessageBlock(message, name=name))

        return blocks
