.. _language-guide:

Language Guide
===============

This document will introduce how to use bitproto language to describe data structures.

Semicolon
^^^^^^^^^

Semicolons are optional in bitproto:

.. sourcecode:: bitproto

   message Pen {
       Color color = 1;  // OK with a semicolon.
       Timestamp produced_at  // OK without a semicolon.
   }


Proto name
^^^^^^^^^^^

A bitproto file must declare its name:

.. sourcecode:: bitproto

   proto pen

Basic Types
^^^^^^^^^^^

An overview of bitproto basic types:

``bool``
  | Boolean type. A bool value occupies a single bit.

``uint{n}``
  | Unsigned bit-level integer type, where ``n`` ranges from ``1`` to ``64``.
    For examples: ``uint3``, ``uint13``, ``uint41``, ``uint64`` are all supported.
    An unsigned integer ``uint{n}`` occupies extactly ``n`` bits after encoding.
    In code generation, ``uint{n}`` is mapped to the smallest type in target language
    that can cover its size, for examples for C, ``uint3`` maps to ``uint8_t``, ``uint13``
    maps to ``uint16_t`` and so on.

``int{8,16,32,64}``
  | Signed integers. It's different from unsigned
    integers that only four signed integer types are supported:
    ``int8``, ``int16``, ``int32``, ``int64``. Signed integers with non-integer number
    of bytes are not supported.
    For examples, ``int16`` is valid, but ``int3`` is not.
    A signed integer ``int{n}`` occupies ``n`` bits after encoded.,

``byte``
  | Byte type. A byte value occupies 8 bits.
    The ``byte`` maps to ``unsigned char`` in C, ``byte`` in Go, and ``int`` in Python.

.. note:: Further talks

   Maybe interesting, are ``uint1`` and ``bool`` the same? Don't be confused that,
   bitproto still maps ``uint1`` to ``uint8_t`` rather than ``bool``, just like
   ``uint8`` is not ``byte``, the former is about numbers, the latter is all about
   yes or not.

.. _language-guide-enum:

Enum
^^^^^

Declaring an enum:

.. sourcecode:: bitproto

   enum Color : uint3 {
       COLOR_UNKNOWN = 0
       COLOR_RED = 1
       COLOR_BLUE = 2
       COLOR_GREEN = 3
   }

An enum is bound to an unsigned integer type ``uint{n}``, and occupies ``n`` bits.

It's highly recommended to define the first value of an enum to ``0``, which usually
represents for the unknown value.

Use the enum as a field's type in message:

.. sourcecode:: bitproto

   message Pen {
       Color color = 1
   }


Enum value in hex format is also supported:


.. sourcecode:: bitproto

   enum Color : uint3 {
       COLOR_UNKNOWN = 0x00
       COLOR_RED = 0x01
   }

.. _language-guide-message:

Message
^^^^^^^

Declaring a message:

.. sourcecode:: bitproto

   message Pen {
       bool is_new = 1
       uint3 lucy_number = 2
       Color color = 3
   }

A message is made up of multiple message fields. The syntax is very similar to protobuf.

A message field consists of a type and name on the left, a field number on the right.
It's supported to use any bitproto types as a message field's type. The field number should
be unique in a message scope.

Bitproto encodes the message to bytes following the order of field numbers.
Field numbers shouldn't be changed once they are in use.
What's more, we should pick a larger field number when adding a field to a message in use:

.. sourcecode:: bitproto

   message Pen {
       Color color = 3

       // Added a field
       uint3 new_field = 4
   }

The number of bits occupied by a message is the sum of the number of bits occupied by
all its fields. For instance, the ``Pen`` in the example above occupies ``6`` bits after encoded.

A message can of course be used as a field type:

.. sourcecode:: bitproto

   message Eye {
       bool is_open = 1
   }

   message Face {
       Eye left = 1
       Eye right = 2
   }

.. note::

   * In bitproto, message size is constrained up to ``65535`` bits (``8191`` bytes).
   * The message field number is constrained up to ``255``.

