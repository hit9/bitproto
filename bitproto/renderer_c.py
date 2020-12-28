"""
bitproto.renderer_c
~~~~~~~~~~~~~~~~~~~~

Renderer for C.
"""

import os
from typing import List, Optional, cast

from bitproto.renderer import (
    Renderer,
    Block,
    BlockForDefinition,
    Formatter,
    BITPROTO_DECLARATION,
)
from bitproto.errors import InternalError
from bitproto.ast import Proto, Constant, Alias, Uint, Int, Array, EnumField
from bitproto.utils import write_file


class CFormatter(Formatter):
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
        """Overrides super method to use upper case."""
        return super(CFormatter, self).format_enum_field_name(f).upper()

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
        return "__BITPROTO__{0}_H".format(self.proto.name.upper())

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


class HeaderExternDeclaration(Block):
    def render(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push('extern "C"')
        self.push("#endif")

    def defer(self) -> None:
        self.push("#if defined(__cplusplus)")
        self.push("}")
        self.push("#endif")


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
        self.push(f"typedef {uint_type} {name}")
        self.push_location_doc()

    def render_enum_fields(self) -> None:
        for name, field in self.as_enum.enum_fields().items():
            block = EnumFieldBlock(field, name=name, formatter=self.formatter)
            block.render()
            self.push(block.collect())

    def render(self) -> None:
        self.render_doc()
        self.render_enum_typedef()
        self.render_enum_fields()


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
            HeaderExternDeclaration(),
            HeaderBuiltinMacroDefines(),
        ]

        # Constants
        for name, constant in self.proto.constants().items():
            blocks.append(ConstantBlock(constant, name=name))

        # Alias
        for name, alias in self.proto.aliases().items():
            blocks.append(AliasBlock(alias, name=name))

        # Enum
        for name, enum in self.proto.enums().items():
            blocks.append(EnumBlock(enum, name=name))

        return blocks
