"""
Go formatter
"""

from typing import Optional

from bitproto._ast import (Alias, Array, Bool, Constant, EnumField, Int,
                           MessageField, Proto, Uint)
from bitproto.renderer.formatter import CaseStyleMapping, Formatter
from bitproto.utils import cast_or_raise, override


class GoFormatter(Formatter):
    """Formatter for Go language."""

    @override(Formatter)
    def case_style_mapping(self) -> CaseStyleMapping:
        return {
            Alias: "pascal",
            Constant: "upper",
            EnumField: ("snake", "upper"),
            MessageField: "pascal",
        }

    @override(Formatter)
    def indent_character(self) -> str:
        return "\t"

    @override(Formatter)
    def support_import_as_member(self) -> bool:
        return True

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
        return "byte"

    @override(Formatter)
    def format_uint_type(self, t: Uint) -> str:
        return "uint{0}".format(self.get_nbits_of_integer(t))

    @override(Formatter)
    def format_int_type(self, t: Int) -> str:
        return "int{0}".format(self.get_nbits_of_integer(t))

    @override(Formatter)
    def format_array_type(self, t: Array, name: Optional[str] = None) -> str:
        return "[{cap}]{type}".format(type=self.format_type(t.element_type), cap=t.cap)

    @override(Formatter)
    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        path = t.get_option_as_string_or_raise("go.package_path") or f"{t.name}_bp"
        if as_name:
            return f'import {as_name} "{path}"'
        return f'import "{path}"'

    @override(Formatter)
    def format_int_value_type(self) -> str:
        return "int"

    @override(Formatter)
    def format_string_value_type(self) -> str:
        return "string"

    @override(Formatter)
    def format_bool_value_type(self) -> str:
        return "bool"

    @override(Formatter)
    def format_endecoder_message_name(self) -> str:
        return "m"

    @override(Formatter)
    def format_encoder_item(
        self, chain: str, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        pass  # TODO

    @override(Formatter)
    def format_decoder_item(
        self, chain: str, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        pass  # TODO
