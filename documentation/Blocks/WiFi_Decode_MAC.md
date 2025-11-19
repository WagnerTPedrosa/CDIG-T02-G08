# WiFi Decode MAC Block - Technical Analysis

## Overview

The **WiFi Decode MAC** block is the final processing stage in the GNU Radio IEEE 802.11 receiver chain that performs **complete frame decoding** from soft bits to MAC layer packets. It handles **deinterleaving**, **Viterbi decoding**, **descrambling**, and **CRC verification** to produce valid IEEE 802.11 MAC frames ready for network stack processing or analysis.

## Block Interface

### Inputs (1 port)
1. **Port 0 - `in`** (`uint8[48]`): Soft bit vectors from Frame Equalizer (48 data subcarriers per OFDM symbol)

### Outputs (1 port)  
1. **Port 0 - `out`** (message): Complete MAC frames as PMT messages with metadata

### Parameters
- **`log`** (bool, default: false): Enable logging output for debugging
- **`debug`** (bool, default: false): Enable detailed debug information and hex dumps

## Functionality

### Core Processing Pipeline

The WiFi Decode MAC block implements the **complete IEEE 802.11 PHY to MAC conversion**:

#### 1. Frame Assembly and Buffering
- **Tag Processing**: Detects frame start tags from Frame Equalizer
- **Parameter Extraction**: Reads frame length, encoding, and metadata from tags
- **Symbol Collection**: Buffers complete frame (up to MAX_SYM symbols)
- **Frame Validation**: Checks for reasonable frame sizes before processing

#### 2. Bit Extraction and Conversion
- **Symbol-to-Bit Mapping**: Converts 48-element soft bit vectors to hard bits
- **Bit Packing**: Applies modulation-specific bit extraction (n_bpsc bits per symbol)
- **Stream Assembly**: Creates continuous bit stream for entire frame

#### 3. Deinterleaving Process
- **Two-Stage Deinterleaving**: Implements IEEE 802.11 deinterleaving algorithm
- **First Permutation**: `first[j] = s*(j/s) + ((j + floor(16*j/n_cbps)) % s)`
- **Second Permutation**: `second[i] = 16*i - (n_cbps-1)*floor(16*i/n_cbps)`
- **Complete Reordering**: `output[i*n_cbps + second[first[k]]] = input[i*n_cbps + k]`

#### 4. Viterbi Decoding
- **Convolutional Decoding**: Uses constraint length 7, rate 1/2 Viterbi decoder
- **Puncturing Support**: Handles rate 2/3 and 3/4 codes via puncturing patterns
- **Soft Decision**: Processes deinterleaved bits through trellis decoder
- **Error Correction**: Provides forward error correction for noisy channels

#### 5. Descrambling Operation
- **LFSR Descrambling**: Implements IEEE 802.11 scrambler polynomial x⁷ + x⁴ + 1
- **Initial State**: Uses first 7 bits as scrambler seed (SERVICE field)
- **Feedback Generation**: `feedback = (state[6]) XOR (state[3])`
- **Bit Processing**: `output_bit = input_bit XOR feedback`
- **State Update**: Shifts register and inserts feedback

#### 6. CRC Verification
- **CRC-32 Calculation**: Computes IEEE 802.11 Frame Check Sequence
- **Payload Verification**: Checks PSDU content (excluding SERVICE field)
- **Error Detection**: Drops frames with invalid CRC (checksum ≠ 558161692)
- **Frame Validation**: Ensures data integrity before MAC delivery

## Technical Details

### Frame Structure Processing

#### IEEE 802.11 Frame Composition
```
┌─────────────┬──────────────┬─────────────┬─────────────┐
│ SIGNAL (24) │ SERVICE (16) │  PSDU (var) │  CRC-32 (32)│
│   + TAIL    │              │             │             │
└─────────────┴──────────────┴─────────────┴─────────────┘
```

