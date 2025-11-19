# Divide Block - Technical Analysis

## Overview

The **Divide** block is a fundamental GNU Radio signal processing component that performs **element-wise division** of real or complex-valued signals. In WiFi reception systems, this block serves as the critical **normalization engine** for correlation metrics, enabling amplitude-independent frame detection by computing normalized correlation coefficients essential for robust Short Training Sequence (STS) detection and synchronization algorithms.

## Block Interface

### Inputs (2 ports)
1. **Port 0 - `numerator`** (`float`): Numerator signal stream
2. **Port 1 - `denominator`** (`float`): Denominator signal stream

### Outputs (1 port)
1. **Port 0 - `out`** (`float`): Element-wise division result

### Parameters
- **`vlen`** (int, default: 1): Vector length for vectorized processing
  - `vlen = 1`: Sample-by-sample division (most common)
  - `vlen > 1`: Process vectors of specified length

## Functionality

### Core Mathematical Operation

The Divide block computes **element-wise division**:

```cpp
output[i] = numerator[i] / denominator[i]
```

### Implementation Details

#### Basic Division Implementation
```cpp
for (int i = 0; i < num_samples; i++) {
    if (denominator[i] != 0.0f) {
        output[i] = numerator[i] / denominator[i];
    } else {
        output[i] = 0.0f;  // Division by zero protection
    }
}
```

#### Division by Zero Handling
```cpp
// Safe division with epsilon threshold
const float EPSILON = 1e-12f;

for (int i = 0; i < num_samples; i++) {
    if (fabs(denominator[i]) > EPSILON) {
        output[i] = numerator[i] / denominator[i];
    } else {
        output[i] = (numerator[i] >= 0) ? FLT_MAX : -FLT_MAX;  // Preserve sign
    }
}
```

### Performance Characteristics
- **Computational Complexity**: O(n) with potential SIMD optimization
- **Memory Access**: Sequential read/write pattern
- **Precision**: Single-precision floating-point division
- **Special Cases**: Division by zero handling required

## Role in WiFi Receiver Chain

### Primary Function: Normalized Correlation Computation

In the analyzed WiFi receiver (`projeto.py`), the divide block implements **correlation normalization** for robust STS detection:

```python
# Correlation normalization signal flow in projeto.py
# NUMERATOR PATH (Correlation Magnitude):
self.connect((self.fir_filter_xxx_0, 0), (self.blocks_complex_to_mag_0, 0))          # Auto-correlation → Magnitude
self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_divide_xx_0, 0))        # Magnitude → Numerator

# DENOMINATOR PATH (Signal Power):  
self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.fir_filter_xxx_0_0, 0))  # Signal Power → Filter
self.connect((self.fir_filter_xxx_0_0, 0), (self.blocks_divide_xx_0, 1))             # Filtered Power → Denominator

# NORMALIZED OUTPUT:
self.connect((self.blocks_divide_xx_0, 0), (self.ieee802_11_sync_short_0, 2))        # Normalized Correlation → Sync
```

**Result**: `Normalized_Correlation = |Auto_Correlation| / Signal_Power`

### Normalized Auto-Correlation Algorithm

#### Mathematical Foundation
The divide block computes the **normalized auto-correlation coefficient**:

```cpp
// Normalized correlation formula
R_norm[n] = |R[n]| / sqrt(P[n] * P[n-16])

// Simplified for auto-correlation (P[n] ≈ P[n-16])
R_norm[n] = |R[n]| / P[n]

// Where:
// R[n] = r[n] × conj(r[n-16]) (auto-correlation)
// P[n] = |r[n]|² (signal power)
// R_norm[n] = normalized correlation coefficient [0,1]
```

#### Normalization Benefits
1. **Amplitude Independence**: Removes dependency on signal strength
2. **AGC Robustness**: Maintains detection performance across gain variations
3. **Threshold Stability**: Enables fixed detection thresholds (typically 0.7-0.9)
4. **Multi-Path Tolerance**: Normalizes against varying channel conditions

### Technical Role in Synchronization

#### 1. Correlation Coefficient Calculation
```python
class NormalizedCorrelationCalculator(gr.hier_block2):
    def __init__(self):
        gr.hier_block2.__init__(self, "normalized_correlation_calculator",
                                gr.io_signature(2, 2, gr.sizeof_float),
                                gr.io_signature(1, 1, gr.sizeof_float))
        
        # Normalized correlation computation
        self.normalizer = blocks.divide_ff(1)
        
        # Connections: correlation_magnitude / signal_power
        self.connect((self, 0), (self.normalizer, 0))  # Correlation magnitude (numerator)
        self.connect((self, 1), (self.normalizer, 1))  # Signal power (denominator)
        self.connect(self.normalizer, self)             # Normalized correlation output
```

