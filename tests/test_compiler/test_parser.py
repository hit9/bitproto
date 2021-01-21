import os
from typing import Union as Fixture

import pytest
from bitproto._ast import (Alias, Array, Bool, Constant, Enum, Int,
                           IntegerConstant, Message, MessageField, Option,
                           Proto, StringConstant)
from bitproto.parser import GrammarError, parse
from bitproto.utils import cast_or_raise


def bitproto_filepath(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "parser-cases", filename)


@pytest.fixture
def proto_drone() -> Proto:
    return parse(bitproto_filepath("drone.bitproto"))


def test_parse_drone() -> None:
    filepath = bitproto_filepath("drone.bitproto")
    proto = parse(filepath)

    # Test Proto
    assert proto.name == "drone"
    assert proto.is_frozen()
    assert os.path.samefile(proto.filepath, filepath)
    assert proto._bound is None

    # Test scope.get_member()
    message_drone = proto.get_member("Drone")
    assert message_drone is not None
    assert isinstance(message_drone, Message)
    assert message_drone.name == "Drone"
    assert message_drone.bound is proto

    message_drone = cast_or_raise(Message, message_drone)

    # Test message.nfields
    assert message_drone.nfields() == 7

    # Test message.sorted_fields()
    assert tuple(f.number for f in message_drone.sorted_fields()) == tuple(range(1, 8))

    # Test message.number_to_field()
    assert 1 in message_drone.number_to_field()
    assert len(message_drone.number_to_field()) == 7

    # Test message.number_to_field_sorted()
    assert 1 in message_drone.number_to_field()
    assert len(message_drone.number_to_field()) == 7
    assert tuple(message_drone.number_to_field_sorted().keys()) == tuple(range(1, 8))

    # Test field
    field_position = message_drone.number_to_field()[2]
    assert field_position is not None
    assert isinstance(field_position, MessageField)
    assert field_position.name == "position"
    assert field_position is message_drone.get_member("position")
    assert isinstance(field_position.type, Message)

    # Test message nbits.
    message_network = proto.get_member("Network")
    message_network = cast_or_raise(Message, message_network)
    assert message_network.nbits() == 4 + 64

    # Test message options
    assert message_drone.options() == []

    # Test enum
    enum_drone_status = proto.get_member("DroneStatus")
    assert enum_drone_status is not None
    assert isinstance(enum_drone_status, Enum)
    assert not enum_drone_status.extensible

    enum_drone_status = cast_or_raise(Enum, enum_drone_status)

    # Test enum nbits
    assert enum_drone_status.nbits() == 3
    assert len(enum_drone_status.fields()) == 5

    # Test enum.name_to_values()
    assert tuple(enum_drone_status.name_to_values().keys()) == (
        "DRONE_STATUS_UNKNOWN",
        "DRONE_STATUS_STANDBY",
        "DRONE_STATUS_RISING",
        "DRONE_STATUS_LANDING",
        "DRONE_STATUS_FLYING",
    )

    # Test enum.value_to_names()
    assert tuple(enum_drone_status.value_to_names()) == (0, 1, 2, 3, 4)

    # Test array.
    field_propellers = message_drone.get_member("propellers")
    assert field_propellers and isinstance(field_propellers, MessageField)
    field_propellers = cast_or_raise(MessageField, field_propellers)
    assert isinstance(field_propellers.type, Array)
    array_of_propellers = cast_or_raise(Array, field_propellers.type)
    assert array_of_propellers.cap == 4
    assert array_of_propellers.nbits() == 4 * array_of_propellers.element_type.nbits()
    assert not array_of_propellers.extensible

    # Test alias
    alias_timestamp = cast_or_raise(Alias, proto.get_member("Timestamp"))
    assert alias_timestamp
    assert isinstance(alias_timestamp.type, Int)


def test_parse_optional_semicolon() -> None:
    parse(bitproto_filepath("optional_semicolon.bitproto"))


