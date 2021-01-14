// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto
// Encoding library for bitproto in C language.

#include "bitproto.h"

///////////////////
// Implementations
///////////////////

// BpContext returns a BpProcessorContext.
struct BpProcessorContext BpContext(bool is_encode, unsigned char *s) {
    return (struct BpProcessorContext){is_encode, 0, s};
}

// BpBool returns a bool BpType.
struct BpType BpBool() {
    return (struct BpType){BP_TYPE_BOOL, 1, sizeof(bool), NULL};
}

// BpInt returns a int BpType for given nbits.
struct BpType BpInt(size_t nbits) {
    return (struct BpType){BP_TYPE_INT, nbits, BpIntSizeFromNbits(nbits), NULL};
}

// BpUint returns a uint BpType for given nbits.
struct BpType BpUint(size_t nbits) {
    return (struct BpType){BP_TYPE_UINT, nbits, BpUintSizeFromNbits(nbits),
                           NULL};
}

// BpByte returns a byte BpType for given nbits.
struct BpType BpByte() {
    return (struct BpType){BP_TYPE_BYTE, 8, sizeof(unsigned char), NULL};
}

// BpMessage returns a message BpType.
struct BpType BpMessage(size_t nbits, size_t size, BpProcessor processor) {
    return (struct BpType){BP_TYPE_MESSAGE, nbits, size, processor};
}

// BpEnum returns an enum BpType.
struct BpType BpEnum(size_t nbits, size_t size, BpProcessor processor) {
    return (struct BpType){BP_TYPE_ENUM, nbits, size, processor};
}

// BpArray returns an array BpType.
struct BpType BpArray(size_t nbits, size_t size, BpProcessor processor) {
    return (struct BpType){BP_TYPE_ARRAY, nbits, size, processor};
}

// BpAlias returns an alias BpType.
struct BpType BpAlias(size_t nbits, size_t size, BpProcessor processor) {
    return (struct BpType){BP_TYPE_ALIAS, nbits, size, processor};
}

// BpMessageFieldDescriptor returns a descriptor for a message.
struct BpMessageDescriptor BpMessageDescriptor(
    bool extensible, int nfields,
    struct BpMessageFieldDescriptor *field_descriptors) {
    return (struct BpMessageDescriptor){extensible, nfields, field_descriptors};
}

// BpEnumDescriptor returns a descriptor for an enum.
struct BpEnumDescriptor BpEnumDescriptor(bool extensible, struct BpType uint) {
    return (struct BpEnumDescriptor){extensible, uint};
}

// BpArrayDescriptor returns a descriptor for an array.
struct BpArrayDescriptor BpArrayDescriptor(bool extensible, size_t cap,
                                           struct BpType element_type) {
    return (struct BpArrayDescriptor){extensible, cap, element_type};
}

// BpAliasDescriptor returns a descriptor for an alias.
struct BpAliasDescriptor BpAliasDescriptor(struct BpType to) {
    return (struct BpAliasDescriptor){to};
}

// BpEndecodeMessage process given message at data with provided message
// descriptor. It iterate all message fields to process.
void BpEndecodeMessage(struct BpMessageDescriptor *descriptor,
                       struct BpProcessorContext *ctx, void *data) {
    // TODO: extensible.
    for (int k = 0; k < descriptor->nfields; k++) {
        struct BpMessageFieldDescriptor field_descriptor =
            descriptor->field_descriptors[k];
        BpEndecodeMessageField(&field_descriptor, ctx, NULL);
    }
}

// BpEndecodeMessageField dispatch the process by given message field's type.
void BpEndecodeMessageField(struct BpMessageFieldDescriptor *descriptor,
                            struct BpProcessorContext *ctx, void *data) {
    switch (descriptor->type.flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpEndecodeBaseType(descriptor->type, ctx, descriptor->data);
            break;
        case BP_TYPE_ENUM:
        case BP_TYPE_ALIAS:
        case BP_TYPE_ARRAY:
        case BP_TYPE_MESSAGE:
            descriptor->type.processor(descriptor->data, ctx);
            break;
    }
}

// BpEndecodeAlias process alias at given data and described by given
// descriptor. It simply propagates the process to the type it alias to.
// In bitproto, only types without names can be aliased
// (bool/int/uint/byte/array).
void BpEndecodeAlias(struct BpAliasDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data) {
    switch (descriptor->to.flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpEndecodeBaseType(descriptor->to, ctx, data);
            break;
        case BP_TYPE_ARRAY:
            descriptor->to.processor(data, ctx);
            break;
    }
}

void BpEndecodeEnum(struct BpEnumDescriptor *descriptor,
                    struct BpProcessorContext *ctx, void *data) {
    // TODO: extensible.
    BpEndecodeBaseType(descriptor->uint, ctx, data);
}

void BpEndecodeArray(struct BpArrayDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data) {
    // TODO: extensible.
    for (int k = 0; k < descriptor->cap; k++) {
        // Lookup the address of this element's data.
        void *element_data =
            (void *)((unsigned char *)data + k * descriptor->element_type.size);
        switch (descriptor->element_type.flag) {
            case BP_TYPE_BOOL:
            case BP_TYPE_INT:
            case BP_TYPE_UINT:
            case BP_TYPE_BYTE:
                BpEndecodeBaseType(descriptor->element_type, ctx, element_data);
                break;
            case BP_TYPE_ALIAS:
            case BP_TYPE_MESSAGE:
            case BP_TYPE_ENUM:
                descriptor->element_type.processor(element_data, ctx);
                break;
        }
    }
}

