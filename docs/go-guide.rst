.. _quickstart-go-guide:

Go Guide
========

This document will introduce how to use bitproto with Go language.

Compile bitproto for Go
^^^^^^^^^^^^^^^^^^^^^^^

Firstly, creates a output directory named ``bp``:

.. sourcecode:: bash

    $ mkdir bp

Then run the bitproto compiler to generate code for Go:

.. sourcecode:: bash

   $ bitproto go pen.bitproto bp/

Where the `pen.bitproto` is introduced in earlier section :ref:`quickstart-example-bitproto`.

We will find that bitproto generates us a file named `pen_bp.go` in the output directory,
which contains the mapped structs, constants and api methods etc.

In the generated `pen_bp.go`:

* The ``enum Color`` in bitproto is mapped to a ``type`` definition on unsigned integer
  statement in Go, and the enum values are mapped to constants:

  .. sourcecode:: go

     type Color uint8 // 3bit
     const (
     	COLOR_UNKNOWN Color = 0
     	COLOR_RED = 1
     	COLOR_BLUE = 2
     	COLOR_GREEN = 3
     )

* The ``Timestamp`` in bitproto is mapped to a ``type`` definition on ``int64`` in Go:

  .. sourcecode:: go

     type Timestamp int64 // 64bit

* The ``message Pen`` in bitproto is mapped to a struct in Go:

  .. sourcecode:: go

     type Pen struct {
     	Color Color `json:"color"` // 3bit
     	ProducedAt Timestamp `json:"produced_at"` // 64bit
     }

* The compiler also generates two functions for the struct, they are the encoder and the decoder:

  .. sourcecode:: go

     func (m *Pen) Encode() []byte
     func (m *Pen) Decode(s []byte)

Install bitproto Go library
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bitproto serialization requires a language-specific library to work, the generated
encoder and decoder depends on the bitproto Go library underlying.

The source code of the bitproto Go library is hosted on `Github <https://github.com/hit9/bitproto/tree/master/lib/go>`_.
And can be installed via ``go get``:

.. sourcecode:: bash

   $ go get github.com/hit9/bitproto/lib/go

If you wish to install bitproto go library to local vendor directory via ``go mod``:

.. sourcecode:: bash

    $ cd bp && go mod init && go mod vendor


Run the code
^^^^^^^^^^^^

Now, we create a file named  `main.go` and put the following code in it:

.. sourcecode:: go

   package main

   import (
   	"fmt"

   	bp "path/to/bp"
   )

   func main() {
   	// Encode
   	p := &bp.Pen{bp.COLOR_RED, 1611515729966}
   	s := p.Encode()

   	// Decode
   	p1 := &bp.Pen{}
   	p1.Decode(s)

   	fmt.Printf("%v", p1)
   }

Notes to replace the import path of the generated `pen_bp.go` to yours.

In the code above, we firstly creates a ``p`` of type ``Pen`` with data initilization,
then call a method ``p.Encode()`` to encode ``p`` and return the encoded buffer ``s``, which
is a slice of bytes.

In the decoding part, we constructs another ``p1`` instance of type ``Pen`` with zero initilization,
then call a method ``p1.Decode()`` to decode bytes from buffer ``s`` into ``p1``.

The compiler also generates json tags on the generated struct's fields. And generates a method ``String()``
to return the json format of the structure.

Let's run it:

.. sourcecode:: bash

   $ go run main.go
   {"color":1,"produced_at":1611515729966}

The encoder and decoder functions copy bits between the structure's memory and buffer ``s`` byte-to-byte.
The bitproto go library doesn't use any reflection (think the ``encodig/json``), which may slow
the performance, neither use any type assertions or dynamic function generations.

There's another larger example source code on `the github <https://github.com/hit9/bitproto/tree/master/example>`_.
