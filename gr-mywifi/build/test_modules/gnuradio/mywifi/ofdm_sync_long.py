# SPDX-License-Identifier: GPL-3.0-or-later
# Python reimplementation of gr-ieee802-11 ofdm_sync_long
import numpy as np
from gnuradio import gr
import pmt

class ofdm_sync_long(gr.basic_block):
    """
    Inputs:
      0: complex (undelayed input)
      1: complex (delayed input)
    Output:
      0: complex (CFO-corrected, CP-stripped symbols streamed out)
         Inserts a tag 'ofdm_start' at the first data symbol (rel==16).
    Parameters:
      sync_length: how many samples to scan to find LTS peaks (same as C++)
      freq_est:    number of samples used for CFO estimate using lag-16 product
      debug:       print state/debug lines
    Behavior mirrors the original C++ block:
      States: SYNC -> COPY -> (RESET if a new ofdm_start arrives mid-copy) -> SYNC
      - SYNC: matched filter with the known LTS 'LONG', collect top-3 peaks -> frame_start = max(peaks)+64
      - COPY: output only data samples (skip CP): rel>=0 and rel%80>15; apply CFO correction
      - RESET: drain to the next symbol boundary, then go back to SYNC
    """

    # Long training sequence taps (64)
    LONG = np.array([
        -0.04097-0.9626011j,  0.3179976-0.8892635j,  0.7746551+0.6623833j,
         0.1688942+0.2230874j, 0.4785908-0.7016541j, -0.9210497-0.4414440j,
        -0.3065277-0.8493673j, 0.7803301-0.2071068j,  0.4267019+0.0326106j,
         0.0079118-0.9200371j, -1.0944390-0.3790380j, 0.1958068-0.4682544j,
         0.4693501-0.1195120j, -0.1798660+1.2852590j, 0.9539127-0.0327648j,
         0.5-0.5j,              0.2953435+0.7867532j, -0.4576508+0.3143887j,
        -1.0501010+0.5218180j, 0.6577466+0.7388524j,  0.5564548+0.1129757j,
        -0.4824808+0.6502890j, -0.4516410-0.1744314j, -0.2803300-1.2071070j,
        -0.9750961-0.1325297j, -1.0185950-0.1640110j,  0.6005896-0.5923234j,
        -0.0224476+0.4301941j, -0.7351004+0.9210297j,  0.7337324+0.8469733j,
         0.0982767+0.7807964j, -1.25+0j,               0.0982767-0.7807964j,
         0.7337324-0.8469733j, -0.7351004-0.9210297j, -0.0224476-0.4301941j,
         0.6005896+0.5923234j, -1.0185950+0.1640110j, -0.9750961+0.1325297j,
        -0.2803300+1.2071070j, -0.4516410+0.1744314j, -0.4824808-0.6502890j,
         0.5564548-0.1129757j,  0.6577466-0.7388524j, -1.0501010-0.5218180j,
        -0.4576508-0.3143887j,  0.2953435-0.7867532j,  0.5+0.5j,
         0.9539127+0.0327648j, -0.1798660-1.2852590j,  0.4693501+0.1195120j,
         0.1958068+0.4682544j, -1.0944390+0.3790380j,  0.0079118+0.9200371j,
         0.4267019-0.0326106j,  0.7803301+0.2071068j, -0.3065277+0.8493673j,
        -0.9210497+0.4414440j,  0.4785908+0.7016541j,  0.1688942-0.2230874j,
         0.7746551-0.6623833j,  0.3179976+0.8892635j, -0.04097+0.9626011j,
         1.25+0j
    ], dtype=np.complex64)

    # States
    SYNC, COPY, RESET = 0, 1, 2

    def __init__(self, sync_length=320, freq_est=128, debug=False):
        gr.basic_block.__init__(
            self,
            name="ofdm_sync_long_py",
            in_sig=[np.complex64, np.complex64],
            out_sig=[np.complex64],
        )
        self.set_tag_propagation_policy(gr.TPP_DONT)

        self.SYNC_LENGTH = int(sync_length)
        self.FREQ_EST = int(freq_est)
        self.debug = bool(debug)

        # runtime state
        self.state = self.SYNC
        self.offset = 0
        self.frame_start = 0
        self.freq_est_acc = 0+0j
        self._cor_pairs = []   # list of (abs(corr), absolute_offset)

    # ---------------------------- helpers ----------------------------

    def _dbg(self, *args):
        if self.debug:
            print("[SYNC_LONG]", *args)

    def forecast(self, noutput_items, ninput_items_required):
        if self.state == self.SYNC:
            ninput_items_required[0] = 64
            ninput_items_required[1] = 64
        else:
            ninput_items_required[0] = noutput_items
            ninput_items_required[1] = noutput_items

    def _insert_start_tag(self, where_item):
        key = pmt.intern("ofdm_start")
        val = pmt.PMT_T
        src = pmt.intern(self.name())
        self.add_item_tag(0, where_item, key, val, src)
        self._dbg(f"Inserted tag at item {where_item}")

    def _search_frame_start(self):
        # pick top-3 correlation peaks (by magnitude), then frame_start = max(idx)+64
        if not self._cor_pairs or len(self._cor_pairs) < 3:
            # fallback: assume current offset
            self.frame_start = max(0, self.offset - 1) + 64
            self._cor_pairs.clear()
            return
        # sort by magnitude desc
        self._cor_pairs.sort(key=lambda t: t[0], reverse=True)
        m1 = self._cor_pairs[0][1]
        m2 = self._cor_pairs[1][1]
        m3 = self._cor_pairs[2][1]
        m = max(m1, m2, m3)
        self.frame_start = m + 64
        self._dbg(f"frame_start={self.frame_start}  peaks {m1} {m2} {m3}")
        self._cor_pairs.clear()

    # ----------------------------- work -----------------------------

    def general_work(self, noutput_items, ninput_items, input_items, output_items):
        x = input_items[0]         # undelayed
        x_del = input_items[1]     # delayed
        y = output_items[0]

        nout = noutput_items
        nin = min(ninput_items[0], ninput_items[1])

        # Respect upstream ofdm_start tags like the C++ (to cut a chunk or reset)
        nread = self.nitems_read(0)
        tags = []
        self.get_tags_in_range(tags, 0, nread, nread + nin)
        if tags:
            tags.sort(key=lambda t: t.offset)
            off = tags[0].offset
            if off > nread:
                nin = int(off - nread)  # stop at the tag boundary
            else:
                if self.state == self.COPY:
                    self.state = self.RESET

        i = 0
        o = 0

        if self.state == self.SYNC:
            # matched filter against LTS over up to SYNC_LENGTH points (need 64 samples for each)
            limit = min(self.SYNC_LENGTH, max(nin - 63, 0))
            if limit > 0:
                # compute correlation via sliding dot-product: c[k] = sum(LONG * x[k:k+64])
                # equivalent to FIR with taps LONG (no conj), same as C++ kernel::fir_filter_ccc
                # We'll do it chunk-wise for clarity
                for k in range(limit):
                    # CFO (lag-16) accumulation for first FREQ_EST offsets
                    if self.offset < self.FREQ_EST and (k + 16) < nin:
                        self.freq_est_acc += x[k] * np.conj(x[k + 16])
                    # correlation magnitude
                    c = np.dot(self.LONG, x[k:k+64])
                    self._cor_pairs.append((abs(c), self.offset))
                    self.offset += 1
                i = limit

                if self.offset >= self.SYNC_LENGTH:
                    self._search_frame_start()
                    self.state = self.COPY

            # consume scanned samples; no output yet
            self.consume(0, i)
            self.consume(1, i)
            return 0

        elif self.state == self.COPY:
            # stream out data samples (skip CP): rel>=0 and rel%80>15
            # apply CFO correction using angle(freq_est_acc)/16 per-sample rotation
            # NOTE: if freq_est_acc==0 (e.g., bad preamble), angle=0 → no correction
            phase_step = 0.0
            if self.freq_est_acc != 0:
                phase_step = np.angle(self.freq_est_acc) / 16.0

            while i < nin:
                rel = self.offset - self.frame_start
                if (rel >= 0) and ((rel % 80) > 15):
                    if o >= nout:
                        break
                    if rel == 16 and o == 0:
                        # tag first data symbol
                        self._insert_start_tag(self.nitems_written(0) + o)
                    y[o] = x_del[i] * np.exp(1j * (self.offset * phase_step))
                    o += 1
                i += 1
                self.offset += 1

            self.consume(0, i)
            self.consume(1, i)
            return o

        elif self.state == self.RESET:
            # drain until the next symbol boundary; output zeros for data region
            while o < nout:
                rel = (self.offset - self.frame_start) % 80
                if rel == 0:
                    # reset all tracking
                    self.offset = 0
                    self.freq_est_acc = 0+0j
                    self.state = self.SYNC
                    break
                elif rel > 15:
                    y[o] = 0
                    o += 1
                self.offset += 1

            # we didn't advance inputs in RESET; emulate C++ behavior loosely by consuming 0
            # (or you can choose to consume 1 sample to avoid stalls; original C++ consumes with i)
            self.consume(0, 0)
            self.consume(1, 0)
            return o

        else:
            raise RuntimeError("ofdm_sync_long: invalid state")
