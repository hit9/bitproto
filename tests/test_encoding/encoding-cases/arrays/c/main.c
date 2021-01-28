
#include <assert.h>
#include <stdio.h>

#include "arrays_bp.h"

int main(void) {
    // Encode.
    struct M m = {};
    for (int i = 0; i < 7; i++) m.a[i] = (unsigned char)(i);
    for (int i = 0; i < 7; i++) m.b[i] = (int32_t)(i);
    for (int i = 0; i < 7; i++) m.c[i] = (int8_t)(i);
    for (int i = 0; i < 7; i++) m.d[i] = (uint8_t)(i & 7);
    for (int i = 0; i < 7; i++) m.e[i] = (uint32_t)(i + 118);
    for (int i = 0; i < 7; i++)
        m.f[i] = (struct Note){i, false, {1, 2, 3, 4, 5, 6, 7}};
    m.g = (struct Note){2, false, {7, 2, 3, 4, 5, 6, 7}};
    unsigned char s[BYTES_LENGTH_M] = {0};
    EncodeM(&m, s);

    // Output
    for (int i = 0; i < BYTES_LENGTH_M; i++) printf("%u ", s[i]);

    // Decode.
    struct M m1 = {0};
    DecodeM(&m1, s);

    for (int i = 0; i < 7; i++) assert(m1.a[i] == m.a[i]);
    for (int i = 0; i < 7; i++) assert(m1.b[i] == m.b[i]);
    for (int i = 0; i < 7; i++) assert(m1.c[i] == m.c[i]);
    for (int i = 0; i < 7; i++) assert(m1.d[i] == m.d[i]);
    for (int i = 0; i < 7; i++) assert(m1.e[i] == m.e[i]);
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 7; j++) assert(m1.f[i].arr[j] == m.f[i].arr[j]);
        assert(m1.f[i].number == m.f[i].number);
        assert(m1.f[i].ok == m.f[i].ok);
    }
    for (int j = 0; j < 7; j++) assert(m1.g.arr[j] == m.g.arr[j]);
    assert(m1.g.number == m.g.number);
    assert(m1.g.ok == m.g.ok);

    return 0;
}
