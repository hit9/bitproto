"""
C formatter.
"""

from typing import Optional

from bitproto._ast import (Array, Constant, Enum, EnumField, Int, Message,
                           MessageField, Proto, Uint)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import CaseStyleMapping, Formatter
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
        return "uint{0}_t".format(self.get_nbits_of_integer(t))

    @override(Formatter)
    def format_int_type(self, t: Int) -> str:
        return "int{0}_t".format(self.get_nbits_of_integer(t))

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

    def format_bp_uint(self, t: Uint) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"BpUint({nbits})"

    def format_bp_enum_descriptor(self, t: Enum) -> str:
        extensible = self.format_bool_value(t.extensible)
        bp_uint = self.format_bp_uint(t.type)
        return f"BpEnumDescriptor({extensible}, {bp_uint})"

    def format_bp_enum_processor_name(self, t: Enum) -> str:
        enum_name = self.format_enum_name(t)
        return f"BpProcessor{enum_name}"
