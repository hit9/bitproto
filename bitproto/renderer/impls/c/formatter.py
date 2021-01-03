"""
C formatter.
"""

from typing import Optional

from bitproto._ast import Array, Constant, EnumField, Int, Message, Proto, Uint
from bitproto.errors import InternalError
from bitproto.renderer.formatter import Formatter, CaseStyleMapping
from bitproto.utils import override


class CFormatter(Formatter):
    """CFormatter implements Formatter for C language."""

    @override(Formatter)
    def case_style_mapping(self) -> CaseStyleMapping:
        return {
            Constant: "upper",
            EnumField: ("snake", "upper"),
        }

    @override(Formatter)
    def indent_character(self) -> str:
        return " "

    @override(Formatter)
    def support_import_as_member(self) -> bool:
        return False

    @override(Formatter)
    def format_comment(self, content: str) -> str:
        return f"// {content}"

    @override(Formatter)
    def format_bool_value(self, value: bool) -> str:
        if value:
            return "true"
        return "false"

    @override(Formatter)
    def format_str_value(self, value: str) -> str:
        return '"{0}"'.format(value)

    @override(Formatter)
    def format_int_value(self, value: int) -> str:
        return "{0}".format(value)

    @override(Formatter)
    def format_bool_type(self) -> str:
        return "bool"

    @override(Formatter)
    def format_byte_type(self) -> str:
        return "unsigned char"

    @override(Formatter)
    def format_uint_type(self, t: Uint) -> str:
        return "uint{0}_t".format(self.nbits_from_integer_type(t))

    @override(Formatter)
    def format_int_type(self, t: Int) -> str:
        return "int{0}_t".format(self.nbits_from_integer_type(t))

    @override(Formatter)
    def format_array_type(self, t: Array, name: Optional[str] = None) -> str:
        assert name is not None, InternalError("format_array_type got name=None")
        return "{element_type} {name}[{capacity}]".format(
            element_type=self.format_type(t.element_type), name=name, capacity=t.cap
        )

    @override(Formatter)
    def format_message_type(self, t: Message) -> str:
        return "struct {0}".format(self.format_message_name(t))

    @override(Formatter)
    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        return '#include "{0}_bp.h"'.format(t.name)
