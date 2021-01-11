// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto
// Encoding library for bitproto in C language.

#ifndef __BITPROTO_LIB_H__
#define __BITPROTO_LIB_H__ 1

#include <inttypes.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if defined(__cplusplus)
extern "C" {
#endif

#define BP_TYPE_BOOL 1
#define BP_TYPE_INT 2
#define BP_TYPE_UINT 3
#define BP_TYPE_BYTE 4
#define BP_TYPE_ENUM 5
#define BP_TYPE_ALIAS 6
#define BP_TYPE_ARRAY 7
#define BP_TYPE_MESSAGE 8

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

// BpProcessor function first constructs its own descriptor, and then continues
// the encoding and decoding processing with given context.
// BpProcessor functions will be generated by bitproto compiler.
typedef void (*BpProcessor)(void *data, struct BpProcessorContext *ctx);

// BpType is an abstraction for all bitproto types.
struct BpType {
    // Flag of this type.
    int flag;
    // Number of bits this type occupy in encoding.
    size_t nbits;
    // Number of bytes this type occupy in memory.
    size_t size;

    // Processor function for this type.
    // Sets if this type is message, enum, alias or array, otherwise NULL.
    BpProcessor processor;
};

// BpAliasDescriptor describes an alias definition.
struct BpAliasDescriptor {
    // The type alias to.
    struct BpType to;
};

// BpEnumDescriptor describes an enum definition.
struct BpEnumDescriptor {
    // Whether this enum is extensible.
    bool extensible;
    // The corresponding uint type.
    struct BpType uint;
};

// BpArrayDescriptor describes an array type.
struct BpArrayDescriptor {
    // Whether this array is extensible.
    bool extensible;
    // Capacity of this array.
    size_t cap;
    // The array element's type.
    struct BpType element_type;
};

// BpMessageFieldDescriptor describes a message field.
struct BpMessageFieldDescriptor {
    // The address of this field's data.
    void *data;
    // Type of this field.
    struct BpType type;
};

// BpMessageDescriptor describes a message.
struct BpMessageDescriptor {
    // Whether this message is extensible.
    bool extensible;
    // Number of fields this message contains.
    int nfields;
    // List of descriptors of the message fields.
    struct BpMessageFieldDescriptor *field_descriptors;
};

////////////////
// Declarations
////////////////

// Context Constructor.
struct BpProcessorContext BpContext(bool is_encode, unsigned char *s);

// BpType Constructors.

struct BpType BpBool();
struct BpType BpInt(size_t nbits);
struct BpType BpUint(size_t nbits);
struct BpType BpByte();
struct BpType BpMessage(size_t nbits, size_t size, BpProcessor processor);
struct BpType BpEnum(size_t nbits, size_t size, BpProcessor processor);
struct BpType BpArray(size_t nbits, size_t size, BpProcessor processor);
struct BpType BpAlias(size_t nbits, size_t size, BpProcessor processor);

// Descriptor Constructors.

struct BpMessageDescriptor BpMessageDescriptor(
    bool extensible, int nfields,
    struct BpMessageFieldDescriptor *field_descriptors);
struct BpEnumDescriptor BpEnumDescriptor(bool extensible, struct BpType uint);
struct BpArrayDescriptor BpArrayDescriptor(bool extensible, size_t cap,
                                           struct BpType element_type);
struct BpAliasDescriptor BpAliasDescriptor(struct BpType to);

// Encoding & Decoding

void BpEncodeSingleByte(struct BpProcessorContext *ctx, void *data, int j,
                        int c);
void BpDecodeSingleByte(struct BpProcessorContext *ctx, void *data, int j,
                        int c);
void BpEndecodeSingleByte(struct BpProcessorContext *ctx, void *data, int j,
                          int c);
void BpEndecodeBaseType(struct BpType type, struct BpProcessorContext *ctx,
                        void *data);
void BpEndecodeMessageField(struct BpMessageFieldDescriptor *descriptor,
                            struct BpProcessorContext *ctx, void *data);
void BpEndecodeMessage(struct BpMessageDescriptor *descriptor,
                       struct BpProcessorContext *ctx, void *data);
void BpEndecodeAlias(struct BpAliasDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data);
void BpEndecodeEnum(struct BpEnumDescriptor *descriptor,
                    struct BpProcessorContext *ctx, void *data);
void BpEndecodeArray(struct BpArrayDescriptor *descriptor,
                     struct BpProcessorContext *ctx, void *data);

// Utils

size_t BpIntSizeFromNbits(size_t nbits);
size_t BpUintSizeFromNbits(size_t nbits);
int BpMin(int a, int b);
int BpSmartShift(int n, int k);
int BpGetMask(int k, int c);
int BpGetNbitsToCopy(int i, int j, int n);

#if defined(__cplusplus)
}
#endif

#endif
