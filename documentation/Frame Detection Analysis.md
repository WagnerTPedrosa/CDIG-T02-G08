# Frame Detection

## Autocorrelation calculation:
The frame detection algorithm is based on calculating the autocorrelation value, a[n], of the incoming sample stream s with a lag of 16, summed over an adjustable window $N_{\text{win}}$. This calculation allows the system to detect the beginning of an OFDM frame and to estimate the frequency offset between the transmittor and the receiver.

$a[n] = \sum_{k=0}^{N_{\text{win}} - 1} s[n+k]\, \overline{s[n+k+16]}$.

**Block Implementation:** The calculation of the normalized autocorrelation coefficient, 𝑐[𝑛] (which incorporates 𝑎[𝑛]), is distributed across eight blocks.  
**Block Type:** These operations are realized using standard GNU Radio blocks;  
**Performance Requirement:** All eight involved blocks utilize the VOLK library, since frame detection must process the incoming stream from the USRP at full speed.

## Power calculation:
To ensure the autocorrelation coefficient is independent of the absolute signal level, the autocorrelation 𝑎[𝑛] is normalized by the average power, 𝑝[𝑛]:

$p[n] = \sum_{k=0}^{N_{\text{win}} - 1} s[n+k]\, s^{\ast}[n+k]$.

The normalized autocorrelation coefficient is given by $c[n] = \frac{|a[n]|}{p[n]}$.

**Block implementation:** The power calculation is integrated into the same set of eight blocks that perform the normalized autocorrelation computation.

## Effect of varying $N_{\text{win}}$
- The moving average acts as a low-pass filter, smoothing the signal;
- This filtering improves the robustness of frame detection in noisy environments;
- Changing $N_{\text{win}}$ directly affects the shape and clarity of the autocorrelation function c[n]. The goal is to obtain a clear constant region of high autocorrelation coefficients during the short training sequence. With $N_{\text{win}}$ = 48, this steady region becomes well-defined, allowing the receiver to detect a frame when three consecutive samples of c[n] exceed a configurable threshold.