"""
bitproto.renderer_c
~~~~~~~~~~~~~~~~~~~~

Renderer for C.
"""

import os
from typing import List

from bitproto.renderer import (
    Renderer,
    Block,
    BlockForDefinition,
    Formatter,
    BITPROTO_DECLARATION,
)
from bitproto.ast import Proto, Constant, Alias, Uint, Int
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

    def format_bool_type(self) -> str:
        return "bool"

    def format_byte_type(self) -> str:
        return "unsigned char"

    def format_uint_type(self, t: Uint) -> str:
        return "uint{0}_t".format(self.nbits_from_integer_type(t))

    def format_int_type(self, t: Int) -> str:
        return "int{0}_t".format(self.nbits_from_integer_type(t))


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
        value = self.formatter.format_literal(self.definition_as_constant.value)
        self.push(f"#define {self.definition_name} {value}")

    def render(self) -> None:
        self.render_doc()
        self.render_constant_define()


class AliasBlock(BlockForDefinition):
    def render_alias_typedef(self) -> None:
        # TODO
        self.push("")

    def render(self) -> None:
        self.render_doc()
        self.render_alias_typedef()


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
        return blocks
