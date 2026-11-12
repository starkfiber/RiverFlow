# Bytes, hexadecimal and ASCII in RF2

This is a representation reference for the qualified native systems compiler, not a claim of a new instruction set or arbitrary binary compatibility.

## Values and spellings

One byte contains eight bits and can hold an unsigned value from 0 through 255. Hexadecimal writes that byte with two base-16 digits, `00` through `FF`. ASCII defines only values 0 through 127. Bytes above 127 have no single universal “extended ASCII” meaning; UTF-8 encodes Unicode using one to four bytes per scalar.

| Value | Decimal spelling | Hex spelling in systems RF2 | Eight-bit binary representation | ASCII interpretation |
| --- | --- | --- | --- | --- |
| Zero | `0` | `0x00` | `00000000` | NUL |
| Line feed | `10` | `0x0A` | `00001010` | LF |
| Space | `32` | `0x20` | `00100000` | SP |
| Capital A | `65` | `0x41` | `01000001` | A |
| Lowercase a | `97` | `0x61` | `01100001` | a |
| Full byte | `255` | `0xFF` | `11111111` | Not ASCII |

The systems lexer accepts decimal literals and a lowercase `0x` prefix with uppercase or lowercase hex digits. It does not implement `0b` binary literals, uppercase `0X` prefixes or underscore separators. Binary strings in this page are notation, not accepted numeric spellings. Seven selected literal admission/execution checks were run against the qualified 0.14 compiler; broader language checks remain in its release corpus.

Systems scalars are u64 machine words. Numeric literal accumulation and ordinary systems arithmetic are machine-word operations; do not infer checked overflow merely from a short spelling. Checked u32 Core is a different profile with its own explicit checked/wrapping contract. A double-quoted systems string is a byte-string address, not an integer character literal. Use `0x41` or `65` for the scalar byte value A.

## Representation is separate from byte order

The integer `0x12345678` has the same value regardless of the way it is printed. Storing a 32-bit value through the current little-endian ARM64 target produces bytes `78 56 34 12` at increasing addresses. A text file containing the eight characters `12345678` instead contains ASCII bytes `31 32 33 34 35 36 37 38`. A raw byte array has no endianness until code interprets a group of its bytes as a multibyte value.

For file formats and network protocols, specify the width, byte order and bounds explicitly. Do not infer them from a filename, hex display or language name. RF2 currently targets Apple Silicon macOS; this reference does not establish a portable ABI or x86 backend.

## ASCII chart

Control names are shown instead of executing their effects. SP is the ordinary space; DEL is delete. The table contains every ASCII value exactly once.

