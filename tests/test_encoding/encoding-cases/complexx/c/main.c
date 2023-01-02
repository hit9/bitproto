#include <assert.h>
#include <stdio.h>

#include "complexx_bp.h"

int main(void) {
    // Encode
    struct M1 m = {0};

    m.a = 1;
    m.b = true;
    m.c = 2;
    m.m3.e = 15;
    m.m3.f = -17;
    m.m3.bytes[11] = 1;
    m.m3.bytes[12] = 24;
    m.m3.bytes[13] = 23;
    m.m3.table[0][0] = -1;
    m.m3.table[0][1] = 1;
    m.m3.table[1][1] = -3;
    m.m3.table[3][3] = -9;
    m.m3.e8 = E32;
    m.x.b = 9223372036854775807;
    m.x.a = true;
    m.x.c = 2064;
    m.x.e9 = X_E92;
    m.x.d = -181818;
    m.m4.b = false;
    m.m4.xy = 3;
    m.o[1] = 1;
    m.o[2] = -1;
    m.o[3] = -53;
    m.m[1].e = 2;
    m.m[1].f = -18;
    m.m[7].f = -3;
    m.m[7].table[0][1] = 2;
    m.n[0] = -1;
    m.n[1] = -2;
    m.n[3] = 1;
    m.n[30] = -2;
    m.n[23] = 23;
    m.tx[0][0] = 41;
    m.tx[0][1] = 42;
    m.tx[0][3] = 33;
    m.tx[1][3] = -1;
    m.tx[2][3] = -23;
    m.t[2] = 15;

    unsigned char s[BYTES_LENGTH_M1] = {0};
    EncodeM1(&m, s);

    // Output
    for (int i = 0; i < BYTES_LENGTH_M1; i++) printf("%u ", s[i]);

    // Decode
    struct M1 m1 = {0};
    DecodeM1(&m1, s);

    assert(m1.a == m.a);
    assert(m1.b == m.b);
    assert(m1.c == m.c);
    assert(m1.m3.e == m.m3.e);
    assert(m1.m3.f == m.m3.f);
    assert(m1.m3.bytes[11] == m.m3.bytes[11]);
    assert(m1.m3.bytes[12] == m.m3.bytes[12]);
    assert(m1.m3.bytes[13] == m.m3.bytes[13]);
    assert(m1.m3.table[0][0] == m.m3.table[0][0]);
    assert(m1.m3.table[0][1] == m.m3.table[0][1]);
    assert(m1.m3.table[1][1] == m.m3.table[1][1]);
    assert(m1.m3.table[3][3] == m.m3.table[3][3]);
    assert(m1.m3.e8 == m.m3.e8);
    assert(m1.x.b == m.x.b);
    assert(m1.x.a == m.x.a);
    assert(m1.x.c == m.x.c);
    assert(m1.x.e9 == m.x.e9);
    assert(m1.x.d == m.x.d);
    assert(m1.m4.b == m.m4.b);
    assert(m1.m4.xy == m.m4.xy);
    assert(m1.o[1] == m.o[1]);
    assert(m1.o[2] == m.o[2]);
    assert(m1.o[3] == m.o[3]);
    assert(m1.m[1].e == m.m[1].e);
    assert(m1.m[1].f == m.m[1].f);
    assert(m1.m[7].f == m.m[7].f);
    assert(m1.m[7].table[0][1] == m.m[7].table[0][1]);
    assert(m1.n[0] == m.n[0]);
    assert(m1.n[1] == m.n[1]);
    assert(m1.n[3] == m.n[3]);
    assert(m1.n[30] == m.n[30]);
    assert(m1.n[23] == m.n[23]);
    assert(m1.tx[0][0] == m.tx[0][0]);
    assert(m1.tx[0][1] == m.tx[0][1]);
    assert(m1.tx[0][3] == m.tx[0][3]);
    assert(m1.tx[1][3] == m.tx[1][3]);
    assert(m1.tx[2][3] == m.tx[2][3]);
    assert(m1.t[2] == m.t[2]);

    return 0;
}