.. _language-guide-array:

Array
^^^^^

Examples:

.. sourcecode:: bitproto

  byte[10]  // Array of bytes, occupies 8*10bits.
  Color[2]  // Array of enums, occupies 8*3bits.
  uint3[3]  // Array of uint3, occupies 8*3bits.
  bool[3] // Array of bool, occupies 3bits.
  Pen[3] // Array of messages, occupies 3*7bits.

An array is made up of an element type and a capacity number.

In bitproto, it's required specify the capacity to a constant number of array.
The varying capacity array is not supported in bitproto.

The number of bits occupied by an array is the sum of the number of bits occupied by
all its elements. For instance, ``byte[10]`` occupies ``8 * 10`` bits.

Example to use an array in message:

.. sourcecode:: bitproto

   message Pen {
       byte[8] remark = 1
   }

.. _language-guide-alias:

.. note::

   In bitproto, array's capacity is constrained up to ``65535``.

Type Alias
^^^^^^^^^^

Similar to ``typedef`` in C, we can name a type in bitproto:

.. sourcecode:: bitproto

   type Bytes = byte[16]
   type Timestamp = int64
   type Colors = Color[7]

Example to use a type alias in message:

.. sourcecode:: bitproto

   type Timestamp = int64

   message Pen {
       Timestamp created_at = 1
   }

The number of bits occupied by a type alias is the same as the number of bits occupied by the type it names.

Note that there's a constraint in bitproto that types already with a
name (messages, enums) cannot be referenced in type alias, for instance,
the following bitproto is invalid:

.. sourcecode:: bitproto

   message Empty {}
   type Void = Empty  // invalid

.. _language-guide-constant:

Constant
^^^^^^^^

Declaring constants:

.. sourcecode:: bitproto

   const SOF = 0x01
   const LENGTH = 20
   const ENABLE = true // true, false, yes, no
   const NAME = "string"

Constants can be integers, booleans or strings.

Constant is designed for protocol related constants sharing,
such as the widely used sof (start of frame) byte etc, it's a part of
the protocol though it doesn't participate the serialization process.

Integer constants can be used as array's capacity:

.. sourcecode:: bitproto

   const LENGTH = 20

   message Pen {
       byte[LENGTH] name = 1
   }

.. _language-guide-nested-types:

Nested Types
^^^^^^^^^^^^

You can declare messages inside messages:

.. sourcecode:: bitproto

   message Outer {
       message Inner {
          bool ok = 1
       }

       Inner inner = 1
   }

Nested enums inside messages are also supported:

.. sourcecode:: bitproto

   message Outer {
       enum Color : uint3 {
           COLOR_UNKNOWN = 0
           COLOR_RED = 1
       }
       Color color = 1
   }

You can nest messages as deeply as you like:

.. sourcecode:: bitproto

    message Outer {
        message Middle {
            message Inner {
                bool ok = 1
            }
        }

        Middle.Inner inner = 2
    }

Nested types can also be referenced across message scopes:

.. sourcecode:: bitproto

   message Outer {
       enum Color : uint3 {
           COLOR_UNKNOWN = 0
           COLOR_RED = 1
       }
   }

   message Pen {
       Outer.Color color = 1;
   }

A bitproto message opens a scope, bitproto will lookup a type from local scopes first
and then the outer scopes. In the following example, the type of field ``color`` is
enum ``Color`` in local ``B``:

.. sourcecode:: bitproto

   message B {
       enum Color : uint3 {}
   }

   message A {
       message B {
           enum Color : uint3 {}
       }

       B.Color color = 1   // Local `B.Color` wins
   }

In bitproto, only messages and enums can be nested declared.

A nested type is mapped to a global type definition in code generation
with concatenated names, for instance, in the following example, bitproto
generates a global type ``struct ZooMonkey`` in C.

.. sourcecode:: bitproto

   message Zoo {
       message Monkey {}
   }

.. sourcecode:: C

   struct ZooMonkey {};
   struct Zoo {};

