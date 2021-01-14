// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto

// Package bitproto is the encoding library for bitproto in Go language.
//
// Implementation Note:
//	* No reflection.
//	* No type assertion.
//	* No dynamic function construction.
package bitproto

// ProcessorContext shares a context across sub-called processor functions
// during a encoding and decoding processing.
type ProcessorContext struct {
	// Indicates whether current processing is encoding or decoding.
	isEncode bool
	// Tracks the number of bits processed across the total processing.
	i int
	// Bytes buffer processing.
	// When encoding, s is the destination buffer to write.
	// When decoding, s is the source buffer to read.
	s []byte
}

// NewEncodeProcessorContext returns a new ProcessorContext for encoding.
func NewEncodeProcessorContext(s []byte) *ProcessorContext {
	return &ProcessorContext{true, 0, s}
}

// NewDecodeProcessorContext returns a new ProcessorContext for decoding.
func NewDecodeProcessorContext(s []byte) *ProcessorContext {
	return &ProcessorContext{false, 0, s}
}

// DataIndexer contains the arguments to index data from current accessor.
type DataIndexer struct {
	// Field number in current accessor.
	f int
	// Index in the array, if the field is an array.
	a int
}

// FieldNumber returns the field number of this data indexer.
func (di DataIndexer) FieldNumber() int { return di.f }

// ArrayElementIndex  returns the element index in array of this data indexer.
func (di DataIndexer) ArrayElementIndex() int { return di.a }

// NewDataIndexer returns a new data indexer.
func NewDataIndexer(f, a int) DataIndexer { return DataIndexer{f, a} }

// Nil data indexer.
var DataIndexerNil = NewDataIndexer(-1, -1)

// Accessor is the data container with two methods implemented: SetByte and
// GetByte. We don't use reflection (the "encoding/json" way), which slows the
// performance, bitproto compiler will generate SetByte and GetByte methods
// for all messages.
// Accessor only cares about base types and array of them, other type will
// finally falls to processors of base types.
type Accessor interface {
	// SetByte sets given byte b to target data, the data will be lookedup by
	// given indexer di from this accessor.
	// Argument lshift is the number of bits to shift left on given delta bits
	// before writing applied.
	//
	// Expecting compiler generates this function like following:
	//
	//	switch di.FieldNumber() {
	//	case 1:          // Not an array.
	//		m.Field |= ...
	//	case 2:          // Array of base type
	//		m.Field[di.ArrayElementIndex()] |= ...
	//	default: // Do nothing if not Bool/Uint/Int/Byte/Array (of base)
	//		panic
	//	}
	//
	// Each item like this:
	//
	//	m.Field |= type(b) << ishift    // When the field is a Byte/Uint/Int
	//	m.Field = byte2bool(b)          // When the field is a Bool
	//	m.Field = alias(byte2bool(b))   // When the field is a Alias of Bool.
	SetByte(di DataIndexer, lshift int, b byte)

	// GetByte returns the byte from target data, the data will be lookedup by
	// given indexer di from this accessor.
	// Argument rshift is the number of bits to shift right on the data before
	// the byte is returned.
	//
	// Expecting compiler generates this function like following:
	//
	//	switch di.FieldNumber() {
	//	case 1:          // Not an array.
	//		return ..
	//	case 2:          // Array of base type
	//		return ..
	//	default: // Do nothing if not Bool/Uint/Int/Byte/Array (of base)
	//		panic
	//	}
	//
	// Each item like this:
	//
	//	return byte(data >> rshift)  // When the field is a Byte/Uint/Int
	//	return bool2byte(data)       // When the field is a Bool
	//	return bool2byte(bool(data)) // When the field is a Alias of Bool.
	GetByte(di DataIndexer, rshift int) byte
}

// Flag of type.
type TypeFlag = int

const (
	TypeBool    TypeFlag = 1
	TypeInt              = 2
	TypeUint             = 3
	TypeByte             = 4
	TypeEnum             = 5
	TypeAlias            = 6
	TypeArray            = 7
	TypeMessage          = 8
)

// Type is the abstraction for a bitproto type.
type Type interface {
	// Flag returns the flag number of this type.
	Flag() TypeFlag
	// Nbits returns the number of bits this type occupy.
	Nbits() int
	// Process continues the encoding/decoding processing on this type.
	Process(ctx *ProcessorContext, di DataIndexer, accessor Accessor)
}

// Bool implements interface Type.
type Bool struct{}

