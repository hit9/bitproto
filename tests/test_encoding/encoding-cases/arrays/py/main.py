import arrays_bp as bp


def main() -> None:
    m = bp.M()
    for i in range(7):
        m.a[i] = i
    for i in range(7):
        m.b[i] = i
    for i in range(7):
        m.c[i] = i
    for i in range(7):
        m.d[i] = i
    for i in range(7):
        m.e[i] = i + 118
    for i in range(7):
        m.f[i] = bp.Note(i, False, [j for j in range(1, 8)])
    for i in range(7):
        for j in range(7):
            m.t[i][j] = i + j + 129
    m.g = bp.Note(2, False, [7, 2, 3, 4, 5, 6, 7])
    s = m.encode()

    for x in s:
        print(x, end=" ")

    m1 = bp.M()
    m1.decode(s)

    for i in range(7):
        assert m1.a[i] == m.a[i]
    for i in range(7):
        assert m1.b[i] == m.b[i]
    for i in range(7):
        assert m1.c[i] == m.c[i]
    for i in range(7):
        assert m1.d[i] == m.d[i]
    for i in range(7):
        assert m1.e[i] == m.e[i]
    for i in range(7):
        for j in range(7):
            assert m1.f[i].arr[j] == m.f[i].arr[j]
        assert m1.f[i].number == m.f[i].number
        assert m1.f[i].ok == m.f[i].ok
    for j in range(7):
        assert m1.g.arr[j] == m.g.arr[j]
    assert m1.g.number == m.g.number
    assert m1.g.ok == m.g.ok
    for i in range(7):
        for j in range(7):
            assert m1.t[i][j] == m.t[i][j]


if __name__ == "__main__":
    main()