.. _language-guide-array-of-array:

Array of Array
^^^^^^^^^^^^^^

It's invalid to declare an array of array (aka the two-dimensional array) using
simple double square-bracket pairs, due to its lack of readability:

.. sourcecode:: bitproto

   byte[2][3] // Invalid

But, we can still use the :ref:`type alias <language-guide-alias>` syntax to implement
a two-dimensional array:

.. sourcecode:: bitproto

   type Row = byte[2]
   type Table = Row[3]

In the same way, we can declare three or more dimensional array type.

.. sourcecode:: bitproto

   type Row = bool[2]
   type Table = Row[3]
   type Cube = Table[4]


By this design, the readability is much better.

.. _language-guide-import:

Import
^^^^^^

We can import another bitproto via the import statement:

.. sourcecode:: bitproto

   import "path/to/shared.bitproto"

The path of the importing bitproto can be an absolute path or a path relative
to current bitproto:

.. sourcecode:: bitproto

   import "/home/user/shared.bitproto" // absolute
   import "shared.bitproto" // relative

The import statement binds the name of imported bitproto to local, we can refer
imported definitions via dot:

.. sourcecode:: bitproto

   import "shared.bitproto"

   message Pen {
       shared.Color color = 1
   }

However it is sometimes desirable to bind to a different name, to avoid name clashes:

.. sourcecode:: bitproto

   import lib "path/to/shared.bitproto"

The statement above import ``shared.bitproto`` as a name ``lib`` in current bitproto, the reference
now starts with ``lib.``:

.. sourcecode:: bitproto

   import lib "shared.bitproto"

   message Pen {
       lib.Color color = 1
   }

.. _language-guide-extensibility:

Extensibility
^^^^^^^^^^^^^

Bitproto knows exactly how many bits a message will occupy at compile time, because all types
are fix-sized. This may make backwards-compatibility hard.

It seems ok to add new fields to the end of a message in use, because the structures of
existing fields are unchanged, the decoding end won't scan the encoded bytes of new fields,
then "the backward-compatibility achieved":

.. sourcecode:: bitproto

   message Packet {
      bool old_field = 1
      // Add new field at end with a larger field number
      uint3 new_field = 2
   }

But this mechanism works only if there's no data after this message, that's to say, to make
this mechanism work, this message should be a top-level message, none of other messages can
refer it, for instance, it can only be a communication packet itself.

This mechanism fails with in-middle messages, for instance, we can't add new fields to the
following message ``Middle``, it affects the decoding of other old fields, like the
``following_field``:

.. sourcecode:: bitproto

   message Middle {
       bool old_field = 1
   }

   messages Packet {
       Middle middle = 1
       uint7 following_field = 2
   }

We have to break the traditional encoding layout of bitproto. The current mechanism of bitproto
is to put additional bytes at the head of messages during encoding. These bytes indicate the
size of the following message in encoding buffer. The decoder will skip redundant bits and
continue the remaining data decoding at right positions.

There are two kinds of messages in bitproto, extensible messages and traditional messages.
For an extensible message, bitproto adds ``2`` bytes at the head of encoded buffer.
For a traditional message, no additional bytes are added.

Bitproto introduces a symbol ``'`` to mark a message to be extensible:

.. sourcecode:: bitproto

   message ExtensibleMessage' {
       bool old_field = 1
   }

   message TraditionalMessage {
       bool ok = 1
   }

In the code above, ``ExtensibleMessage`` occupies ``1+16`` bits, and ``TraditionalMessage`` still
occupies ``1`` bit.

By marking a message to be extensible via a single quote, we increase buffer size by two bytes
in exchange for the possibility of adding new fields in the future. You should balance buffer size
and extensibility when declaring a message, mark the messages those will be extended in the future.

Back to the example of message ``Middle``, if this message in use is marked to be extensible in advance
(by both encoding and decoding ends), adding a new field by one end, doesn't affect the other ends:

