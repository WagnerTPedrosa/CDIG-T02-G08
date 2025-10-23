# SPDX-License-Identifier: GPL-3.0-or-later
# Python reimplementation of gr-ieee802-11 ofdm_decode_signal
import numpy as np
from gnuradio import gr
import pmt
import math
from commpy.channelcoding import Trellis, viterbi_decode

class ofdm_decode_signal(gr.basic_block):
    """
    OFDM Decode SIGNAL field (802.11a/g)
    ------------------------------------
    Input:  stream of 48 complex values per symbol (equalized)
    Output: stream of 48 complex values (forwarded)
      - Detects 'ofdm_start' tag
      - Demaps, deinterleaves, and convolutionally decodes SIGNAL field
      - Parses rate and length bits, sets number of symbols to copy
      - Emits 'ofdm_start' tag with payload (length, encoding)
    """

    # Interleaver pattern
    INTER = np.array([
        0,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,
        1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,46,
        2,5,8,11,14,17,20,23,26,29,32,35,38,41,44,47
    ], dtype=np.int32)

    def __init__(self, debug=False):
        gr.basic_block.__init__(
            self,
            name="ofdm_decode_signal_py",
            in_sig=[np.complex64],
            out_sig=[np.complex64],
        )
        self.debug = bool(debug)
        self.d_copy_symbols = 0
        self.d_len = 0
        self.d_encoding = 0
        self.bits = np.zeros(48)
        self.decoded_bits = np.zeros(24, dtype=int)
        self.set_relative_rate(1)
        self.set_tag_propagation_policy(gr.TPP_DONT)

        # IEEE 802.11 rate table: (r_value, encoding, bits_per_symbol)
        self.rate_table = {
            11: (0, 24),   # 3 Mbps
            15: (1, 36),   # 4.5 Mbps
            10: (2, 48),   # 6 Mbps
            14: (3, 72),   # 9 Mbps
             9: (4, 96),   # 12 Mbps
            13: (5, 144),  # 18 Mbps
             8: (6, 192),  # 24 Mbps
            12: (7, 216)   # 27 Mbps
        }

    # -------------------------------------------------------------

    def general_work(self, noutput_items, ninput_items, input_items, output_items):
        x = input_items[0]
        y = output_items[0]

        nsyms_in = ninput_items[0] // 48
        nsyms_out = noutput_items // 48
        nsyms = min(nsyms_in, nsyms_out)

        nread = self.nitems_read(0)
        o = 0
        i = 0

        for s in range(nsyms):
            start = s * 48
            stop = start + 48
            tags = []
            self.get_tags_in_range(tags, 0, nread + start, nread + stop,
                                   pmt.intern("ofdm_start"))

            if tags:
                # ---------- SIGNAL FIELD DETECTION ----------
                if self.debug:
                    print("[DECODE_SIGNAL] Detected ofdm_start tag")

                # Demap (BPSK: bit = -real(x))
                self.bits = -np.real(x[start:stop])

                # Deinterleave
                self.bits = self.bits[self.INTER]

                # Convolutional decode (rate 1/2, constraint length 7, 133/171)
                trellis = Trellis(memory=6, g_matrix=np.array([[0o133, 0o171]]))
                decoded = viterbi_decode(self.bits, trellis, tb_depth=30, decoding_type='hard')
                self.decoded_bits = np.array(decoded[:24], dtype=int)

                # Parse SIGNAL field
                if self._parse_signal():
                    # Tag first output symbol with (len, encoding)
                    key = pmt.intern("ofdm_start")
                    val = pmt.cons(pmt.from_uint64(self.d_len),
                                   pmt.from_uint64(self.d_encoding))
                    src = pmt.intern(self.name())
                    self.add_item_tag(0, self.nitems_written(0) + o * 48, key, val, src)

            elif self.d_copy_symbols > 0:
                # Forward subsequent data symbols
                y[o*48:(o+1)*48] = x[start:stop]
                o += 1
                self.d_copy_symbols -= 1

            i += 1

        self.consume(0, i * 48)
        return o * 48

    # -------------------------------------------------------------

    def _parse_signal(self):
        """Interpret 24 decoded SIGNAL bits → rate, length, parity."""
        parity = False
        r_val = 0
        d_len = 0

        for i in range(17):
            parity ^= bool(self.decoded_bits[i])
            if i < 4 and self.decoded_bits[i]:
                r_val |= (1 << i)
            if self.decoded_bits[i] and (4 < i < 17):
                d_len |= (1 << (i - 5))

        if parity != bool(self.decoded_bits[17]):
            if self.debug:
                print("[DECODE_SIGNAL] Wrong parity")
            return False

        if r_val not in self.rate_table:
            if self.debug:
                print(f"[DECODE_SIGNAL] Unknown rate field: {r_val}")
            return False

        self.d_encoding, bits_per_sym = self.rate_table[r_val]
        self.d_len = d_len
        n_sym = math.ceil((16 + 8 * d_len + 6) / float(bits_per_sym))
        if n_sym > 57:
            n_sym = 0
        self.d_copy_symbols = int(n_sym)

        if self.debug:
            rate_labels = [
                "3","4.5","6","9","12","18","24","27"
            ]
            rate_str = rate_labels[self.d_encoding] if self.d_encoding < len(rate_labels) else "?"
            print(f"[DECODE_SIGNAL] Rate={rate_str} Mbps  Len={d_len}  copy_symbols={n_sym}")

        return True