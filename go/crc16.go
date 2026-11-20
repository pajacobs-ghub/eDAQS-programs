// file: crc16.go

package edaqs


// CRC-16 calculation using CCITT polynomial 0x11021.
// Adapted from our C code.
func Crc16b(data []byte, n int, remainder uint16) uint16 {
    for i := 0; i < n; i++ {
        remainder ^= uint16(data[i]) << 8;
        for ibit := 8; ibit > 0; ibit-- {
            if remainder & 0x8000 > 0 {
                remainder = (remainder << 1) ^ 0x1021;
            } else {
                remainder <<= 1;
            }
        }
    }
    return remainder;
}
