"""
C formatter.
"""

from typing import Optional

from bitproto._ast import (
    Alias,
    Array,
    Bool,
    Byte,
    Constant,
    Definition,
    Enum,
    EnumField,
    Int,
    Message,
    MessageField,
    Proto,
    SingleType,
    Type,
    Uint,
)
from bitproto.errors import InternalError
from bitproto.renderer.formatter import CaseStyleMapping, Formatter
from bitproto.utils import override


class CFormatter(Formatter):
    """CFormatter implements Formatter for C language."""

    #################
    # Language Basics
    #################

    @override(Formatter)
    def case_style_mapping(self) -> CaseStyleMapping:
        return {
            Constant: "upper",
            Alias: "pascal",
            Enum: "pascal",
            EnumField: ("snake", "upper"),
            Message: "pascal",
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

    def format_sizeof(self, t: str) -> str:
        return f"sizeof({t})"

    @override(Formatter)
    def format_import_statement(self, t: Proto, as_name: Optional[str] = None) -> str:
        return '#include "{0}_bp.h"'.format(t.name)

    ##################
    # Naming prefix
    ##################

    @override(Formatter)
    def definition_name_prefix_option_name(self) -> str:
        return "c.name_prefix"

    def bp_processor_name_prefix(self) -> str:
        return "BpXXXProcess"

    def bp_json_formatter_name_prefix(self) -> str:
        return "BpXXXJsonFormat"

    ############################
    # Value literal representing
    #############################

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

    ###########################
    # Type literal representing
    ###########################

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

    ###################
    # Library Supports
    ###################

    def format_bp_type(self, t: Type, d: Optional[Definition] = None) -> str:
        if isinstance(t, Bool):
            return self.format_bp_bool()
        if isinstance(t, Int):
            return self.format_bp_int(t)
        if isinstance(t, Uint):
            return self.format_bp_uint(t)
        if isinstance(t, Byte):
            return self.format_bp_byte()
        if isinstance(t, Enum):
            return self.format_bp_enum(t)
        if isinstance(t, Alias):
            return self.format_bp_alias(t)
        if isinstance(t, Message):
            return self.format_bp_message(t)
        if isinstance(t, Array):
            assert d is not None, InternalError("format_bp_array requires defintion")
            return self.format_bp_array(t, d)
        raise InternalError("format_bp_type got unexpected type")

    def format_bp_bool(self) -> str:
        return "BpBool()"

    def format_bp_int(self, t: Int) -> str:
        nbits = self.format_int_value(t.nbits())
        size = self.format_sizeof(self.format_int_type(t))
        return f"BpInt({nbits}, {size})"

    def format_bp_uint(self, t: Uint) -> str:
        nbits = self.format_int_value(t.nbits())
        size = self.format_sizeof(self.format_uint_type(t))
        return f"BpUint({nbits}, {size})"

    def format_bp_byte(self) -> str:
        return f"BpByte()"

    def format_bp_message(self, t: Message) -> str:
        nbits = self.format_int_value(t.nbits())
        message_type = self.format_message_type(t)
        size = self.format_sizeof(message_type)
        processor = self.format_bp_message_processor_name(t)
        formatter = self.format_bp_message_json_formatter_name(t)
        return f"BpMessage({nbits}, {size}, {processor}, {formatter})"

    def format_bp_enum(self, t: Enum) -> str:
        nbits = self.format_int_value(t.nbits())
        enum_type = self.format_enum_type(t)
        size = self.format_sizeof(enum_type)
        return f"BpEnum({nbits}, {size})"

    def format_bp_array(self, t: Array, d: Definition) -> str:
        nbits = self.format_int_value(t.nbits())
        element_type = self.format_type(t.element_type)
        size_element = self.format_sizeof(element_type)
        capacity = self.format_int_value(t.cap)
        size = f"{capacity} * {size_element}"
        processor = self.format_bp_array_processor_name(t, d)
        formatter = self.format_bp_array_json_formatter_name(t, d)
        return f"BpArray({nbits}, {size}, {processor}, {formatter})"

    def format_bp_alias(self, t: Alias) -> str:
        nbits = self.format_int_value(t.nbits())
        alias_type = self.format_alias_type(t)
        size = self.format_sizeof(alias_type)
        processor = self.format_bp_alias_processor_name(t)
        formatter = self.format_bp_alias_json_formatter_name(t)
        return f"BpAlias({nbits}, {size}, {processor}, {formatter})"

    def format_bp_enum_descriptor(self, t: Enum) -> str:
        bp_uint = self.format_bp_uint(t.type)
        return f"BpEnumDescriptor({bp_uint})"

    def format_bp_message_descriptor(
        self, t: Message, field_descriptors: str = "field_descriptors"
    ) -> str:
        extensible = self.format_bool_value(t.extensible)
        nfields = self.format_int_value(t.nfields())
        nbits = self.format_int_value(t.nbits())
        return f"BpMessageDescriptor({extensible}, {nfields}, {nbits}, {field_descriptors})"

    def format_bp_message_processor_name(self, t: Message) -> str:
        message_name = self.format_message_name(t)
        prefix = self.bp_processor_name_prefix()
        return f"{prefix}{message_name}"

    def format_bp_alias_descriptor(self, t: Alias) -> str:
        bp_type = self.format_bp_type(t.type, t)
        return f"BpAliasDescriptor({bp_type})"

    def format_bp_alias_processor_name(self, t: Alias) -> str:
        alias_name = self.format_alias_name(t)
        prefix = self.bp_processor_name_prefix()
        return f"{prefix}{alias_name}"

    def format_bp_array_descriptor(self, t: Array) -> str:
        bp_type = self.format_bp_type(t.element_type)  # element_type won't be array
        extensible = self.format_bool_value(t.extensible)
        cap = self.format_int_value(t.cap)
        return f"BpArrayDescriptor({extensible}, {cap}, {bp_type})"

    def format_bp_array_processor_name(self, t: Array, d: Definition) -> str:
        if isinstance(d, MessageField):
            return self.format_bp_array_processor_name_from_message_field(t, d)
        if isinstance(d, Alias):
            return self.format_bp_array_processor_name_from_alias(t, d)
        raise InternalError(
            "format_bp_array_processor_name got unexpected defintion type"
        )

    def format_bp_array_processor_name_from_message_field(
        self, t: Array, d: MessageField
    ) -> str:
        message_name = self.format_message_name(d.message)
        prefix = self.bp_processor_name_prefix()
        return f"{prefix}Array{message_name}{d.number}"

    def format_bp_array_processor_name_from_alias(self, t: Array, d: Alias) -> str:
        alias_name = self.format_alias_name(d)
        prefix = self.bp_processor_name_prefix()
        return f"{prefix}Array{alias_name}"

    def format_bp_message_field_descriptor_initer(self, t: Message) -> str:
        message_name = self.format_message_name(t)
        return f"BpFieldDescriptorsInit{message_name}"

    def format_bp_message_json_formatter_name(self, t: Message) -> str:
        message_name = self.format_message_name(t)
        prefix = self.bp_json_formatter_name_prefix()
        return f"{prefix}{message_name}"

    def format_bp_alias_json_formatter_name(self, t: Alias) -> str:
        alias_name = self.format_alias_name(t)
        prefix = self.bp_json_formatter_name_prefix()
        return f"{prefix}{alias_name}"

    def format_bp_array_json_formatter_name(self, t: Array, d: Definition) -> str:
        if isinstance(d, MessageField):
            return self.format_bp_array_json_formatter_name_from_message_field(t, d)
        if isinstance(d, Alias):
            return self.format_bp_array_json_formatter_name_from_alias(t, d)
        raise InternalError(
            "format_bp_array_json_formatter_name got unexpected defintion type"
        )

    def format_bp_array_json_formatter_name_from_message_field(
        self, t: Array, d: MessageField
    ) -> str:
        message_name = self.format_message_name(d.message)
        prefix = self.bp_json_formatter_name_prefix()
        return f"{prefix}Array{message_name}{d.number}"

    def format_bp_array_json_formatter_name_from_alias(self, t: Array, d: Alias) -> str:
        alias_name = self.format_alias_name(d)
        prefix = self.bp_json_formatter_name_prefix()
        return f"{prefix}Array{alias_name}"

    ###################
    # Optimization Mode.
    ###################

    @override(Formatter)
    def format_op_mode_endecoder_message_var(self) -> str:
        return "(*m)"

    @override(Formatter)
    def format_op_mode_encoder_item(
        self, chain: str, t: Type, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        """Implements format_op_mode_encoder_item for C.
        Generated C statement like:

            s[0] = (((unsigned char *)&((*m).color))[0] >> 3) & 7;

        """
        assign = "=" if r == 0 else "|="
        shift_s = self.format_op_mode_smart_shift(shift)
        return f"s[{si}] {assign} (((unsigned char *)&({chain}))[{fi}] {shift_s}) & {mask};"

    @override(Formatter)
    def format_op_mode_decoder_item(
        self, chain: str, t: Type, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        """Implements format_op_mode_encoder_item for C.
        Generated C statement like:

            ((unsigned char *)&((*m).color))[0] = (s[0] << 3) & 7;

        """
        assign = "=" if r == 0 else "|="
        shift_s = self.format_op_mode_smart_shift(shift)
        return f"((unsigned char *)&({chain}))[{fi}] {assign} (s[{si}] {shift_s}) & {mask};"
