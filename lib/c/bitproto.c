// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto
// Encoding library for bitproto in C language.

#include "bitproto.h"

///////////////////
// Implementations
///////////////////

// BpContext returns a BpProcessorContext.
struct BpProcessorContext BpProcessorContext(bool is_encode, unsigned char *s) {
    return (struct BpProcessorContext){is_encode, 0, s};
}
// BpJsonFormatContext returns a BpJsonFormatContext.
struct BpJsonFormatContext BpJsonFormatContext(char *s) {
    return (struct BpJsonFormatContext){0, s};
}

// BpEndecodeMessage process given message at data with provided message
// descriptor. It iterate all message fields to process.
void BpEndecodeMessage(struct BpMessageDescriptor *descriptor,
                       struct BpProcessorContext *ctx, void *data) {
    // Keep current number of bits total processed.
    int i = ctx->i;
    // Opponent message nbits if extensible is set.
    uint16_t ahead = 0;

    if (descriptor->extensible) {
        if (ctx->is_encode) {
            // Encode extensible ahead if extensible.
            BpEncodeMessageExtensibleAhead(descriptor, ctx);
        } else {
            // Decode extensible ahead if extensible.
            ahead = BpDecodeMessageExtensibleAhead(descriptor, ctx);
        }
    }

    // Process message fields.
    for (int k = 0; k < descriptor->nfields; k++) {
        struct BpMessageFieldDescriptor *field_descriptor =
            &(descriptor->field_descriptors[k]);
        BpEndecodeMessageField(field_descriptor, ctx, NULL);
    }

    // Skip redundant bits if decoding.
    if (descriptor->extensible && (!(ctx->is_encode))) {
        int ito = i + (int)ahead;
        if (ito >= ctx->i) {
            ctx->i = ito;
        }
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
            BpEndecodeBaseType((descriptor->type).nbits, ctx, descriptor->data);
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
            BpEndecodeBaseType((descriptor->to).nbits, ctx, data);
            break;
        case BP_TYPE_ARRAY:
            descriptor->to.processor(data, ctx);
            break;
    }
}

void BpEndecodeEnum(struct BpEnumDescriptor *descriptor,
                    struct BpProcessorContext *ctx, void *data) {
    // Process inner uint.
    BpEndecodeBaseType((descriptor->uint).nbits, ctx, data);
}

void BpEndecodeArray(struct BpArrayDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data) {
    // Keep current number of bits total processed.
    int i = ctx->i;
    // Opponent array capacity if extensible is set.
    uint16_t ahead = 0;

    if (descriptor->extensible) {
        if (ctx->is_encode) {
            // Encode extensible ahead if extensible.
            BpEncodeArrayExtensibleAhead(descriptor, ctx);
        } else {
            // Decode extensible ahead if extensible.
            ahead = BpDecodeArrayExtensibleAhead(descriptor, ctx);
        }
    }

    int element_nbits = descriptor->element_type.nbits;
    int element_size = descriptor->element_type.size;
    unsigned char *data_ptr = (unsigned char *)data;

    // Process array elements.
    for (int k = 0; k < descriptor->cap; k++) {
        // Lookup the address of this element's data.
        void *element_data = (void *)(data_ptr + k * element_size);

        switch (descriptor->element_type.flag) {
            case BP_TYPE_BOOL:
            case BP_TYPE_INT:
            case BP_TYPE_UINT:
            case BP_TYPE_BYTE:
                BpEndecodeBaseType(element_nbits, ctx, element_data);
                break;
            case BP_TYPE_ALIAS:
            case BP_TYPE_MESSAGE:
            case BP_TYPE_ENUM:
                descriptor->element_type.processor(element_data, ctx);
                break;
        }
    }

    // Skip redundant bits if decoding.
    if (descriptor->extensible && (!ctx->is_encode)) {
        int ito = i + (((int)ahead) * descriptor->cap);
        if (ito >= ctx->i) {
            ctx->i = ito;
        }
    }
}

