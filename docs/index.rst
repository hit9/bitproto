The bit level data interchange format
=====================================

Introduction
------------

Bitproto is a lightweight, easy-to-use and production-proven bit level data interchange data format
for serializing data structures.

The protocol describing syntax looks like the great
`protocol buffers <https://developers.google.com/protocol-buffers>`_ ,
but in bit level:

.. sourcecode:: bitproto

   message Data {
       uint3 the = 1
       uint3 bit = 2
       uint5 level = 3
       uint4 data = 4
       uint11 interchange = 6
       uint6 format = 7
   }  // 32 bits => 4B


The ``Data`` above is called a message, it consists of 7 fields and will occupy a total
of 4 bytes after encoding.

This image shows the layout of data fields in the encoded bytes buffer:

.. image:: _static/images/data-encoding-sample.png
    :align: center


You may want to checkout
`a larger example on github <https://github.com/hit9/bitproto/tree/master/example>`_.

Features
---------

- Supports bit level data encoding and decoding.
- Supports protocol extensiblity, for backward-compatibility (:ref:`extensibility`).
- Very easy to start:
   - Protocol syntax is similar to the well-known protobuf.
   - Generating code with very simple serialization api.
- Supports the following languages:
   - C (ANSI C) - No dynamic memory allocation. (:ref:`quickstart-c-guide`)
   - Golang - No reflection or type assertions. (:ref:`quickstart-go-guide`)
   - Python - No magic :) (:ref:`quickstart-python-guide`)

How to ?
--------

Code example to encode bitproto message in C:

.. sourcecode:: c

    struct Data data = {};
    unsigned char s[BYTES_LENGTH_DATA] = {0};
    EncodeData(&data, s);

And the decoding example:

.. sourcecode:: c

    struct Data data = {};
    DecodeData(&data, s);

Simple and green, isn't it?

Code patterns of bitproto encoding are exactly similar in C, Go and Python.
Please checkout :ref:`quickstart` for further guide.

Why bitproto ?
--------------

There is protobuf, why bitproto?

The bitproto was originally made when I'm working with embedded programs on
micro-controllers. Where usually exists many programming constraints:

- tight communication size.
- limited compiled code size.
- better no dynamic memory allocation.

And, protobuf dosen't live on embedded field, it dosen't target ANSI C.

It's recommended to use bitproto over protobuf when:

* Working on microcontrollers.
* Wants bit-level message fields.
* Wants to know clearly how many bytes the encoded data will occupy.

Content list
------------

.. toctree::
    :maxdepth: 2

    quickstart
    compiler
    language
    style
    extensibility
    changelog
    license

Language Guides
---------------

.. toctree::
    :maxdepth: 1

    c-guide
    go-guide
    python-guide
