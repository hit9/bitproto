"""
Go formatter
"""

from typing import Optional

from bitproto._ast import (Alias, Array, Bool, Byte, Constant, Enum, EnumField,
                           Int, Integer, Message, MessageField, Proto, Type,
                           Uint)
from bitproto.errors import InternalError
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
            Message: "pascal",
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

    def format_bp_type(self, t: Type) -> str:
        if isinstance(t, Bool):
            return self.format_bp_bool()
        elif isinstance(t, Int):
            return self.format_bp_int(t)
        elif isinstance(t, Uint):
            return self.format_bp_uint(t)
        elif isinstance(t, Byte):
            return self.format_bp_byte()
        elif isinstance(t, Array):
            return self.format_bp_array(t)
        elif isinstance(t, Enum):
            return self.format_bp_enum(t)
        elif isinstance(t, Alias):
            return self.format_bp_alias(t)
        elif isinstance(t, Message):
            return self.format_bp_message(t)
        raise InternalError("format_bp_type got unexpected t")

    def format_bp_bool(self) -> str:
        return "bp.NewBool()"

    def format_bp_int(self, t: Int) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"bp.NewInt({nbits})"

    def format_bp_uint(self, t: Uint) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"bp.NewUint({nbits})"

    def format_bp_byte(self) -> str:
        return f"bp.NewByte()"

    def format_bp_enum(self, t: Enum) -> str:
        enum_name = self.format_enum_name(t)
        return f"{enum_name}(0)"

    def format_bp_alias(self, t: Alias) -> str:
        alias_name = self.format_alias_name(t)
        s: str
        if isinstance(t.type, Bool):
            return f"{alias_name}(false)"
        elif isinstance(t.type, (Integer, Enum, Byte)):
            return f"{alias_name}(0)"
        elif isinstance(t.type, Array):
            return f"{alias_name}{{}}"
        raise InternalError("format_bp_alias got unexpected alias type")

    def format_bp_array(self, t: Array) -> str:
        extensible = self.format_bool_value(t.extensible)
        capacity = self.format_int_value(t.cap)
        et = self.format_bp_type(t.element_type)
        return f"bp.NewArray({extensible}, {capacity}, {et})"

    def format_bp_message(self, t: Message) -> str:
        message_name = self.format_message_name(t)
        return f"&{message_name}{{}}"
