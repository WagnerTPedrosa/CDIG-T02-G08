# OFDM system design parameters:

**Bandwidth**: 20MHz  
**Sub-carrier spacing:** 20 × 10^6 / 64 (FFT size) = 312.5 kHz
**Number of sub-carriers:** 64  
**IFFT/ FFT size:** 64  
**Number of data sub-carriers:** 48  
**Number of pilot sub-carriers:** 4  

**OFDM symbol duration:** 80 samples ÷ 20 × 10^6 = 4μs  
**Sampling rate:** 20 Msps  
**OFDM symbol length (samples):** 80 samples  
**Cyclic prefix length:** 16 samples  

### Frame prefix sequence:
- Short Preamble Sequence:
    - Length: 16 samples;
    - Repetition: 10x;
    - Duration: 16 samples × 10 × 0.05μs/sample = 8μs
    - Function: Frame detection and frequency offset estimation;
- Long Training Sequence: 
    - Length: 64 samples;
    - Repetition: 2.5x;
    - Duration: 64 samples × 2.5 × 0.05μs/sample = 8μs
    - Function: Symbol alignment;

### ❔Why are there unused sub-carriers and where are they located?
The unused subcarriers in the IEEE 802.11a/g/p OFDM system are present and subsequently removed for essential control, synchronization and spectral protection purposes. The transformation from the time domain results in a 64 symbol input vector in the frequency domain. However, only 48 of these subcarriers carry data payload, meaning 16 subcarriers are reserved or removed. The unused subcarriers fall into three categories, corresponding to specific functions in the receiver chain:

1. Pilot Subcarriers (necessary for phase offset correction);
2. DC Subcarrier (hardware consideration);
3. Guard Subcarriers (spectral protection).

The removal of the unused subcarriers takes place in the frequency domain and the block responsible for this function is the OFDM Equalize Symbols block.
