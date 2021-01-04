"""
Python formatter.
"""

from typing import Optional

from bitproto._ast import (Array, Byte, Constant, Enum, EnumField, Int, Proto,
                           Uint)
from bitproto.renderer.formatter import CaseStyleMapping, Formatter
from bitproto.utils import final, override


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
        """Python dosen't have a type 'byte', using str instead."""
        return "str"

    @override(Formatter)
    def format_uint_type(self, t: Uint) -> str:
        return "int"

    @override(Formatter)
    def format_int_type(self, t: Int) -> str:
        return "int"

    @override(Formatter)
    def format_array_type(self, t: Array, name: Optional[str] = None) -> str:
        if isinstance(t.element_type, Byte):  # Array of byte is str
            return "str"
        return "List[{type}]".format(type=self.format_type(t.element_type))

    @override(Formatter)
    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        module_name = (
            t.get_option_as_string_or_raise("py.module_name") or f"{t.name}_bp"
        )
        if as_name:
            return f"import {module_name} as {as_name}"
        return f"import {module_name}"

    @final
    def format_enum_value_to_name_map_name(self, enum: Enum) -> str:
        enum_name = self.format_enum_name(enum)
        return "_{0}_VALUE_TO_NAME_MAP".format(enum_name)
