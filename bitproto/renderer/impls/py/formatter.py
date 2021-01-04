"""
Python formatter.
"""

from typing import Optional

from bitproto._ast import (Alias, Array, Bool, Byte, Constant, Enum, EnumField,
                           Int, Message, Proto, Type, Uint)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import CaseStyleMapping, Formatter
from bitproto.utils import final, override, upper_case


class PyFormatter(Formatter):
    """Formatter for Python language."""

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
        return True

    @override(Formatter)
    def format_comment(self, content: str) -> str:
        return f"# {content}"

    @override(Formatter)
    def format_docstring(self, content: str) -> str:
        return f'"""{content}"""'

    @override(Formatter)
    def format_bool_value(self, value: bool) -> str:
        if value:
            return "True"
        return "False"

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
        """Python dosen't have a type 'byte', using int instead."""
        return "int"

    @override(Formatter)
    def format_uint_type(self, t: Uint) -> str:
        return "int"

    @override(Formatter)
    def format_int_type(self, t: Int) -> str:
        return "int"

    @override(Formatter)
    def format_array_type(self, t: Array, name: Optional[str] = None) -> str:
        if isinstance(t.element_type, Byte):  # Array of byte is bytearray
            return "bytearray"
        return "List[{type}]".format(type=self.format_type(t.element_type))

    @override(Formatter)
    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        module_name = (
            t.get_option_as_string_or_raise("py.module_name") or f"{t.name}_bp"
        )
        if as_name:
            return f"import {module_name} as {as_name}"
        return f"import {module_name}"

    @override(Formatter)
    def format_int_value_type(self) -> str:
        return "int"

    @override(Formatter)
    def format_string_value_type(self) -> str:
        return "str"

    @override(Formatter)
    def format_bool_value_type(self) -> str:
        return "bool"

    @final
    def format_enum_value_to_name_map_name(self, enum: Enum) -> str:
        enum_name = self.format_enum_name(enum)
        return upper_case("_{0}_VALUE_TO_NAME_MAP".format(enum_name))

    @final
    def format_field_default_value(self, t: Type) -> str:
        if isinstance(t, Bool):
            return self.format_field_default_value_bool()
        elif isinstance(t, Byte):
            return self.format_field_default_value_byte()
        elif isinstance(t, Uint):
            return self.format_field_default_value_uint()
        elif isinstance(t, Int):
            return self.format_field_default_value_int()
        elif isinstance(t, Array):
            return self.format_field_default_value_array(t)
        elif isinstance(t, Enum):
            return self.format_field_default_value_enum(t)
        elif isinstance(t, Message):
            return self.format_field_default_value_message(t)
        elif isinstance(t, Alias):
            return self.format_field_default_value_alias(t)
        raise InternalError(f"got unexpected type {t}")

    def format_dataclass_field_default(self, default_factory: str = "") -> str:
        return f"field(default_factory={default_factory})"

    def format_field_default_value_bool(self) -> str:
        return "False"

    def format_field_default_value_byte(self) -> str:
        return '""'

    def format_field_default_value_uint(self) -> str:
        return "0"

    def format_field_default_value_int(self) -> str:
        return "0"

    def format_field_default_value_array(self, t: Array) -> str:
        if isinstance(t.element_type, Byte):
            return self.format_dataclass_field_default(f"lambda: bytearray({t.cap})")
        return self.format_dataclass_field_default("list")

    def format_field_default_value_enum(self, t: Enum) -> str:
        return "0"

    def format_field_default_value_message(self, t: Message) -> str:
        message_type = self.format_message_type(t)
        return self.format_dataclass_field_default(message_type)

    def format_field_default_value_alias(self, t: Alias) -> str:
        if isinstance(t.type, Bool):
            return self.format_field_default_value_bool()
        elif isinstance(t.type, Uint):
            return self.format_field_default_value_uint()
        elif isinstance(t.type, Int):
            return self.format_field_default_value_int()
        elif isinstance(t.type, Array):
            return self.format_field_default_value_array(t.type)
        else:
            alias_type = self.format_alias_type(t)
            return self.format_dataclass_field_default(alias_type)