#### Frame Parameter Extraction
- **Frame Length**: Extracted from SIGNAL field (12 bits, 0-4095 bytes)
- **Encoding Rate**: Modulation and coding scheme from SIGNAL field
- **Symbol Count**: Calculated as `ceil((SERVICE + 8*LENGTH + TAIL) / data_bits_per_symbol)`

### Deinterleaving Algorithm

#### Mathematical Implementation
```cpp
// Parameters
int n_cbps = coded_bits_per_symbol;  // Depends on modulation
int s = max(n_bpsc/2, 1);           // Subcarrier rotation parameter

// First permutation (frequency diversity)
first[j] = s*(j/s) + ((j + floor(16*j/n_cbps)) % s);

// Second permutation (time diversity)  
second[i] = 16*i - (n_cbps-1)*floor(16*i/n_cbps);

// Combined deinterleaving
deinterleaved[symbol][second[first[k]]] = input[symbol][k];
```

#### Modulation-Specific Parameters
- **BPSK**: n_cbps=48, s=1 (no subcarrier rotation)
- **QPSK**: n_cbps=96, s=1 (minimal rotation)
- **16-QAM**: n_cbps=192, s=2 (moderate rotation)
- **64-QAM**: n_cbps=288, s=3 (maximum rotation)

### Viterbi Decoder Integration

#### Decoder Configuration
- **Constraint Length**: K=7 (64-state trellis)
- **Generator Polynomials**: G0=133₈, G1=171₈ (industry standard)
- **Puncturing Patterns**: Support for rates 1/2, 2/3, 3/4
- **Trace-back Length**: Optimized for performance vs. latency

#### Rate-Dependent Processing
```cpp
switch(encoding_rate) {
    case BPSK_1_2:  // Rate 1/2, no puncturing
    case QPSK_1_2:  
    case QAM16_1_2:
    case QAM64_2_3: // Rate 2/3, puncturing pattern [1,1,1,0]
    case BPSK_3_4:  // Rate 3/4, puncturing pattern [1,1,1,0,0,1]
    case QPSK_3_4:
    case QAM16_3_4:
    case QAM64_3_4:
}
```

### Scrambling/Descrambling

#### LFSR Implementation
```cpp
// Scrambler polynomial: x^7 + x^4 + 1
// State register: [b6, b5, b4, b3, b2, b1, b0]
feedback = state[6] XOR state[3];           // Polynomial taps
output_bit = input_bit XOR feedback;        // Descrambling operation
state = ((state << 1) & 0x7E) | feedback;  // Shift and update
```

#### SERVICE Field Processing
- **Initialization**: First 7 bits determine scrambler state
- **Zero Padding**: Remaining 9 SERVICE bits should be zero
- **Validation**: Can be used for additional frame integrity checking

### Message System and Metadata

#### Output Message Format
```cpp
// PMT Message Structure
pmt::cons(metadata_dict, payload_blob)

// Metadata Dictionary Contents
"frame bytes" -> uint64 (PSDU size)
"encoding"    -> uint64 (modulation index)
"snr"         -> double (from equalizer)
"frequency offset" -> double (carrier offset)
"beta"        -> double (phase error)
"csi"         -> complex vector (channel state)
"dlt"         -> long (LINKTYPE_IEEE802_11 = 105)
```

#### Payload Blob
- **Content**: Raw MAC frame bytes (PSDU without SERVICE/CRC)
- **Format**: Binary data ready for pcap/Wireshark analysis
- **Size**: Variable, 0-4095 bytes per IEEE 802.11 standard

## Performance Characteristics

### Computational Complexity
- **Deinterleaving**: O(n_cbps × n_symbols) - linear with frame size
- **Viterbi Decoding**: O(64 × coded_bits) - trellis state transitions
- **Descrambling**: O(payload_bits) - linear shift register operations
- **CRC Verification**: O(payload_bytes) - polynomial division

### Memory Requirements
- **Symbol Buffer**: 48 × MAX_SYM bytes (≈2.4KB for 50 symbols)
- **Bit Arrays**: MAX_ENCODED_BITS (typically 16KB)
- **Viterbi State**: Decoder trellis memory (≈4KB)
- **Output Buffer**: MAX_PSDU_SIZE + 2 (≈4KB)