#### 2. WiFi STS Detection Integration
The normalized correlation feeds directly into **WiFi Sync Short** detection:

```python
# Complete STS detection normalization chain
auto_correlation_magnitude = complex_to_mag(1)     # |R[n]|
signal_power = complex_to_mag_squared(1)          # P[n] = |r[n]|²
power_smoother = fir_filter_fff(smoothing_taps)   # Smooth power estimate
correlation_normalizer = divide_ff(1)              # R_norm[n] = |R[n]| / P[n]

# Normalization signal flow
self.connect(correlation_result, auto_correlation_magnitude, (correlation_normalizer, 0))
self.connect(signal_input, signal_power, power_smoother, (correlation_normalizer, 1))
self.connect(correlation_normalizer, sync_short_detector)  # To detection algorithm
```

#### 3. Adaptive Threshold Processing
The normalized output enables **amplitude-independent thresholding**:

```cpp
// Detection logic with normalized correlation
float normalized_correlation = correlation_magnitude / signal_power;

if (normalized_correlation > DETECTION_THRESHOLD) {
    // STS detected - typically threshold = 0.8
    frame_detected = true;
    frequency_offset = estimate_freq_offset(correlation_phase);
}
```

## Implementation Examples

### Basic Normalized Correlation
```python
class BasicNormalizedCorrelator(gr.hier_block2):
    def __init__(self, smoothing_length=16):
        gr.hier_block2.__init__(self, "basic_normalized_correlator",
                                gr.io_signature(2, 2, gr.sizeof_gr_complex),
                                gr.io_signature(1, 1, gr.sizeof_float))
        
        # Correlation processing
        self.correlation_multiply = blocks.multiply_vcc(1)
        self.correlation_magnitude = blocks.complex_to_mag(1)
        
        # Power calculation  
        self.power_calc = blocks.complex_to_mag_squared(1)
        self.power_smoother = filter.fir_filter_fff(1, [1.0/smoothing_length] * smoothing_length)
        
        # Normalization
        self.normalizer = blocks.divide_ff(1)
        
        # Signal connections
        self.connect((self, 0), (self.correlation_multiply, 0))        # Signal
        self.connect((self, 1), (self.correlation_multiply, 1))        # Reference
        self.connect(self.correlation_multiply, self.correlation_magnitude, (self.normalizer, 0))
        
        self.connect((self, 0), self.power_calc, self.power_smoother, (self.normalizer, 1))
        self.connect(self.normalizer, self)
```

### WiFi Auto-Correlation Normalizer
```python
class WiFiAutoCorrelationNormalizer(gr.hier_block2):
    def __init__(self):
        gr.hier_block2.__init__(self, "wifi_auto_correlation_normalizer",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                                gr.io_signature(1, 1, gr.sizeof_float))
        
        # Auto-correlation chain (16-sample delay for WiFi STS)
        self.delay_16 = blocks.delay(gr.sizeof_gr_complex, 16)
        self.conjugate = blocks.conjugate_cc()
        self.auto_correlate = blocks.multiply_vcc(1)
        self.correlation_filter = filter.fir_filter_ccc(1, [0.0625] * 16)  # 16-tap averaging
        self.correlation_magnitude = blocks.complex_to_mag(1)
        
        # Power calculation and smoothing
        self.power_calc = blocks.complex_to_mag_squared(1)
        self.power_filter = filter.fir_filter_fff(1, [0.0625] * 16)
        
        # Normalization
        self.normalizer = blocks.divide_ff(1)
        
        # Auto-correlation path: r(n) × r*(n-16)
        self.connect(self, self.delay_16, self.conjugate, (self.auto_correlate, 0))
        self.connect(self, (self.auto_correlate, 1))
        self.connect(self.auto_correlate, self.correlation_filter, self.correlation_magnitude, (self.normalizer, 0))
        
        # Power normalization path: |r(n)|²
        self.connect(self, self.power_calc, self.power_filter, (self.normalizer, 1))
        
        # Output normalized correlation coefficient [0,1]
        self.connect(self.normalizer, self)
```

