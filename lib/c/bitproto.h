// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto
// Encoding library for bitproto in C language.
//
// Keep it simple:
// * No dynamic memory allocation (malloc).
// * All structs and functions named starting with 'Bp'.

#ifndef __BITPROTO_LIB_H__
#define __BITPROTO_LIB_H__ 1

#include <inttypes.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#ifndef __cplusplus
#include <stdbool.h>
#endif

#if defined(__cplusplus)
extern "C" {
#endif

#define __BITPROTO_VERSION__ "1.0.1"

////////////////////
// Macros
////////////////////

// BpType Flags.

#define BP_TYPE_BOOL 1
#define BP_TYPE_INT 2
#define BP_TYPE_UINT 3
#define BP_TYPE_BYTE 4
#define BP_TYPE_ENUM 5
#define BP_TYPE_ALIAS 6
#define BP_TYPE_ARRAY 7
#define BP_TYPE_MESSAGE 8

// Context Constructors.
#define BpProcessorContext(is_encode, s) \
    ((struct BpProcessorContext){(is_encode), 0, (s)})
#define BpJsonFormatContext(s) \
    (struct BpJsonFormatContext) { 0, (s) }

// BpType Constructors.
#define BpBool() ((struct BpType){BP_TYPE_BOOL, 1, sizeof(bool), NULL, NULL})
#define BpUint(nbits, size) \
    ((struct BpType){BP_TYPE_UINT, (nbits), (size), NULL, NULL})
#define BpInt(nbits, size) \
    ((struct BpType){BP_TYPE_INT, (nbits), (size), NULL, NULL})
#define BpByte() \
    ((struct BpType){BP_TYPE_BYTE, 8, sizeof(unsigned char), NULL, NULL})
#define BpMessage(nbits, size, processor, formatter)                \
    ((struct BpType){BP_TYPE_MESSAGE, (nbits), (size), (processor), \
                     (formatter)})
#define BpEnum(nbits, size) \
    ((struct BpType){BP_TYPE_ENUM, (nbits), (size), NULL, NULL})
#define BpArray(nbits, size, processor, formatter) \
    ((struct BpType){BP_TYPE_ARRAY, (nbits), (size), (processor), (formatter)})
#define BpAlias(nbits, size, processor, formatter) \
    ((struct BpType){BP_TYPE_ALIAS, (nbits), (size), (processor), (formatter)})

// Descriptors

#define BpMessageDescriptor(extensible, nfields, nbits, field_descriptors) \
    ((struct BpMessageDescriptor){(extensible), (nfields), (nbits),        \
                                  (field_descriptors)})
#define BpMessageFieldDescriptor(data, type, name) \
    ((struct BpMessageFieldDescriptor){(data), (type), (name)})
#define BpArrayDescriptor(extensible, cap, element_type) \
    ((struct BpArrayDescriptor){(extensible), (cap), (element_type)})
#define BpAliasDescriptor(to) ((struct BpAliasDescriptor){(to)})

////////////////////
// Data Abstractions
////////////////////

// BpProcessorContext is the general encoding and decoding context, as an
// argument of processor functions.
struct BpProcessorContext {
    // Indicates whether current processing is encoding or decoding.
    bool is_encode;
    // Tracks the total bits processed.
    // Maintained by function BpEndecodeBaseType.
    int i;
    // Bytes buffer processing. It's the destination buffer under encoding
    // context, and source buffer under decoding context.
    unsigned char *s;
};

// BpJsonFormatContext is the context to format bitproto messages.
struct BpJsonFormatContext {
    // Number of bytes formatted.
    int n;
    // Target buffer to format into.
    char *s;
};

// BpProcessor function first constructs its own descriptor, and then continues
// the encoding and decoding processing with given context.
// BpProcessor functions will be generated by bitproto compiler.
typedef void (*BpProcessor)(void *data, struct BpProcessorContext *ctx);

// BpJsonFormatter function formats given data with its descriptor into json.
typedef void (*BpJsonFormatter)(void *data, struct BpJsonFormatContext *ctx);

// BpType is an abstraction for all bitproto types.
struct BpType {
    // Flag of this type.
    int flag;
    // Number of bits this type occupy in encoding.
    int nbits;
    // Number of bytes this type occupy in memory.
    int size;

    // Processor function for this type.
    // Sets if this type is message, enum, alias or array, otherwise NULL.
    BpProcessor processor;

    // JsonFormatter function for this type.
    // Sets if this type is message, enum, alias or array, otherwise NULL.
    BpJsonFormatter json_formatter;
};

// BpAliasDescriptor describes an alias definition.
struct BpAliasDescriptor {
    // The type alias to.
    struct BpType to;
};

// BpArrayDescriptor describes an array type.
struct BpArrayDescriptor {
    // Whether this array is extensible.
    bool extensible;
    // Capacity of this array.
    int cap;
    // The array element's type.
    struct BpType element_type;
};

// BpMessageFieldDescriptor describes a message field.
struct BpMessageFieldDescriptor {
    // The address of this field's data.
    void *data;
    // Type of this field.
    struct BpType type;
    // Name of this field.
    // Required for json formatter.
    char *name;
};

// BpMessageDescriptor describes a message.
struct BpMessageDescriptor {
    // Whether this message is extensible.
    bool extensible;
    // Number of fields this message contains.
    int nfields;
    // Number of bits this message occupy.
    int nbits;
    // List of descriptors of the message fields.
    struct BpMessageFieldDescriptor *field_descriptors;
};

////////////////
// Declarations
////////////////

// Encoding & Decoding

unsigned char BpCopyBits(unsigned char dst, unsigned char src,
                         int dst_bit_index, int src_bit_index, int c);
void BpCopyBufferBits(int nbits, unsigned char *dst, unsigned char *src,
                      int dst_bit_index, int src_bit_index);
void BpEndecodeBaseType(int nbits, struct BpProcessorContext *ctx, void *data);
void BpEndecodeInt(int nbits, int size, struct BpProcessorContext *ctx,
                   void *data);
void BpEndecodeMessageField(struct BpMessageFieldDescriptor *descriptor,
                            struct BpProcessorContext *ctx, void *data);
void BpEndecodeMessage(struct BpMessageDescriptor *descriptor,
                       struct BpProcessorContext *ctx, void *data);
void BpEndecodeAlias(struct BpAliasDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data);
void BpEndecodeArray(struct BpArrayDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data);

// Extensible Processor.

void BpEncodeArrayExtensibleAhead(struct BpArrayDescriptor *descriptor,
                                  struct BpProcessorContext *ctx);
uint16_t BpDecodeArrayExtensibleAhead(struct BpArrayDescriptor *descriptor,
                                      struct BpProcessorContext *ctx);

void BpEncodeMessageExtensibleAhead(struct BpMessageDescriptor *descriptor,
                                    struct BpProcessorContext *ctx);
uint16_t BpDecodeMessageExtensibleAhead(struct BpMessageDescriptor *descriptor,
                                        struct BpProcessorContext *ctx);

// Json Formatting

void BpJsonFormatString(struct BpJsonFormatContext *ctx, const char *format,
                        ...);
void BpJsonFormatMessage(struct BpMessageDescriptor *descriptor,
                         struct BpJsonFormatContext *ctx, void *data);
void BpJsonFormatBaseType(int flag, int nbits, struct BpJsonFormatContext *ctx,
                          void *data);
void BpJsonFormatAlias(struct BpAliasDescriptor *descriptor,
                       struct BpJsonFormatContext *ctx, void *data);
void BpJsonFormatMessageField(struct BpMessageFieldDescriptor *descriptor,
                              struct BpJsonFormatContext *ctx);
void BpJsonFormatArray(struct BpArrayDescriptor *descriptor,
                       struct BpJsonFormatContext *ctx, void *data);

// Utils

int BpMinTriple(int a, int b, int c);
unsigned char BpSmartShift(unsigned char n, int k);

#if defined(__cplusplus)
}
#endif

#endif
