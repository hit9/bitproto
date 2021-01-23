#include <assert.h>
#include <stdio.h>

#include "nested_bp.h"

int main(void) {
    // Encode
    struct B b = {};
    b.a.b = true;
    b.d.ok = true;
    unsigned char s1[BYTES_LENGTH_B] = {0};
    EncodeB(&b, s1);

    struct C c = {};
    c.a.d.d.ok = true;
    c.a.d.f = 2;
    c.d.d.ok = true;
    c.d.f = 1;

    unsigned char s2[BYTES_LENGTH_C] = {0};
    EncodeC(&c, s2);

    struct D d = {};
    d.d.g = 2;
    d.a = D_A_OK;

    unsigned char s3[BYTES_LENGTH_C] = {0};
    EncodeD(&d, s3);

    // Output
    for (int i = 0; i < BYTES_LENGTH_B; i++) printf("%d ", s1[i]);
    for (int i = 0; i < BYTES_LENGTH_C; i++) printf("%d ", s2[i]);
    for (int i = 0; i < BYTES_LENGTH_D; i++) printf("%d ", s3[i]);

    // Decode
    struct B b1 = {};
    DecodeB(&b1, s1);
    assert(b1.a.b == true);
    assert(b1.d.ok == true);

    struct C c1 = {};
    DecodeC(&c1, s2);
    assert(c1.a.d.d.ok == true);
    assert(c1.a.d.f == 2);
    assert(c1.d.d.ok == true);
    assert(c1.d.f == 1);

    struct D d1 = {};
    DecodeD(&d1, s3);
    assert(d1.d.g == 2);
    assert(d1.a == D_A_OK);
}
