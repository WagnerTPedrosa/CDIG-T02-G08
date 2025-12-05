"""
Embedded Python Block for Channel Sweep Control
Add this to GNU Radio Companion as an "Embedded Python Block"
"""

import numpy as np
from gnuradio import gr
from PyQt5 import Qt, QtCore
import pmt


class channel_sweep_block(gr.basic_block):
    """
    Channel Sweep Controller
    This block manages automatic channel sweeping with GUI controls
    """
    def __init__(self, parent, freq_options, freq_labels, freq_combo_box, scan_interval=2.0):
        gr.basic_block.__init__(
            self,
            name="Channel Sweep Control",
            in_sig=None,
            out_sig=None
        )
        
        self.parent = parent
        self.freq_options = freq_options
        self.freq_labels = freq_labels
        self.freq_combo_box = freq_combo_box
        self.scan_interval = scan_interval
        
        self.current_channel_index = 0
        self.sweep_enable = True
        
        # Disconnect original callback
        try:
            self.freq_combo_box.currentIndexChanged.disconnect()
        except:
            pass
        
        # Reconnect with manual select handler
        self.freq_combo_box.currentIndexChanged.connect(self.manual_channel_select)
        
        # Create sweep control button
        self.sweep_button = Qt.QPushButton("Pause Sweep")
        self.sweep_button.clicked.connect(self.toggle_sweep)
        self.parent.top_layout.addWidget(self.sweep_button)
        
        # Setup timer
        self.timer = Qt.QTimer()
        self.timer.timeout.connect(self.sweep_next_channel)
        if self.sweep_enable:
            self.timer.start(int(self.scan_interval * 1000))
        
        print("\n*** Channel Sweep initialized ***")
        print(f"*** Sweeping {len(self.freq_options)} channels every {self.scan_interval}s ***\n")
    
    def sweep_next_channel(self):
        """Advance to next channel"""
        self.current_channel_index = (self.current_channel_index + 1) % len(self.freq_options)
        new_freq = self.freq_options[self.current_channel_index]
        channel_label = self.freq_labels[self.current_channel_index]
        print(f"\n=== Scanning {channel_label} ===")
        self.parent.set_freq(new_freq)
    
    def toggle_sweep(self):
        """Toggle sweep on/off"""
        if self.sweep_enable:
            self.timer.stop()
            self.sweep_enable = False
            self.sweep_button.setText("Resume Sweep")
            print("\n*** Channel sweep PAUSED ***")
        else:
            self.sweep_enable = True
            self.sweep_button.setText("Pause Sweep")
            self.timer.start(int(self.scan_interval * 1000))
            print("\n*** Channel sweep RESUMED ***")
    
    def manual_channel_select(self, index):
        """Handle manual channel selection"""
        if self.sweep_enable:
            self.timer.stop()
            self.sweep_enable = False
            self.sweep_button.setText("Resume Sweep")
            print("\n*** Channel sweep PAUSED (manual) ***")
        
        self.current_channel_index = index
        self.parent.set_freq(self.freq_options[index])
        print(f"\n=== Manual: {self.freq_labels[index]} ===")
    
    def work(self, input_items, output_items):
        return 0
