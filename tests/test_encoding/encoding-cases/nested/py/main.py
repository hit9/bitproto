import nested_bp as bp


def main() -> None:
    b = bp.B()
    b.a.b = True
    b.d.ok = True
    s1 = b.encode()

    c = bp.C()
    c.a.d.d.ok = True
    c.a.d.f = 2
    c.d.d.ok = True
    c.d.f = 1
    s2 = c.encode()

    d = bp.D()
    d.d.g = 2
    d.a = bp.D_A_OK
    s3 = d.encode()

    # Output
    for x in s1:
        print(int(x), end=" ")
    for x in s2:
        print(int(x), end=" ")
    for x in s3:
        print(int(x), end=" ")

    # Decode
    b1 = bp.B()
    b1.decode(s1)
    assert b1.a.b == True
    assert b1.d.ok == True

    c1 = bp.C()
    c1.decode(s2)
    assert c1.a.d.d.ok == True
    assert c1.a.d.f == 2
    assert c1.d.d.ok == True
    assert c1.d.f == 1

    d1 = bp.D()
    d1.decode(s3)
    assert d1.d.g == 2
    assert d1.a == bp.D_A_OK


if __name__ == "__main__":
    main()
