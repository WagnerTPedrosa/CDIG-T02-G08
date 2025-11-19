# WiFi Parse MAC Block - Technical Analysis

## Overview

The **WiFi Parse MAC** block is a comprehensive IEEE 802.11 frame analysis component in the GNU Radio implementation that performs **detailed MAC frame parsing** and **protocol analysis**. It operates as a post-processing stage that extracts and interprets all MAC layer information from decoded frames, providing structured metadata for network analysis, monitoring, and research applications.

## Block Interface

### Inputs (1 port)
1. **Port 0 - `in`** (message): MAC frame messages from Decode MAC block containing raw frame bytes and metadata

### Outputs (1 port)
1. **Port 0 - `out`** (message): Enhanced frame messages with comprehensive MAC layer parsing and analysis

### Parameters
- **`log`** (bool, default: false): Enable frame logging and analysis output
- **`debug`** (bool, default: false): Enable detailed debug information and frame dumps

## Functionality

### Core Processing Pipeline

The WiFi Parse MAC block implements **comprehensive IEEE 802.11 frame analysis**:

#### 1. Frame Reception and Validation
- **Message Processing**: Handles PMT messages from upstream decode blocks
- **Length Validation**: Ensures minimum frame size (20 bytes for basic MAC header)
- **Format Verification**: Validates frame structure and accessibility
- **Metadata Extraction**: Preserves all upstream metadata (PHY parameters, timing, etc.)

#### 2. MAC Header Parsing
- **Frame Control Analysis**: Extracts protocol version, type, subtype, and flags
- **Duration Field**: Parses duration/ID field for medium access control
- **Address Fields**: Extracts and formats all MAC addresses (up to 3 addresses)
- **Sequence Control**: Analyzes sequence numbers and fragment information

#### 3. Frame Type Classification
- **Management Frames**: Association, authentication, beacon, probe, action frames
- **Control Frames**: RTS, CTS, ACK, Block ACK, PS-Poll frames  
- **Data Frames**: Regular data, QoS data, null frames, CF-Poll variants
- **Reserved Types**: Handles unknown or future frame types gracefully

#### 4. Subtype-Specific Processing
- **Management Subtypes**: 16 different management frame subtypes
- **Data Subtypes**: 16 data frame variants including QoS extensions
- **Control Subtypes**: 10 control frame types for medium access
- **Beacon Analysis**: Special handling for SSID extraction from beacon frames

#### 5. Address Field Interpretation
- **Address 1**: Receiver Address (RA) or Destination Address (DA)
- **Address 2**: Transmitter Address (TA) or Source Address (SA)  
- **Address 3**: BSSID, DA, or SA depending on frame type and DS flags
- **MAC Formatting**: Standard colon-separated hexadecimal format

#### 6. Performance Metrics Calculation
- **Sequence Tracking**: Monitors sequence numbers for frame loss detection
- **Frame Error Rate**: Calculates instantaneous FER based on missing frames
- **Loss Statistics**: Tracks dropped frames using sequence number gaps

## Technical Details

### MAC Header Structure

#### IEEE 802.11 MAC Header Format (24 bytes minimum)
```cpp
struct mac_header {
    uint16_t frame_control;    // Protocol, type, subtype, flags
    uint16_t duration;         // Duration/ID field  
    uint8_t  addr1[6];        // Address 1 (RA/DA)
    uint8_t  addr2[6];        // Address 2 (TA/SA)
    uint8_t  addr3[6];        // Address 3 (BSSID/DA/SA)
    uint16_t seq_nr;          // Sequence control field
};
```

#### Frame Control Field Breakdown
```cpp
// Bits 0-1: Protocol Version (always 0 for 802.11)
// Bits 2-3: Type (Management=0, Control=1, Data=2, Reserved=3)  
// Bits 4-7: Subtype (16 variants per type)
// Bit 8: To DS flag
// Bit 9: From DS flag
// Bit 10: More Fragments
// Bit 11: Retry
// Bit 12: Power Management
// Bit 13: More Data
// Bit 14: WEP/Protected Frame
// Bit 15: Order
```

### Frame Type Analysis

#### Management Frame Subtypes (Type = 0)
```cpp
switch (subtype) {
    case 0:  Association Request
    case 1:  Association Response  
    case 2:  Reassociation Request
    case 3:  Reassociation Response
    case 4:  Probe Request
    case 5:  Probe Response
    case 6:  Timing Advertisement
    case 7:  Reserved
    case 8:  Beacon (with SSID extraction)
    case 9:  ATIM
    case 10: Disassociation
    case 11: Authentication
    case 12: Deauthentication
    case 13: Action
    case 14: Action No Ack
    case 15: Reserved
}
```

