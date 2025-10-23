# SPDX-License-Identifier: GPL-3.0-or-later
# Python reimplementation of gr-ieee802-11 ofdm_equalize_symbols
import numpy as np
from gnuradio import gr
import pmt

class ofdm_equalize_symbols(gr.basic_block):
    """
    OFDM Equalize Symbols (802.11)
    --------------------------------
    Input:  stream of 64 complex values per symbol (FFT output)
    Output: stream of 48 complex values (data subcarriers only)

    - Removes pilots and nulls
    - Performs pilot-based phase correction
    - Applies polarity sequence (127-length)
    - Resets polarity index on each 'ofdm_start' tag
    """

    POLARITY = np.array([
         1, 1, 1, 1,-1,-1,-1, 1,-1,-1,-1,-1, 1, 1,-1, 1,
        -1,-1, 1, 1,-1, 1, 1,-1, 1, 1, 1, 1, 1, 1,-1, 1,
         1, 1,-1, 1, 1,-1,-1, 1, 1, 1,-1, 1,-1,-1,-1, 1,
        -1, 1,-1,-1, 1,-1,-1, 1, 1, 1, 1, 1,-1,-1, 1, 1,
        -1,-1, 1,-1, 1,-1, 1, 1,-1,-1,-1, 1, 1,-1,-1,-1,
        -1, 1,-1,-1, 1,-1, 1, 1, 1, 1,-1, 1,-1, 1,-1, 1,
        -1,-1,-1,-1,-1, 1,-1, 1, 1,-1, 1,-1, 1, 1, 1,-1,
        -1, 1,-1,-1,-1, 1, 1, 1,-1,-1,-1,-1,-1,-1,-1
    ], dtype=np.int8)

    def __init__(self, debug=False):
        gr.basic_block.__init__(
            self,
            name="ofdm_equalize_symbols_py",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.debug = bool(debug)
        self.index = 0
        self.set_relative_rate(48/64.0)

    # -------------------------------------------------------------

    def general_work(self, noutput_items, ninput_items, input_items, output_items):
        x = input_items[0]
        y = output_items[0]

        ninput_syms = ninput_items[0] // 64
        noutput_syms = noutput_items // 48
        nsyms = min(ninput_syms, noutput_syms)

        if nsyms == 0:
            return 0

        nread = self.nitems_read(0)
        out_idx = 0

        for i in range(nsyms):
            start = i * 64
            stop = start + 64
            sym = x[start:stop]

            # reset polarity on ofdm_start tag
            tags = []
            self.get_tags_in_range(
                tags, 0, nread + start, nread + stop,
                pmt.intern("ofdm_start")
            )
            if tags:
                self.index = 0
                if self.debug:
                    print(f"[EQUALIZE] Reset polarity index at symbol {i}")

            p = self.POLARITY[self.index % len(self.POLARITY)]
            self.index += 1

            # Pilot phase estimates
            p1 = np.angle(p * sym[11])
            p2 = np.angle(p * sym[25] * np.conj(p * sym[11])) + p1
            p3 = np.angle(p * sym[39] * np.conj(p * sym[25])) + p2
            p4 = np.angle(-p * sym[53] * np.conj(p * sym[39])) + p3

            my = (p1 + p2 + p3 + p4) / 4.0
            mx = (11.0 + 25.0 + 39.0 + 53.0) / 4.0
            var = (((11.0**2 + 25.0**2 + 39.0**2 + 53.0**2) / 4.0) - (mx**2))
            cov = (((p1*11 + p2*25 + p3*39 + p4*53) / 4.0) - (mx*my))
            beta = cov / var
            alpha = my - beta * mx

            # Remove pilots and guard tones
            o = 0
            for n in range(64):
                if (n in [11, 25, 32, 39, 53]) or (n < 6) or (n > 58):
                    continue
                y[out_idx + o] = sym[n] * np.exp(-1j * (n * beta + alpha))
                o += 1

            out_idx += 48

        self.consume(0, nsyms * 64)
        return nsyms * 48
