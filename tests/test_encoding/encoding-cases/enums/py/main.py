import enums_bp as bp


def main() -> None:
    # Encode.
    enum_container = bp.EnumContainer(my_enum=bp.MyEnum.MY_ENUM_ONE)

    s = enum_container.encode()  # bytearray

    for b in s:
        print(int(b), end=" ")

    # Decode
    enum_container_new = bp.EnumContainer()
    enum_container_new.decode(s)

    assert enum_container_new.my_enum == enum_container.my_enum
    assert enum_container_new.encode() == s
    assert isinstance(enum_container.my_enum, bp.MyEnum)
    assert isinstance(enum_container_new.my_enum, bp.MyEnum)
    assert enum_container.my_enum is bp.MyEnum.MY_ENUM_ONE
    assert enum_container_new.my_enum is bp.MyEnum.MY_ENUM_ONE

    # try to pass in plain integer
    enum_container = bp.EnumContainer(my_enum=2)
    assert isinstance(enum_container.my_enum, bp.MyEnum)
    assert enum_container.my_enum is bp.MyEnum.MY_ENUM_TWO


if __name__ == "__main__":
    main()
