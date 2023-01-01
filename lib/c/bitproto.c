// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto
// Encoding library for bitproto in C language.

#include "bitproto.h"

///////////////////
// Implementations
///////////////////

// BpMin returns the smaller one int.
static inline int BpMin(int a, int b) { return (a < b) ? a : b; }

// BpMinTriple returns the smaller one of given three integers.
static inline int BpMinTriple(int a, int b, int c) {
    return (a < b) ? ((a < c) ? a : c) : ((b < c) ? b : c);
}

// BpSmartShift shifts given unsigned char n by k.
// If k is larger than 0, performs a right shift, otherwise left.
static inline unsigned char BpSmartShift(unsigned char n, int k) {
    // Quote: If the value of the right operand is negative or is greater
    // than or equal to the width of the promoted left operand, the behavior
    // is undefined.
    return (k > 0) ? (n >> k) : ((k == 0) ? n : (n << (0 - k)));
}

// BpEndecodeMessage process given message at data with provided message
// descriptor. It iterates all message fields to process.
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
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
        case BP_TYPE_ENUM:
            BpEndecodeBaseType((descriptor->type).nbits, ctx, descriptor->data);
            break;
        case BP_TYPE_INT:
            BpEndecodeInt((descriptor->type).size, (descriptor->type).nbits,
                          ctx, descriptor->data);
            break;
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
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpEndecodeBaseType((descriptor->to).nbits, ctx, data);
            break;
        case BP_TYPE_INT:
            BpEndecodeInt((descriptor->to).size, (descriptor->to).nbits, ctx,
                          data);
            break;
        case BP_TYPE_ARRAY:
            descriptor->to.processor(data, ctx);
            break;
    }
}

// BpEndecodeArray process given array at data with provided descriptor. It
// iterates all array elements to process.
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

        switch (descriptor->element_type.flag) {
            case BP_TYPE_BOOL:
            case BP_TYPE_UINT:
            case BP_TYPE_BYTE:
            case BP_TYPE_ENUM:
                BpEndecodeBaseType(element_nbits, ctx, data_ptr);
                break;
            case BP_TYPE_INT:
                BpEndecodeInt(element_size, element_nbits, ctx, data_ptr);
                break;
            case BP_TYPE_ALIAS:
            case BP_TYPE_MESSAGE:
                descriptor->element_type.processor(data_ptr, ctx);
                break;
        }

        data_ptr += element_size;
    }

    // Skip redundant bits if decoding.
    if (descriptor->extensible && (!ctx->is_encode)) {
        int ito = i + (((int)ahead) * descriptor->cap);
        if (ito >= ctx->i) {
            ctx->i = ito;
        }
    }
}

// BpCopyBufferBits copy number of nbits from source buffer src to destination
// buffer dst.
// The argument n is the total number of bits to copy.
// The argument src_bit_idx is the index to start coping on buffer src.
// The argument dst_bit_idx is the index to start coping on buffer dst.
void BpCopyBufferBits(int n, unsigned char *dst, unsigned char *src,
                      int dst_bit_idx, int src_bit_idx) {
    // n is the number of bits remaining to process.
    while (n > 0) {
        // Byte index in destination buffer.
        // `>> 3` just is faster `/8`
        int dst_byte_idx = dst_bit_idx >> 3;
        // Byte index in source buffer.
        int src_byte_idx = src_bit_idx >> 3;

        // Remainder of destination bit index on 8.
        // `& 7` just is faster `%8`
        int dst_bit_im = dst_bit_idx & 7;
        // Remainder of source bit index on 8.
        int src_bit_im = src_bit_idx & 7;

        // Pointer to the destination to write this iteration.
        unsigned char *dst_ptr = dst + dst_byte_idx;
        // Pointer to the destination to read this iteration.
        unsigned char *src_ptr = src + src_byte_idx;

        // Number of bits to shift if goes into the optimized batch writing
        // branch.
        int shift = src_bit_im;
        // The capacity of bits for batch writing.
        int bits = n + shift;

        // Number of bits to copy this iteration.
        int c = 0;

        if (dst_bit_im == 0) {
            // When dst_bit_im == 0, we can directly ASSGIN values from shifted
            // src byte.
            if (bits >= 32) {
                // Copy as an uint32 integer.
                // This way, performance faster x2 than bits copy approach.
                ((uint32_t *)dst_ptr)[0] = (*(uint32_t *)(src_ptr)) >> shift;
                c = 32 - shift;
            } else if (bits >= 16) {
                // Copy as an uint16 integer.
                ((uint16_t *)dst_ptr)[0] = (*(uint16_t *)(src_ptr)) >> shift;
                c = 16 - shift;
            } else if (bits >= 8) {
                // Copy as an unsigned char.
                dst_ptr[0] = (src_ptr[0] >> shift) & 0xff;
                c = 8 - shift;
            } else {
                // When bits < 8 and dst_bit_im == 0
                // Copy partial bits inside a byte.
                // For the original statement:
                // c = BpMinTriple(8 - dst_bit_im, 8 - src_bit_im, n);
                // since dst_bit_im is 0 and bits <8, then 8-dst_bit_im is 8 and
                // n <8 , the 8-dst_bit_im won't be the smallest, we just pick
                // function BpMin over BpMinTriple for the little little
                // performance improvement.
                c = BpMin(8 - src_bit_im, n);
                // Also, when dst_bit_im is 0, special case of next case.
                dst_ptr[0] |= ((src_ptr[0] >> src_bit_im) & ~(0xff << c));
            }
        } else {
            // When dst_bit_im != 0, we have to copy partial bits inside a
            // single byte.
            // But, after some rounds of this case, dst_bit_im would goes to 0,
            // for large sized types.

            // Number of bits to copy.
            // 8-dst_bit_im ensures the destination space is enough.
            // 8-src_bit_im ensures the source space is enough.
            // nbits ensures the total bits remaining enough.
            c = BpMinTriple(8 - dst_bit_im, 8 - src_bit_im, n);

            // Explaination:
            // src >> si << di  Margins byte src with byte dst at position di.
            // this also clears the right bits up to position si.
            // ~(0xff << di << c) Gives a mask to clear higher not-need bits all
            // to 0, e.g. 00001111 on di=4, c=4;
            // Finally: dst |= src to copy bits.
            dst_ptr[0] |= ((src_ptr[0] >> src_bit_im << dst_bit_im) &
                           ~(0xff << dst_bit_im << c));
        }

        // Maintain in(de)crements.
        n -= c;
        dst_bit_idx += c;
        src_bit_idx += c;
    }
}