.. sourcecode:: bitproto

   // Before
   message Middle' {
       bool old_field = 1
   }

   messages Packet {
       Middle middle = 1
       uint7 following_field = 2
   }

.. sourcecode:: bitproto

   // After
   message Middle' {
       bool old_field = 1
       // Add new field at end with a larger field number
       // This field will be skipped, by the end holding
       // an older version protocol.
       uint3 new_field = 2
   }

   messages Packet {
       Middle middle = 1
       uint7 following_field = 2
   }

But decoding will go wrong if you exchange data between two ends, of which one marks this message as extensible,
and the other marks it as traditional.

Extensible messages can also be nested declared, in the example below, message ``Outer`` occupies ``2+2`` bytes:

.. sourcecode:: bitproto

   message Outer' {
       message Inner' {}
       // Ha, empty extensible messages still cost bytes ~
   }

In addtion, arrays are also supported to be marked as extensible:

.. sourcecode:: bitproto

   message Packet {
       byte[4]' words = 1;
   }

The decoding end will skip redundant elements if the encoder end increases the array's capacity.
It is the same with extensible messages, an extensible array gains ``2`` bytes on its size.

.. note::

   For enums, extensibility is not supported, because enum values are atomic in targeting languages,
   the decoding end holding an older version protocol will get a wrong enum value if the encoder end
   increases the enum's number of bits, the unsigned integer types mapped in languages may cast large
   values to unexpected smaller values.

.. _language-guide-option:

Option
^^^^^^^

The bitproto language supports a few options.
We can define an option in global scope and message scopes, like this:

.. sourcecode:: bitproto

   option name = value

The value of an option can be an integer, string or boolean, according to the option itself.

For an example, there's an option named ``max_bytes`` to constraint message sizes, the
bitproto compiler will report an error and refuse to compile if the declared message's
size is larger than the configured value:

.. sourcecode:: bitproto

   message Pen {
       option max_bytes = 3
       byte[4] field = 1  // Violated max_bytes constraint
   }

Full table of options supported:

``c.struct_packing_alignment``
  | Proto level option, defaults to ``0``.
  | The struct alignment of generated C structs.
  | Setting to ``0`` means to left the attribute unset.

``c.name_prefix``
  | Proto level option, defaults to ``""``.
  | Name prefix of generated C types's names.

``go.package_path``
  | Proto level option, defaults to ``""``.
  | Importing path of current bitproto. Used when another bitproto import this bitproto,
    the path of the import statement in Go will be replaced by this value if set.

``py.module_name``
  | Proto level option, defaults to ``""``.
  | Importing path of current bitproto. Used when another bitproto import this bitproto,
    the name to import in Python will be replaced by this value if set.

``max_bytes``
  | Message level option, defaults to ``0``.
  | Setting the maximum limit of number of bytes for current message.
  | Setting to ``0`` means no size limitation.

.. _style-guide:

Style Guide
^^^^^^^^^^^

The bitproto compiler :ref:`contains a simple linter <compiler-linter>`,
which gives warnings if given bitproto violates style guidelines.

Indentation
""""""""""""

The parser ignores all whitespaces, but it's recommended to use 4 spaces
as indentation.

Naming Style
"""""""""""""

The bitproto naming guidelines are introduced in following code example:

.. sourcecode:: bitproto

   // Suggest a document for each proto.
   proto lower_snake_case

   type PascalCaseTypeAlias = byte[7]

   enum PascalCaseEnum : uint7 {
       // Always define a value 0 for enum.
       PASCAL_CASE_ENUM_UNKNOWN = 0

       UPPER_CASE_ENUM_FIELD = 1
   }

   message PascalCaseMessage {
       uint3 lower_snake_case_field = 2
   }

Editor Integration
^^^^^^^^^^^^^^^^^^

Vim
"""
A syntax plugin for `vim <https://www.vim.org/>`_ is available from
`bitproto's github repository <https://github.com/hit9/bitproto/tree/master/editors/vim>`_.
This plugin only supports syntax highlighting of bitproto language.