def test_parse_nested_message() -> None:
    proto = parse(bitproto_filepath("nested_message.bitproto"))

    message_a = cast_or_raise(Message, proto.get_member("A"))
    message_b = cast_or_raise(Message, proto.get_member("A", "B"))
    message_c = cast_or_raise(Message, proto.get_member("A", "B", "C"))

    field_a_b = message_a.sorted_fields()[0]
    field_a_c = message_a.sorted_fields()[1]
    field_b_c = message_b.sorted_fields()[0]
    field_c_is_ok = message_c.sorted_fields()[0]

    assert field_a_b.type is message_b
    assert field_a_c.type is message_c
    assert field_b_c.type is message_c
    assert isinstance(field_c_is_ok.type, Bool)

    assert message_c.nbits() == 1
    assert message_b.nbits() == 1
    assert message_a.nbits() == 1 + 1


def test_parse_reference_message() -> None:
    proto = parse(bitproto_filepath("reference_message.bitproto"))

    message_a = cast_or_raise(Message, proto.get_member("A"))
    message_b = cast_or_raise(Message, proto.get_member("A", "B"))
    message_c = cast_or_raise(Message, proto.get_member("A", "B", "C"))
    message_d = cast_or_raise(Message, proto.get_member("D"))
    message_e = cast_or_raise(Message, proto.get_member("E"))
    message_f = cast_or_raise(Message, proto.get_member("E", "F"))

    field_a_b = message_a.sorted_fields()[0]
    field_a_c = message_a.sorted_fields()[1]
    field_b_c = message_b.sorted_fields()[0]
    field_c_is_ok = message_c.sorted_fields()[0]
    field_d_a = message_d.sorted_fields()[0]
    field_d_b = message_d.sorted_fields()[1]
    field_d_c = message_d.sorted_fields()[2]
    field_f_c = message_f.sorted_fields()[0]

    assert field_a_b.type is message_b
    assert field_a_c.type is message_c
    assert field_b_c.type is message_c
    assert isinstance(field_c_is_ok.type, Bool)
    assert field_d_a.type is message_a
    assert field_d_b.type is message_b
    assert field_d_c.type is message_c
    assert field_f_c.type is message_c

    assert message_c.nbits() == 1
    assert message_b.nbits() == 1
    assert message_a.nbits() == 1 + 1
    assert message_d.nbits() == (1 + 1) + 1 + 1
    assert message_f.nbits() == 1


def test_parse_nested_enum() -> None:
    proto = parse(bitproto_filepath("nested_enum.bitproto"))

    message_a = cast_or_raise(Message, proto.get_member("A"))
    message_b = cast_or_raise(Message, proto.get_member("A", "B"))
    enum_c = cast_or_raise(Enum, proto.get_member("A", "B", "C"))
    message_d = cast_or_raise(Message, proto.get_member("D"))

    field_a_c = message_a.sorted_fields()[0]
    field_b_c = message_b.sorted_fields()[0]
    field_d_c = message_d.sorted_fields()[0]

    assert field_a_c.type is enum_c
    assert field_b_c.type is enum_c
    assert field_d_c.type is enum_c

    assert len(enum_c.fields()) == 3


def test_parse_option() -> None:
    proto = parse(bitproto_filepath("option_.bitproto"))

    option = proto.get_option_or_raise("c.struct_packing_alignment")
    assert option is not None

    option_c_alignment = proto.get_option_as_int_or_raise("c.struct_packing_alignment")
    assert option_c_alignment and option_c_alignment == 1

    message_a = cast_or_raise(Message, proto.get_member("A"))

    option_max_bytes = message_a.get_option_as_int_or_raise("max_bytes")
    assert option_max_bytes and option_max_bytes == 3


def test_parse_option_not_supported() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("option_not_supported.bitproto"))


def test_parse_extensible() -> None:
    proto = parse(bitproto_filepath("extensible.bitproto"))

    enum_c = cast_or_raise(Enum, proto.get_member("C"))
    enum_f = cast_or_raise(Enum, proto.get_member("F"))
    message_a = cast_or_raise(Message, proto.get_member("A"))
    message_b = cast_or_raise(Message, proto.get_member("B"))
    message_d = cast_or_raise(Message, proto.get_member("D"))
    message_e = cast_or_raise(Message, proto.get_member("E"))

    assert enum_c.extensible
    assert not enum_f.extensible
    assert message_a.extensible
    assert not message_b.extensible
    assert not message_d.extensible
    assert not message_e.extensible

    assert enum_c.nbits() == 3 + 8
    assert enum_f.nbits() == 3
    assert message_a.nbits() == 1 + 16
    assert message_b.nbits() == 1
    assert message_d.nbits() == enum_c.nbits()
    assert message_e.nbits() == message_a.nbits()


