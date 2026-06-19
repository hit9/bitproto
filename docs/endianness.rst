.. currentmodule:: bitproto

.. _endianness:

Endianness
==========

bitproto's wire format is **little-endian on every platform**: the lowest byte
index on the wire holds the least-significant bits of a field. This is a fixed
property of the encoding, independent of the machine that runs the encoder or
decoder — two peers with different byte orders always interoperate.

.. _endianness-languages:

Language support
----------------

Whether the *host* CPU is big-endian only ever mattered for C, because only C
reads an integer field's raw memory bytes. Python and Go operate on integer
*values* with shifts and masks, which is byte-order independent by construction.

.. list-table::
   :header-rows: 1
   :widths: 22 40 22

   * - Target
     - How bits are moved
     - Big-endian host
   * - Python
     - value math on Python ints
     - always correct
   * - Go
     - value shifts on typed fields
     - always correct
   * - C (standard mode)
     - ``lib/c`` runtime
     - correct
   * - C (optimization mode)
     - generated bit-copy statements
     - correct

So nothing special is required for Go or Python. The remainder of this page is
about C.

.. _endianness-c-standard-mode:

C standard mode
---------------

The C library (``lib/c/bitproto.c``) detects a big-endian host automatically
(via ``__BYTE_ORDER__`` for GCC/Clang, ``__BIG_ENDIAN__`` for the TI ARM CGT
compiler, and ``__LITTLE_ENDIAN__ == 0`` for IAR) and selects an endian-neutral
code path. You may also force it by defining ``BP_BIG_ENDIAN`` when compiling
the library, for toolchains that expose none of these macros:

.. sourcecode:: bash

   $ cc -DBP_BIG_ENDIAN -c bitproto.c

On a little-endian host the library is byte-for-byte unchanged, so there is no
performance impact on the common target.

.. _endianness-c-optimization-mode:

C optimization mode
-------------------

:ref:`Optimization mode <performance-optimization-mode>` generates plain bit-copy
statements that read and write integer fields through their in-memory bytes. To
stay correct on both little-endian and big-endian hosts, by default bitproto
emits two equivalent code paths guarded by a preprocessor macro:

.. sourcecode:: c

   #ifndef BP_BIG_ENDIAN
       // fast byte-pointer path (little-endian hosts)
   #else
       // portable bit-shift path (big-endian hosts)
   #endif

A big-endian host is auto-detected (via ``__BYTE_ORDER__`` for GCC/Clang,
``__BIG_ENDIAN__`` for the TI ARM CGT compiler, and ``__LITTLE_ENDIAN__ == 0``
for IAR); you may also force the big-endian path by defining ``BP_BIG_ENDIAN``
when compiling the generated code.
The little-endian path is identical to earlier bitproto releases, so there is no
performance change on little-endian targets — only the generated source is a
little larger.

.. _endianness-option:

The ``--endian`` option
-----------------------

If you know your target's byte order you can drop the unused path and shrink the
generated source with the ``--endian`` option (optimization mode only):

.. sourcecode:: bash

   # default: both paths, host auto-detected
   $ bitproto c example.bitproto -O

   # only the fast little-endian path (smaller output, no big-endian support)
   $ bitproto c example.bitproto -O --endian=little

   # only the portable big-endian path
   $ bitproto c example.bitproto -O --endian=big

``--endian`` only affects optimization-mode C/C++ code. It has no effect on the
wire format, and none on Go or Python.
