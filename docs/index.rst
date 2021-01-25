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

- Supports bit level data serialization.
- Supports protocol :ref:`extensiblity <extensibility>`, for backward-compatibility.
- Very easy to :ref:`start <quickstart>`:
   - Protocol syntax is similar to the well-known protobuf.
   - Generating code with very simple serialization api.
- Supports the following languages:
   - :ref:`C (ANSI C)<quickstart-c-guide>` - No dynamic memory allocation.
   - :ref:`Go <quickstart-go-guide>` - No reflection or type assertions.
   - :ref:`Python <quickstart-python-guide>` - No magic :)

Code Example
------------

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
Please checkout :ref:`the quickstart document <quickstart>` for further guide.

Why bitproto ?
--------------

There is protobuf, why bitproto?

Origin
''''''

The bitproto was originally made when I'm working with embedded programs on
micro-controllers. Where usually exists many programming constraints:

- tight communication size.
- limited compiled code size.
- better no dynamic memory allocation.

Protobuf does not live on embedded field natively,
it doesn't target ANSI C out of box.

Scenario
'''''''''

It's recommended to use bitproto over protobuf when:

* Working on or with microcontrollers.
* Wants bit-level message fields.
* Wants to know clearly how many bytes the encoded data will occupy.

For scenarios other than the above, I recommend to use protobuf over bitproto.

Vs Protobuf
'''''''''''

The differences between bitproto and protobuf are:

* bitproto supports bit level data serialization, like the `bit fields in C <https://en.wikipedia.org/wiki/Bit_field>`_.

* bitproto doesn't use any dynamic memory allocations. Few of
  `protobuf C implementations <https://github.com/protocolbuffers/protobuf/blob/master/docs/third_party.md>`_
  support this except `nanopb <https://jpa.kapsi.fi/nanopb>`_.

* bitproto doesn't support varying sized data, all type are fixed sized.

  bitproto won't encode typing or size reflection information into the buffer.
  It only encodes the data itself, the encoded data is arranged like it's arranged in the memory,
  with fixed size, without paddings, think setting `aligned attribute to 1 <https://stackoverflow.com/a/11772340>`_
  on structs in C.

* Protobuf works good on `backward compatibility <https://developers.google.com/protocol-buffers/docs/overview#backwards_compatibility>`_.
  For bitproto, this is the main shortcome of bitproto serialization until :ref:`v0.4.0 <version-0.4.0>`,
  since this version, it supports message's :ref:`extensiblity <extensibility>` by adding two bytes indicating the message size
  at head of the message's encoded buffer. This breaks the traditional data layout design by encoding some minimal reflection
  size information in, so this is designed as an optional feature.

Shortcomes
''''''''''

Known shortcomes of bitproto:

* bitproto doesn't support varying sized types. For example, a ``unit37`` always occupies 37 bits even you
  assign it a small value like ``1``.

  Which means there will be lots of zero bytes if the meaningful data occupies little on this type.
  For instance, there will be ``n-1`` bytes left zero if only one byte of a type with ``n`` bytes size is used.

  Generally, we actually don't care much about this, since there are not so many bytes in communication
  with embedded devices. The protocol itself is meant to be designed tight and compact. Consider to wrap
  a compression mechanism like `zlib <https://zlib.net/>`_ on the encoded buffer if you really care.


Content list
------------

.. toctree::
    :maxdepth: 2

    quickstart
    c-guide
    go-guide
    python-guide
    compiler
    language
    style
    extensibility
    changelog
    license
