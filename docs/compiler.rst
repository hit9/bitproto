.. _the-compiler:

Compiler
=========

The bitproto compiler generates language-specific code, which provides
the encode and decode api functions.

.. _install-compiler:

Installing the compiler
-----------------------

The bitproto compiler is written in Python, and requires `Python3.7+ <https://www.python.org/downloads/>`_ to work,
it's best to be installed via `pip <http://pip-installer.org/>`_:

.. sourcecode:: bash

    $ pip install bitproto

This will install a command named ``bitproto`` to your system, you can check it's version after the installation:

.. sourcecode:: bash

   $ bitproto -v
   bitproto 0.4.0

If you're new to Python, or wish to skip a Python installation,
you can download the compiler from `this download link <https://github.com/hit9/bitproto/releases>`_
directly, there provides the prebuilt one-file executables for Mac OS, Windows and Linux,
which works without having to install a Python3.7+.

Command line usage
------------------

Generates code for given language:

.. sourcecode:: bash

   $ bitproto c proto.bitproto
   $ bitproto go proto.bitproto
   $ bitproto py proto.bitproto

It generates language-specific codes to current directory by default,
to specify a output directory:

.. sourcecode:: bash

   $ bitproto c proto.bitproto outs/

Validates bitproto source file syntax, exits with a non-zero code if any syntax wrongs:

.. sourcecode:: bash

   $ bitproto -c proto.bitproto

The compiler won't generate files but only run a protocol syntax checking if `-c` option is given.

.. _compiler-linter:

By default, the compiler runs a simple protocol linter, which gives warnings if the given
bitproto file doesn't meet the :ref:`style-guide`, to disable the linter:

.. sourcecode:: bash

   $ bitproto c proto.bitproto -q
