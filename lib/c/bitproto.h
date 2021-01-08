// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto
// Encoding library for bitproto in C language.

#ifndef __BITPROTO_LIB_H__
#define __BITPROTO_LIB_H__

#include <inttypes.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if defined(__cplusplus)
extern "C" {
#endif

#define BP_DESCRIPTOR_TYPE_BOOL 1
#define BP_DESCRIPTOR_TYPE_INT 2
#define BP_DESCRIPTOR_TYPE_UINT 3
#define BP_DESCRIPTOR_TYPE_BYTE 4
#define BP_DESCRIPTOR_TYPE_EX_N 8
#define BP_DESCRIPTOR_TYPE_EX_N_BITS 9

// Exports.

// BpFieldDescriptor is a descriptor of bitproto generated single typed field.
struct BpFieldDescriptor {
    // Pointer of the single typed field.
    void *field;
    // Number of bits this filed occupy.
    int nbits;
    // Type of this field descriptor.
    int type;
};

// BpEncode runs encoding processor on given descriptor list and encodes bytes
// into given buffer s.
int BpEncode(struct BpFieldDescriptor **descriptors, int descriptors_len,
             unsigned char *s);

// BpDecode runs decoding processor on given descriptor list and decodes bytes
// from given buffer s.
int BpDecode(struct BpFieldDescriptor **descriptors, int descriptors_len,
             unsigned char *s);

// Implementation.

// BpMin returns the smaller one of given two numbers.
int BpMin(int a, int b) {
    if (a > b) {
        return b;
    }
    return a;
}

// BpGetMask returns the mask value to copy number of `c` bits at bit index `k`
// inside a single byte.
// TODO: comments
int BpGetMask(int k, int c) {
    if (k == 0) {
        return (1 << c) - 1;
    }
    return ((1 << (k + 1 + c)) - 1) - ((1 << (k + 1)) - 1);
}

// BpSmartShift shift `k` bits on given integer `n`.
// Shift right if given `k` is larger than 0, otherwise shift left.
// Returns the original `n` without any shifts if given `k` is 0.
int BpSmartShift(int n, int k) {
    if (k > 0) {
        return n >> k;
    }
    if (k < 0) {
        return n << k;
    }
    return n;
}

int BpGetNumberOfBitsToCopy(int i, int j, int n) {
    return BpMin(BpMin(n - j, 8 - (j % 8)), 8 - (i % 8));
}

void BpEncodeSingleByte(void *field, int field_index, unsigned char *s,
                        int s_index, int i, int j, int c) {
    int shift = (j % 8) - (i % 8);
    int mask = BpGetMask(i % 8, c);
    unsigned char value = ((unsigned char *)(field))[field_index];
    int d = BpSmartShift(value, shift) & mask;

    if (j % 8 == 0) {
        s[s_index] = d;
    } else {
        s[s_index] |= d;
    }
}

void BpDecodeSingleByte(void *field, int field_index, unsigned char *s,
                        int s_index, int i, int j, int c) {
    int shift = (i % 8) - (j % 8);
    int mask = BpGetMask(j % 8, c);
    unsigned char value = s[s_index];
    int d = BpSmartShift(value, shift) & mask;

    if (j % 8 == 0) {
        ((unsigned char *)(field))[field_index] = d;
    } else {
        ((unsigned char *)(field))[field_index] |= d;
    }
}

int BpEndecode(struct BpFieldDescriptor **descriptors, int descriptors_len,
               unsigned char *s, int is_encode) {
    // `i` tracks the current total bits encoded in the full endecoding context.
    int i = 0;
    // `k` tracks the index of descriptor in the list `descriptors`.
    int k = 0;

    for (k = 0; k < descriptors_len; k++) {
        struct BpFieldDescriptor *descriptor = descriptors[i];
        // j tracks the current bits encoded in the current field.
        int j = 0;
        // `n` is the number of bits this field occupy.
        int n = descriptor->nbits;

        while (j < n) {
            // `c` is the number of bits to copy.
            int c = BpGetNumberOfBitsToCopy(i, j, n);

            // Target index in the buffer `s`.
            int s_index = i / 8;
            // Target index in the field memory buffer.
            int field_index = j / 8;

            if (is_encode) {
                BpEncodeSingleByte(descriptor->field, field_index, s, s_index,
                                   i, j, c);
            } else {
                BpDecodeSingleByte(descriptor->field, field_index, s, s_index,
                                   i, j, c);
            }
            j += c;
            i += c;
        }
    }
    return 0;
}

int BpEncode(struct BpFieldDescriptor **descriptors, int descriptors_len,
             unsigned char *s) {
    return BpEndecode(descriptors, descriptors_len, s, 1);
}

int BpDecode(struct BpFieldDescriptor **descriptors, int descriptors_len,
             unsigned char *s) {
    return BpEndecode(descriptors, descriptors_len, s, 0);
}

#if defined(__cplusplus)
}
#endif

#endif
