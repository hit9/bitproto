bitproto
========

Bitproto is a lightweight, easy-to-use and production-proven bit level data
interchange data format for serializing data structures.

Website: TODO

Features
---------

- Supports bit level data serialization.
- Supports protocol extensiblity, for backward-compatibility.
- Very easy to start:
   - Protocol syntax is similar to the well-known protobuf.
   - Generating code with very simple serialization api.
- Supports the following languages:
   - C - No dynamic memory allocation.
   - Go - No reflection or type assertions.
   - Python - No magic :)

Language Example
----------------

An example bitproto message:

.. sourcecode:: bitproto

   message Data {
       uint3 the = 1
       uint3 bit = 2
       uint5 level = 3
       uint4 data = 4
       uint11 interchange = 6
       uint6 format = 7
   }  // 32 bits => 4B

Layout of this message's data fields in the encoded bytes buffer:

.. image:: docs/_static/images/data-encoding-sample.png


The code example to encode and decode bitproto message in C:

.. sourcecode:: c

    struct Data data = {};
    unsigned char s[BYTES_LENGTH_DATA] = {0};
    EncodeData(&data, s);

.. sourcecode:: c

    struct Data data = {};
    DecodeData(&data, s);
