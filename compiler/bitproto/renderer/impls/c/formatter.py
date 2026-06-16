"""
C formatter.
"""

from typing import List, Optional

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
        return CaseStyleMapping(
            {
                Constant: "upper",
                Alias: "pascal",
                Enum: "pascal",
                EnumField: ("snake", "upper"),
                Message: "pascal",
            }
        )

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

    def format_bp_type_flag(self, t: Type) -> str:
        """Formats the BP_XXX flag name in C."""
        if isinstance(t, Bool):
            return "BP_TYPE_BOOL"
        if isinstance(t, Int):
            return "BP_TYPE_INT"
        if isinstance(t, Uint):
            return "BP_TYPE_UINT"
        if isinstance(t, Byte):
            return "BP_TYPE_BYTE"
        if isinstance(t, Enum):
            return "BP_TYPE_ENUM"
        if isinstance(t, Alias):
            return "BP_TYPE_ALIAS"
        if isinstance(t, Message):
            return "BP_TYPE_BP_TYPE_MESSAGE"
        if isinstance(t, Array):
            return "BP_TYPE_ARRAY"
        raise InternalError("format_bp_type_flag got unexpected type")

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
        to_flag = self.format_bp_type_flag(t.type)
        return f"BpAlias({nbits}, {size}, {processor}, {formatter}, {to_flag})"

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

    def _format_unsigned_chain_type(self, t: Type) -> str:
        """Returns the unsigned C integer type for the field type t.
        Used to generate endian-neutral bit-shift code instead of byte-pointer
        indexing, which assumes little-endian host byte order.
        """
        if isinstance(t, Alias):
            return self._format_unsigned_chain_type(t.type)
        if isinstance(t, Enum):
            return self._format_unsigned_chain_type(t.type)
        if isinstance(t, Bool):
            return "uint8_t"
        if isinstance(t, Byte):
            return "unsigned char"
        if isinstance(t, Uint):
            return self.format_uint_type(t)
        if isinstance(t, Int):
            n = self.get_nbits_of_integer(t)
            return f"uint{n}_t"
        return "unsigned"

    @override(Formatter)
    def format_op_mode_encoder_item(
        self, chain: str, t: Type, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        """Implements format_op_mode_encoder_item for C.
        Generated C statement like:

            s[0] = ((uint8_t)((*m).color) >> 3) & 7;

        Uses explicit bit shifts instead of byte-pointer indexing so the output
        is correct on both little-endian and big-endian hosts.  fi*8 scales the
        byte index into a bit offset; the per-byte shift is then folded in so
        a single right- or left-shift covers both.
        """
        assign = "=" if r == 0 else "|="
        unsigned_type = self._format_unsigned_chain_type(t)
        total_shift = fi * 8 + shift
        total_shift_s = self.format_op_mode_smart_shift(total_shift)
        return f"s[{si}] {assign} (({unsigned_type})({chain}){total_shift_s}) & {mask};"

    @override(Formatter)
    def format_op_mode_decoder_item(
        self, chain: str, t: Type, si: int, fi: int, shift: int, mask: int, r: int
    ) -> str:
        """Implements format_op_mode_decoder_item for C.
        Generated C statement like:

            (*m).color |= (uint8_t)(((unsigned)(s[0]) << 3) & 7);

        Always uses |= (never =) so each byte contributes its bits without
        clobbering already-written bytes.  The generated Decode function starts
        with memset(m, 0, sizeof(*m)) to guarantee a zero baseline.
        fi*8 positions the extracted bits at the correct byte of the field.
        """
        chain_type = self.format_type(t)
        shift_s = self.format_op_mode_smart_shift(shift)
        fi_shift = fi * 8
        byte_val = f"(((unsigned)(s[{si}]){shift_s}) & {mask})"
        if fi_shift > 0:
            unsigned_type = self._format_unsigned_chain_type(t)
            return (
                f"{chain} |= ({chain_type})(({unsigned_type}){byte_val} << {fi_shift});"
            )
        return f"{chain} |= ({chain_type}){byte_val};"

    @override(Formatter)
    def post_format_op_mode_endecode_single_type(
        self, t: Type, chain: str, is_encode: bool
    ) -> List[str]:
        """
        Hook function called after a message field is generated.
        """
        if isinstance(t, Alias):
            t = t.type
        if isinstance(t, Int):
            return self.post_format_op_mode_endecode_int(t, chain, is_encode)
        return []

    def post_format_op_mode_endecode_int(
        self, t: Int, chain: str, is_encode: bool
    ) -> List[str]:
        """
        Process signed integers during decoding code generation in optimization mode.

        Generated C statement example:

            if (((*m).pressure_sensor.pressure >> 23) & 1) (*m).pressure_sensor.pressure |= -16777216;
        """
        if is_encode:
            return []

        # Signed integers processing is only about decoding
        n = t.nbits()

        if n in {8, 16, 32, 64}:
            # No need to do additional actions
            # int8/16/32/64 signed integers' sign bit is already on the highest bit position.
            return []

        m = ~((1 << n) - 1)
        mask = f"{m}"

        if n == 63:
            # Avoid this compiler error for mask == -9223372036854775808;
            # warning: integer literal is too large to be represented in a signed integer type,
            # interpreting as unsigned [-Wimplicitly-unsigned-literal]
            mask = f"(-9223372036854775807 - 1)"

        # For a signed integer e.g. 16777205, the most concise approach should be: 16777205 << 24 >> 24,
        # this shifts the 24th bit to the highest bit position, and then shift right again.
        # By doing an arithmetic right shifting, the leftmost sign bit got propagated, the result is -11.
        # This way is concise, but may not be portable.
        # Right shift behavior on negative signed integers is implementation-defined.
        # Another safe approach is: test the 24th bit at first ((16777205 >> 23) & 1), if it’s 1,
        # then do a OR operation with a mask,  16777205 |= ~(1<<24 -1) , the result is also -11.
        return [f"if (({chain} >> {n-1}) & 1) {chain} |= {mask};"]