// BpEndecodeBaseType process given base type at given data.
void BpEndecodeBaseType(int nbits, struct BpProcessorContext *ctx, void *data) {
    if (ctx->is_encode) {
        BpCopyBufferBits(nbits, ctx->s, (unsigned char *)data, ctx->i, 0);
    } else {
        BpCopyBufferBits(nbits, (unsigned char *)data, ctx->s, 0, ctx->i);
    }
    ctx->i += nbits;
}

// BpEndecodeInt process signed integer at given data.
// The most left bit (Nth bit for int{N}) of a signed integer indicates the
// sign. For example 00000101 is a negative integer for a int3, but a positive
// integer for a int4.
void BpEndecodeInt(int size, int nbits, struct BpProcessorContext *ctx,
                   void *data) {
    // Copy bits without concern about sign bit.
    BpEndecodeBaseType(nbits, ctx, data);

    // Signed integer's sign bit processing is only about decoding.
    if (ctx->is_encode) return;

    // For int8/16/32/64 signed integers, the sign bit is already on the
    // most-left bit position. There's no additional actions should be done.
    if (nbits == 8 || nbits == 16 || nbits == 32 || nbits == 64) return;

    // Number of bits occupied in C intXX_t types.
    int n = 8 * size;

    switch (n) {
        // Suppose pointer data points to a int24 value V:
        // 1. Check its sign: (V >> (24-1)) & 1
        // 2. If V is negative:
        //    Make a mask that keeps right 24bits be 0, left 8bits be 1:
        //    mask = ~(1 << 24 - 1)
        //    Recover the original integer is: V | mask.
        //
        // Why not use V << 8 >> 8 solution here? This depends on arithmetic
        // shifting. Which propagates the sign bit on the left vacant bits when
        // doing a right shift. But C standard points that this behavior is
        // implementation-defined.
        case 8:  // int8_t
            if (((*(int8_t *)data) >> (nbits - 1)) & 1) {
                *(int8_t *)data |= ~((1 << nbits) - 1);
            }
            break;
        case 16:  // int16_t
            if (((*(int16_t *)data) >> (nbits - 1)) & 1) {
                *(int16_t *)data |= ~((1 << nbits) - 1);
            }
            break;
        case 32:  // int32_t
            if (((*(int32_t *)data) >> (nbits - 1)) & 1) {
                *(int32_t *)data |= ~((1 << nbits) - 1);
            }
            break;
        case 64:  // int64_t
            if (((*(int64_t *)data) >> (nbits - 1)) & 1) {
                *(int64_t *)data |= ~((1 << nbits) - 1);
            }
            break;
    }
}

// BpEncodeArrayExtensibleAhead encode the array capacity as the ahead flag
// to current bit encoding stream.
void BpEncodeArrayExtensibleAhead(struct BpArrayDescriptor *descriptor,
                                  struct BpProcessorContext *ctx) {
    // Safe to cast to uint16_t:
    // the capacity of an array always <= 65535.
    uint16_t data = (uint16_t)(descriptor->cap);
    BpEndecodeBaseType(16, ctx, (void *)&data);
}