| Decimal | Hex | ASCII | Meaning |
| ---: | --- | --- | --- |
| 0 | `0x00` | NUL | Null |
| 1 | `0x01` | SOH | Start of heading |
| 2 | `0x02` | STX | Start of text |
| 3 | `0x03` | ETX | End of text |
| 4 | `0x04` | EOT | End of transmission |
| 5 | `0x05` | ENQ | Enquiry |
| 6 | `0x06` | ACK | Acknowledge |
| 7 | `0x07` | BEL | Bell |
| 8 | `0x08` | BS | Backspace |
| 9 | `0x09` | HT | Horizontal tab |
| 10 | `0x0A` | LF | Line feed |
| 11 | `0x0B` | VT | Vertical tab |
| 12 | `0x0C` | FF | Form feed |
| 13 | `0x0D` | CR | Carriage return |
| 14 | `0x0E` | SO | Shift out |
| 15 | `0x0F` | SI | Shift in |
| 16 | `0x10` | DLE | Data link escape |
| 17 | `0x11` | DC1 | Device control 1 |
| 18 | `0x12` | DC2 | Device control 2 |
| 19 | `0x13` | DC3 | Device control 3 |
| 20 | `0x14` | DC4 | Device control 4 |
| 21 | `0x15` | NAK | Negative acknowledge |
| 22 | `0x16` | SYN | Synchronous idle |
| 23 | `0x17` | ETB | End of transmission block |
| 24 | `0x18` | CAN | Cancel |
| 25 | `0x19` | EM | End of medium |
| 26 | `0x1A` | SUB | Substitute |
| 27 | `0x1B` | ESC | Escape |
| 28 | `0x1C` | FS | File separator |
| 29 | `0x1D` | GS | Group separator |
| 30 | `0x1E` | RS | Record separator |
| 31 | `0x1F` | US | Unit separator |
| 32 | `0x20` | SP | Space |
| 33 | `0x21` | ! | Printable character |
| 34 | `0x22` | " | Printable character |
| 35 | `0x23` | # | Printable character |
| 36 | `0x24` | $ | Printable character |
| 37 | `0x25` | % | Printable character |
| 38 | `0x26` | &amp; | Printable character |
| 39 | `0x27` | ' | Printable character |
| 40 | `0x28` | ( | Printable character |
| 41 | `0x29` | ) | Printable character |
| 42 | `0x2A` | * | Printable character |
| 43 | `0x2B` | + | Printable character |
| 44 | `0x2C` | , | Printable character |
| 45 | `0x2D` | - | Printable character |
| 46 | `0x2E` | . | Printable character |
| 47 | `0x2F` | / | Printable character |
| 48 | `0x30` | 0 | Printable character |
| 49 | `0x31` | 1 | Printable character |
| 50 | `0x32` | 2 | Printable character |
| 51 | `0x33` | 3 | Printable character |
| 52 | `0x34` | 4 | Printable character |
| 53 | `0x35` | 5 | Printable character |
| 54 | `0x36` | 6 | Printable character |
| 55 | `0x37` | 7 | Printable character |
| 56 | `0x38` | 8 | Printable character |
| 57 | `0x39` | 9 | Printable character |
| 58 | `0x3A` | : | Printable character |
| 59 | `0x3B` | ; | Printable character |
| 60 | `0x3C` | &lt; | Printable character |
| 61 | `0x3D` | = | Printable character |
| 62 | `0x3E` | &gt; | Printable character |
| 63 | `0x3F` | ? | Printable character |
| 64 | `0x40` | @ | Printable character |
| 65 | `0x41` | A | Printable character |
| 66 | `0x42` | B | Printable character |
| 67 | `0x43` | C | Printable character |
| 68 | `0x44` | D | Printable character |
| 69 | `0x45` | E | Printable character |
| 70 | `0x46` | F | Printable character |
| 71 | `0x47` | G | Printable character |
| 72 | `0x48` | H | Printable character |
| 73 | `0x49` | I | Printable character |
| 74 | `0x4A` | J | Printable character |
| 75 | `0x4B` | K | Printable character |
| 76 | `0x4C` | L | Printable character |
| 77 | `0x4D` | M | Printable character |
| 78 | `0x4E` | N | Printable character |
| 79 | `0x4F` | O | Printable character |
| 80 | `0x50` | P | Printable character |
| 81 | `0x51` | Q | Printable character |
| 82 | `0x52` | R | Printable character |
| 83 | `0x53` | S | Printable character |
| 84 | `0x54` | T | Printable character |
| 85 | `0x55` | U | Printable character |
| 86 | `0x56` | V | Printable character |
| 87 | `0x57` | W | Printable character |
| 88 | `0x58` | X | Printable character |
| 89 | `0x59` | Y | Printable character |
| 90 | `0x5A` | Z | Printable character |
| 91 | `0x5B` | [ | Printable character |
| 92 | `0x5C` | \ | Printable character |
| 93 | `0x5D` | ] | Printable character |
| 94 | `0x5E` | ^ | Printable character |
| 95 | `0x5F` | _ | Printable character |
| 96 | `0x60` | &#96; | Printable character |
| 97 | `0x61` | a | Printable character |
| 98 | `0x62` | b | Printable character |
| 99 | `0x63` | c | Printable character |
| 100 | `0x64` | d | Printable character |
| 101 | `0x65` | e | Printable character |
| 102 | `0x66` | f | Printable character |
| 103 | `0x67` | g | Printable character |
| 104 | `0x68` | h | Printable character |
| 105 | `0x69` | i | Printable character |
| 106 | `0x6A` | j | Printable character |
| 107 | `0x6B` | k | Printable character |
| 108 | `0x6C` | l | Printable character |
| 109 | `0x6D` | m | Printable character |
| 110 | `0x6E` | n | Printable character |
| 111 | `0x6F` | o | Printable character |
| 112 | `0x70` | p | Printable character |
| 113 | `0x71` | q | Printable character |
| 114 | `0x72` | r | Printable character |
| 115 | `0x73` | s | Printable character |
| 116 | `0x74` | t | Printable character |
| 117 | `0x75` | u | Printable character |
| 118 | `0x76` | v | Printable character |
| 119 | `0x77` | w | Printable character |
| 120 | `0x78` | x | Printable character |
| 121 | `0x79` | y | Printable character |
| 122 | `0x7A` | z | Printable character |
| 123 | `0x7B` | { | Printable character |
| 124 | `0x7C` | &#124; | Printable character |
| 125 | `0x7D` | } | Printable character |
| 126 | `0x7E` | ~ | Printable character |
| 127 | `0x7F` | DEL | Delete |

## Use the right text layer

* A u8 array stores bytes. Its capacity is not automatically its populated input length.
* A byte view selects a checked byte range. It does not establish valid UTF-8.
* A text view validates a selected UTF-8 span. `.byte_length` counts bytes; `.length` and indexing use Unicode scalar values.
* Scalar counts do not give grapheme count, display width, normalization or language identity. A Tamil-block count is a code-point-range statistic, not language detection.

[Text and byte operations](TEXT-BYTES.md) · [Unicode views](UNICODE-CLEANUP.md) · [Current capability map](CAPABILITY-MAP.md)
