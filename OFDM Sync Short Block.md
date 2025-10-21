#  OFDM Sync Short block

**Purpose:** To control the flow of samples in the processing pipeline based on the detection of the frame preamble, determining when an incoming OFDM frame starts;  
**Input:** Raw complex baseband samples from the USRP and the normalized autocorrelation coefficient c[n];  
**Main Fucntions:**
- Frame detection: Detects the start of the STS by looking for a region where c[n] exceeds a configurable threshold for severeal consecutive samples;
- Sample gating: Once a frame start is detected, it opens a valve and passes a fixed number of samples to the downstream blocks in the receiver chain.

## Meaning of the Thresholds:  
The threshold determines the necessary minimum level of confidence for a successful detection of the short preamble.
- When the incoming signal is just noise: c[n] ≈ 0;
- When a short training sequence arrives, c[n] forms a high plateau (≈ 1).  

So the threshold is used as a cut-off, only when 𝑐[𝑛] > thresholdf or several consecutive samples is a frame considered to have started.

### Effect of changing the tresholds:
- Decreasing: More sensitive to small peaks → detects weaker frames, but also more noise.
- Increasing: More selective (reduce the rate of false positives) → ignores noise, but may fail when the SNR is low.

### Limitations:
While simple and effective, this detection method has some weaknesses:
- **Fixed window and threshold:** not adaptive to noise or varying SNR;
- **Multiple frames arriving close together:** If a second frame starts soon after the first, it might not be detected because the valve is still open and streaming samples from the previous frame;
- **Timing uncertainty:** The detected start position depends on the threshold and $N_{\text{win}}$;​
- **Frame Size Limitation:** The receiver's ability to decode frames is limited to a configurable number of OFDM symbols.

### ⚠️ Failure Case:
→ The receiver misses Clear To Send Frames.

Why?: The CTS frame typically follows immediately after a Request To Send frame. While the receiver is still processing the fixed number of samples corresponding to the detected RTS frame, the OFDM Sync Short block remains busy (“valve open”) and does not monitor for new preambles.