// BpDecodeArrayExtensibleAhead decode the ahead flag as the array capacity
// from current bit decoding buffer.
uint16_t BpDecodeArrayExtensibleAhead(struct BpArrayDescriptor *descriptor,
                                      struct BpProcessorContext *ctx) {
    uint16_t data = 0;
    BpEndecodeBaseType(16, ctx, (void *)&data);
    return data;
}

// BpEncodeMessageExtensibleAhead encode the message number of bits as the
// ahead flag to current bit encoding stream.
void BpEncodeMessageExtensibleAhead(struct BpMessageDescriptor *descriptor,
                                    struct BpProcessorContext *ctx) {
    // Safe to cast to uint16_t:
    // The bitproto compiler constraints message size up to 65535 bits.
    uint16_t data = (uint16_t)(descriptor->nbits);
    BpEndecodeBaseType(16, ctx, (void *)&data);
}

// BpDecodeMessageExtensibleAhead decode the ahead flag as message's number
// of bits from current decoding buffer.
uint16_t BpDecodeMessageExtensibleAhead(struct BpMessageDescriptor *descriptor,
                                        struct BpProcessorContext *ctx) {
    uint16_t data = 0;
    BpEndecodeBaseType(16, ctx, (void *)&data);
    return data;
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

// BpJsonFormatMessage formats the message with given descriptor to json
// format string and writes the formatted string into buffer given by ctx.
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

    int flag = descriptor->type.flag;
    int nbits = descriptor->type.nbits;

    // Format value.
    switch (flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
        case BP_TYPE_ENUM:
            BpJsonFormatBaseType(flag, nbits, ctx, descriptor->data);
            break;
        case BP_TYPE_ARRAY:
        case BP_TYPE_ALIAS:
        case BP_TYPE_MESSAGE:
            descriptor->type.json_formatter(descriptor->data, ctx);
            break;
    }
}

// BpJsonFormatBaseType formats a data in base type to json format.
void BpJsonFormatBaseType(int flag, int nbits, struct BpJsonFormatContext *ctx,
                          void *data) {
    switch (flag) {
        case BP_TYPE_BOOL:
            // Bool
            BpJsonFormatString(ctx, "%s",
                               (*((bool *)(data))) ? "true" : "false");
            break;
        case BP_TYPE_INT:
            // Int
            // FIXME 32bit differs with 64bit
            if (nbits <= 8) {
                BpJsonFormatString(ctx, "%d", (*((int8_t *)data)));
            } else if (nbits <= 16) {
                BpJsonFormatString(ctx, "%d", (*((int16_t *)data)));
            } else if (nbits <= 32) {
                BpJsonFormatString(ctx, "%d", (*((int32_t *)data)));
            } else {
                BpJsonFormatString(ctx, "%ld", (*((int64_t *)data)));
            }
            break;
        case BP_TYPE_UINT:
        case BP_TYPE_ENUM:
            // Uint
            // FIXME 32bit differs with 64bit
            if (nbits <= 8) {
                BpJsonFormatString(ctx, "%u", (*((uint8_t *)data)));
            } else if (nbits <= 16) {
                BpJsonFormatString(ctx, "%u", (*((uint16_t *)data)));
            } else if (nbits <= 32) {
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

// BpJsonFormatAlias formats an alias with given descriptor to json format.
void BpJsonFormatAlias(struct BpAliasDescriptor *descriptor,
                       struct BpJsonFormatContext *ctx, void *data) {
    int flag = descriptor->to.flag;
    switch (flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpJsonFormatBaseType(flag, descriptor->to.nbits, ctx, data);
            break;
        case BP_TYPE_ARRAY:
            descriptor->to.json_formatter(data, ctx);
            break;
    }
}

// BpJsonFormatArray formats an array with given descriptor to json format.
void BpJsonFormatArray(struct BpArrayDescriptor *descriptor,
                       struct BpJsonFormatContext *ctx, void *data) {
    BpJsonFormatString(ctx, "[");

    int element_size = descriptor->element_type.size;
    int element_flag = descriptor->element_type.flag;
    int element_nbits = descriptor->element_type.nbits;
    unsigned char *data_ptr = (unsigned char *)data;

    // Format array elements.
    for (int k = 0; k < descriptor->cap; k++) {
        // Lookup the address of this element's data.
        void *element_data = (void *)(data_ptr + k * element_size);
        switch (element_flag) {
            case BP_TYPE_BOOL:
            case BP_TYPE_INT:
            case BP_TYPE_UINT:
            case BP_TYPE_BYTE:
            case BP_TYPE_ENUM:
                BpJsonFormatBaseType(element_flag, element_nbits, ctx,
                                     element_data);
                break;
            case BP_TYPE_ALIAS:
            case BP_TYPE_MESSAGE:
                descriptor->element_type.json_formatter(element_data, ctx);
                break;
        }

        if (k + 1 < descriptor->cap) {
            BpJsonFormatString(ctx, ",");
        }
    }

    BpJsonFormatString(ctx, "]");
}
