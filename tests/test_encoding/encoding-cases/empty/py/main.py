import empty_bp as bp


def main() -> None:
    a = bp.A()
    s1 = a.encode()

    b = bp.B()
    b.ok = True
    s2 = b.encode()

    c = bp.C()
    s3 = c.encode()

    for x in s1:
        print(int(x), end=" ")
    for x in s2:
        print(int(x), end=" ")
    for x in s3:
        print(int(x), end=" ")

    b1 = bp.B()
    b1.decode(s2)
    assert b1.ok


if __name__ == "__main__":
    main()
