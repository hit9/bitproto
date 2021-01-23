#include <assert.h>
#include <stdio.h>

#include "empty_bp.h"

int main(void) {
    // Encode.
    struct A a = {};
    unsigned char s1[BYTES_LENGTH_A] = {};
    EncodeA(&a, s1);

    struct B b = {};
    b.ok = true;
    unsigned char s2[BYTES_LENGTH_B] = {};
    EncodeB(&b, s2);

    struct C c = {};
    unsigned char s3[BYTES_LENGTH_C] = {};
    EncodeC(&c, s3);

    // Output
    for (int i = 0; i < BYTES_LENGTH_A; i++) printf("%u ", s1[i]);
    for (int i = 0; i < BYTES_LENGTH_B; i++) printf("%u ", s2[i]);
    for (int i = 0; i < BYTES_LENGTH_C; i++) printf("%u ", s3[i]);

    // Decode
    struct B b1 = {};
    DecodeB(&b1, s2);
    assert(b1.ok);
    return 0;
}