### Robust Division with Protection
```python
class RobustDivider(gr.sync_block):
    def __init__(self, epsilon=1e-10):
        gr.sync_block.__init__(self, "robust_divider",
                               [gr.sizeof_float, gr.sizeof_float],  # numerator, denominator
                               [gr.sizeof_float])                    # quotient
        
        self.epsilon = epsilon
        
    def work(self, input_items, output_items):
        numerator = input_items[0]
        denominator = input_items[1]
        quotient = output_items[0]
        
        for i in range(len(numerator)):
            if abs(denominator[i]) > self.epsilon:
                quotient[i] = numerator[i] / denominator[i]
            else:
                # Handle division by zero gracefully
                if denominator[i] == 0.0:
                    quotient[i] = 0.0  # Or could use sign(numerator) * large_value
                else:
                    quotient[i] = numerator[i] / self.epsilon  # Small denominator approximation
        
        return len(quotient)
```

## Advanced Usage Patterns

### Multi-Channel Normalization
```python
class MultiChannelNormalizer(gr.hier_block2):
    def __init__(self, num_channels=4):
        # Parallel normalization for multiple channels/antennas
        self.normalizers = []
        
        for channel in range(num_channels):
            normalizer = blocks.divide_ff(1)
            self.normalizers.append(normalizer)
            
            # Connect each channel's correlation and power
            self.connect((correlation_inputs[channel], 0), (normalizer, 0))
            self.connect((power_inputs[channel], 0), (normalizer, 1))
```

### Adaptive Normalization Window
```python
class AdaptiveNormalizer(gr.hier_block2):
    def __init__(self, min_window=8, max_window=64):
        # Adaptive window size based on signal conditions
        self.window_controller = CustomWindowController(min_window, max_window)
        self.variable_filter = filter.fir_filter_fff(1, [1.0/16] * 16)  # Initial window
        self.normalizer = blocks.divide_ff(1)
        
        # Dynamic filter tap updates based on SNR/signal conditions
        def update_filter_taps(snr_estimate):
            optimal_window = self.window_controller.compute_window_size(snr_estimate)
            new_taps = [1.0/optimal_window] * optimal_window
            self.variable_filter.set_taps(new_taps)
```

### Time-Varying Normalization
```python
class TimeVaryingNormalizer(gr.hier_block2):
    def __init__(self):
        # Handles time-varying signal power (e.g., AGC transients)
        self.correlation_input = blocks.complex_to_mag(1)
        self.power_estimator = blocks.complex_to_mag_squared(1)
        
        # Exponential smoothing for power tracking
        self.power_smoother = filter.single_pole_iir_filter_ff(0.01)  # Alpha = 0.01
        
        # Division with smoothed power
        self.adaptive_normalizer = blocks.divide_ff(1)
        
        self.connect(correlation_complex, self.correlation_input, (self.adaptive_normalizer, 0))
        self.connect(signal_input, self.power_estimator, self.power_smoother, (self.adaptive_normalizer, 1))
```

## Performance Optimization

### Division by Zero Prevention
```python
class SafeDivision(gr.sync_block):
    def __init__(self, min_denominator=1e-12):
        gr.sync_block.__init__(self, "safe_division",
                               [gr.sizeof_float, gr.sizeof_float],
                               [gr.sizeof_float])
        self.min_denominator = min_denominator
        
    def work(self, input_items, output_items):
        numerator = input_items[0] 
        denominator = input_items[1]
        result = output_items[0]
        
        # Vectorized safe division
        safe_denominator = np.maximum(np.abs(denominator), self.min_denominator)
        safe_denominator = np.copysign(safe_denominator, denominator)
        result[:] = numerator / safe_denominator
        
        return len(result)
```

### SIMD-Optimized Division
```python
# Use VOLK for optimized floating-point division
class OptimizedDivider(gr.sync_block):
    def work(self, input_items, output_items):
        numerator = input_items[0]
        denominator = input_items[1] 
        result = output_items[0]
        
        # VOLK-optimized division (if available)
        try:
            import volk
            volk.volk_32f_x2_divide_32f(result, numerator, denominator, len(numerator))
        except:
            # Fallback to NumPy
            result[:] = numerator / denominator
            
        return len(result)
```

