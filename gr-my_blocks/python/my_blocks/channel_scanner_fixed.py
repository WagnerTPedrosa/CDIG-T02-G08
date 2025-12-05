"""
WiFi Channel Scanner Block - Fixed Version
Automatically scans through WiFi channels every 10 seconds and detects SSIDs
"""

import numpy as np
from gnuradio import gr
import pmt
import time
import threading

class channel_scanner(gr.sync_block):
    """
    WiFi Channel Scanner for 5 GHz bands
    Cycles through channels every 10 seconds and collects SSIDs
    """
    
    def __init__(self, scan_interval=10, flowgraph=None):
        gr.sync_block.__init__(
            self,
            name="WiFi Channel Scanner",
            in_sig=None,
            out_sig=None
        )
        
        # WiFi 5 GHz channels (center frequencies)
        self.channels = {
            32: 5160000000,   # 5.16 GHz
            36: 5180000000,   # 5.18 GHz
            40: 5200000000,   # 5.20 GHz
            44: 5220000000,   # 5.22 GHz
            48: 5240000000,   # 5.24 GHz
            52: 5260000000,   # 5.26 GHz
            56: 5280000000,   # 5.28 GHz
            60: 5300000000,   # 5.30 GHz
            64: 5320000000,   # 5.32 GHz
            68: 5340000000,   # 5.34 GHz
            96: 5480000000,   # 5.48 GHz
            100: 5500000000,  # 5.50 GHz (DFS - eduroam target)
            104: 5520000000,  # 5.52 GHz
            108: 5540000000,  # 5.54 GHz
            112: 5560000000,  # 5.56 GHz
            116: 5580000000,  # 5.58 GHz
            120: 5600000000,  # 5.60 GHz
            124: 5620000000,  # 5.62 GHz
            128: 5640000000,  # 5.64 GHz
            132: 5660000000,  # 5.66 GHz
            136: 5680000000,  # 5.68 GHz
            140: 5700000000,  # 5.70 GHz
            144: 5720000000,  # 5.72 GHz
            149: 5745000000,  # 5.745 GHz
            153: 5765000000,  # 5.765 GHz
            157: 5785000000,  # 5.785 GHz
            161: 5805000000,  # 5.805 GHz
            165: 5825000000,  # 5.825 GHz
            169: 5845000000,  # 5.845 GHz
            173: 5865000000,  # 5.865 GHz
            177: 5885000000   # 5.885 GHz
        }
        
        self.channel_list = list(self.channels.keys())
        self.current_channel_idx = 0
        self.scan_interval = scan_interval
        self.last_scan = time.time()
        self.ssids_found = {}  # {channel: set(ssids)}
        self.scanning = True
        self.flowgraph = flowgraph
        
        # Message ports
        self.message_port_register_in(pmt.intern('ssid_in'))
        self.set_msg_handler(pmt.intern('ssid_in'), self.handle_ssid)
        
        # Start scanner thread
        self.scanner_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scanner_thread.start()
        
        print("\n" + "="*80)
        print("📡 WiFi Channel Scanner Started - 10 Second Intervals")
        print(f"⏱️  Scan interval: {scan_interval} seconds per channel")
        print(f"📻 Total channels: {len(self.channel_list)}")
        print(f"📡 Channel range: {min(self.channel_list)} - {max(self.channel_list)}")
        print(f"🌍 Frequency range: {min(self.channels.values())/1e9:.3f} - {max(self.channels.values())/1e9:.3f} GHz")
        print(f"🎯 Target: Channel 100 (5.50 GHz) for eduroam detection")
        print("="*80 + "\n")
    
    def set_scan_interval(self, scan_interval):
        """Update scan interval"""
        self.scan_interval = scan_interval
        print(f"⏱️  Scan interval updated to {scan_interval} seconds")
    
    def handle_ssid(self, msg):
        """Handle incoming SSID messages from Parse MAC"""
        meta = pmt.car(msg)
        
        if pmt.is_dict(meta):
            # Extract SSID
            if pmt.dict_has_key(meta, pmt.intern('ssid')):
                ssid = pmt.symbol_to_string(pmt.dict_ref(meta, pmt.intern('ssid'), pmt.PMT_NIL))
                current_channel = self.channel_list[self.current_channel_idx]
                
                # Store unique SSIDs per channel
                if ssid and len(ssid) > 0:
                    if current_channel not in self.ssids_found:
                        self.ssids_found[current_channel] = set()
                    
                    if ssid not in self.ssids_found[current_channel]:
                        self.ssids_found[current_channel].add(ssid)
                        freq_ghz = self.channels[current_channel] / 1e9
                        print(f"✅ Channel {current_channel} ({freq_ghz:.3f} GHz): '{ssid}'")
                        
                        # Special highlight for eduroam
                        if 'eduroam' in ssid.lower():
                            print(f"🎯 ** EDUROAM DETECTED on Channel {current_channel}! **")
    
    def scan_loop(self):
        """Main scanning loop - changes channel every 10 seconds"""
        while self.scanning:
            time.sleep(0.5)  # Check every 0.5 seconds
            
            current_time = time.time()
            elapsed = current_time - self.last_scan
            
            # Check if it's time to change channel
            if elapsed >= self.scan_interval:
                current_channel = self.channel_list[self.current_channel_idx]
                current_freq = self.channels[current_channel]
                
                print(f"\n🔍 Scanning Channel {current_channel} ({current_freq/1e9:.3f} GHz) - {self.scan_interval}s scan")
                
                # Update PlutoSDR frequency
                if self.flowgraph and hasattr(self.flowgraph, 'set_pluto_freq'):
                    self.flowgraph.set_pluto_freq(current_freq)
                elif self.flowgraph and hasattr(self.flowgraph, 'set_freq'):
                    try:
                        self.flowgraph.set_freq(current_freq)
                    except:
                        pass
                
                # Move to next channel
                self.current_channel_idx = (self.current_channel_idx + 1) % len(self.channel_list)
                self.last_scan = current_time
                
                # Print summary when full cycle completes
                if self.current_channel_idx == 0 and self.ssids_found:
                    self.print_summary()
    
    def print_summary(self):
        """Print scan results summary"""
        print("\n" + "="*80)
        print("SCAN SUMMARY - Networks Found:")
        print("="*80)
        
        total_ssids = 0
        unique_ssids = set()
        eduroam_channels = []
        
        for ch in sorted(self.ssids_found.keys()):
            channel_ssids = self.ssids_found[ch]
            if channel_ssids:
                freq_ghz = self.channels[ch] / 1e9
                print(f"\n  Channel {ch:3d} ({freq_ghz:.3f} GHz): {len(channel_ssids)} network(s)")
                
                for ssid in sorted(channel_ssids):
                    print(f"    • '{ssid}'")
                    unique_ssids.add(ssid)
                    
                    # Track eduroam locations
                    if 'eduroam' in ssid.lower():
                        eduroam_channels.append(ch)
                
                total_ssids += len(channel_ssids)
        
        print(f"\n  TOTAL: {len(unique_ssids)} unique network(s) across {len(self.ssids_found)} active channel(s)")
        
        if eduroam_channels:
            print(f"🎯 EDUROAM found on channel(s): {eduroam_channels}")
        else:
            print("🔍 EDUROAM not detected yet - continuing scan...")
            
        print("="*80 + "\n")
    
    def stop(self):
        """Stop scanning"""
        self.scanning = False
        if self.scanner_thread.is_alive():
            self.scanner_thread.join(timeout=1)
        self.print_summary()
        return True
    
    def work(self, input_items, output_items):
        """Required by gr.sync_block but not used"""
        return 0
