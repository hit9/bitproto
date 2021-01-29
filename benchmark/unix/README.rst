bitproto benchmark on Unix OS
=============================

This directory contains a simple benchmark for bitproto on Unix-like system (linux, macos etc).


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