#### Data Frame Subtypes (Type = 2)
```cpp
switch (subtype) {
    case 0:  Data
    case 1:  Data + CF-ACK
    case 2:  Data + CF-Poll
    case 3:  Data + CF-ACK + CF-Poll
    case 4:  Null (no data)
    case 5:  CF-ACK (no data)
    case 6:  CF-Poll (no data)
    case 7:  CF-ACK + CF-Poll (no data)
    case 8:  QoS Data
    case 9:  QoS Data + CF-ACK
    case 10: QoS Data + CF-Poll
    case 11: QoS Data + CF-ACK + CF-Poll
    case 12: QoS Null (no data)
    case 13: Reserved
    case 14: QoS CF-Poll (no data)
    case 15: QoS CF-ACK + CF-Poll (no data)
}
```

#### Control Frame Subtypes (Type = 1)
```cpp
switch (subtype) {
    case 7:  Control Wrapper
    case 8:  Block ACK Request
    case 9:  Block ACK
    case 10: PS-Poll
    case 11: RTS (Request to Send)
    case 12: CTS (Clear to Send)
    case 13: ACK (Acknowledgment)
    case 14: CF-End
    case 15: CF-End + CF-ACK
}
```

### Special Processing Features

#### Beacon Frame SSID Extraction
```cpp
// Beacon-specific processing for SSID extraction
if (subtype == 8) { // Beacon frame
    uint8_t* ssid_len = (uint8_t*)(buf + 24 + 13);  // Skip to SSID IE
    if (length >= 38 + *ssid_len) {
        std::string ssid(buf + 24 + 14, *ssid_len);  // Extract SSID string
        metadata["ssid"] = ssid;
    }
}
```

#### Data Payload Processing  
```cpp
// Extract payload for data frames
if (frame_type == 2) {          // Regular data frame
    payload_start = frame + 24;  // After MAC header
    payload_length = frame_len - 24;
} else if (frame_subtype == 34) { // QoS data frame  
    payload_start = frame + 26;  // After MAC header + QoS control
    payload_length = frame_len - 26;
}
```

#### Frame Error Rate Calculation
```cpp
// Sequence number tracking for FER calculation
int current_seq = (seq_control >> 4) & 0xFFF;  // Extract 12-bit sequence number
float lost_frames = current_seq - last_seq - 1;
if (lost_frames < 0) lost_frames += 4096;     // Handle wraparound
float fer = lost_frames / (lost_frames + 1);   // Instantaneous FER
```

### Address Field Processing

#### MAC Address Formatting
```cpp
std::string format_mac_address(uint8_t* addr) {
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    ss << std::setw(2) << (int)addr[0];
    for (int i = 1; i < 6; i++) {
        ss << ":" << std::setw(2) << (int)addr[i];
    }
    return ss.str();  // Returns "aa:bb:cc:dd:ee:ff" format
}
```

#### Address Interpretation by Frame Type
- **Management/Data**: Address 1 = DA, Address 2 = SA, Address 3 = BSSID
- **Control RTS**: Address 1 = RA, Address 2 = TA
- **Control CTS/ACK**: Address 1 = RA only
- **DS Flags**: Modify interpretation for infrastructure vs. ad-hoc networks

### Enhanced Metadata System

#### Comprehensive Frame Metadata
```cpp
// Original metadata from PHY layers preserved, plus:
metadata["type"] = "Management"/"Control"/"Data"/"Unknown";
metadata["subtype"] = specific_subtype_string;
metadata["duration"] = duration_field_value;
metadata["sequence number"] = sequence_number;
metadata["address 1"] = formatted_mac_address_1;
metadata["address 2"] = formatted_mac_address_2; 
metadata["address 3"] = formatted_mac_address_3;
metadata["lost frames"] = calculated_frame_loss;
metadata["instantaneous fer"] = frame_error_rate;
metadata["ssid"] = network_name; // For beacon frames
```

## Performance Characteristics

### Computational Complexity
- **Header Parsing**: O(1) - fixed-size MAC header processing
- **Address Formatting**: O(1) - simple string formatting operations
- **Subtype Analysis**: O(1) - switch statement lookups
- **SSID Extraction**: O(N) where N = SSID length (max 32 bytes)

### Memory Requirements
- **Message Processing**: Minimal - operates on existing PMT messages
- **String Operations**: Temporary strings for MAC addresses and SSID
- **State Tracking**: Single integer for sequence number tracking
- **Total Overhead**: <1KB additional memory per instance

### Processing Latency
- **Message-Driven**: Zero buffering latency - immediate processing
- **Parse Time**: <1μs per frame on modern processors
- **String Formatting**: Dominant operation, still sub-microsecond
- **Real-Time Capable**: Suitable for high-rate frame processing

