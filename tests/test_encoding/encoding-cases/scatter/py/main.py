import scatter_bp as bp


def main() -> None:
    # Encode.
    b = bp.B()

    b.a.a = 1
    b.a.b = 2
    b.a.c = 3
    b.a.d = 4
    b.a.e = 5
    b.a.f = 6
    b.a.g = 7
    b.a.h = 8
    b.a.i = 9
    b.a.j = 10
    b.a.k = 11
    b.a.l = 12
    b.a.m = 13
    b.a.n = 14
    b.a.p = 15
    b.a.q = 16
    b.a.r = 17
    b.a.s = 18
    b.a.t = 19
    b.b = True
    b.c = 34567

    s = b.encode()  # bytearray

    for x in s:
        print(int(x), end=" ")

    # Decode
    b1 = bp.B()
    b1.decode(s)

    assert b.a.a == b1.a.a
    assert b.a.b == b1.a.b
    assert b.a.c == b1.a.c
    assert b.a.d == b1.a.d
    assert b.a.e == b1.a.e
    assert b.a.f == b1.a.f
    assert b.a.g == b1.a.g
    assert b.a.h == b1.a.h
    assert b.a.i == b1.a.i
    assert b.a.j == b1.a.j
    assert b.a.k == b1.a.k
    assert b.a.l == b1.a.l
    assert b.a.m == b1.a.m
    assert b.a.n == b1.a.n
    assert b.a.p == b1.a.p
    assert b.a.q == b1.a.q
    assert b.a.r == b1.a.r
    assert b.a.s == b1.a.s
    assert b.a.t == b1.a.t
    assert b.b == b1.b
    assert b.c == b1.c


if __name__ == "__main__":
    main()