func NewBool() *Bool           { return &Bool{} }
func (t *Bool) Flag() TypeFlag { return TypeBool }
func (t *Bool) Nbits() int     { return 1 }
func (t *Bool) Process(ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	endecodeBaseType(t, ctx, di, accessor)
}

// Int implements interface Type.
type Int struct{ nbits int }

func NewInt(nbits int) *Int   { return &Int{nbits} }
func (t *Int) Flag() TypeFlag { return TypeInt }
func (t *Int) Nbits() int     { return t.nbits }
func (t *Int) Process(ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	endecodeBaseType(t, ctx, di, accessor)
}

// Uint implements interface Type.
type Uint struct{ nbits int }

func NewUint(nbits int) *Uint  { return &Uint{nbits} }
func (t *Uint) Flag() TypeFlag { return TypeUint }
func (t *Uint) Nbits() int     { return t.nbits }
func (t *Uint) Process(ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	endecodeBaseType(t, ctx, di, accessor)
}

// Byte implements interface Type.
type Byte struct{}

func NewByte() *Byte           { return &Byte{} }
func (t *Byte) Flag() TypeFlag { return TypeByte }
func (t *Byte) Nbits() int     { return 1 }
func (t *Byte) Process(ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	endecodeBaseType(t, ctx, di, accessor)
}

// Array implements interface Type.
type Array struct {
	extensible bool
	c          int  // Capacity
	et         Type // Element type
}

func NewArray(extensible bool, capacity int, elementType Type) *Array {
	return &Array{extensible, capacity, elementType}
}
func (t *Array) Flag() TypeFlag { return TypeArray }
func (t *Array) Nbits() int     { return t.c * t.et.Nbits() }
func (t *Array) Process(ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	endecodeArray(t, ctx, di, accessor)
}

// Enum interface abstraction.
type Enum interface {
	// Enum is a type.
	// Expecting the bitproto compiler to generate following methods:
	//	(*t) Flag() TypeFlag { return 5 }
	//	(*t) Nbits() int
	//	(*t) Process() { EndecodeEnum(t, ctx, di, accessor) }
	Type

	// Returns the uint type backend.
	// Example of compiler generation:
	//	(*t) Uint() Uint* { return NewUint(3) }
	Uint() *Uint
}

// Alias interface abstraction.
type Alias interface {
	// Alias is a type.
	// Expecting the bitproto compiler to generate following methods:
	//	(*t) Flag() TypeFlag { return 6 }
	//	(*t) Nbits() int
	//	(*t) Process() { bp.EndecodeAlias(t, ctx, di, accessor) }
	Type

	// Returns the type it alias to.
	// Example of compiler generation:
	//	(*t) To() Type { return bp.NewInt(32) }
	To() Type
}

// Message interface abstraction.
type Message interface {
	// Message is a type.
	//
	// Expecting the bitproto compiler to generate following methods:
	//	(*t) Flag() TypeFlag { return 8 }
	//	(*t) Nbits() int
	//	(*t) Process() { bp.EndecodeMessage(t, ctx) }
	Type

	// Message is a data accessor.
	Accessor
	// Returns the list of its message fields.
	//
	// Expecting the compiler generation:
	//	(*t) MessageFields() []*bp.MessageField {
	//		return {
	//			bp.NewMessageField(0, NewInt(32)),
	//			bp.NewMessageField(1, &t.Color)  // Enum
	//			bp.NewMessageField(2, &t.SubMessage) // Message
	//			bp.NewMessageField(3, &t.AliasExample) // Alias
	//		}
	//	}
	MessageFields() []*MessageField

	// Encode this message to given buffer s.
	//
	// Expecting the compiler generation:
	//	(*t) Encode(s []byte) {
	//		ctx := NewProcessorContext(true, s)
	//		t.Process(ctx, bp.DataIndexerNil, t)
	//	}
	Encode(s []byte)

	// Decode from given buffer s to this message.
	//
	// Expecting the compiler generation:
	//	(*t) Decode(s []byte) {
	//		ctx := NewProcessorContext(false, s)
	//		t.Process(ctx, bp.DataIndexerNil, t)
	//	}
	Decode(s []byte)
}

// MessageField is the field of a message.
type MessageField struct {
	f int  // Field number
	t Type // Type
}

func NewMessageField(f int, t Type) *MessageField { return &MessageField{f, t} }

func endecodeArray(a *Array, ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	// TODO: extensible
	for k := 0; k < a.c; k++ {
		a.et.Process(ctx, NewDataIndexer(di.f, k), accessor)
	}
}
func EndecodeEnum(e Enum, ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	// TODO: extensible
	e.Uint().Process(ctx, di, accessor)
}

