.. _quickstart:

Quickstart
==========

Bitproto comes with a proto-to-code :ref:`compiler <the-compiler>` and language-specific libraries.

The compiler parses the bitproto file and generates code files in target languages,
which contains the structure definitions, encoding and decoding function entries.

The language-specific libraries provide the underlying serialization implementation. For different languages,
it's required to install the corresponding serialization library to make bitproto work.

This document will introduce how to start with using bitproto.

.. _quickstart-example-bitproto:

An example bitproto
-------------------

Suppose that we have a bitproto named ``pen.bitproto``, with the following content:

.. sourcecode:: bitproto

   proto pen

   enum Color : uint3 {
       COLOR_UNKNOWN = 0
       COLOR_RED = 1
       COLOR_BLUE = 2
       COLOR_GREEN = 3
   }

   type Timestamp = int64

   message Pen {
       Color color = 1
       Timestamp produced_at = 2
   }

In the bitproto file above:

* ``proto`` declares the name of this bitproto, this statement is required for every bitproto.
* ``Color`` is an enum on ``uint3``, it occupies 3 bits (meaning its value ranges up to 7).
* ``Timestamp`` is a custom type defined by user, aliasing to builtin type ``int64``,
  like what the keyword ``typedef`` does in C.
* ``Pen`` is a message that contains 2 fields. A message field consists of a type on the left, a
  following name and a unique field number on the right. Bitproto encodes a message by the order of
  the field number. So that the field numbers shouldn't be modified once they are in use.

In bitproto, we can determine how long the encoded buffer will be just from the proto defined,
for instance, the message ``Pen`` will occupy ``3 + 64`` bits, that's ``9`` bytes.

You may want to checkout
`a larger example on github <https://github.com/hit9/bitproto/tree/master/example>`_.

Next, we will introduce how to use bitproto with this simple bitproto file in different languages.

Language-Specific Guides
------------------------

.. toctree::
    :maxdepth: 2

    c-guide
    go-guide
    python-guide