// BpEndecodeBaseType process given base type at given data.
void BpEndecodeBaseType(int nbits, struct BpProcessorContext *ctx, void *data) {
    // j tracks the number bits processed on current base.
    int j = 0;
    int i = ctx->i;

    while (j < nbits) {
        // Remaing and multiple of i / 8 and j / 8.
        int ir = i % 8;
        int im = i / 8;
        int jr = j % 8;
        int jm = j / 8;
        // Number of bits to copy, smallest value of following numbers:
        //   The remaining bits to process to for current byte, 8 - (j % 8);
        //   The remaining bits to process from for current byte, 8 - (i % 8);
        //   The remaining bits to process for current base type, n - j;
        int c = BpMinTriple(8 - jr, 8 - ir, nbits - j);

        if (ctx->is_encode)
            BpEncodeSingleByte(ctx, data, ir, im, jr, jm, c);
        else
            BpDecodeSingleByte(ctx, data, ir, im, jr, jm, c);

        // Maintain j and i.
        j += c;
        i += c;
    }

    ctx->i = i;
}

// BpEncodeSingleByte encode number of c bits in a single byte of data to target
// buffer s in given context ctx.
void BpEncodeSingleByte(struct BpProcessorContext *ctx, void *data, int ir,
                        int im, int jr, int jm, int c) {
    // Number of bits to shift.
    int shift = jr - ir;
    // Mask value to intercept bits.
    int mask = BpGetMask(ir, c);
    // Get the value at this index as an unsigned char (byte).
    unsigned char value = ((unsigned char *)(data))[jm];

    // Delta to put on.
    int delta = BpSmartShift(value, shift) & mask;

    if (ir == 0) {  // Assign if writing at start of a byte.
        ctx->s[im] = delta;
    } else {  // Otherwise, run OR to copy bits.
        ctx->s[im] |= delta;
    }
}

// BpDecodeSingleByte decode number of c bits from buffer s in given context ctx
// to target data.
void BpDecodeSingleByte(struct BpProcessorContext *ctx, void *data, int ir,
                        int im, int jr, int jm, int c) {
    // Number of bits to shift.
    int shift = ir - jr;
    // Mask value to intercept bits.
    int mask = BpGetMask(jr, c);

    // Get the char at this index from buffer `s`.
    unsigned char value = ctx->s[im];

    // Index of current byte in the target base type data.
    unsigned char *data_buffer = (unsigned char *)(data);

    // Delta to put on.
    int delta = BpSmartShift(value, shift) & mask;

    if (jr == 0) {  // Assign if writing to starting of a byte.
        data_buffer[jm] = delta;
    } else {  // Otherwise, run OR to copy bits.
        data_buffer[jm] |= delta;
    }
}

// BpEncodeArrayExtensibleAhead encode the array capacity as the ahead flag to
// current bit encoding stream.
void BpEncodeArrayExtensibleAhead(struct BpArrayDescriptor *descriptor,
                                  struct BpProcessorContext *ctx) {
    // Safe to cast to uint16_t:
    // the capacity of an array always <= 65535.
    uint16_t data = (uint16_t)(descriptor->cap);
    BpEndecodeBaseType(16, ctx, (void *)&data);
}

// BpDecodeArrayExtensibleAhead decode the ahead flag as the array capacity from
// current bit decoding buffer.
uint16_t BpDecodeArrayExtensibleAhead(struct BpArrayDescriptor *descriptor,
                                      struct BpProcessorContext *ctx) {
    uint16_t data = 0;
    BpEndecodeBaseType(16, ctx, (void *)&data);
    return data;
}

// BpEncodeMessageExtensibleAhead encode the message number of bits as the ahead
// flag to current bit encoding stream.
void BpEncodeMessageExtensibleAhead(struct BpMessageDescriptor *descriptor,
                                    struct BpProcessorContext *ctx) {
    // Safe to cast to uint16_t:
    // The bitproto compiler constraints message size up to 65535 bits.
    uint16_t data = (uint16_t)(descriptor->nbits);
    BpEndecodeBaseType(16, ctx, (void *)&data);
}

// BpDecodeMessageExtensibleAhead decode the ahead flag as message's number of
// bits from current decoding buffer.
uint16_t BpDecodeMessageExtensibleAhead(struct BpMessageDescriptor *descriptor,
                                        struct BpProcessorContext *ctx) {
    uint16_t data = 0;
    BpEndecodeBaseType(16, ctx, (void *)&data);
    return data;
}