def test_parse_array_cap_constraint() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("array_cap_constraint.bitproto"))


def test_parse_message_size_constraint() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("message_size_constraint.bitproto"))


def test_parse_message_size_constraint_by_option() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("message_size_constraint_by_option.bitproto"))


def test_parse_2d_array() -> None:
    proto = parse(bitproto_filepath("_2d_array.bitproto"))

    alias_slice = cast_or_raise(Alias, proto.get_member("Slice"))
    alias_matrix = cast_or_raise(Alias, proto.get_member("Matrix"))
    message_a = cast_or_raise(Message, proto.get_member("A"))

    assert alias_slice.nbits() == 4 * 8
    assert alias_matrix.nbits() == 4 * 4 * 8
    assert message_a.nbits() == alias_matrix.nbits()
    assert message_a.fields()[0].type is alias_matrix


def test_parse_2d_array_e() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("_2d_array_e.bitproto"))


def test_parse_import() -> None:
    proto = parse(bitproto_filepath("import_.bitproto"))

    message_a = cast_or_raise(Message, proto.get_member("A"))
    constant_pi = cast_or_raise(IntegerConstant, proto.get_member("Pi"))
    proto_shared = cast_or_raise(Proto, proto.get_member("base"))
    proto_color = cast_or_raise(Proto, proto.get_member("color"))
    alias_slice = cast_or_raise(Alias, proto.get_member("base", "Slice"))
    enum_color = cast_or_raise(Enum, proto.get_member("color", "Color"))
    message_container = cast_or_raise(Message, proto.get_member("base", "Container"))

    assert proto_shared.name == "shared"
    assert constant_pi.value == 314

    field_container = message_a.fields()[0]
    field_slice = message_a.fields()[1]
    field_color = message_a.fields()[2]

    assert field_container.type is message_container
    assert field_slice.type is alias_slice
    assert field_color.type is enum_color


def test_parse_empty_message() -> None:
    proto = parse(bitproto_filepath("empty_message.bitproto"))

    message_empty = cast_or_raise(Message, proto.get_member("Empty"))
    message_a = cast_or_raise(Message, proto.get_member("A"))

    assert message_empty.nbits() == 0
    assert message_a.nbits() == 0


def test_parse_enum_size_constraint() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("enum_size_constraint.bitproto"))


def test_parse_escaping_char() -> None:
    proto = parse(bitproto_filepath("escaping_char.bitproto"))
    constant_a = cast_or_raise(StringConstant, proto.get_member("A"))
    constant_b = cast_or_raise(StringConstant, proto.get_member("B"))
    constant_c = cast_or_raise(StringConstant, proto.get_member("C"))
    constant_d = cast_or_raise(StringConstant, proto.get_member("D"))

    assert constant_a.value == "simple char \t"
    assert constant_b.value == 'simple char "V"'
    assert constant_c.value == "simple char \\"
    assert constant_d.value == "simple char '''"


def test_parse_duplicate_definition() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_1.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_2.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_3.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_4.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_5.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_6.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_definition_7.bitproto"))


def test_parse_reference_constant() -> None:
    proto = parse(bitproto_filepath("reference_constant.bitproto"))

    constant_a = cast_or_raise(IntegerConstant, proto.get_member("A"))
    constant_b = cast_or_raise(IntegerConstant, proto.get_member("B"))
    message_c = cast_or_raise(Message, proto.get_member("C"))
    constant_d = cast_or_raise(StringConstant, proto.get_member("D"))
    constant_e = cast_or_raise(StringConstant, proto.get_member("E"))

    assert constant_a.value == 2
    assert constant_b.value == 2 * 3
    assert constant_d.value == "abcde"
    assert constant_e.value == "abcde"

    field_c_b = message_c.fields()[0]
    assert isinstance(field_c_b.type, Array)
    array_type = cast_or_raise(Array, field_c_b.type)
    assert array_type.cap == constant_b.value


