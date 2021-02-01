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

The data in the following tables comes from `this github actions run <https://github.com/hit9/bitproto/actions/runs/526600150>`_.

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
     - 1.63μs
     - 1.55μs
   * - Ubuntu 20.04
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.78μs
     - 0.72μs
   * - Ubuntu 20.04
     - C
     - Standard
     - ``gcc -O2``
     - 1000000
     - 0.57μs
     - 0.59μs
   * - Ubuntu 20.04
     - Go
     - Standard
     - /
     - 1000000
     - 6.95μs
     - 7.08μs
   * - Ubuntu 20.04
     - Python
     - Standard
     - /
     - 10000
     - 386μs
     - 410μs
   * - Ubuntu 18.04
     - C
     - Standard
     - No ``-O``
     - 1000000
     - 1.96μs
     - 1.91μs
   * - Ubuntu 18.04
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.87μs
     - 0.82μs
   * - Ubuntu 18.04
     - C
     - Standard
     - ``gcc -O2``
     - 1000000
     - 0.66μs
     - 0.68μs
   * - Ubuntu 18.04
     - Go
     - Standard
     - /
     - 1000000
     - 8.53μs
     - 8.58μs
   * - Ubuntu 18.04
     - Python
     - Standard
     - /
     - 10000
     - 477μs
     - 496μs
   * - MacOS 10.15
     - C
     - Standard
     - No ``-O``
     - 1000000
     - 1.77μs
     - 1.76μs
   * - MacOS 10.15
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.79μs
     - 0.76μs
   * - MacOS 10.15
     - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.48μs
     - 0.15μs
   * - MacOS 10.15
     - Go
     - Standard
     - /
     - 1000000
     - 7.66μs
     - 7.70μs
   * - MacOS 10.15
     - Python
     - Standard
     - /
     - 10000
     - 553μs
     - 563μs

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
     - 0.16μs
     - 0.17μs
   * - Ubuntu 20.04
     - C
     - ``bitproto -O``
     - ``gcc -O2``
     - 1000000
     - 0.06μs
     - 0.06μs
   * - Ubuntu 20.04
     - Go
     - ``bitproto -O``
     - /
     - 1000000
     - 0.12μs
     - 0.08μs
   * - MacOS 10.15
     - C
     - ``bitproto -O``
     - No ``-O``
     - 1000000
     - 0.16μs
     - 0.15μs
   * - MacOS 10.15
     - C
     - ``bitproto -O``
     - ``gcc -O2``
     - 1000000
     - 0.06μs
     - 0.06μs
   * - MacOS 10.15
     - Go
     - ``bitproto -O``
     - /
     - 1000000
     - 0.14μs
     - 0.08μs

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
     - 1.46μs
     - 1.40μs
   * - C
     - Standard
     - ``gcc -O1``
     - 1000000
     - 0.66μs
     - 1.64μs
   * - C
     - Standard
     - ``gcc -O2``
     - 1000000
     - 0.44μs
     - 0.47μs
   * - Go
     - Standard
     - /
     - 1000000
     - 6.57μs
     - 6.71μs
   * - Python
     - Standard
     - /
     - 10000
     - 492μs
     - 495μs
   * - C
     - ``bitproto -O``
     - No ``-O``
     - 1000000
     - 0.16μs
     - 0.16μs
   * - C
     - ``bitproto -O``
     - ``gcc -O2``
     - 1000000
     - 0.07μs
     - 0.06μs
   * - Go
     - ``bitproto -O``
     - /
     - 1000000
     - 0.14μs
     - 0.07μs


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