// BpMinTriple returns the smaller one of given three integers.
int BpMinTriple(int a, int b, int c) {
    return (a < b) ? ((a < c) ? a : c) : ((b < c) ? b : c);
}

// BpIntSizeFromNbits returns the size of corresponding integer type for given
// bits number.
int BpIntSizeFromNbits(int nbits) {
    if (nbits <= 8) {
        return (int)sizeof(int8_t);
    }
    if (nbits <= 16 && nbits > 8) {
        return (int)sizeof(int16_t);
    }
    if (nbits <= 32 && nbits > 16) {
        return (int)sizeof(int32_t);
    }
    if (nbits <= 64 && nbits > 32) {
        return (int)sizeof(int64_t);
    }
    return 0;
}

// BpUintSizeFromNbits returns the size of corresponding unsigned integer type
// for given bits number.
int BpUintSizeFromNbits(int nbits) {
    if (nbits <= 8) {
        return (int)sizeof(uint8_t);
    }
    if (nbits <= 16 && nbits > 8) {
        return (int)sizeof(uint16_t);
    }
    if (nbits <= 32 && nbits > 16) {
        return (int)sizeof(uint32_t);
    }
    if (nbits <= 64 && nbits > 32) {
        return (int)sizeof(uint64_t);
    }
    return 0;
}

// BpGetNbitsToCopy returns the number of bits to copy for current base type
// processing. Where argument i is the total bits processed in the whole
// processing contxt, argument j is the number of bits processed in current base
// type processing, argument n is the number of bits current base type occupy.
// The result is the smallest value of following numbers:
//   The remaining bits to process to for current byte, 8 - (j % 8);
//   The remaining bits to process from for current byte, 8 - (i % 8);
//   The remaining bits to process for current base type, n - j;
int BpGetNbitsToCopy(int i, int j, int n) {
    return BpMinTriple(8 - (j % 8), 8 - (i % 8), n - j);
}

// BpGetMask returns the mask value to copy bits inside a single byte.
// The argument k is the start bit index in the byte, argument c is the number
// of bits to copy.
//
// Examples of returned mask:
//
//   Returns                Arguments
//   00001111               k=0, c=4
//   01111100               k=2, c=5
//   00111100               k=2, c=4
int BpGetMask(int k, int c) { return (1 << (k + c)) - (1 << k); }

// BpSmartShift shifts given number n by k.
// If k is larger than 0, performs a right shift, otherwise left.
int BpSmartShift(int n, int k) {
    // Quote: If the value of the right operand is negative or is greater
    // than or equal to the width of the promoted left operand, the behavior is
    // undefined.
    return (k > 0) ? (n >> k) : ((k == 0) ? n : (n << (0 - k)));
}

// BpJsonFormatString is a simple wrapper on sprintf that accepts
// BpJsonFormatContext as an argment.
void BpJsonFormatString(struct BpJsonFormatContext *ctx, const char *format,
                        ...) {
    va_list va;
    va_start(va, format);
    ctx->n += vsprintf((char *)&(ctx->s[ctx->n]), format, va);
    va_end(va);
}

// BpJsonFormatMessage formats the message with given descriptor to json format
// string and writes the formatted string into buffer given by ctx.
void BpJsonFormatMessage(struct BpMessageDescriptor *descriptor,
                         struct BpJsonFormatContext *ctx, void *data) {
    // Formats left brace.
    BpJsonFormatString(ctx, "{");

    // Format key values.
    for (int k = 0; k < descriptor->nfields; k++) {
        struct BpMessageFieldDescriptor *field_descriptor =
            &(descriptor->field_descriptors[k]);

        BpJsonFormatMessageField(field_descriptor, ctx);

        if (k + 1 < descriptor->nfields) {
            BpJsonFormatString(ctx, ",");
        }
    }

    // Formats right brace.
    BpJsonFormatString(ctx, "}");
}