// EndecodeAlias process given alias on given processor context.
// Processing on alias is the same with its aliased type.
func EndecodeAlias(a Alias, ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	a.To().Process(ctx, di, accessor)
}

// EndecodeMessage process given message on given processor context.
// Note that m must be passed as an address referencing the message.
// For a message, argument `di` and `accessor` in function Process() will be
// dropped in inner call of function EndecodeMessage() (replaced indeed).
func EndecodeMessage(m Message, ctx *ProcessorContext) {
	// TODO: extensible
	for _, f := range m.MessageFields() {
		// for each field, its message is the accessor.
		f.t.Process(ctx, NewDataIndexer(f.f, 0), m)
	}
}

// endecodeBaseType process given base type t with given processor context.
func endecodeBaseType(t Type, ctx *ProcessorContext, di DataIndexer, accessor Accessor) {
	// Number of bits this type occupy.
	n := t.Nbits()
	// Tracks the number ofbits processed on current base type.
	j := 0

	for j < n {
		// Number of bits to copy.
		c := getNbitsToCopy(ctx.i, j, n)
		// Process single byte copy.
		endecodeSingleByte(ctx, di, accessor, j, c)
		// Maintain j and c.
		j += c
		ctx.i += c
	}
}

func endecodeSingleByte(ctx *ProcessorContext, di DataIndexer, accessor Accessor, j, c int) {
	if ctx.isEncode {
		encodeSingleByte(ctx, di, accessor, j, c)
	} else {
		decodeSingleByte(ctx, di, accessor, j, c)
	}
}

// TODO: Comment
func encodeSingleByte(ctx *ProcessorContext, di DataIndexer, accessor Accessor, j, c int) {
	i := ctx.i // Assign

	// Number of bits to shift.
	// The cast is safe: j%8 and i%8 always in [0,8).
	shift := (j % 8) - (i % 8)

	// Mask value to intercept bits.
	// The cast is safe: i%8 and c always in [0, 8].
	mask := byte(getMask(i%8, c))

	// Number of bits to shift right before the original data cast to byte.
	rshift := int(j/8) * 8

	// Index of byte in the target buffer.
	bufferIndex := int(i / 8)

	// Get ther byte from internal data.
	b := accessor.GetByte(di, rshift)

	// Delta to put on s[bufferIndex].
	delta := smartShift(b, shift) & byte(mask)

	// Using OR operator to put on delta.
	ctx.s[bufferIndex] |= delta
}

// TODO: comment
func decodeSingleByte(ctx *ProcessorContext, di DataIndexer, accessor Accessor, j, c int) {
	i := ctx.i // Assign

	// Number of bits to shift.
	// The cast is safe: j%8 and i%8 must in [0,8).
	shift := (i % 8) - (j % 8)

	// Mask value to intercept bits.
	// The cast is safe: j%8 and c must in [0, 8].
	mask := byte(getMask(j%8, c))

	// Number of bits to shift left in accessor before
	// the original data cast to byte.
	lshift := int(j/8) * 8

	// Index of byte in the target buffer.
	bufferIndex := int(i / 8)

	// Byte at index bufferIndex in s.
	b := ctx.s[bufferIndex]

	// Delta to put on internal data.
	delta := smartShift(b, shift) & byte(mask)

	// Get ther byte from internal data.
	accessor.SetByte(di, lshift, delta)
}

// getNbitsToCopy returns the number of bits to copy for current base type.
// Where i is the number of total bits in the whole processing context, j is
// the number of bits processed in current base type, n is the number of bits
// current base type occupy.
// The result is the smallest value of following numbers:
//   The remaining bits to process for current base type, n - j;
//   The remaining bits to process to for current byte, 8 - (j % 8);
//   The remaining bits to process from for current byte, 8 - (i % 8);
// The returned value always in [0, 8].
func getNbitsToCopy(i, j, n int) int {
	return min(min(n-j, 8-(j%8)), 8-(i%8))
}

// getMask returns the mask value to copy bits inside a single byte.
// TODO: comment
func getMask(k, c int) int {
	if k == 0 {
		return (1 << c) - 1
	}
	return (1 << ((k + 1 + c) - 1)) - (1 << ((k + 1) - 1))
}

// Returns the smaller one of given two integers.
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// BpSmartShift shifts given byte n by k bits.
// If k is larger than 0, performs a right shift, otherwise left.
func smartShift(n byte, k int) byte {
	if k > 0 {
		return n >> k
	}
	if k < 0 {
		return n << (0 - k)
	}
	return n
}
