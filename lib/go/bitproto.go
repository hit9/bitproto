// Copyright (c) 2021, hit9. https://github.com/hit9/bitproto

// Package bitproto is the encoding library for bitproto in Go language.
//
// Implementation Note:
//	* No reflection.
//	* No type assertion.
//	* No dynamic function construction.
package bitproto

// ProcessContext is the context accross all processor functions in a encoding
// or decoding process.
type ProcessContext struct {
	// Indicates whether current processing is encoding.
	isEncode bool
	// Tracks the number of total bits processed.
	i int
	// Bytes buffer processing.
	// When encoding, s is the destination buffer to write.
	// When decoding, s is the source buffer to read.
	s []byte
}

// NewEncodeContext returns a ProcessContext for encoding to given buffer s.
func NewEncodeContext(s []byte) *ProcessContext {
	return &ProcessContext{true, 0, s}
}

// NewDecodeContext returns a ProcessContext for decoding from given buffer s.
func NewDecodeContext(s []byte) *ProcessContext {
	return &ProcessContext{false, 0, s}
}

// Processor is the abstraction type that able to process encoding and
// decoding.
type Processor interface {
	// Process continues the encoding and decoding with given context.
	// The argument di and accessor is to index data to read and write byte.
	Process(ctx *ProcessContext, di DataIndexer, accessor Accessor)
}

// Accessor is the data container.
// We don't use reflection (the "encoding/json" way, which slows the
// performance) since there's already a bitproto compiler to generate code.
type Accessor interface {
	// XXXSetByte sets given byte b to target data, the data will be lookedup
	// by given indexer di from this accessor.
	// Argument lshift is the number of bits to shift right on b before it's
	// written onto the indexed data.
	XXXSetByte(di DataIndexer, lshift int, b byte)

	// XXXGetByte returns the byte from the data lookedup by given indexer di
	// from this accessor.
	// Argument rshift is the number of bits to shift left on the data before
	// it's cast to byte.
	XXXGetByte(di DataIndexer, rshift int) byte
}

// DataIndexer contains the argument to index data from current accessor.
type DataIndexer struct {
	fieldNumber       int
	arrayElementIndex int
}

// NewDataIndexer returns a new DataIndexer.
func NewDataIndexer(f, a int) DataIndexer     { return DataIndexer{f, a} }
func (di DataIndexer) FieldNumber() int       { return di.fieldNumber }
func (di DataIndexer) ArrayElementIndex() int { return di.arrayElementIndex }

// Bool implements Processor for bool type.
type Bool struct{}

func NewBool() *Bool { return &Bool{} }
func (t *Bool) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	processBaseType(1, ctx, di, accessor)
}

// Int implements Processor for int type.
type Int struct{ nbits int }

func NewInt(nbits int) *Int { return &Int{nbits} }
func (t *Int) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	processBaseType(t.nbits, ctx, di, accessor)
}

// Uint implements Processor for uint type.
type Uint struct{ nbits int }

func NewUint(nbits int) *Uint { return &Uint{nbits} }
func (t *Uint) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	processBaseType(t.nbits, ctx, di, accessor)
}

// Byte implements Processor for byte type.
type Byte struct{}

func NewByte() *Byte { return &Byte{} }
func (t *Byte) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	processBaseType(8, ctx, di, accessor)
}

// Array implements Processor for array type.
type Array struct {
	extensible       bool
	capacity         int
	elementProcessor Processor
}

func NewArray(extensible bool, capacity int, elementProcessor Processor) *Array {
	return &Array{
		extensible, capacity, elementProcessor,
	}
}
func (t *Array) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	// TODO: extensible
	for k := 0; k < t.capacity; k++ {
		// Rewrite data indexer's ArrayElementIndex.
		t.elementProcessor.Process(ctx, NewDataIndexer(di.FieldNumber(), k), accessor)
	}
}

// EnumProcessor implements Processor for enum.
// Assuming compiler generates Enum a method: XXXProcessor to returns this.
type EnumProcessor struct {
	extensible bool
	ut         *Uint
}

func NewEnumProcessor(extensible bool, ut *Uint) *EnumProcessor {
	return &EnumProcessor{extensible, ut}
}
func (t *EnumProcessor) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	// TODO: extensible
	t.ut.Process(ctx, di, accessor)
}

