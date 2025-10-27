# SPDX-License-Identifier: GPL-3.0-or-later
# Python reimplementation of gr-ieee802-11 ofdm_sync_long
import numpy as np
from gnuradio import gr
import pmt

class ofdm_sync_long(gr.basic_block):
    """
    Simplified OFDM sync long block - pass-through for now
    """

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

    def _dbg(self, *args):
        if self.debug:
            print("[SYNC_LONG]", *args)

    def general_work(self, input_items, output_items):
        """
        Simplified general_work implementation - pass-through with tag propagation
        """
        try:
            x = input_items[0]         # undelayed
            x_del = input_items[1]     # delayed  
            y = output_items[0]

            nin = min(len(x), len(x_del))
            nout = len(y)
            
            if nin == 0 or nout == 0:
                return 0

            # Simple pass-through for now
            samples_to_copy = min(nin, nout)
            for i in range(samples_to_copy):
                y[i] = x[i]  # Pass through undelayed input
            
            # Propagate tags from input 0 to output
            nread = self.nitems_read(0)
            nwritten = self.nitems_written(0)
            tags = self.get_tags_in_range(0, nread, nread + samples_to_copy)
            
            for tag in tags:
                new_offset = nwritten + (tag.offset - nread)
                self.add_item_tag(0, new_offset, tag.key, tag.value, tag.srcid)
                if self.debug:
                    self._dbg(f"Propagated tag {pmt.symbol_to_string(tag.key)} at offset {new_offset}")
                
            self.consume(0, samples_to_copy)
            self.consume(1, samples_to_copy)
            
            if self.debug and samples_to_copy > 0:
                self._dbg(f"Pass-through: {samples_to_copy} samples")
                
            return samples_to_copy
            
        except Exception as e:
            self._dbg(f"Error in general_work: {e}")
            # Consume at least one sample to avoid infinite loops
            if nin > 0:
                self.consume(0, 1)
                self.consume(1, 1)
            return 0
