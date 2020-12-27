"""
bitproto.renderer_c
~~~~~~~~~~~~~~~~~~~~

Renderer for C.

Produces:

  {proto_filename}_bp.h
  {proto_filename}_bp.c

Structure of XXX_bp.h:

    // {bitproto_declaration}
    //
    // {proto_docstrings}

    {header_declaration_begin}
    {includes}
    {extern_begin}
    {macro_defines}
    {constants}
    {aliases}
    {enums}
    {message_decalrations}
    {extern_end}
    {header_declaration_end}


Structure of XXX_bp.c:

    // {bitproto_declaration}
    //
    // {proto_docstrings}
    //
    // {}

"""

import os
from typing import List

from bitproto.renderer import Renderer
from bitproto.utils import write_file


class RendererC(Renderer):
    """Renderer for C language.

    Produces:
        {proto_filename}_bp.h
        {proto_filename}_bp.c
    """

    def h_out_filename(self) -> str:
        return self.format_out_filename(".h")

    def c_out_filename(self) -> str:
        return self.format_out_filename(".c")

    def h_out_filepath(self) -> str:
        return self.format_out_filepath(".h")

    def c_out_filepath(self) -> str:
        return self.format_out_filepath(".c")

    def render(self) -> None:
        self.render_h()
        self.render_c()

    def render_h(self) -> None:
        self.render_bitproto_declaration()

        self.render_proto_docstring()
        self.render_header_declaration_begin()
        self.push_line()

        self.render_includes()
        self.push_line()

        self.render_extern_begin()
        self.push_line()

        self.render_macro_defines()
        self.push_line()

        # TODO

        self.render_extern_end()
        self.push_line()
        self.render_header_declaration_end()

        write_file(self.h_out_filepath(), self.collect())

    def render_c(self) -> None:
        self.render_bitproto_declaration()
        self.push_line()
        self.render_proto_docstring()
        self.push_line()
        self.render_include_proto_header()
        self.push_line()
        # TODO
        write_file(self.c_out_filepath(), self.collect())

    def render_bitproto_declaration(self) -> None:
        """block {bitproto_declaration}"""
        self.block_begin()
        self.push_line("// {0}".format(self.bitproto_declaration()))

    def render_proto_docstring(self) -> None:
        self.push_lines(self.format_proto_docstring())

    def render_header_declaration_begin(self) -> None:
        header_macro = self.format_header_macro()
        self.push_line(f"#ifndef {header_macro}")
        self.push_line(f"#define {header_macro} 1")

    def render_header_declaration_end(self) -> None:
        self.push_line("#endif")

    def render_includes(self) -> None:
        self.push_line(self.format_include("<inttypes.h>"))
        self.push_line(self.format_include("<stdbool.h>"))
        self.push_line(self.format_include("<stdint.h>"))
        self.push_line(self.format_include("<stdio.h>"))

    def render_include_proto_header(self) -> None:
        self.push_line(self.format_include('"{0}"'.format(self.h_out_filename())))

    def render_extern_begin(self) -> None:
        self.push_line("#if defined(__cplusplus)")
        self.push_line('extern "C" {')
        self.push_line("#endif")

    def render_extern_end(self) -> None:
        self.push_line("#if defined(__cplusplus)")
        self.push_line("}")
        self.push_line("#endif")

    def render_macro_defines(self) -> None:
        self.push_line(self.format_define('btoa(x) ((x) ? "true" : "false")'))

    def format_proto_docstring(self) -> List[str]:
        lines: List[str] = []
        for comment in self.proto.comment_block:
            lines.append("// {0}".format(comment.content()))
        return lines

    def format_header_macro(self) -> str:
        proto_name_upper = self.proto.name.upper()
        return f"__BITPROTO__{proto_name_upper}_H__"

    def format_include(self, file: str) -> str:
        return f"#include {file}"

    def format_define(self, macro: str) -> str:
        return f"#define {macro}"