## Integration in Receiver Chain

### Upstream Dependencies
- **Decode MAC**: Requires validated MAC frame messages
- **Frame Equalizer**: Benefits from PHY-layer metadata (SNR, CSI, etc.)
- **Message Format**: PMT cons(metadata_dict, payload_blob)

### Downstream Applications
- **Network Analysis**: Wireshark, protocol analyzers
- **Research Tools**: Custom analysis applications
- **Monitoring Systems**: Network performance and security monitoring
- **Statistics Collection**: Frame type distribution, error rates

## Usage Example

```python
# Create WiFi Parse MAC block
parse_mac = ieee802_11.parse_mac(
    log=True,           # Enable frame analysis logging
    debug=False         # Disable detailed hex dumps
)

# Message handler for processed frames
def handle_parsed_frame(msg):
    metadata = pmt.car(msg)
    payload = pmt.cdr(msg)
    
    # Extract parsed information
    frame_type = pmt.to_string(pmt.dict_ref(metadata, pmt.intern("type"), pmt.intern("")))
    subtype = pmt.to_string(pmt.dict_ref(metadata, pmt.intern("subtype"), pmt.intern("")))
    addr1 = pmt.to_string(pmt.dict_ref(metadata, pmt.intern("address 1"), pmt.intern("")))
    addr2 = pmt.to_string(pmt.dict_ref(metadata, pmt.intern("address 2"), pmt.intern("")))
    
    # Special handling for different frame types
    if frame_type == "Management" and subtype == "Beacon":
        ssid = pmt.to_string(pmt.dict_ref(metadata, pmt.intern("ssid"), pmt.intern("")))
        print(f"Beacon from {addr2}: SSID = '{ssid}'")
    elif frame_type == "Data":
        seq_num = pmt.to_long(pmt.dict_ref(metadata, pmt.intern("sequence number"), pmt.from_long(0)))
        fer = pmt.to_double(pmt.dict_ref(metadata, pmt.intern("instantaneous fer"), pmt.from_double(0)))
        print(f"Data frame {seq_num}: {addr2} -> {addr1}, FER = {fer:.3f}")

# Connect in processing chain
self.msg_connect((decode_mac, 'out'), (parse_mac, 'in'))      # MAC frames input
self.msg_connect((parse_mac, 'out'), (frame_handler, 'in'))    # Parsed frames output
```

## Advanced Features

### Protocol Analysis Capabilities
- **Frame Classification**: Automatic categorization of all 802.11 frame types
- **Address Tracking**: Comprehensive MAC address extraction and formatting
- **Sequence Analysis**: Frame loss detection and FER calculation
- **Payload Inspection**: ASCII representation of data frame payloads

### Network Monitoring Support
- **SSID Discovery**: Automatic beacon frame SSID extraction
- **Station Tracking**: MAC address-based device identification
- **Performance Metrics**: Real-time frame error rate calculation
- **Traffic Analysis**: Frame type distribution and communication patterns

### Research and Development
- **Complete Metadata**: Preserves all PHY and MAC layer information
- **Flexible Output**: PMT message format compatible with GNU Radio ecosystem
- **Standards Compliance**: Exact IEEE 802.11 frame format interpretation
- **Extensible Design**: Easy addition of new analysis features

### Debugging and Validation
- **Frame Dumps**: Optional hexadecimal and ASCII frame content display
- **Verbose Logging**: Detailed frame parsing information
- **Error Detection**: Robust handling of malformed or truncated frames
- **Validation Checks**: Frame length and structure verification

## Common Applications

1. **Network Monitoring**: Real-time 802.11 network analysis and monitoring
2. **Security Research**: Wireless security assessment and penetration testing
3. **Protocol Analysis**: Deep inspection of 802.11 protocol behavior
4. **Performance Evaluation**: Network performance measurement and optimization
5. **Spectrum Management**: RF environment analysis and interference detection
6. **Academic Research**: Educational and research platform for 802.11 studies
7. **Compliance Testing**: Validation of 802.11 implementation compliance

## Key Advantages

- **Comprehensive Parsing**: Complete 802.11 frame analysis in single block
- **Standards Compliance**: Exact IEEE 802.11-2020 frame format support
- **Rich Metadata**: Detailed frame and network information extraction
- **Performance Monitoring**: Built-in frame error rate and loss tracking
- **Research Support**: Complete frame information for analysis applications
- **Real-Time Capable**: Efficient processing suitable for live monitoring
- **Flexible Output**: PMT message format compatible with analysis tools

This block serves as the **protocol analysis engine** of the WiFi receiver chain, transforming raw MAC frames into structured, comprehensive network information suitable for monitoring, analysis, and research applications while maintaining full IEEE 802.11 standards compliance.
