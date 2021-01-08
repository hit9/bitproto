package bitproto

type ByteExtractor func(shift int) byte

type FieldConstructor func(b byte, shift int)

type FieldDescriptor struct {
	Nbits       int
	Extractor   ByteExtractor
	Constructor FieldConstructor
}

func Encode(descriptors []*FieldDescriptor, s []byte) {

}

func Decode(descriptors []*FieldDescriptor, s []byte) {

}

func min(a, b int) int {
	if a > b {
		return b
	}
	return a
}

func getMask(k, c int) int {
	if k == 0 {
		return (1 << c) - 1
	}
	return ((1 << (k + 1 + c)) - 1) - ((1 << (k + 1)) - 1)
}

func smartShift(n, k int) int {
	if k > 0 {
		return n >> k
	}
	if k < 0 {
		return n << k
	}
	return n
}

func getNumberOfBitsToCopy(i, j, n int) int {
	return min(min(n-j, 8-(j%8)), 8-(i%8))
}

func encodeSingleByte(descriptor *FieldDescriptor, s []byte, sIndex, i, j, c int) {

}
