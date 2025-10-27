# IEEE 802.11 OFDM Receiver - Block Documentation

## Overview

This project implements a complete IEEE 802.11 OFDM (Orthogonal Frequency Division Multiplexing) receiver using GNU Radio. The system can process real WiFi baseband recordings, decode frames, and output packets for analysis with tools like Wireshark.

## System Architecture

The receiver consists of several cascaded processing blocks that implement the IEEE 802.11 OFDM demodulation and decoding pipeline:

```
RF Signal → Frame Detection → Synchronization → Equalization → Signal Decoding → MAC Decoding → Packet Output
```

## Block Descriptions

### 1. **OFDM Sync Short** (`ofdm_sync_short.py`)

**Purpose**: Detects the start of WiFi frames using short preamble correlation.

**Functionality**:
- Performs autocorrelation on the input signal to detect the 802.11 short training sequence
- Uses a sliding window correlation with configurable threshold
- Inserts `ofdm_start` tags when frames are detected
- Implements plateau detection to avoid false positives

**Key Parameters**:
- `threshold`: Correlation threshold for frame detection (default: 0.56)
- `max_samples`: Maximum samples to copy per frame (default: 8000)
- `min_plateau`: Minimum plateau length for valid detection (default: 2)

**Input**: Complex baseband signal
**Output**: Same signal with `ofdm_start` tags marking frame boundaries

---

### 2. **OFDM Sync Long** (`ofdm_sync_long.py`)

**Purpose**: Performs fine frequency and timing synchronization using the long preamble.

**Functionality**:
- Detects and processes the IEEE 802.11 long training sequence
- Estimates and corrects carrier frequency offset (CFO)
- Provides precise timing alignment for OFDM symbol boundaries
- Propagates frame start tags to downstream blocks

**Key Parameters**:
- `sync_length`: Length of synchronization sequence (default: 320)
- `freq_est`: Frequency estimation window (default: 128)

**Input**: Complex signal with `ofdm_start` tags
**Output**: Frequency-corrected signal with refined timing tags

---

### 3. **OFDM Equalize Symbols** (`ofdm_equalize_symbols.py`)

**Purpose**: Converts time-domain OFDM symbols to frequency domain and performs channel equalization.

**Functionality**:
- Applies FFT to convert OFDM symbols to frequency domain
- Extracts pilot subcarriers for channel estimation
- Performs zero-forcing equalization using pilot symbols
- Removes cyclic prefix and extracts data subcarriers

**Key Features**:
- 64-point FFT for IEEE 802.11a/g OFDM
- Pilot-based channel estimation
- Data subcarrier extraction (48 data + 4 pilot subcarriers)

**Input**: Time-domain OFDM symbols
**Output**: Equalized frequency-domain data symbols

---

### 4. **OFDM Decode Signal** (`ofdm_decode_signal.py`)

**Purpose**: Decodes the SIGNAL field to extract frame parameters.

**Functionality**:
- Demodulates the first OFDM symbol (SIGNAL field) using BPSK
- Performs deinterleaving and Viterbi decoding
- Extracts rate, length, and parity information
- Determines modulation scheme and frame duration
- Copies the required number of data symbols for MAC processing

**Supported Rates**:
- 6, 9, 12, 18, 24, 36, 48, 54 Mbps (IEEE 802.11a/g standard rates)
- BPSK 1/2, BPSK 3/4, QPSK 1/2, QPSK 3/4, 16-QAM 1/2, 16-QAM 3/4, 64-QAM 2/3, 64-QAM 3/4

**Input**: Equalized OFDM symbols
**Output**: Data symbols for the detected frame with encoding metadata

---

### 5. **OFDM Decode MAC** (`ofdm_decode_mac.py`)

**Purpose**: Demodulates and decodes the MAC frame data.

**Functionality**:
- Demodulates data symbols based on detected encoding (BPSK/QPSK/16-QAM/64-QAM)
- Performs frequency-domain deinterleaving
- Applies Viterbi decoding for error correction
- Descrambles the data using the IEEE 802.11 scrambling sequence
- Extracts the MAC frame payload

**Supported Modulations**:
- **BPSK**: Binary Phase Shift Keying (1 bit/symbol)
- **QPSK**: Quadrature Phase Shift Keying (2 bits/symbol)
- **16-QAM**: 16-Quadrature Amplitude Modulation (4 bits/symbol)
- **64-QAM**: 64-Quadrature Amplitude Modulation (6 bits/symbol)

**Input**: Data symbols with encoding information
**Output**: Decoded MAC frame bytes

---

### 6. **OFDM Parse MAC** (`ofdm_parse_mac.py`)

**Purpose**: Parses and analyzes the decoded MAC frame headers.

**Functionality**:
- Parses IEEE 802.11 MAC header fields
- Extracts frame control, duration, addresses, and sequence numbers
- Identifies frame types (management, control, data)
- Validates frame check sequence (FCS/CRC)
- Provides detailed frame analysis for debugging

**Frame Information Extracted**:
- Frame type and subtype
- Source, destination, and BSSID addresses
- Sequence numbers
- Frame duration
- CRC validation status

**Input**: Raw MAC frame bytes
**Output**: Same frames forwarded with parsed header information

---

## Signal Processing Flow

### 1. **Frame Detection Phase**
```
Raw IQ → Autocorrelation → Threshold Detection → Frame Start Tags
```

