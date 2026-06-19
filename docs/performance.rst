.. _performance:

Performance
===========

This document will introduce the performance of bitproto encoding and decoding,
along with the optimization mechanism.

.. _performance-benchmark:

Performance Benchmark
^^^^^^^^^^^^^^^^^^^^^

Benchmark of bitproto encoding/decoding shows that it runs very fast.

Unix OS
''''''''

On unix like systems (mac, ubuntu etc.), a single encoding/decoding call costs for a ``100`` bytes message:

* ``< 2μs`` in C
* ``< 10μs`` in Go
* ``< 1ms`` in Python

You can checkout `the detail benchmark results for unix on github <https://github.com/hit9/bitproto/tree/master/benchmark/unix>`_.

Embedded
'''''''''

I have tested the benchmark on a `stm32 board <https://www.st.com/content/st_com/en/products/microcontrollers-microprocessors/stm32-32-bit-arm-cortex-mcus/stm32-mainstream-mcus/stm32f1-series/stm32f103/stm32f103ze.html>`_
(arm cortex-m3 72MHz cpu) for a ``100`` bytes message, a single encoding/decoding call costs around ``120~140 μs``, and can be optimized to around ``15 μs``
in :ref:`the optimization mode <performance-optimization-mode>`.

You can checkout `the detail benchmark results for stm32 on github <https://github.com/hit9/bitproto/tree/master/benchmark/stm32>`_.

.. _performance-optimization-mode:

The Optimization Mode
^^^^^^^^^^^^^^^^^^^^^^

For most cases, the performance may meet the requirements. But if you are not satisfied with this,
there's still a way to go, the called "optimization mode" in bitproto, by adding an option ``-O`` to the
bitproto compiler:

.. sourcecode:: bash

   $ bitproto c example.bitproto -O

By this way, bitproto will generate code for you in optimization mode.

The mechanism behind optimization mode is to generate plain encoding/decoding code statements directly
at code-generation time. We known that all types are fixed-sized in bitproto, so the encoding and decoding
processing can be totally determined at code-generation time, bitproto just iterates all the fields of a message
and generate bits coping statements.

.. note::

   The optimization mode doesn't work for :ref:`extensible messages <language-guide-extensibility>`. Because
   extensible messages decoding requires dynamic calculation.

For an instance in C, the generated code in optimization mode looks like this:

.. sourcecode:: c

   int EncodeDrone(struct Drone *m, unsigned char *s) {
       s[0] |= (((unsigned char *)&((*m).position.latitude))[0] << 3) & 248;
       s[1] = (((unsigned char *)&((*m).position.latitude))[0] >> 5) & 7;
       ...
   }

   int DecodeDrone(struct Drone *m, unsigned char *s) {
       ((unsigned char *)&((*m).position.latitude))[0] = (s[0] >> 3) & 31;
       ((unsigned char *)&((*m).position.latitude))[0] |= (s[1] << 5) & 224;
       ...
   }

See the generated code example above, there's no loops, no if-else, all statements are plain bit operations.
In this way, bitproto's optimization mode gives us a maximum performance improvement on encoding/decoding.

.. note::

   The byte-pointer code shown above is the little-endian path. By default the
   compiler also emits an equivalent big-endian path behind ``#ifdef BP_BIG_ENDIAN``,
   see :ref:`performance-optimization-mode-endianness` below.

It's fine of course to use optimization mode on one end and non-optimization mode (the standard mode) on another end
in message communication. The optimization mode only changes the way how to execute the encoder and decoder,
without changing the format of the message encoding.

In fact, using the optimization mode is also a trade-off sometimes. In this mode, we have to drop the benefits of
:ref:`extensibility <language-guide-extensibility>` , it's not friendly to the compatibility design of the protocol.
Optimization mode is designed for performance-sensitive scenarios, such as low power consumption embedded boards,
compute-intensive microcontrollers. I recommend to use the optimization mode when:

* Performance-sensitive scenarios, where ``100μs`` means totally different with ``10μs``.
* The firmwares of communication ends are always upgraded together, thus the forward-compatibility is not so important.
* Firmware updates are not frequent, even only once for a long time.

Specially, for the scenario that firmware-upgrading of communication ends have to be processed partially,
such as the typical one-to-many `client-server artitecture <https://en.wikipedia.org/wiki/Client%E2%80%93server_model>`_,
I recommend to stick to the standard mode rather than the optimization mode.

The optimization mode is currently supported for language C and Go, (not yet Python).

Another benefit of optimization mode is that the bitproto libraries are no longer required to be dropped in.
The bitproto compiler in optimization mode already throws out the final encoding and decoding statements,
so the bitproto libraries aren't required. The libraries are designed to use with standard mode, where
protocol extensibility is a feature.

Smaller Code Size
''''''''''''''''''

Embedded firmware may be limited in program size. Bitproto provides another compiler option ``-F`` to filter
messages to generate in optimization mode:

.. sourcecode:: bash

   $ bitproto example.bitproto -O -F "Packet"

The command above tells bitproto only to generate encoder and decoder functions for message ``Packet``, other messages's
encoder and decoder functions will be skpped without generating.

The ``-F`` trick is useful because in most scenarios we just exchange a single "top-level" bitproto message
in communication. This option can also be used with multiple message names:

.. sourcecode:: bash

   $ bitproto example.bitproto -O -F "PacketA,PacketB"

Finally to note that, the ``-F`` option can be only used together with option ``-O``.

.. _performance-optimization-mode-endianness:

Host Byte Order (Endianness)
''''''''''''''''''''''''''''

bitproto's wire format is little-endian on every platform: the lowest byte index
holds the least-significant bits of a field. The encoding produced by Python, Go
and the C standard-mode library is the same regardless of the host's byte order.

The C optimization mode, however, generates plain bit-copy statements that read
and write integer fields through their in-memory bytes. To stay correct on both
little-endian and big-endian hosts, by default bitproto emits two equivalent code
paths guarded by a preprocessor macro:

.. sourcecode:: c

   #ifndef BP_BIG_ENDIAN
       // fast byte-pointer path (little-endian hosts)
   #else
       // portable bit-shift path (big-endian hosts)
   #endif

A big-endian host is auto-detected via ``__BYTE_ORDER__``; you may also force the
big-endian path by defining ``BP_BIG_ENDIAN`` when compiling the generated code.
The little-endian path is byte-for-byte identical to earlier releases, so there
is no performance change on little-endian targets — only the generated source is
a little larger.

If you know your target's byte order you can drop the unused path with the
``--endian`` option:

.. sourcecode:: bash

   # default: both paths, auto-detected
   $ bitproto c example.bitproto -O

   # only the fast little-endian path (smaller output, no big-endian support)
   $ bitproto c example.bitproto -O --endian=little

   # only the portable big-endian path
   $ bitproto c example.bitproto -O --endian=big

The ``--endian`` option only affects optimization-mode C/C++ code; it has no
effect on the wire format, nor on Go and Python which are endian-neutral already.
