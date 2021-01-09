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

// Type flags.
#define BP_TYPE_BOOL 1
#define BP_TYPE_BYTE 2
#define BP_TYPE_INT 3
#define BP_TYPE_UINT 4
#define BP_TYPE_ENUM 5
#define BP_TYPE_ARRAY 6
#define BP_TYPE_ALIAS 7
#define BP_TYPE_MESSAGE 8

struct BpTypeDescriptor {
    // Flag of this type.
    int flag;
    // Number of bits this type occupy.
    int nbits;
    // Descriptor of this type.
    // NULL if the type is a BaseType (Bool,Byte,Int,Uint).
    // Otherwise, a pointer to a descriptor struct, one of following:
    // BpAliasDescriptor, BpArrayDescriptor, BpEnumDescriptor,
    // BpMessageDescriptor
    void *descriptor;
};

// BpAliasDescriptor describes an alias type.
struct BpAliasDescriptor {
    // Descriptor of the type alias to.
    BpTypeDescriptor to;
};

// BpArrayDescriptor describes an array type.
struct BpArrayDescriptor {
    // The capacity of this array.
    int cap;
    // Number of bits this array occupy.
    int nbits;
    // Descriptor of the element type.
    BpTypeDescriptor element_type;
};

// BpEnumDescriptor describes an enum type.
struct BpEnumDescriptor {
    // Whether this enum is extensible.
    bool extensible;
    // Descriptor of the corresponding uint type.
    BpTypeDescriptor uint_type;
};

// BpMessageFieldDescriptor describes a message field.
struct BpMessageFieldDescriptor {
    // Pointer to the field member.
    void *field;
    // Descriptor of the field's type.
    BpTypeDescriptor type;
};

// BpMessageDescriptor describes a message struct.
struct BpMessageDescriptor {
    // Number of bits this message occupy.
    int nbits;
    // Whether this message is extensible.
    bool extensible;
    // Number of message field this message contains.
    int nfields;
    // Pointer to the array of message field descriptors.
    // The length of this array is the value of nfields.
    struct BpMessageFieldDescriptor *field_descriptors;
};

void BpEndecode(struct BpMessageDescriptor *message_descriptor,
                unsigned char *s, bool is_encode) {}

#if defined(__cplusplus)
}
#endif

#endif