def test_parse_array_of_message() -> None:
    proto = parse(bitproto_filepath("array_of_message.bitproto"))

    message_a = cast_or_raise(Message, proto.get_member("A"))
    message_b = cast_or_raise(Message, proto.get_member("B"))
    alias_c = cast_or_raise(Alias, proto.get_member("C"))

    assert message_a.nbits() == 1
    assert isinstance(alias_c.type, Array)

    array_of_a = cast_or_raise(Array, alias_c.type)
    field_b_a = message_b.fields()[0]
    field_b_c = message_b.fields()[1]
    field_b_d = message_b.fields()[2]

    assert array_of_a.cap == 3
    assert array_of_a.element_type is message_a

    assert field_b_d.type is alias_c
    assert isinstance(field_b_a.type, Array)
    assert isinstance(field_b_c.type, Array)

    array_of_field_b_a = cast_or_raise(Array, field_b_a.type)
    array_of_field_b_c = cast_or_raise(Array, field_b_c.type)
    assert array_of_field_b_a.element_type is message_a
    assert array_of_field_b_c.element_type is alias_c

    assert alias_c.nbits() == 3 * 1
    assert message_b.nbits() == 2 * 1 + 3 * 1 * 3 + 3 * 1


def test_parse_reference_not_type() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("reference_not_type_1.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("reference_not_type_2.bitproto"))


def test_parse_reference_type_undefined() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("reference_type_undefined_1.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("reference_type_undefined_2.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("reference_type_undefined_3.bitproto"))


def test_parse_alias_named_definition() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("alias_named_definition_1.bitproto"))
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("alias_named_definition_2.bitproto"))


def test_parse_cycle_import() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("cycle_import.bitproto"))


def test_parse_nested_import() -> None:
    proto = parse(bitproto_filepath("nested_import.bitproto"))

    proto_shared_3 = cast_or_raise(Proto, proto.get_member("shared_3"))
    proto_shared_4 = cast_or_raise(Proto, proto.get_member("shared_4"))
    message_a = cast_or_raise(Message, proto.get_member("A"))
    message_c = cast_or_raise(Message, proto_shared_3.get_member("B", "C"))

    alias_timestamp = cast_or_raise(Alias, proto.get_member("shared_4", "Timestamp"))
    assert alias_timestamp is proto_shared_4.get_member("Timestamp")
    assert alias_timestamp.bound is proto_shared_4
    assert len(alias_timestamp.scope_stack) == 2

    message_record = cast_or_raise(Message, proto.get_member("shared_3", "Record"))
    assert message_record is proto_shared_3.get_member("Record")
    assert message_record.bound is proto_shared_3
    assert len(message_record.scope_stack) == 2

    enum_color = cast_or_raise(Enum, proto.get_member("shared_3", "Color"))
    assert enum_color is proto_shared_3.get_member("Color")
    assert enum_color.bound is proto_shared_3
    assert len(enum_color.scope_stack) == 2

    assert message_a.bound is proto

    field_a_color = message_a.fields()[0]
    field_a_record = message_a.fields()[1]
    field_a_created_at = message_a.fields()[2]
    field_a_c = message_a.fields()[3]

    assert field_a_color.type is enum_color
    assert field_a_record.type is message_record
    assert field_a_created_at.type is alias_timestamp
    assert field_a_c.type is message_c


def test_parse_message_field_number_constraint() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("message_field_number_constraint.bitproto"))


def test_parse_duplicate_message_field_number() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_message_field_number.bitproto"))


def test_parse_dupliate_enum_field_value() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("duplicate_enum_field_value.bitproto"))


def test_parse_hex_value() -> None:
    proto = parse(bitproto_filepath("hex_value.bitproto"))

    constant_a = cast_or_raise(IntegerConstant, proto.get_member("A"))
    constant_c = cast_or_raise(Constant, proto.get_member("C"))
    enum_b = cast_or_raise(Enum, proto.get_member("B"))

    assert constant_a.value == 0xF
    assert constant_c.value == 0x40
    assert enum_b.fields()[0].value == 0xF


def test_option_wrong_type() -> None:
    with pytest.raises(GrammarError):
        parse(bitproto_filepath("option_wrong_type.bitproto"))


def test_constants() -> None:
    pass
