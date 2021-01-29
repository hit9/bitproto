"""
Go formatter
"""

from typing import Optional

from bitproto._ast import (
    Alias,
    Array,
    Bool,
    Byte,
    Constant,
    Enum,
    EnumField,
    Int,
    Integer,
    Message,
    MessageField,
    Proto,
    Type,
    Uint,
)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import CaseStyleMapping, Formatter
from bitproto.utils import cast_or_raise, override


class GoFormatter(Formatter):
    """Formatter for Go language."""

    ###################
    # Language Basics
    ###################

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
    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        path = t.get_option_as_string_or_raise("go.package_path") or f"{t.name}_bp"
        if as_name:
            return f'import {as_name} "{path}"'
        return f'import "{path}"'

    ###################
    # Value literals
    ###################

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

    ###################
    # Type representing
    ###################

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
    def format_int_value_type(self) -> str:
        return "int"

    @override(Formatter)
    def format_string_value_type(self) -> str:
        return "string"

    @override(Formatter)
    def format_bool_value_type(self) -> str:
        return "bool"

    ###################
    # Library Supports
    ###################

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
        return "bp.NewBool()"

    def format_processor_int(self, t: Int) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"bp.NewInt({nbits})"

    def format_processor_uint(self, t: Uint) -> str:
        nbits = self.format_int_value(t.nbits())
        return f"bp.NewUint({nbits})"

    def format_processor_byte(self) -> str:
        return f"bp.NewByte()"

    def format_processor_array(self, t: Array) -> str:
        extensible = self.format_bool_value(t.extensible)
        capacity = self.format_int_value(t.cap)
        et = self.format_processor(t.element_type)
        return f"bp.NewArray({extensible}, {capacity}, {et})"

    def format_processor_enum(self, t: Enum) -> str:
        enum_name = self.format_enum_name(t)
        return f"({enum_name}(0)).BpProcessor()"

    def format_processor_alias(self, t: Alias) -> str:
        alias_name = self.format_alias_name(t)
        s: str
        if isinstance(t.type, Bool):
            s = f"{alias_name}(false)"
        elif isinstance(t.type, (Integer, Enum, Byte)):
            s = f"{alias_name}(0)"
        elif isinstance(t.type, Array):
            s = f"{alias_name}{{}}"
        else:
            raise InternalError("format_bp_alias got unexpected alias type")
        return f"({s}).BpProcessor()"

    def format_processor_message(self, t: Message) -> str:
        message_name = self.format_message_name(t)
        return f"(&{message_name}{{}}).BpProcessor()"

    ###################
    # Optimization Mode.
    ###################

    @override(Formatter)
    def format_op_mode_endecoder_message_var(self) -> str:
        return "m"

    @override(Formatter)
    def format_op_mode_encoder_item(
        self, chain: str, t: Type, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        """Implements format_op_mode_encoder_item for Go.
        Generated Go statement like:

                s[0] |= (byte(m.Color >> 8) >> 5) & 7

        """
        bshift = " >> {0}".format(fi * 8) if fi > 0 else ""
        shift_s = self.format_op_mode_smart_shift(shift)

        # Handle go's annoying type casting
        if isinstance(t, Bool):
            chain = f"bool2byte({chain})"
        elif isinstance(t, Alias):
            alias_t = cast_or_raise(Alias, t)
            if isinstance(alias_t.type, Bool):
                chain = f"bool2byte(bool({chain}))"

        return f"s[{si}] |= (byte({chain}{bshift}) {shift_s}) & {mask}"

    @override(Formatter)
    def format_op_mode_decoder_item(
        self, chain: str, t: Type, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        """Implements format_op_mode_encoder_item for Go.
        Generated Go statement like:

                m.Color |= uint16(byte(s[0]>>3) & 31) << 8

        """
        bshift = " << {0}".format(fi * 8) if fi > 0 else ""
        shift_s = self.format_op_mode_smart_shift(shift)

        byte = f"byte(s[{si}] {shift_s}) & {mask}"

        assign = "|="
        type_s = self.format_type(t)
        data = f"{type_s}({byte})"

        # Handle go's annoying type casting
        if isinstance(t, Bool):
            data = f"byte2bool({byte})"
            assign = "="
        elif isinstance(t, Alias):
            alias_t = cast_or_raise(Alias, t)
            if isinstance(alias_t.type, Bool):
                data = f"{type_s}(byte2bool({byte}))"
                assign = "="

        return f"{chain} {assign} {data}{bshift}"
