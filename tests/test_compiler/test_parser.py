import os
from typing import Union as Fixture

import pytest
from bitproto._ast import Array, Bool, Enum, Message, MessageField, Proto
from bitproto.parser import parse
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
    pass


def test_parse_extensible() -> None:
    pass


def test_parse_array_cap_constraint() -> None:
    pass


def test_parse_message_size_constraint() -> None:
    pass


def test_parse_2d_array() -> None:
    pass


def test_parse_import() -> None:
    pass


def test_parse_empty() -> None:
    pass