// BpJsonFormatMessageField formats a message field with given descriptor to
// json format into target buffer in given ctx.
void BpJsonFormatMessageField(struct BpMessageFieldDescriptor *descriptor,
                              struct BpJsonFormatContext *ctx) {
    // Format key.
    BpJsonFormatString(ctx, "\"%s\":", descriptor->name);

    // Format value.
    switch (descriptor->type.flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpJsonFormatBaseType(descriptor->type, ctx, descriptor->data);
            break;
        case BP_TYPE_ARRAY:
        case BP_TYPE_ENUM:
        case BP_TYPE_ALIAS:
        case BP_TYPE_MESSAGE:
            descriptor->type.json_formatter(descriptor->data, ctx);
            break;
    }
}

// BpJsonFormatBaseType formats a data in base type to json format.
void BpJsonFormatBaseType(struct BpType type, struct BpJsonFormatContext *ctx,
                          void *data) {
    switch (type.flag) {
        case BP_TYPE_BOOL:
            // Bool
            BpJsonFormatString(ctx, "%s",
                               (*((bool *)(data))) ? "true" : "false");
            break;
        case BP_TYPE_INT:
            // Int
            // FIXME 32bit differs with 64bit
            if (type.nbits <= 8) {
                BpJsonFormatString(ctx, "%d", (*((int8_t *)data)));
            } else if (type.nbits <= 16) {
                BpJsonFormatString(ctx, "%d", (*((int16_t *)data)));
            } else if (type.nbits <= 32) {
                BpJsonFormatString(ctx, "%d", (*((int32_t *)data)));
            } else {
                BpJsonFormatString(ctx, "%ld", (*((int64_t *)data)));
            }
            break;
        case BP_TYPE_UINT:
            // Uint
            // FIXME 32bit differs with 64bit
            if (type.nbits <= 8) {
                BpJsonFormatString(ctx, "%u", (*((uint8_t *)data)));
            } else if (type.nbits <= 16) {
                BpJsonFormatString(ctx, "%u", (*((uint16_t *)data)));
            } else if (type.nbits <= 32) {
                BpJsonFormatString(ctx, "%lu", (*((uint32_t *)data)));
            } else {
                BpJsonFormatString(ctx, "%llu", (*((uint64_t *)data)));
            }
            break;
        case BP_TYPE_BYTE:
            // Byte
            BpJsonFormatString(ctx, "%u", (*((unsigned char *)data)));
            break;
    }
}

// BpJsonFormatEnum formats an enum with given descriptor to json format.
void BpJsonFormatEnum(struct BpEnumDescriptor *descriptor,
                      struct BpJsonFormatContext *ctx, void *data) {
    BpJsonFormatBaseType(descriptor->uint, ctx, data);
}

// BpJsonFormatEnum formats an alias with given descriptor to json format.
void BpJsonFormatAlias(struct BpAliasDescriptor *descriptor,
                       struct BpJsonFormatContext *ctx, void *data) {
    switch (descriptor->to.flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpJsonFormatBaseType(descriptor->to, ctx, data);
            break;
        case BP_TYPE_ARRAY:
            descriptor->to.json_formatter(data, ctx);
            break;
    }
}

// BpJsonFormatEnum formats an array with given descriptor to json format.
void BpJsonFormatArray(struct BpArrayDescriptor *descriptor,
                       struct BpJsonFormatContext *ctx, void *data) {
    BpJsonFormatString(ctx, "[");

    // Format array elements.
    for (int k = 0; k < descriptor->cap; k++) {
        // Lookup the address of this element's data.
        void *element_data =
            (void *)((unsigned char *)data + k * descriptor->element_type.size);
        switch (descriptor->element_type.flag) {
            case BP_TYPE_BOOL:
            case BP_TYPE_INT:
            case BP_TYPE_UINT:
            case BP_TYPE_BYTE:
                BpJsonFormatBaseType(descriptor->element_type, ctx,
                                     element_data);
                break;
            case BP_TYPE_ALIAS:
            case BP_TYPE_MESSAGE:
            case BP_TYPE_ENUM:
                descriptor->element_type.json_formatter(element_data, ctx);
                break;
        }

        if (k + 1 < descriptor->cap) {
            BpJsonFormatString(ctx, ",");
        }
    }

    BpJsonFormatString(ctx, "]");
}
