# SPDX-License-Identifier: GPL-3.0-or-later
# Python reimplementation of gr-ieee802-11 OFDM Sync Short
import numpy as np
from gnuradio import gr
import pmt

class ofdm_sync_short(gr.sync_block):
    """
    Detects OFDM short training sequence plateau and tags frame start.
    Inputs:
      0: complex signal stream
      1: float correlation magnitude stream
    Output:
      0: complex stream (frame samples after detection)
    """

    def __init__(self, threshold=0.8, max_samples=1600, min_plateau=3, debug=False):
        gr.sync_block.__init__(
            self,
            name="ofdm_sync_short_py",
            in_sig=[np.complex64, np.float32],
            out_sig=[np.complex64],
        )

        self.debug = bool(debug)
        self.threshold = float(threshold)
        self.MAX_SAMPLES = int(max_samples)
        self.MIN_PLATEAU = int(min_plateau)

        self.state = "SEARCH"
        self.plateau = 0
        self.copy_left = 0

        self.set_tag_propagation_policy(gr.TPP_DONT)

    # ------------------------------------------------------------------

    def work(self, input_items, output_items):
        in_complex = input_items[0]
        in_corr = input_items[1]
        out = output_items[0]

        ninput = min(len(in_complex), len(in_corr))
        noutput = len(out)

        if self.state == "SEARCH":
            # Look for a plateau of correlation values above threshold
            for i in range(ninput):
                if in_corr[i] > self.threshold:
                    self.plateau += 1
                    if self.plateau >= self.MIN_PLATEAU:
                        # Detected frame start
                        self.state = "COPY"
                        self.copy_left = self.MAX_SAMPLES
                        self.plateau = 0
                        self._insert_tag(self.nitems_written(0))
                        if self.debug:
                            print(f"[SYNC_SHORT] Frame detected at sample {self.nitems_written(0)}")
                        # consume samples up to current i
                        self.consume_each(i)
                        return 0
                else:
                    self.plateau = 0

            # If we reach here, no detection yet
            self.consume_each(ninput)
            return 0

        elif self.state == "COPY":
            to_copy = min(self.copy_left, ninput, noutput)
            out[:to_copy] = in_complex[:to_copy]

            self.copy_left -= to_copy
            if self.copy_left == 0:
                self.state = "SEARCH"

            if self.debug:
                print(f"[SYNC_SHORT] Copied {to_copy} samples, {self.copy_left} left")

            self.consume_each(to_copy)
            return to_copy

        else:
            raise RuntimeError("sync_short: invalid state")

    # ------------------------------------------------------------------

    def _insert_tag(self, item):
        """Insert 'ofdm_start' tag like the C++ version."""
        key = pmt.intern("ofdm_start")
        value = pmt.PMT_T
        srcid = pmt.intern(self.name())
        self.add_item_tag(0, item, key, value, srcid)
        if self.debug:
            print(f"[SYNC_SHORT] Inserted tag at item {item}")
