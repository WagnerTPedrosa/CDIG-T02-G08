"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import blocks
import pmt
from gnuradio import blocks, gr
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import foo
import ieee802_11



# Custom message handler for WiFi info
class wifi_info_printer(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self,
            name="WiFi Info Printer",
            in_sig=None,
            out_sig=None)
        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
    
    def handle_msg(self, msg):
        try:
            meta = pmt.car(msg)
            ssid = pmt.dict_ref(meta, pmt.intern('ssid'), pmt.PMT_NIL)
            freq = pmt.dict_ref(meta, pmt.intern('nominal frequency'), pmt.PMT_NIL)
            
            if not pmt.is_null(ssid):
                ssid_str = pmt.symbol_to_string(ssid)
                
                if not pmt.is_null(freq):
                    freq_val = pmt.to_double(freq)
                    channel = self.freq_to_channel(freq_val)
                    print(f"SSID: {ssid_str}  |  Channel: {channel} ({freq_val/1e9:.2f} GHz)")
                else:
                    print(f"SSID: {ssid_str}  |  Channel: N/A")
        except Exception as e:
            print(f"[WiFi Info] Erro ao processar mensagem: {e}")
    
    def freq_to_channel(self, freq_hz):
        # 5 GHz band channels
        if 5000e6 < freq_hz < 6000e6:
            channel = int((freq_hz - 5000e6) / 5e6)
            return channel
        # 2.4 GHz band channels
        elif 2400e6 < freq_hz < 2500e6:
            if freq_hz == 2484e6:
                return 14
            else:
                return int((freq_hz - 2407e6) / 5e6)
        return "Unknown"