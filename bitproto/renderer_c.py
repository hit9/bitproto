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

    {includes}

    {header_declaration_begin}
    {macro_defines}
    {constants}
    {aliases}
    {enums}
    {message_decalrations}
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
        self.push_line()
        self.render_proto_docstring()
        self.push_line()
        self.render_includes()
        # TODO
        write_file(self.h_out_filepath(), self.collect())

    def render_c(self) -> None:
        self.render_bitproto_declaration()
        self.push_line()
        self.render_proto_docstring()
        self.push_line()
        self.render_include_proto_header()
        # TODO
        write_file(self.c_out_filepath(), self.collect())

    def render_bitproto_declaration(self) -> None:
        self.push_line("// {0}".format(self.bitproto_declaration()))

    def render_proto_docstring(self) -> None:
        self.push_lines(self.format_proto_docstring())

    def render_includes(self) -> None:
        self.push_line(self.format_include("<inttypes.h>"))
        self.push_line(self.format_include("<stdbool.h>"))
        self.push_line(self.format_include("<stdint.h>"))
        self.push_line(self.format_include("<stdio.h>"))

    def render_include_proto_header(self) -> None:
        self.push_line(self.format_include('"{0}"'.format(self.h_out_filename())))

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
