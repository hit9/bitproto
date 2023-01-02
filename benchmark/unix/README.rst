bitproto benchmark on Unix OS
=============================

This directory contains a simple benchmark for bitproto on Unix-like system (linux, macos etc).


Benchmark result
----------------

Github Actions
^^^^^^^^^^^^^^

The results of bitproto benchmark on unix like system can be found on `github actions <https://github.com/hit9/bitproto/actions?query=workflow%3A%22bitproto+benchmark%22>`_,
which are runned on `virtual machines <https://docs.github.com/en/actions/reference/specifications-for-github-hosted-runners#supported-runners-and-hardware-resources>`_
(with 2-core CPU).

The data in the following tables comes from `this github actions run <https://github.com/hit9/bitproto/actions/runs/3822976409>`_.

Standard Mode
''''''''''''''

The "standard mode" means to run bitproto compiler **without**
the optimization mode flag ``-O``, that is to use `the bitproto lib <../../lib>`_.


.. list-table::
   :header-rows: 1

   * - OS
     - Language
     - Mode
     - GCC Optimization Flag
     - Number of calls
     - Encode cost per call
     - Decode cost per call
   * - Ubuntu 20.04
     - C
     - Standard
     - No ``-O``
     - 1000000
     - 1.78μs
     - 1.182μs
   * - Ubuntu 20.04
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.64μs
     - 0.64μs
   * - Ubuntu 20.04
     - C
     - Standard
     - ``gcc -O2``
     - 1000000
     - 0.53μs
     - 0.55μs
   * - Ubuntu 20.04
     - Go
     - Standard
     - /
     - 1000000
     - 8.11μs
     - 7.94μs
   * - Ubuntu 20.04
     - Python
     - Standard
     - /
     - 10000
     - 369μs
     - 395μs
   * - MacOS 10.15
     - C
     - Standard
     - No ``-O``
     - 1000000
     - 2.07μs
     - 2.02μs
   * - MacOS 10.15
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.75μs
     - 0.80μs
   * - MacOS 10.15
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.63μs
     - 0.62μs
   * - MacOS 10.15
     - Go
     - Standard
     - /
     - 1000000
     - 9.60μs
     - 9.27μs
   * - MacOS 10.15
     - Python
     - Standard
     - /
     - 10000
     - 588μs
     - 655μs

Optimization Mode
''''''''''''''''''

The "optimization mode" means to run bitproto compiler **with**
the optimization mode flag ``-O``, that is not to use `the bitproto lib <../../lib>`_.

.. list-table::
   :header-rows: 1

   * - OS
     - Language
     - Mode
     - GCC Optimization Flag
     - Number of calls
     - Encode cost per call
     - Decode cost per call
   * - Ubuntu 20.04
     - C
     - ``bitproto -O``
     - No ``-O``
     - 1000000
     - 0.26μs
     - 0.30μs
   * - Ubuntu 20.04
     - C
     - ``bitproto -O``
     - ``gcc -O2``
     - 1000000
     - 0.07μs
     - 0.08μs
   * - Ubuntu 20.04
     - Go
     - ``bitproto -O``
     - /
     - 1000000
     - 0.21μs
     - 0.11μs
   * - MacOS 10.15
     - C
     - ``bitproto -O``
     - No ``-O``
     - 1000000
     - 0.33μs
     - 0.30μs
   * - MacOS 10.15
     - C
     - ``bitproto -O``
     - ``gcc -O2``
     - 1000000
     - 0.09μs
     - 0.11μs
   * - MacOS 10.15
     - Go
     - ``bitproto -O``
     - /
     - 1000000
     - 0.18μs
     - 0.12μs

Macbook
''''''''

The following table is the benchmark result on my macbook (Intel Core i5, 2 CPU Core, 2133 MHz).

.. list-table::
   :header-rows: 1
   * - Language
     - Mode
     - GCC Optimization Flag
     - Number of calls
     - Encode cost per call
     - Decode cost per call
   * - C
     - Standard
     - No ``-O``
     - 1000000
     - 1.47μs
     - 1.45μs
   * - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.62μs
     - 1.62μs
   * - C
     - Standard
     - ``gcc -O2``
     - 1000000
     - 0.49μs
     - 0.52μs
   * - Go
     - Standard
     - /
     - 1000000
     - 7.38μs
     - 7.41μs
   * - Python
     - Standard
     - /
     - 10000
     - 438μs
     - 492μs
   * - C
     - ``bitproto -O``
     - No ``-O``
     - 1000000
     - 0.33μs
     - 0.22μs
   * - C
     - ``bitproto -O``
     - ``gcc -O2``
     - 1000000
     - 0.10μs
     - 0.10μs
   * - Go
     - ``bitproto -O``
     - /
     - 1000000
     - 0.18μs
     - 0.14μs


How to reproduce
-----------------

* Run benchmark for C / Go / Python:

  .. sourcecode:: bash

     $ make bench

* Run benchmark for C with GCC -O1 option enabled:

  .. sourcecode:: bash

     $ make bench-c-o1

* Run benchmark for C with GCC -O2 option enabled:

  .. sourcecode:: bash

     $ make bench-c-o2

* Run benchmark for C / Go with bitproto -O option enabled:

  .. sourcecode:: bash

     $ make bench-optimization-mode
