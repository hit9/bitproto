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

// BpTypeDescriptor describes a bitproto type.
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
    struct BpTypeDescriptor to;
};

// BpArrayDescriptor describes an array type.
struct BpArrayDescriptor {
    // The capacity of this array.
    int cap;
    // Number of bits this array occupy.
    int nbits;
    // Descriptor of the element type.
    struct BpTypeDescriptor element_type;
};

// BpEnumDescriptor describes an enum type.
struct BpEnumDescriptor {
    // Whether this enum is extensible.
    bool extensible;
    // Descriptor of the corresponding uint type.
    struct BpTypeDescriptor uint_type;
};

// BpMessageFieldDescriptor describes a message field.
struct BpMessageFieldDescriptor {
    // Pointer to the field member.
    void *field;
    // Descriptor of the field's type.
    struct BpTypeDescriptor type;
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
    struct BpMessageFieldDescriptor **field_descriptors;
};

// Exports
void BpEncodeMessage(struct BpMessageDescriptor *message_descriptor,
                     unsigned char *s);
void BpDecodeMessage(struct BpMessageDescriptor *message_descriptor,
                     unsigned char *s);

// Declarations.
void BpEndecodeMessage(struct BpMessageDescriptor *message_descriptor,
                       unsigned char *s, bool is_encode);
void BpEndecodeMessageField(struct BpMessageFieldDescriptor *field_descriptor,
                            unsigned char *s, bool is_encode);
void BpEndecodeBaseType(void *data, int flag, int nbits, unsigned char *s,
                        bool is_encode);
void BpEndecodeAlias(struct BpAliasDescriptor *alias_descriptor,
                     unsigned char *s, bool is_encode);
void BpEndecodeArray(struct BpArrayDescriptor *array_descriptor,
                     unsigned char *s, bool is_encode);
void BpEndecodeEnum(struct BpEnumDescriptor *enum_descriptor, void *data,
                    unsigned char *s, bool is_encode);
// Implementation

void BpEndecodeBaseType(void *data, int flag, int nbits, unsigned char *s,
                        bool is_encode) {
    // TODO
}

void BpEndecodeAlias(struct BpAliasDescriptor *alias_descriptor,
                     unsigned char *s, bool is_encode) {
    // TODO
}
void BpEndecodeArray(struct BpArrayDescriptor *array_descriptor,
                     unsigned char *s, bool is_encode) {
    // TODO
}

void BpEndecodeEnum(struct BpEnumDescriptor *enum_descriptor, void *data,
                    unsigned char *s, bool is_encode) {
    // TODO: extensible
    BpEndecodeBaseType(data, enum_descriptor->uint_type.flag,
                       enum_descriptor->uint_type.nbits, s, is_encode);
}

void BpEndecodeMessageField(struct BpMessageFieldDescriptor *field_descriptor,
                            unsigned char *s, bool is_encode) {
    // TODO: i parameter
    void *descriptor = field_descriptor->type.descriptor;

    switch ((field_descriptor->type).flag) {
        case BP_TYPE_BOOL:
        case BP_TYPE_INT:
        case BP_TYPE_UINT:
        case BP_TYPE_BYTE:
            BpEndecodeBaseType(field_descriptor->field,
                               field_descriptor->type.flag,
                               field_descriptor->type.nbits, s, is_encode);
            break;
        case BP_TYPE_MESSAGE:
            BpEndecodeMessage((struct BpMessageDescriptor *)(descriptor), s,
                              is_encode);
            break;
        case BP_TYPE_ARRAY:
            BpEndecodeArray((struct BpArrayDescriptor *)(descriptor), s,
                            is_encode);
            break;
        case BP_TYPE_ALIAS:
            BpEndecodeAlias((struct BpAliasDescriptor *)(descriptor), s,
                            is_encode);
            break;
        case BP_TYPE_ENUM:
            BpEndecodeEnum((struct BpEnumDescriptor *)(descriptor),
                           field_descriptor->field, s, is_encode);
            break;
    }
}

void BpEndecodeMessage(struct BpMessageDescriptor *message_descriptor,
                       unsigned char *s, bool is_encode) {
    for (int i = 0; i < message_descriptor->nfields; i++) {
        struct BpMessageFieldDescriptor *field_descriptor =
            message_descriptor->field_descriptors[i];
        BpEndecodeMessageField(field_descriptor, s, is_encode);
    }
}

void BpEncodeMessage(struct BpMessageDescriptor *message_descriptor,
                     unsigned char *s) {
    BpEndecodeMessage(message_descriptor, s, true);
}

void BpDecodeMessage(struct BpMessageDescriptor *message_descriptor,
                     unsigned char *s) {
    BpEndecodeMessage(message_descriptor, s, false);
}
#if defined(__cplusplus)
}
#endif

#endif
