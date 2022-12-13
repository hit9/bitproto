import signed_bp as bp


def main() -> None:
    # Encode
    y = bp.Y()

    y.x.a = -11
    y.x.b[0] = 61
    y.x.b[1] = -3
    y.x.b[2] = -29
    y.x.c = 23009
    y.xs[0].a = 1
    y.xs[1].a = -2008

    s = y.encode()  # bytearray

    for b in s:
        print(int(b), end=" ")

    # Decode
    y1 = bp.Y()
    y1.decode(s)

    assert y1.x.b[0] == y.x.b[0]
    assert y1.x.b[1] == y.x.b[1]
    assert y1.x.b[2] == y.x.b[2]
    assert y1.x.c == y.x.c
    assert y1.xs[0].a == y.xs[0].a
    assert y1.xs[1].a == y.xs[1].a


if __name__ == "__main__":
    main()
