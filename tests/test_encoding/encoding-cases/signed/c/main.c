#include <assert.h>
#include <stdio.h>

#include "signed_bp.h"

int main(void) {
    // Encode
    struct Y y = {0};

    y.x.a = -11;
    y.x.b[0] = 61;
    y.x.b[1] = -3;
    y.x.b[2] = -29;
    y.x.c = 23009;
    y.xs[0].a = 1;
    y.xs[1].a = -2008;
    y.p = 0;
    y.q = -1;

    unsigned char s[BYTES_LENGTH_Y] = {0};
    EncodeY(&y, s);

    // Output
    for (int i = 0; i < BYTES_LENGTH_Y; i++) printf("%u ", s[i]);

    // Decode.
    struct Y y1 = {0};
    DecodeY(&y1, s);

    assert(y1.x.a == y.x.a);
    assert(y1.x.b[0] == y.x.b[0]);
    assert(y1.x.b[1] == y.x.b[1]);
    assert(y1.x.b[2] == y.x.b[2]);
    assert(y1.x.c == y.x.c);
    assert(y1.xs[0].a == y.xs[0].a);
    assert(y1.xs[1].a == y.xs[1].a);
    assert(y1.p == y.p);
    assert(y1.q == y.q);

    return 0;
}