### Error Handling and Robustness
- **Frame Size Limits**: MAX_SYM and MAX_PSDU_SIZE prevent buffer overflows
- **CRC Validation**: Drops corrupted frames automatically
- **Incomplete Frame Detection**: Handles partial frame reception gracefully
- **Metadata Validation**: Checks encoding parameters for consistency

## Integration in Receiver Chain

### Upstream Dependencies
- **Frame Equalizer**: Provides soft bits and frame metadata tags
- **Synchronization Chain**: Requires accurate frame timing and parameters
- **Channel Coding**: Depends on proper equalization and bit decisions

### Downstream Applications
- **Network Stack**: Delivers standard 802.11 MAC frames
- **Protocol Analysis**: Wireshark-compatible pcap format
- **Research Tools**: Rich metadata for performance analysis
- **Quality Assessment**: Frame success rate and error statistics

## Usage Example

```python
# Create WiFi Decode MAC block
decode_mac = ieee802_11.decode_mac(
    log=True,           # Enable frame logging
    debug=False         # Disable hex dumps
)

# Message handling setup
def handle_mac_frame(msg):
    metadata = pmt.car(msg)
    payload = pmt.cdr(msg)
    
    # Extract frame information
    frame_bytes = pmt.to_uint64(pmt.dict_ref(metadata, pmt.intern("frame bytes"), pmt.from_uint64(0)))
    encoding = pmt.to_uint64(pmt.dict_ref(metadata, pmt.intern("encoding"), pmt.from_uint64(0)))
    snr = pmt.to_double(pmt.dict_ref(metadata, pmt.intern("snr"), pmt.from_double(0)))
    
    # Process payload
    payload_bytes = pmt.blob_data(payload)
    print(f"Received frame: {frame_bytes} bytes, encoding {encoding}, SNR {snr:.1f} dB")

# Connect in receiver chain
self.connect((frame_equalizer, 0), (decode_mac, 0))       # Soft bits input
self.msg_connect((decode_mac, 'out'), (mac_handler, 'in')) # MAC frame output
```

## Advanced Features

### Debug and Analysis Capabilities
- **Hex Dumps**: Complete frame content in hexadecimal format
- **ASCII Display**: Printable character representation of payload
- **Frame Statistics**: Success/failure rates and error patterns
- **Timing Analysis**: Processing latency and throughput metrics

### Research Applications
- **Protocol Reverse Engineering**: Complete frame capture and analysis
- **Performance Evaluation**: BER/PER measurements with rich metadata
- **Channel Analysis**: CSI correlation with frame success rates
- **Algorithm Development**: Testbed for improved decoding techniques

### Standards Compliance
- **IEEE 802.11-2020**: Full compliance with current standard
- **Backward Compatibility**: Supports legacy 802.11a/g rates
- **Interoperability**: Works with standard WiFi equipment
- **Pcap Compatibility**: Direct integration with network analysis tools

## Common Applications

1. **WiFi Monitoring**: Passive monitoring of 802.11 networks
2. **Protocol Analysis**: Deep packet inspection and frame analysis  
3. **Research Platforms**: Academic and industrial WiFi research
4. **Security Analysis**: Wireless security assessment and penetration testing
5. **Network Troubleshooting**: RF performance analysis and optimization
6. **SDR Development**: Software-defined radio WiFi implementations

## Key Advantages

- **Complete Processing**: Full PHY-to-MAC conversion in single block
- **Standards Compliance**: Exact IEEE 802.11 algorithm implementation
- **Rich Metadata**: Comprehensive frame and channel information
- **Error Resilience**: Robust handling of corrupted or partial frames
- **Analysis Support**: Built-in debugging and frame inspection tools
- **Performance Optimized**: Efficient algorithms for real-time processing

This block serves as the **final decoding stage** of the WiFi receiver, transforming equalized soft bits into complete, validated MAC frames ready for network processing or analysis, while providing comprehensive metadata for performance evaluation and research applications.