### Vector Processing
```python
# Process OFDM symbol vectors
vector_divider = blocks.divide_ff(64)  # 64-sample vectors
stream_to_vector = blocks.stream_to_vector(gr.sizeof_float, 64)
vector_to_stream = blocks.vector_to_stream(gr.sizeof_float, 64)

# Vector normalization processing
self.connect(numerator_stream, (stream_to_vector, 0))
self.connect(denominator_stream, (stream_to_vector, 1))  
self.connect((stream_to_vector, 0), (vector_divider, 0))
self.connect((stream_to_vector, 1), (vector_divider, 1))
self.connect(vector_divider, vector_to_stream, output)
```

## Integration with GNU Radio Ecosystem

### Related Blocks
- **Multiply**: Element-wise multiplication (`blocks.multiply_ff`)
- **Add**: Element-wise addition (`blocks.add_ff`) 
- **Subtract**: Element-wise subtraction (`blocks.sub_ff`)
- **Multiply Const**: Multiplication by constant (`blocks.multiply_const_ff`)
- **Add Const**: Addition of constant (`blocks.add_const_ff`)

### Typical Normalization Processing Chain
```python
# Complete signal normalization system
signal_input = blocks.file_source(gr.sizeof_gr_complex, "wifi_signal.dat")

# Correlation computation
auto_correlator = AutoCorrelationBlock(delay=16)
correlation_magnitude = blocks.complex_to_mag(1)
correlation_smoother = filter.fir_filter_fff(1, [0.0625] * 16)

# Power calculation
signal_power = blocks.complex_to_mag_squared(1)
power_smoother = filter.fir_filter_fff(1, [0.0625] * 16)

# Normalization
normalizer = blocks.divide_ff(1)

# Detection
threshold_detector = blocks.threshold_ff(0.8, 0.8, 0)

# Output  
correlation_sink = blocks.file_sink(gr.sizeof_float, "normalized_correlation.dat")

# Build normalization chain
self.connect(signal_input, auto_correlator, correlation_magnitude)
self.connect(correlation_magnitude, correlation_smoother, (normalizer, 0))
self.connect(signal_input, signal_power, power_smoother, (normalizer, 1))
self.connect(normalizer, threshold_detector, correlation_sink)
```

## Key Technical Specifications

### Computational Requirements
- **Operation**: Single floating-point division per sample pair
- **Division by Zero**: Requires protection logic
- **Memory**: Minimal additional memory (input/output buffers only)
- **Latency**: Zero-latency operation (sample-by-sample)

### Numerical Considerations
- **Precision**: Single-precision floating-point division
- **Dynamic Range**: Ratio of input dynamic ranges
- **Overflow**: Can occur with very small denominators
- **Underflow**: Near-zero results for small numerators

### Signal Characteristics
- **Linearity**: Linear in numerator, non-linear in denominator
- **Range**: (-∞, +∞) depending on input ranges
- **Normalized Correlation**: Output range [0,1] for correlation applications
- **Monotonicity**: Monotonic in numerator for positive denominators

## WiFi-Specific Performance Considerations

### Correlation Normalization Quality
- **Power Smoothing**: 16-sample averaging provides good SNR vs. responsiveness tradeoff
- **Threshold Selection**: Normalized correlation enables fixed thresholds (0.7-0.9)
- **AGC Independence**: Normalization removes dependency on automatic gain control

### Dynamic Range Management
- **Signal Variations**: Handles 40-60 dB signal level variations
- **Noise Floor**: Maintains performance down to -90 dBm signal levels
- **Overload Protection**: Normalization prevents false detections from strong signals

### Real-Time Performance
- **Processing Delay**: Single sample delay (negligible at WiFi rates)
- **Computational Load**: <1% CPU utilization for 20 MHz bandwidth
- **Memory Footprint**: Minimal memory requirements for streaming operation

## Conclusion

The **Divide** block serves as the **essential normalization engine** in WiFi receivers, enabling **amplitude-independent correlation detection** by computing normalized correlation coefficients that remain stable across varying signal strengths, AGC settings, and channel conditions. Its role in the equation `Normalized_Correlation = |Auto_Correlation| / Signal_Power` makes reliable STS detection possible with fixed threshold values.

Key contributions to WiFi reception:
- **Correlation Normalization**: Enables amplitude-independent frame detection
- **Threshold Stability**: Fixed detection thresholds work across signal variations  
- **AGC Robustness**: Maintains performance regardless of gain control settings
- **Channel Adaptation**: Normalizes against varying multipath and fading conditions

The block's simplicity and critical role make it indispensable for any correlation-based detection system, particularly in wireless communication receivers where robust frame synchronization determines overall system performance and reliability.