### 2. **Synchronization Phase**  
```
Tagged Signal → Long Preamble Detection → CFO Estimation → Fine Timing
```

### 3. **OFDM Demodulation Phase**
```
Time Domain → FFT → Pilot Extraction → Channel Estimation → Equalization
```

### 4. **Signal Field Decoding Phase**
```
SIGNAL Symbol → BPSK Demod → Deinterleave → Viterbi Decode → Rate/Length
```

### 5. **Data Decoding Phase**
```
Data Symbols → QAM Demod → Deinterleave → Viterbi Decode → Descramble → MAC Frame
```

### 6. **MAC Processing Phase**
```
MAC Bytes → Header Parse → CRC Check → Frame Analysis → Packet Output
```

## File Structure

```
proyecto/
├── projeto.py                     # Main GNU Radio flowgraph (original with Pluto SDR)
├── test_with_samples.py           # Test flowgraph for baseband file input
├── capture_wifi_pcap.py           # Packet capture utility for Wireshark
├── captured_wifi_packets.pcap     # Example captured WiFi packets
├── sample_capture.pcap            # Sample packet capture
│
├── gr-mywifi/                     # Custom GNU Radio module
│   ├── python/mywifi/
│   │   ├── ofdm_sync_short.py     # Frame detection block
│   │   ├── ofdm_sync_long.py      # Fine synchronization block  
│   │   ├── ofdm_equalize_symbols.py # OFDM equalization block
│   │   ├── ofdm_decode_signal.py  # SIGNAL field decoder block
│   │   ├── ofdm_decode_mac.py     # MAC frame decoder block
│   │   └── ofdm_parse_mac.py      # MAC header parser block
│   │
│   └── grc/                       # GNU Radio Companion block definitions
│       ├── mywifi_ofdm_sync_short.block.yml
│       ├── mywifi_ofdm_sync_long.block.yml
│       ├── mywifi_ofdm_equalize_symbols.block.yml
│       ├── mywifi_ofdm_decode_signal.block.yml
│       ├── mywifi_ofdm_decode_mac.block.yml
│       └── mywifi_ofdm_parse_mac.block.yml
│
└── Wifi_Project_Baseband_recordings/ # Sample WiFi recordings
    ├── Sample1_20MHz_Channel36.bin    # 5 GHz recording
    ├── Sample2_20MHz_Channel6.bin     # 2.4 GHz recording  
    └── Sample3_20MHz_Channel100.bin   # 5 GHz recording
```

## Usage Instructions

### 1. **Testing with Sample Files**
```bash
# Process baseband recordings and capture packets
python3 capture_wifi_pcap.py output.pcap &
python3 test_with_samples.py --sample-file ./Wifi_Project_Baseband_recordings/Sample2_20MHz_Channel6.bin
```

### 2. **Live Reception with SDR**
```bash
# Use original flowgraph with Pluto SDR
python3 capture_wifi_pcap.py live_capture.pcap &
python3 projeto.py
```

### 3. **Analyzing Captured Packets**
```bash
# Open in Wireshark
wireshark captured_wifi_packets.pcap

# Or analyze with command-line tools
tcpdump -r captured_wifi_packets.pcap -n
```

## Performance Characteristics

### **Tested Configurations**:
- ✅ **Sample 1**: Channel 36 (5 GHz) - Multiple frame types detected
- ✅ **Sample 2**: Channel 6 (2.4 GHz) - **Packets successfully captured**
- ✅ **Sample 3**: Channel 100 (5 GHz) - Frame processing working

### **Supported Features**:
- All standard IEEE 802.11a/g data rates (6-54 Mbps)
- BPSK, QPSK, 16-QAM, and 64-QAM demodulation  
- Robust frame detection and synchronization
- Real-time packet capture and PCAP output
- Wireshark-compatible packet format

### **Current Limitations**:
- Simplified Viterbi decoder (hard-decision decoding)
- Limited to 20 MHz bandwidth (IEEE 802.11a/g)
- No support for 802.11n/ac features (MIMO, wider bandwidths)
- Symbol count limited for very long frames

## Technical Notes

### **Signal Processing Parameters**:
- **Sample Rate**: 20 MHz (configurable)
- **FFT Size**: 64 points
- **Cyclic Prefix**: 16 samples
- **Subcarriers**: 52 total (48 data + 4 pilots)

### **Frame Detection Sensitivity**:
- Correlation threshold optimized for SNR > 10 dB
- Plateau detection reduces false positives
- Automatic gain control recommended for varying signal levels

### **Output Format**:
- PCAP files use 802.11 radiotap header format
- Compatible with Wireshark and other network analysis tools
- Network socket output on port 12345 for real-time monitoring

## Future Enhancements

1. **Improved Viterbi Decoding**: Implement soft-decision Viterbi decoder
2. **802.11n Support**: Add MIMO and 40 MHz bandwidth support  
3. **Better Error Handling**: Enhanced CRC validation and error recovery
4. **Performance Optimization**: GPU acceleration for real-time processing
5. **Advanced Features**: Support for 802.11ac/ax protocols

---

**Project Status**: ✅ **Fully Functional IEEE 802.11 OFDM Receiver**

Successfully captures and decodes real WiFi packets from baseband recordings with support for all standard modulation schemes and data rates.
