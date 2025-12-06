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
from collections import defaultdict
from datetime import datetime



# Global statistics storage
channel_stats = {
    'networks_per_channel': defaultdict(set),  # channel -> set of SSIDs
    'rssi_per_channel': defaultdict(list),     # channel -> list of RSSI values
    'rssi_per_network': defaultdict(list),     # SSID -> list of (timestamp, RSSI)
    'detection_count': defaultdict(int),       # SSID -> count
    'last_seen': {},                            # SSID -> timestamp
}

def get_channel_stats():
    """Returns formatted statistics about channel occupancy and signal strength"""
    return channel_stats

def get_top_channels(n=5):
    """Returns top N channels by number of detected networks"""
    channel_counts = [(ch, len(ssids)) for ch, ssids in channel_stats['networks_per_channel'].items()]
    return sorted(channel_counts, key=lambda x: x[1], reverse=True)[:n]

def get_best_channels_by_rssi(n=5):
    """Returns top N channels by average RSSI (signal strength)"""
    channel_avg_rssi = []
    for ch, rssi_list in channel_stats['rssi_per_channel'].items():
        if rssi_list:
            avg_rssi = sum(rssi_list) / len(rssi_list)
            channel_avg_rssi.append((ch, avg_rssi, len(rssi_list)))
    return sorted(channel_avg_rssi, key=lambda x: x[1], reverse=True)[:n]


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
            rssi = pmt.dict_ref(meta, pmt.intern('rssi'), pmt.PMT_NIL)
            
            # Debug: print all available keys in metadata
            if False:  # Set to True for debugging
                print(f"[DEBUG] Message metadata keys: {pmt.to_python(meta)}")
            
            if not pmt.is_null(ssid):
                ssid_str = pmt.symbol_to_string(ssid)
                timestamp = datetime.now()
                
                # Update detection count and last seen
                channel_stats['detection_count'][ssid_str] += 1
                channel_stats['last_seen'][ssid_str] = timestamp
                
                # Get frequency and channel info
                channel = None
                freq_val = None
                
                if not pmt.is_null(freq):
                    freq_val = pmt.to_double(freq)
                    channel = self.freq_to_channel(freq_val)
                else:
                    # Try to get current frequency from metadata
                    current_freq = pmt.dict_ref(meta, pmt.intern('frequency'), pmt.PMT_NIL)
                    if not pmt.is_null(current_freq):
                        freq_val = pmt.to_double(current_freq)
                        channel = self.freq_to_channel(freq_val)
                
                # Track networks per channel (even if frequency is unknown, use estimated channel)
                if channel is not None and channel != "Unknown":
                    channel_stats['networks_per_channel'][channel].add(ssid_str)
                    
                    # Track RSSI if available - try multiple fields
                    rssi_val = None
                    if not pmt.is_null(rssi):
                        rssi_val = pmt.to_double(rssi)
                    else:
                        # Try alternative RSSI fields
                        for rssi_key in ['snr', 'signal', 'rx_power']:
                            rssi_alt = pmt.dict_ref(meta, pmt.intern(rssi_key), pmt.PMT_NIL)
                            if not pmt.is_null(rssi_alt):
                                rssi_val = pmt.to_double(rssi_alt)
                                break
                    
                    if rssi_val is not None:
                        channel_stats['rssi_per_channel'][channel].append(rssi_val)
                        channel_stats['rssi_per_network'][ssid_str].append((timestamp, rssi_val))
                    # If no RSSI, don't add to rssi stats - only real signal strength data
                    
                    # Print detection
                    if rssi_val is not None:
                        print(f"SSID: {ssid_str}  |  Channel: {channel} ({freq_val/1e9:.2f} GHz)  |  RSSI: {rssi_val:.1f} dBm  |  Detections: {channel_stats['detection_count'][ssid_str]}")
                    else:
                        print(f"SSID: {ssid_str}  |  Channel: {channel} ({freq_val/1e9:.2f} GHz)  |  RSSI: N/A (estimated -70 dBm)  |  Detections: {channel_stats['detection_count'][ssid_str]}")
                else:
                    # SSID detected but no channel info - still count it
                    print(f"SSID: {ssid_str}  |  Channel: Unknown  |  Detections: {channel_stats['detection_count'][ssid_str]}")
                    print(f"[WiFi Info] Warning: No frequency information for SSID {ssid_str}")
        except Exception as e:
            print(f"[WiFi Info] Error processing message: {e}")
    
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