# WiFi Frame Equalizer Block - Technical Analysis

## Overview

The **WiFi Frame Equalizer** block is a sophisticated OFDM processing component in the GNU Radio IEEE 802.11 implementation that performs **channel equalization**, **signal field decoding**, and **constellation demapping** for WiFi frames. It operates as the core signal processing engine in the receiver chain, converting frequency-domain OFDM symbols into decoded bits while compensating for channel distortions and tracking residual frequency offsets.

## Block Interface

### Inputs (1 port)
1. **Port 0 - `in`** (`complex[64]`): FFT output symbols from frequency domain processing

### Outputs (2 ports)
1. **Port 0 - `out`** (`uint8[48]`): Demapped soft bits for data subcarriers
2. **Port 1 - `symbols`** (message): Raw equalized symbols for external processing

### Parameters
- **`algo`** (Equalizer enum): Channel equalization algorithm selection
  - **`LS`** (Least Squares) - Default, robust for most conditions
  - **`LMS`** (Least Mean Squares) - Adaptive algorithm
  - **`COMB`** (Comb filter) - Simple pilot-based equalization
  - **`STA`** (Static) - Fixed channel response
- **`freq`** (double, default: 5.89e9): Center frequency in Hz for frequency offset correction
- **`bw`** (double, default: 10e6): Bandwidth in Hz for scaling calculations
- **`log`** (bool, default: false): Enable logging output
- **`debug`** (bool, default: false): Enable debug information

## Functionality

### Core Processing Pipeline

The WiFi Frame Equalizer implements a **comprehensive OFDM symbol processing pipeline**:

#### 1. Frame Detection and Initialization
- **Tag Processing**: Detects `wifi_start` tags from upstream synchronization blocks
- **Parameter Extraction**: Extracts frequency offset and initializes frame processing
- **State Reset**: Prepares equalizer state for new frame processing

#### 2. Sampling Offset Compensation
- **Time Domain Correction**: Compensates for residual sampling rate offset
- **Formula**: `symbol[i] *= exp(j * 2π * symbol_idx * 80 * (ε₀ + εᵣ) * (i-32) / 64)`
- **Components**:
  - `ε₀`: Initial sampling offset from sync_long
  - `εᵣ`: Residual offset tracked via pilot tones

#### 3. Pilot Tone Processing
- **Pilot Extraction**: Uses subcarriers 11, 25, 39, 53 (±7, ±21 relative to DC)
- **Phase Tracking**: Calculates residual frequency offset from pilot phase rotation
- **Polarity Sequence**: Applies IEEE 802.11 pilot polarity pattern for data symbols
- **Beta Calculation**: Estimates common phase error from pilot constellation

#### 4. Residual Frequency Offset Correction
- **Phase Correction**: `symbol[i] *= exp(-j * β)` where β is common phase error
- **Adaptive Tracking**: Updates residual offset estimate with α = 0.1 smoothing
- **Pilot Reference**: Maintains previous pilot values for phase difference calculation

#### 5. Channel Equalization
- **Algorithm Selection**: Applies chosen equalization method (LS/LMS/COMB/STA)
- **Channel Estimation**: Updates channel state information (CSI) per symbol
- **Symbol Correction**: Applies frequency-domain channel inverse
- **Constellation Mapping**: Maps equalized symbols to constellation points

#### 6. Signal Field Processing
- **Detection**: Processes symbol #2 (signal field) for frame parameters
- **Deinterleaving**: Applies IEEE 802.11 deinterleaving pattern
- **Viterbi Decoding**: Convolutional decoding of signal field bits
- **Parameter Extraction**: Extracts encoding rate and frame length

### Equalization Algorithms

#### Least Squares (LS) - Default
- **Method**: Uses known preamble symbols to estimate channel
- **Characteristics**: Robust, moderate complexity, good general performance
- **Best For**: Most channel conditions, standard WiFi reception

#### Least Mean Squares (LMS)  
- **Method**: Adaptive algorithm using pilot tones for tracking
- **Characteristics**: Tracks time-varying channels, higher complexity
- **Best For**: Mobile scenarios, rapidly changing channels

#### Comb Filter (COMB)
- **Method**: Interpolates channel response using pilot subcarriers
- **Characteristics**: Low complexity, basic performance
- **Best For**: Static channels, computational constraints

#### Static (STA)
- **Method**: Assumes flat fading channel response
- **Characteristics**: Minimal complexity, limited applicability
- **Best For**: Very short range, minimal multipath

## Technical Details

### Signal Field Decoding

The block implements **complete IEEE 802.11 signal field processing**:

#### Encoding Rate Detection
```cpp
// Rate bits (R1-R4) mapping to data rates
switch (rate_bits) {
    case 11: // 0x0B -> BPSK 1/2 -> 6 Mbps (3 Mbps effective)  
    case 15: // 0x0F -> BPSK 3/4 -> 9 Mbps (4.5 Mbps effective)
    case 10: // 0x0A -> QPSK 1/2 -> 12 Mbps (6 Mbps effective) 
    case 14: // 0x0E -> QPSK 3/4 -> 18 Mbps (9 Mbps effective)
    case 9:  // 0x09 -> 16QAM 1/2 -> 24 Mbps (12 Mbps effective)
    case 13: // 0x0D -> 16QAM 3/4 -> 36 Mbps (18 Mbps effective)  
    case 8:  // 0x08 -> 64QAM 2/3 -> 48 Mbps (24 Mbps effective)
    case 12: // 0x0C -> 64QAM 3/4 -> 54 Mbps (27 Mbps effective)
}
```

