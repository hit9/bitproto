"""
C formatter.
"""

from typing import Optional

from bitproto._ast import Array, Constant, EnumField, Int, Message, Proto, Uint
from bitproto.errors import InternalError
from bitproto.renderer.formatter import Formatter
from bitproto.utils import snake_case


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
        return "{element_type} {name}[{capacity}]".format(
            element_type=self.format_type(t.element_type), name=name, capacity=t.cap
        )

    def format_message_type(self, t: Message) -> str:
        return "struct {0}".format(self.format_message_name(t))

    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        return '#include "{0}_bp.h"'.format(t.name)
