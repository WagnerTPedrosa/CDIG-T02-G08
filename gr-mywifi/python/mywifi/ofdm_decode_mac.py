# SPDX-License-Identifier: GPL-3.0-or-later
# Python reimplementation of gr-ieee802-11 ofdm_decode_mac
import numpy as np
from gnuradio import gr
import pmt
import math
from commpy.channelcoding import Trellis, viterbi_decode


class ofdm_param:
    """Represents modulation parameters per encoding (IEEE 802.11a)."""
    def __init__(self, encoding):
        self.encoding = encoding
        if encoding == 0:     # BPSK 1/2
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 1, 48, 24, 0x0D
        elif encoding == 1:   # BPSK 3/4
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 1, 48, 36, 0x0F
        elif encoding == 2:   # QPSK 1/2
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 2, 96, 48, 0x05
        elif encoding == 3:   # QPSK 3/4
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 2, 96, 72, 0x07
        elif encoding == 4:   # 16-QAM 1/2
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 4, 192, 96, 0x09
        elif encoding == 5:   # 16-QAM 3/4
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 4, 192, 144, 0x0B
        elif encoding == 6:   # 64-QAM 2/3
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 6, 288, 192, 0x01
        elif encoding == 7:   # 64-QAM 3/4
            self.n_bpsc, self.n_cbps, self.n_dbps, self.rate_field = 6, 288, 216, 0x03
        else:
            raise ValueError("Invalid encoding index")

    def __repr__(self):
        return f"<OFDMParam enc={self.encoding} n_cbps={self.n_cbps} n_dbps={self.n_dbps}>"


class tx_param:
    """Per-packet parameters derived from ofdm_param and PSDU length."""
    def __init__(self, ofdm, psdu_length):
        self.psdu_size = psdu_length
        self.n_sym = math.ceil((16 + 8 * psdu_length + 6) / float(ofdm.n_dbps))
        self.n_data = self.n_sym * ofdm.n_dbps
        self.n_pad = self.n_data - (16 + 8 * psdu_length + 6)
        self.n_encoded_bits = self.n_sym * ofdm.n_cbps

    def __repr__(self):
        return f"<TXParam psdu={self.psdu_size} sym={self.n_sym} bits={self.n_encoded_bits}>"