// BpEndecodeBaseType process given base type at given data.
void BpEndecodeBaseType(struct BpType type, struct BpProcessorContext *ctx,
                        void *data) {
    // Number of bits this type occupy.
    int n = (int)(type.nbits);
    // j tracks the number bits processed on current base.
    int j = 0;

    while (j < n) {
        // Number of bits to copy.
        int c = BpGetNbitsToCopy(ctx->i, j, n);
        // Process single byte copy.
        BpEndecodeSingleByte(ctx, data, j, c);
        // Maintain j and i.
        j += c;
        ctx->i += c;
    }
}

// TODO: Comment
void BpEndecodeSingleByte(struct BpProcessorContext *ctx, void *data, int j,
                          int c) {
    if (ctx->is_encode) {
        BpEncodeSingleByte(ctx, data, j, c);
    } else {
        BpDecodeSingleByte(ctx, data, j, c);
    }
}

// TODO: Comment
void BpEncodeSingleByte(struct BpProcessorContext *ctx, void *data, int j,
                        int c) {
    int i = ctx->i;

    // Number of bits to shift.
    int shift = (j % 8) - (i % 8);
    // Mask value to intercept bits.
    int mask = BpGetMask(i % 8, c);
    // Index of current byte in the target base type data.
    int value_index = (int)(j / 8);
    // Get the value at this index as an unsigned char (byte).
    unsigned char value = ((unsigned char *)(data))[value_index];

    // Index of byte in the target buffer.
    int buffer_index = (int)(i / 8);
    // Delta to put on.
    int delta = BpSmartShift(value, shift) & mask;

    if (i % 8 == 0) {  // Assign if writing at start of a byte.
        ctx->s[buffer_index] = delta;
    } else {  // Otherwise, run OR to copy bits.
        ctx->s[buffer_index] |= delta;
    }
}

// TODO: Comment
void BpDecodeSingleByte(struct BpProcessorContext *ctx, void *data, int j,
                        int c) {
    int i = ctx->i;

    // Number of bits to shift.
    int shift = (i % 8) - (j % 8);
    // Mask value to intercept bits.
    int mask = BpGetMask(j % 8, c);

    // Index of bytes in the source buffer.
    int buffer_index = (int)(i / 8);
    // Get the char at this index from buffer `s`.
    unsigned char value = ctx->s[buffer_index];

    // Index of current byte in the target base type data.
    int value_index = (int)(j / 8);
    unsigned char *data_buffer = (unsigned char *)(data);

    // Delta to put on.
    int delta = BpSmartShift(value, shift) & mask;

    if (j % 8 == 0) {  // Assign if writing to starting of a byte.
        data_buffer[value_index] = delta;
    } else {  // Otherwise, run OR to copy bits.
        data_buffer[value_index] |= delta;
    }
}

// BpMin returns the smaller one of given two integers.
int BpMin(int a, int b) {
    if (a < b) {
        return a;
    }
    return b;
}

// BpIntSizeFromNbits returns the size of corresponding integer type for given
// bits number.
size_t BpIntSizeFromNbits(size_t nbits) {
    if (nbits <= 8) {
        return sizeof(int8_t);
    }
    if (nbits <= 16 && nbits > 8) {
        return sizeof(int16_t);
    }
    if (nbits <= 32 && nbits > 16) {
        return sizeof(int32_t);
    }
    if (nbits <= 64 && nbits > 32) {
        return sizeof(int64_t);
    }
    return 0;
}

// BpUintSizeFromNbits returns the size of corresponding unsigned integer type
// for given bits number.
size_t BpUintSizeFromNbits(size_t nbits) {
    if (nbits <= 8) {
        return sizeof(uint8_t);
    }
    if (nbits <= 16 && nbits > 8) {
        return sizeof(uint16_t);
    }
    if (nbits <= 32 && nbits > 16) {
        return sizeof(uint32_t);
    }
    if (nbits <= 64 && nbits > 32) {
        return sizeof(uint64_t);
    }
    return 0;
}

// BpGetNbitsToCopy returns the number of bits to copy for current base type
// processing. Where argument i is the total bits processed in the whole
// processing contxt, argument j is the number of bits processed in current base
// type processing, argument n is the number of bits current base type occupy.
// The result is the smallest value of following numbers:
//   The remaining bits to process for current base type, n - j;
//   The remaining bits to process to for current byte, 8 - (j % 8);
//   The remaining bits to process from for current byte, 8 - (i % 8);
int BpGetNbitsToCopy(int i, int j, int n) {
    return BpMin(BpMin(n - j, 8 - (j % 8)), 8 - (i % 8));
}

// BpGetMask returns the mask value to copy bits inside a single byte.
// TODO: comments
int BpGetMask(int k, int c) {
    if (k == 0) {
        return (1 << c) - 1;
    }
    return (1 << ((k + 1 + c) - 1)) - (1 << ((k + 1) - 1));
}

// BpSmartShift shifts given number n by k.
// If k is larger than 0, performs a right shift, otherwise left.
int BpSmartShift(int n, int k) {
    if (k > 0) {
        return n >> k;
    }
    if (k < 0) {
        return n << (0 - k);
    }
    return n;
}
