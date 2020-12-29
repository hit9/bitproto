"""
bitproto.renderer_go
~~~~~~~~~~~~~~~~~~~~

Renderer for Go.
"""

from typing import List, Optional

from bitproto.ast import Array, Constant, EnumField, Int, Uint
from bitproto.errors import InternalError
from bitproto.renderer import Block, Formatter, Renderer


class GoFormatter(Formatter):
    """Formatter for Go language."""

    def ident_character(self) -> str:
        return "\t"

    def support_import(self) -> bool:
        return True

    def delimer_cross_proto(self) -> str:
        return "."

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
        # TODO: What case?

    def format_enum_field_name(self, f: EnumField) -> str:
        """Overrides super method to use upper case."""
        # TODO: What case?

    def format_bool_type(self) -> str:
        return "bool"

    def format_byte_type(self) -> str:
        return "byte"

    def format_uint_type(self, t: Uint) -> str:
        return "uint{0}".format(self.nbits_from_integer_type(t))

    def format_int_type(self, t: Int) -> str:
        return "int{0}".format(self.nbits_from_integer_type(t))

    def format_array_type(self, t: Array, name: Optional[str] = None) -> str:
        return "[{cap}]{type}".format(type=self.format_type(t.type), cap=t.cap)


class RendererGo(Renderer):
    """Renderer for Go language."""

    def file_extension(self) -> str:
        return ".go"

    def formatter(self) -> Formatter:
        return GoFormatter()

    def blocks(self) -> List[Block]:
        pass  # TODO