// AliasProcessor implements Processor for alias.
// Assuming compiler generates Alias a method: XXXProcessor to returns this.
type AliasProcessor struct{ to Processor }

func NewAliasProcessor(to Processor) *AliasProcessor { return &AliasProcessor{to} }
func (t *AliasProcessor) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	// TODO: extensible
	t.to.Process(ctx, di, accessor)
}

// MessageFieldProcessor implements Processor for message field.
type MessageFieldProcessor struct {
	fieldNumber   int
	typeProcessor Processor
}

func NewMessageFieldProcessor(fieldNumber int, typeProcessor Processor) *MessageFieldProcessor {
	return &MessageFieldProcessor{fieldNumber, typeProcessor}
}
func (t *MessageFieldProcessor) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	// Rewrite data indexer's fieldNumber.
	di = NewDataIndexer(t.fieldNumber, 0)
	t.typeProcessor.Process(ctx, di, accessor)
}

// MessageProcessor implements Processor for message
// Assuming compiler generates Message a method: XXXProcessor to returns this.
type MessageProcessor struct {
	fieldDescriptors []*MessageFieldProcessor
}

func NewMessageProcessor(fieldDescriptors []*MessageFieldProcessor) *MessageProcessor {
	return &MessageProcessor{fieldDescriptors}
}
func (t *MessageProcessor) Process(ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	for _, fieldDescriptor := range t.fieldDescriptors {
		fieldDescriptor.Process(ctx, di, accessor)
	}
}

// processBaseType process encoding and decoding on a base type.
func processBaseType(nbits int, ctx *ProcessContext, di DataIndexer, accessor Accessor) {
	for j := 0; j < nbits; {
		// Gets number of bits to copy (0~8).
		c := getNbitsToCopy(ctx.i, j, nbits)
		// Process bits copy inside a byte.
		processSingleByte(ctx, di, accessor, j, c)
		// Maintain trackers.
		ctx.i += c
		j += c
	}
}

// processSingleByte dispatch process to encodeSingleByte and decodeSingleByte.
func processSingleByte(ctx *ProcessContext, di DataIndexer, accessor Accessor, j, c int) {
	if ctx.isEncode {
		encodeSingleByte(ctx, di, accessor, j, c)
	} else {
		decodeSingleByte(ctx, di, accessor, j, c)
	}
}

// encodeSingleByte encode number of c bits from data to given buffer s.
// Where the data is lookedup by data indexer di from data container accessor.
// And the buffer s is given in ProcessContext ctx.
func encodeSingleByte(ctx *ProcessContext, di DataIndexer, accessor Accessor, j, c int) {
	i := ctx.i

	// Number of bits to shift right to obtain byte from accessor.
	rshift := int(j%8) * 8
	b := accessor.XXXGetByte(di, rshift)

	shift := (j % 8) - (i % 8)
	mask := byte(getMask(i%8, c)) // safe cast: i%8 and c always in [0,8]
	// shift and then take mask to get bits to copy.
	d := smartShift(b, shift) & mask

	// Copy bits to buffer s.
	ctx.s[int(i/8)] |= d
}

// decodeSingleByte decode number of c bits from buffer s to target data.
// Where the data is lookedup by data indexer di from data container accessor.
// And the buffer s is given in ProcessContext ctx.
// Byte decoding is finally done by accessor's generated function XXXSetByte.
func decodeSingleByte(ctx *ProcessContext, di DataIndexer, accessor Accessor, j, c int) {
	i := ctx.i

	b := ctx.s[int(i/8)]
	shift := (i % 8) - (j % 8)
	mask := byte(getMask(j%8, c)) // safe cat: j%8 and c always in [0,8]
	// shift and then take mask to get bits to copy.
	d := smartShift(b, shift) & mask

	// Number of bits to shift left to set byte to accessor.
	lshift := int(j/8) * 8
	accessor.XXXSetByte(di, lshift, d)
}

// Returns the number of bits to copy during a single byte process.
// Argument i, j, n:
//	i is the number of the total bits processed.
//	j is the number of bits processed on current base type.
//	n is the number of bits current base type occupy.
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
