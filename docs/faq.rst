.. _faq:

Frequently Asked Questions
==========================

This document answers some of the often asked questions about bitproto.

Does bitproto depend on endianness ?
''''''''''''''''''''''''''''''''''''

Yes, bitproto is not endianness independent, it currently supports only little-endian systems.
Endianness is always an issue for data serialization. But most of cpu processors, (including x86,
armv7, armv8 and most arm cortex-m mcus) are little-endian, or little-endian as default.
There's no plan for now to support big-endian systems or endianness independent serialization.

What's the advantage of this over a bit field ?
''''''''''''''''''''''''''''''''''''''''''''''''

`Bit fields <https://en.wikipedia.org/wiki/Bit_field>`_ are a standard language feature of C,
but almost everything about bit-field is implementation dependent, including the size of them
and memory layout. Apart from the endianness issue, the ordering of bitfields in memory is
not-portable even between different compilers on the same platform.

Besides, bitproto also targets on Python and Golang, there are no bit fields. If we use
bit fields to exchange data between programs in different languages, non-C language users
need to write the encoding mechanism manually.

Very interesting to figure out that, bitproto actually encodes the same buffer, when
use bit fields with structures setting no paddings in C. For instance, the buffer ``s``
in the C program below is the same with the encoded buffer of the bitproto message ``Data``
following:

.. sourcecode:: c

   struct Data {
       uint8_t a : 3;
       uint8_t b : 3;
       uint8_t c : 5;
       uint8_t d : 7;
   } __attribute__((packed, aligned(1))); // this line matters

   struct Data d = {1, 5, 28, 70};
   unsigned char *s = (unsigned char *)(&d);

.. sourcecode:: bitproto

    message Data {
       uint3 a = 1
       uint3 b = 2
       uint5 c = 3
       uint7 d = 4
    }

Even so, it's recommend to use bitproto over bitfields. It's compiler independent,
cross-multiple-languages and can support extensiblity.

Is it safe to use bit-level unsigned integers ?
''''''''''''''''''''''''''''''''''''''''''''''''

What if the value assigned overflows an unsigned integer type at runtime?
Say what if I assign ``9`` to an ``uint3`` ?

It's very safe for enums, the bitproto compiler checks overflows at compile-time.

.. sourcecode:: bitproto

   enum Color : uint3 {
       // The bitproto compiler will report error here.
       COLOR_OVERFLOW = 18
   }

But it's different for ``uint{n}`` used in a literal way, you have
to ensure the value fits the bit space by yourself, bitproto won't check
boundaries at runtime:

.. sourcecode:: bitproto

   message Data {
       uint3 value = 1
   }

.. sourcecode:: c

   struct Data d = {};
   // No error will be reported here.
   // Having to ensure it's safe by yourself.
   d.value = 18;
