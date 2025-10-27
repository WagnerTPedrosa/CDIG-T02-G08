# IEEE 802.11 OFDM Receiver - Block Documentation

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