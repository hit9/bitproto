Bit-level data interchange format
==================================


Fixed-sized and bit-level typing data interchange format for serializing structured data.

![](_static/misc/images/mini-intro.png)

Focus on
--------

Short, size-limited or tight messages serialization.

Use bitproto over protobuf when
-------------------------------

* Working on microcontrollers.
* Wants bit-level message fields.
* Wants to know clearly how many bytes the encoded data will occupy.

But, if your are working with varying-sized messages, consider protobuf first.

Supported languages
-------------------

* C (ANSI C)
* Go
* Python

Installation
------------

### Install using pip (Recommended)

**Python**: bitproto requires
[Python3.4+](https://www.python.org/downloads/release/python-371/)
or [Python2.7+](https://www.python.org/downloads/release/python-2710/) to be installed.

**Pip**: If there's no `pip` installed on your computer, run `[sudo] easy_install pip` for pip installation.

Then, creates a `~/.pip/pip.conf`, and add following lines:

```
[global]
index-url = https://pypi.douban.com/simple
trusted-host = pypi.douban.com, pypi.yogorobot.io
extra-index-url=http://{user}:{password}@pypi.yogorobot.io:8080/simple
```

Ask @wangchao (@hit9) for the `{user}` and `{password}` settings in the configuration file above.

Then:

```
pip install -U bitproto
```

### Download binary directly

Download from latest version from this [download link](https://github.com/yogorobot/bitproto/releases).

Example
-------

* Please check [example.bitproto](example.bitproto) for a simple example.

* Please check [example-generates](example-generates) for example generated files in different languages.

Usage
-----

```bash
$ bitproto LANG FILE
```

For examples:

```
bitproto c example.bitproto          generate c file
bitproto go example.bitproto         generate go file
bitproto py example.bitproto         generate python file
bitproto -c example.bitproto         validate proto file
bitproto c example.bitproto target/  generate c file to directory target/
```

Syntax Guide
------------

Very similar to protobuf :).

### Proto's name

A bitproto file must declare a proto name:

```
proto my_proto_name
```

### Semicolon

Semicolon is optional rather than required since v0.1.0

### Supported types.

* **`bool`**: One bool occupies a bit.
* **`uint`**: Bit-level unsigned integer types are supported, from `uint1` to `uint64`.
* **`int`**: Supported signed integer types are `int8`, `int16`, `int32`, `int64`.
* **`byte`**
* **`enum`**
* **`message`**
* **`array`**: Array of bools, uints, ints, bytes, enums, messages are all supported.

### Enum

Declare an enum:

```bitproto
enum Color : uint3 { // Where the uint3 declares the type of enum values.
    COLOR_WHITE = 0  // An enum must contain a zero value.
    COLOR_RED = 1
    COLOR_BLACK = 2
    COLOR_BLUE = 3
    COLOR_CYAN = 4
    COLOR_GREEN = 5
}
```

Use the enum type:

```bitproto
message Pencil {
    // The Color is an enum type.
    Color color = 1
}
```

Hex format enum values are also supported:

```bitproto
enum Color : uint8 {
    COLOR_WHITE = 0x00
    COLOR_RED = 0x01
    COLOR_BLACK = 0x02
    COLOR_BLUE = 0x10
    COLOR_CYAN = 0x11
    COLOR_GREEN = 0x12
}
```

### Message

Delcare a message:

```bitproto
message Pencil {
    Color color = 1  // {type} {name} = {field-number}
    uint10 price = 2
}
```

The fields in a message will be serialized in the order of field-numbers.

### Array

```bitproto
byte[10] remark = 1  // Array of bytes with length 10.

Shape[2] shapes = 2  // Array of enums with length 2.

uint3[3] field = 3  // Array of uint3 with length 3, which occupies 3*3=9 bits.

bool[3] field = 4  // Array of bool with length 3, which occupies 3*1=3 bits.

Pencil[3] field = 5 // Array of messages with length 3, which occupies 3*bits_of(Pencil) bits.
```

Notes that the type "array of arrays" is unsupported:

```bitproto
message Person {
    byte[11][4] phone_numbers = 1;  // Illegal syntax.
}
```

But we can use `typedef` to implement the two-dimensional array, and the readability is much better:

```bitproto
type PhoneNumber = byte[11];

message Person {
    PhoneNumber[4] phone_numbers = 1;  // Syntax ok.
}
```

*Note: Currently, the max capacity to delcare an array is `1024`.*

### Type aliases

bitproto supports C/C++ style typedefs:

```bitproto
type MyCustomId = uint3
type Timestamp = uint64
type Phone = byte[11]

message Thing {
    MyCustomId id = 1
    Phone phone = 2
    Timestamp created_at = 3
}
```

But notes that only base types (`bool`, `uint`, `int`, `byte`, `alias` and array of them) can be aliased.

### Constant

Declare a constant:

```bitproto
const PHONE_NUMBER_LENGTH = 11
```

Or:

```bitproto
const WIDTH = 20;
const LENGTH = 30;
const SQUARE = WIDTH * LENGTH;  // It's 20*30=60
```

We can also use constants to define arrays:

```bitproto
const PHONE_NUMBER_LENGTH = 11
type PhoneNumber = byte[PHONE_NUMBER_LENGTH];
```

Or:

```bitproto
const PHONE_NUMBER_LENGTH = 11

message Person {
    byte[PHONE_NUMBER_LENGTH] phone_numebr = 1
}
```

Constants can be defined inside messages:

```bitproto
message Foo {
    const SOME_CONSTANT = 11
}

message Bar {
    byte[Foo.SOME_CONSTANT] some_bytes = 1
}
```

Supported constant types: `integer`, `string`, `boolean`:

```bitproto
const A_INTEGER_CONSTANT = 5
const A_BOOLEAN_CONSTANT = true // false,yes,no
const A_STRING_CONSTANT = "string"
```

Naming Style
------------

```bitproto
proto snake_case_proto_name;

const UPPER_CASE_CONSTANT_NAME = 1;

enum PascalCaseEnumName : uint3 {
    UPPER_CASE_ENUM_ITEM_NAME = 0;
}

message PascalCaseMessageName {
    uint10 snake_case_field_name = 1;
}
```

C Guide
-------

```c
struct Pencil pencil = {0};  // MUST initialized to {0}
pencil.color = COLOR_GREEN;
pencil.price = 12;

// Encode.
// BytesLengthPencil is a macro generated by bitproto, it's the length of bytes required
//to encode target struct.
unsigned char s[BytesLengthPencil];  // Better = {0}
EncodePencil(&pencil, s);

// Decode.
struct Pencil pencil2;  // Better = {0}
DecodePencil(&pencil2, s);
printf("%u\n", pencil2.color);
printf("%u\n", pencil2.price);

// Json.
char buf[1024];  // init a enough size buffer.
JsonPencil(&pencil2, buf);
printf("%s\n", buf);
```

Go Guide
--------

```go
p := &Pencil{}
p.Color = COLOR_GREEN
p.Shape = 2

// Encode
s := p.Encode()  // returns a slice of bytes.

// Decode
q := &Pencil{}
q.Decode(s)

fmt.Printf("q.color: %v\n", q.Color)
fmt.Printf("q.shape: %v\n", q.Shape)
```

Python Guide
------------

```python
import myproto as proto
p = proto.Pencil{}
p.color = proto.COLOR_GREEN
p.shape = 2

# Encode
s = p.encode()  # bytearray.

# Decode
q = proto.Pencil()
q.decode(s)

print(q.json())  # Json printout
```

Endianness
----------

* Currently, **ONLY little endian** is supported.

Editor Plugins
--------------

* [Vim](editors/vim)

   Clone this repo to `~/.vim/bundle`, and then:

   ```vim
   Plugin 'yogorobot/bitproto', {'rtp': 'vim/'}
   ```

* [Sublime-Text](editors/sublime-text)

   Open Sublime-Text and `Tools > Developer > New Syntax`, paste the file `sublime-text/bitproto.sublime-syntax`
   in the buffer. Use `File > Save` to save the file, the location will default to your `User` package.
   Notes the file's name to be saved should be `bitproto.sublime-syntax`.

   Or on mac, move this file directly to `~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User/`.

* [Notepad-Plus-Plus](editors/notepad-plus-plus)

  Open notepad++ and go to `Language -> Define your language...`, click on `Import...` and select the `notepad-plus-plus/bitproto.xml`
  in this repo. Close and restart notepad++.

* [VS Code](editors/vscode)

   * On Mac/Linux: move the folder (or `ln -s`) `vscode/bitproto` to `$HOME/.vscode/extensions`.
   * On Windows: move the folder `vscode/bitproto` to `%USERPROFILE%\.vscode\extensions`.
   * Close and restart VSCode.

Advanced Usage
--------------

### Nested Enum

```bitproto
message Pencil {
    enum Shape : uint2 {
        SHAPE_TRIANGULAR = 0
        SHAPE_ROUND = 1
        SHAPE_HEXAGONAL = 2
    }
    Shape shape = 1
}
```

### Nested Message

```bitproto
message Pencil {
    message Inner {
        enum Shape : uint2 {
            SHAPE_TRIANGULAR = 0
            SHAPE_ROUND = 1
            SHAPE_HEXAGONAL = 2
        }
        Shape shape = 1
    }
    Inner inner = 1
}
```

We can reference types across message scopes:

```bitproto
message Pencil {
    message Inner {
        enum Shape : uint2 {
            SHAPE_TRIANGULAR = 0
            SHAPE_ROUND = 1
            SHAPE_HEXAGONAL = 2
        }
        Shape shape = 1
    }
    Inner.Shape shape = 2
}
```

### Option

We can configure the bitproto compiler's behaviour via declaring options:

```bitproto
proto myproto;

// This sets the struct/macro name prefix for rendering c files. Defaults to "".
option c_name_prefix = "Proto"

// This disables the default underline in the nested type's name rendering.
option enable_nested_type_underline = no

// This disables the camel case conversion for "go"lang file generation.
option go_force_camel_case = no

message Foo {
    // This sets the max number of bytes this message can occupy.
    // Compiler will abort if someone wants to compile a message that breaks this
    // constraint.
    option max_bytes = 10

    byte[9] bar = 1
}
```

We can overide option values parsed from bitproto source files by passing custom
options from command line:

```
bitproto c example.bitproto -k c_name_prefix=ABC -k c_target_32bits=no
```

### Tags

There's a special option named `tags` for partial proto compilation.

```bitproto
const SomeConstant = 5 { option tags = "tag1" };

type SomeTypedef = uint13 { option tags = "tag2" };

enum Color : uint3 {
    // Declare this option in format of a string composed of tags separated by commas.
    option tags = "tag1,tag2"

    COLOR_WHITE = 0
    COLOR_RED = 1
    COLOR_BLACK = 2
}

message Pencil {
    option tags = "tag1"

    Color color = 1
}

message Eraser {
    option tags = "tag2"

    Color color = 1
}
```

Picks messages to compile:

```
# Picks only messages that are tagged with tag1.
bitproto --tags tag1 c myproto.bitproto out/
# Picks messages that are tagged with tag1 or tag2.
bitproto --tags tag1,tag2 c myproto.bitproto out/
```

The validation for referenced types (enums, aliases, messages) tags is very strict,
a referenced type must have a larger set of tags over the message that references it.

### Render Flags

We can pass some render flags (aka "build flags") via command line to generate them in files,
here's an example to generate git tags (versions) and git commit to generated c files:

```
bitproto c myproto.bitproto out/ -x git_tag=`git describe --tags` -x git_commit=`git rev-parse HEAD`
```

The generated file's header of this example is like to be:

```
// Code generated by bitproto. DO NOT EDIT.
// Source file: myproto.bitproto
// Render flags:
//   git_commit=b3a3cde82392ca770594829c2588ba0ec36c836e
//   git_tag=v0.1.4
```

*So far, bitproto dosen't support reference these flags in proto files, this feature may be planed in the future.*

### Templae

Template is introduced into bitproto since v0.2.5. This feature provides
a way to render custom methods during message generations, that makes it
possible to build better and stronger interfaces for bitproto's generated
messages.

```bitproto

// Declare a template for certain language generation.
template GetField for "go" {
    \func (m *{{ message.name }}) Get{{ field.name }}() {{ field.type }} {
    \   return m.{{ field.name }}
    \}
}

message Foo {
    byte bar = 1;

    // Render this template on field bar (that is, the field above would be
    // refereced to the field `bar`).
    render GetField on bar;
}
```

If we define a golang interface here, the generated message `Foo` will implement
it:

```go
type DuckWithBar {
    // bitproto's builtin geneated method.
    Encode() []byte
    // bitproto's builtin geneated method.
    Decode([]byte)
    // Method rendered from the template `GetField`.
    GetBar() byte
}
```

What's more, the `render` syntax can work without a specific field, that is the following
usage is also supported:

```bitproto

template GetBar for "go" {
    \func (m *{{ message.name }}) GetBar() byte {
    \   return m.Bar
    \}
}

message Foo {
    byte bar = 1;

    // Keyword `render` can be used without the keyword 'on'.
    // But notice that the template {field} variable won't be accessable
    // anymore in this mode. Which means you can't render a template with
    // a field variable in this way.
    render GetBar;
}
```

The template's syntax is in [Jinja2](http://jinja.pocoo.org/docs/2.10/). We can
even use directives like [{% include %}](http://jinja.pocoo.org/docs/2.10/templates/#include)
and [{% extend %}](http://jinja.pocoo.org/docs/2.10/templates/#extends) here:

```
template TemplateBase for "go" {
    \My Base Template
}

template TemplateFoo for "go" {
    \{% include "TemplateBase" %}
    \My Foo Template
}
```

The template feature is really cool for "go"lang developers :).

Encoded Bytes Layout
--------------------

![](_static/misc/images/encoding-layout.png)

License
-------

BSD.
