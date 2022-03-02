#include <assert.h>
#include <stdio.h>

#include "enums_bp.h"

int main(void) {
    // Encode.
    struct EnumContainer enum_container = {0};

    enum_container.my_enum = MY_ENUM_ONE;

    unsigned char s[BYTES_LENGTH_ENUM_CONTAINER] = {0};
    EncodeEnumContainer(&enum_container, s);

    // Output
    for (int i = 0; i < BYTES_LENGTH_ENUM_CONTAINER; i++) printf("%u ", s[i]);

    // Decode.
    struct EnumContainer enum_container_new = {0};
    DecodeEnumContainer(&enum_container_new, s);

    assert(enum_container_new.my_enum == enum_container.my_enum);
    return 0;
}