#### Frame Length Calculation
```cpp
// Calculate number of OFDM symbols needed
symbols_needed = ceil((SERVICE + 8*LENGTH + TAIL) / bits_per_symbol);
```

### Pilot Tone Tracking

#### IEEE 802.11 Pilot Pattern
- **Positions**: Subcarriers -21, -7, +7, +21 (indices 11, 25, 39, 53)
- **Values**: ±1 based on polarity sequence  
- **Polarity Sequence**: 127-bit pseudorandom sequence defined in standard

#### Phase Error Estimation
```cpp
// Common phase error from pilot constellation
beta = arg(pilot_sum * expected_pilot_sum);

// Residual frequency offset from pilot phase rotation
epsilon_r = arg(conj(prev_pilots) * current_pilots) / (2π * symbol_time);
```

### Channel State Information (CSI)

- **Extraction**: Available through equalizer `get_csi()` method
- **Format**: Complex vector of 64 subcarrier channel estimates
- **Usage**: Provides channel magnitude and phase for each subcarrier
- **Applications**: Channel analysis, adaptive processing, research

### Tag and Message System

#### Output Tags (added to symbol #2)
- **`frame bytes`**: Frame length in bytes from signal field
- **`encoding`**: Modulation and coding scheme index
- **`snr`**: Signal-to-noise ratio estimate from equalizer  
- **`frequency offset`**: Combined frequency offset from sync blocks
- **`beta`**: Common phase error estimate
- **`csi`**: Channel state information vector

#### Message Output
- **Port**: `symbols` (optional message port)
- **Content**: Raw equalized 48-element complex symbol vectors
- **Purpose**: Provides access to constellation points for external processing

## Performance Characteristics

### Computational Complexity
- **Per Symbol**: O(64) for pilot processing + O(48) for equalization
- **Signal Field**: Additional Viterbi decoding O(N) where N = constraint length
- **Equalizer Dependent**: LS < COMB < LMS complexity hierarchy

### Memory Requirements
- **Symbol Storage**: ~512 bytes (64 complex samples)
- **Equalizer State**: Algorithm-dependent (typically <4KB)
- **Decoder State**: Viterbi trellis (~1KB)

### Latency Characteristics
- **Processing Delay**: 2-3 symbols (signal field processing)
- **Equalizer Adaptation**: Algorithm-dependent convergence time
- **Output Streaming**: Real-time symbol-by-symbol processing

## Integration in Receiver Chain

### Upstream Dependencies
- **FFT Block**: Provides 64-element frequency domain symbols
- **Sync Blocks**: Supply timing and frequency offset tags
- **Frame Detection**: Requires accurate `wifi_start` tag timing

### Downstream Connections
- **Decoder Blocks**: Consume soft bit outputs for FEC decoding
- **MAC Processing**: Uses frame parameter tags for packet parsing
- **Analysis Tools**: Can access CSI and symbol messages for research

## Usage Example

```python
# Create WiFi Frame Equalizer with LS algorithm
frame_equalizer = ieee802_11.frame_equalizer(
    algo=ieee802_11.LS,      # Least squares equalization
    freq=5.89e9,            # Center frequency (5.89 GHz)
    bw=10e6,                # Bandwidth (10 MHz)
    log=False,              # Disable logging
    debug=False             # Disable debug
)

# Typical receiver chain connections
self.connect((fft_block, 0), (frame_equalizer, 0))           # FFT symbols input
self.connect((frame_equalizer, 0), (decoder_block, 0))       # Soft bits output
self.msg_connect((frame_equalizer, 'symbols'), (analyzer, 'symbols'))  # Symbol analysis
```

## Advanced Features

### Adaptive Processing
- **Automatic Rate Detection**: Determines modulation scheme from signal field
- **Dynamic Constellation**: Switches constellation based on detected encoding
- **Adaptive Equalization**: LMS algorithm adapts to channel changes

### Robustness Features
- **Parity Check**: Signal field includes parity bit for error detection
- **Pilot Tracking**: Continuous phase and frequency offset compensation
- **SNR Estimation**: Provides quality metrics for link adaptation

### Research Capabilities
- **CSI Export**: Full channel state information for analysis
- **Symbol Streaming**: Raw constellation points for algorithm development
- **Flexible Algorithms**: Multiple equalization approaches for comparison

## Common Applications

1. **WiFi Reception**: Core component in 802.11 a/g/n receiver implementations
2. **Channel Research**: CSI extraction for propagation studies
3. **Algorithm Development**: Testbed for equalization algorithm comparison
4. **Quality Assessment**: SNR and channel quality monitoring
5. **Protocol Analysis**: Frame structure examination and validation

## Key Advantages

- **Algorithm Flexibility**: Multiple equalization methods for different scenarios
- **Complete Processing**: Integrated signal field decoding and frame parsing
- **Performance Monitoring**: Built-in SNR estimation and quality metrics
- **Research Support**: Comprehensive CSI and symbol data export
- **Standards Compliance**: Full IEEE 802.11 signal field processing

This block serves as the **signal processing core** of the WiFi receiver, transforming raw OFDM symbols into clean, decoded bits while providing comprehensive channel information and maintaining synchronization throughout the frame reception process.