class ofdm_decode_mac(gr.basic_block):
    """
    OFDM Decode MAC (802.11a/g)
    ----------------------------
    - Reads 48-subcarrier symbols (complex)
    - Detects 'ofdm_start' tag with (length, encoding)
    - Demodulates (BPSK/QPSK)
    - Deinterleaves
    - Convolutionally decodes (rate 1/2 or 3/4)
    - Descrambles MAC payload
    - Outputs full MAC frame as PMT blob on port "out"
    """

    def __init__(self, debug=False):
        gr.basic_block.__init__(
            self,
            name="ofdm_decode_mac_py",
            in_sig=[np.complex64],
            out_sig=None
        )
        self.debug = bool(debug)
        self.ofdm = ofdm_param(0)
        self.tx = tx_param(self.ofdm, 0)
        self.copied = 0
        self.symbols = np.zeros((1000, 48), dtype=np.complex64)
        self.message_port_register_out(pmt.intern("out"))

    # -------------------------------------------------------------------

    def general_work(self, noutput_items, ninput_items, input_items, output_items):
        x = input_items[0]
        nsyms = ninput_items[0] // 48
        nread = self.nitems_read(0)
        i = 0

        for s in range(nsyms):
            start = s * 48
            stop = start + 48
            tags = []
            self.get_tags_in_range(tags, 0, nread + start, nread + stop, pmt.intern("ofdm_start"))

            if tags:
                val = tags[0].value
                length = int(pmt.to_uint64(pmt.car(val)))
                encoding = int(pmt.to_uint64(pmt.cdr(val)))
                self.ofdm = ofdm_param(encoding)
                self.tx = tx_param(self.ofdm, length)
                self.copied = 0

                if self.debug:
                    print(f"[MAC] New frame: len={length} enc={encoding} sym={self.tx.n_sym}")

            if self.copied < self.tx.n_sym:
                self.symbols[self.copied, :] = x[start:stop]
                self.copied += 1

                if self.copied == self.tx.n_sym:
                    if self.debug:
                        print("[MAC] Frame complete — decoding")
                    self._decode()
                    break

            i += 1

        self.consume(0, i * 48)
        return 0

    # -------------------------------------------------------------------
    # Decode pipeline

    def _decode(self):
        if self.ofdm.encoding > 3:
            if self.debug:
                print("[MAC] Unsupported encoding > QPSK_3_4")
            return

        bits = self._demodulate()
        deinter = self._deinterleave(bits)
        decoded_bits = self._viterbi_decode(deinter)
        out_bits, out_bytes = self._descramble(decoded_bits)

        # Publish MAC frame (skip service field)
        payload = bytes(out_bytes[2:self.tx.psdu_size + 2])
        blob = pmt.make_u8vector(len(payload), 0)
        for i, b in enumerate(payload):
            pmt.u8vector_set(blob, i, b)
        self.message_port_pub(pmt.intern("out"), blob)

        if self.debug:
            print(f"[MAC] Published {len(payload)} bytes")

    # -------------------------------------------------------------------
    # BPSK/QPSK demodulation
    def _demodulate(self):
        bits = []
        for i in range(self.tx.n_sym):
            for n in range(48):
                s = self.symbols[i, n]
                if self.ofdm.encoding in (0, 1):  # BPSK
                    bits.append(-np.real(s))
                elif self.ofdm.encoding in (2, 3):  # QPSK
                    bits.append(-np.real(s))
                    bits.append(-np.imag(s))
        return np.array(bits)

    # -------------------------------------------------------------------
    # IEEE 802.11 deinterleaving
    def _deinterleave(self, bits):
        n_cbps = self.ofdm.n_cbps
        s = max(self.ofdm.n_bpsc // 2, 1)
        first = np.zeros(n_cbps, dtype=int)
        second = np.zeros(n_cbps, dtype=int)
        for j in range(n_cbps):
            first[j] = s * (j // s) + ((j + int(np.floor(16.0 * j / n_cbps))) % s)
        for i in range(n_cbps):
            second[i] = 16 * i - (n_cbps - 1) * int(np.floor(16.0 * i / n_cbps))
        deinter = np.zeros_like(bits)
        for sym in range(self.tx.n_sym):
            for k in range(n_cbps):
                src = sym * n_cbps + k
                dst = sym * n_cbps + second[first[k]]
                deinter[dst] = bits[src]
        return deinter

    # -------------------------------------------------------------------
    # Convolutional decoding
    def _viterbi_decode(self, deinter):
        trellis = Trellis(memory=6, g_matrix=np.array([[0o133, 0o171]]))
        if self.ofdm.encoding in (0, 2):  # rate 1/2
            rate = 1/2
        elif self.ofdm.encoding in (1, 3):  # rate 3/4 (punctured)
            rate = 3/4
        else:
            rate = 1/2
        tb_depth = 30
        decoded = viterbi_decode(deinter, trellis, tb_depth=tb_depth, decoding_type='hard')
        return np.array(decoded[:self.tx.n_data], dtype=int)

    # -------------------------------------------------------------------
    # Descrambler (7-bit LFSR)
    def _descramble(self, decoded_bits):
        out_bits = np.zeros_like(decoded_bits)
        out_bytes = np.zeros(len(decoded_bits) // 8 + 1, dtype=np.uint8)

        # initial state from first 7 bits
        index = 0
        for i in range(7):
            if decoded_bits[i]:
                index |= 1 << (6 - i)
        state = self._scrambler_init[index]
        for i in range(len(decoded_bits)):
            feedback = ((state & 0x40) != 0) ^ ((state & 0x08) != 0)
            out_bits[i] = feedback ^ decoded_bits[i]
            state = ((state << 1) & 0x7E) | feedback

        # pack bits into bytes
        for i, bit in enumerate(out_bits):
            byte = i // 8
            if bit:
                out_bytes[byte] |= (1 << (i % 8))
        return out_bits, out_bytes

    # -------------------------------------------------------------------
    # Precomputed scrambler initial states (same as in C++)
    _scrambler_init = np.array([
        0,73,18,91,36,109,54,127,72,1,90,19,108,37,126,55,89,16,75,2,125,52,111,38,17,88,3,74,53,124,39,110,
        50,123,32,105,22,95,4,77,122,51,104,33,94,23,76,5,107,34,121,48,79,6,93,20,35,106,49,120,7,78,21,92,
        100,45,118,63,64,9,82,27,44,101,62,119,8,65,26,83,61,116,47,102,25,80,11,66,117,60,103,46,81,24,67,10,
        86,31,68,13,114,59,96,41,30,87,12,69,58,115,40,97,15,70,29,84,43,98,57,112,71,14,85,28,99,42,113,56
    ])
