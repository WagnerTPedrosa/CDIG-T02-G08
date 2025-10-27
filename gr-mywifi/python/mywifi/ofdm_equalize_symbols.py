# SPDX-License-Identifier: GPL-3.0-or-later
# Python implementation of OFDM Symbol Equalizer
from gnuradio import gr
import pmt
import numpy as np

class ofdm_equalize_symbols(gr.basic_block):
    """
    Simplified OFDM Symbol Equalizer
    Input: Complex stream (64 samples per symbol from FFT)
    Output: Complex stream (48 data subcarriers per symbol)
    """

    def __init__(self, debug=False):
        gr.basic_block.__init__(
            self,
            name="ofdm_equalize_symbols_py",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.debug = bool(debug)
        self.buffer = np.array([], dtype=np.complex64)
        self.symbol_size = 64
        self.output_size = 48
        # Set relative rate
        self.set_relative_rate(self.output_size / float(self.symbol_size))

    def general_work(self, input_items, output_items):
        x = input_items[0]
        y = output_items[0]
        
        nin = len(x)
        nout = len(y)
        
        if nin == 0 or nout == 0:
            return 0
        
        # Add new samples to buffer
        self.buffer = np.concatenate([self.buffer, x])
        
        # Calculate how many complete symbols we have
        nsyms_available = len(self.buffer) // self.symbol_size
        max_output_syms = nout // self.output_size
        nsyms = min(nsyms_available, max_output_syms)
        
        if nsyms == 0:
            # Need more input samples
            self.consume(0, nin)
            return 0

        out_idx = 0
        
        for i in range(nsyms):
            start = i * self.symbol_size
            stop = start + self.symbol_size
            sym = self.buffer[start:stop]

            # Simple equalization: just extract data subcarriers
            # In 802.11, data subcarriers are at indices 6-31 and 33-58 (avoiding pilots and DC)
            data_indices = list(range(6, 32)) + list(range(33, 59))
            
            # Extract data subcarriers (48 total)
            o = 0
            for idx in data_indices[:self.output_size]:
                if out_idx + o < nout:
                    y[out_idx + o] = sym[idx]
                    o += 1
                else:
                    break

            out_idx += o
            
            if self.debug and i == 0:
                print(f"[EQUALIZER] Symbol {i}: extracted {o} data subcarriers")

        # Remove processed symbols from buffer
        consumed_samples = nsyms * self.symbol_size
        self.buffer = self.buffer[consumed_samples:]
        
        # Consume all input samples
        self.consume(0, nin)
        
        if self.debug and out_idx > 0:
            print(f"[EQUALIZER] Produced {out_idx} samples from {nsyms} symbols")
        
        return out_idx