"""
Python formatter.
"""

from typing import List, Optional

from bitproto._ast import (
    Alias,
    Array,
    Bool,
    Byte,
    Constant,
    Enum,
    EnumField,
    Int,
    Message,
    Proto,
    Type,
    Uint,
)
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
    def format_docstring(self, *comments: str) -> List[str]:
        strings = ['"""']
        strings.extend([comment for comment in comments])
        strings.append('"""')
        return strings

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

    def format_default_value_bool(self) -> str:
        return "False"

    def format_default_value_byte(self) -> str:
        return "bp.byte(0)"

    def format_default_value_uint(self) -> str:
        return "0"

    def format_default_value_int(self) -> str:
        return "0"

    def format_default_value_message(self, t: Message) -> str:
        factory = self.formart_default_factory_message(t)
        return f"{factory}()"

    def format_default_value_enum(self, t: Enum) -> str:
        return f"{self.format_type(t)}.{self.format_enum_field_name(t.fields()[0])}"

    def format_default_value_array(self, t: Array) -> str:
        cap = self.format_int_value(t.cap)
        if isinstance(t.element_type, Byte):
            return f"bytearray({cap})"
        element_default_value = self.format_default_value(t.element_type)
        return f"[{element_default_value} for _ in range({cap})]"

    def format_default_value_alias(self, t: Alias) -> str:
        factory = self.formart_default_factory_alias(t)
        return f"{factory}()"

    @final
    def format_default_value(self, t: Type) -> str:
        if isinstance(t, Bool):
            return self.format_default_value_bool()
        elif isinstance(t, Byte):
            return self.format_default_value_byte()
        elif isinstance(t, Uint):
            return self.format_default_value_uint()
        elif isinstance(t, Int):
            return self.format_default_value_int()
        elif isinstance(t, Array):
            return self.format_default_value_array(t)
        elif isinstance(t, Enum):
            return self.format_default_value_enum(t)
        elif isinstance(t, Message):
            return self.format_default_value_message(t)
        elif isinstance(t, Alias):
            return self.format_default_value_alias(t)
        raise InternalError(f"format_default_value got unexpected type {t}")

    def format_field_with_default_factory(self, default_factory: str) -> str:
        return f"field(default_factory={default_factory})"

    def formart_default_factory_alias(self, t: Alias) -> str:
        return self.format_name_related_to_definition(
            t, "bp_default_factory_{definition_name}"
        )

    def format_field_default_alias(self, t: Alias) -> str:
        factory = self.formart_default_factory_alias(t)
        return self.format_field_with_default_factory(factory)

    def formart_default_factory_message(self, t: Message) -> str:
        return self.format_message_type(t)

    def format_field_default_message(self, t: Message) -> str:
        factory = self.formart_default_factory_message(t)
        return self.format_field_with_default_factory(factory)

    def formart_default_factory_array(self, t: Array) -> str:
        value = self.format_default_value_array(t)
        return f"lambda: {value}"

    def format_field_default_array(self, t: Array) -> str:
        factory = self.formart_default_factory_array(t)
        return self.format_field_with_default_factory(factory)

    @final
    def format_field_default_value(self, t: Type) -> str:
        if isinstance(t, Bool):
            return self.format_default_value_bool()
        elif isinstance(t, Byte):
            return self.format_default_value_byte()
        elif isinstance(t, Uint):
            return self.format_default_value_uint()
        elif isinstance(t, Int):
            return self.format_default_value_int()
        elif isinstance(t, Array):
            return self.format_field_default_array(t)
        elif isinstance(t, Enum):
            return self.format_default_value_enum(t)
        elif isinstance(t, Message):
            return self.format_field_default_message(t)
        elif isinstance(t, Alias):
            return self.format_field_default_alias(t)
        raise InternalError(f"format_field_default_value got unexpected type {t}")

    def format_processor(self, t: Type) -> str:
        if isinstance(t, Bool):
            return self.format_processor_bool()
        elif isinstance(t, Int):
            return self.format_processor_int(t)
        elif isinstance(t, Uint):
            return self.format_processor_uint(t)
        elif isinstance(t, Byte):
            return self.format_processor_byte()
        elif isinstance(t, Array):
            return self.format_processor_array(t)
        elif isinstance(t, Enum):
            return self.format_processor_enum(t)
        elif isinstance(t, Alias):
            return self.format_processor_alias(t)
        elif isinstance(t, Message):
            return self.format_processor_message(t)
        raise InternalError("format_bp_type got unexpected t")

    def format_processor_bool(self) -> str:
        return "bp.Bool()"

    def format_processor_int(self, t: Int) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"bp.Int({nbits})"

    def format_processor_uint(self, t: Uint) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"bp.Uint({nbits})"

    def format_processor_byte(self) -> str:
        return f"bp.Byte()"

    def format_processor_array(self, t: Array) -> str:
        extensible = self.format_bool_value(t.extensible)
        capacity = self.format_int_value(t.cap)
        et = self.format_processor(t.element_type)
        return f"bp.Array({extensible}, {capacity}, {et})"

    def format_processor_name_enum(self, t: Enum) -> str:
        return self.format_name_related_to_definition(
            t, "bp_processor_{definition_name}"
        )

    def format_processor_enum(self, t: Enum) -> str:
        processor_name = self.format_processor_name_enum(t)
        return f"{processor_name}()"

    def format_processor_name_alias(self, t: Alias) -> str:
        return self.format_name_related_to_definition(
            t, "bp_processor_{definition_name}"
        )

    def format_processor_alias(self, t: Alias) -> str:
        processor_name = self.format_processor_name_alias(t)
        return f"{processor_name}()"

    def format_processor_message(self, t: Message) -> str:
        message_name = self.format_message_name(t)
        return f"{message_name}().bp_processor()"
