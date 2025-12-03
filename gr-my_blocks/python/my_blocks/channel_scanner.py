"""
WiFi Channel Scanner Block
Automatically scans through WiFi channels and detects SSIDs
"""

import numpy as np
from gnuradio import gr
import pmt
import time
import threading

class channel_scanner(gr.sync_block):
    """
    WiFi Channel Scanner for 5 GHz bands
    Cycles through channels and collects SSIDs
    """
    
    def __init__(self, scan_interval=5, flowgraph=None):
        gr.sync_block.__init__(
            self,
            name="WiFi Channel Scanner",
            in_sig=None,
            out_sig=None
        )
        
        # Auto-detect flowgraph if not provided
        if flowgraph is None:
            try:
                flowgraph = self.to_basic_block().parent()
            except:
                pass
        
        # WiFi 5 GHz channels (802.11a/n/ac) - matching projeto.grc freq chooser
        self.channels = {
            36: 5180000000,
            40: 5200000000,
            44: 5220000000,
            48: 5240000000,
            52: 5260000000,
            56: 5280000000,
            60: 5300000000,
            64: 5320000000,
            149: 5745000000,
            153: 5765000000,
            157: 5785000000,
            161: 5805000000
        }
        
        self.channel_list = list(self.channels.keys())
        self.current_idx = 0
        self.scan_interval = scan_interval
        self.last_scan = time.time()
        self.ssids_found = {}  # {channel: [ssid1, ssid2, ...]}
        self.scanning = True
        self.flowgraph = flowgraph
        
        # Message ports
        self.message_port_register_in(pmt.intern('ssid_in'))
        self.set_msg_handler(pmt.intern('ssid_in'), self.handle_ssid)
        
        # Start scanner thread
        self.scanner_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scanner_thread.start()
        
        print("\n" + "="*60)
        print("📡 WiFi Channel Scanner Started")
        print(f"⏱️  Scan interval: {scan_interval} seconds per channel")
        print(f"📻 Channels: {', '.join(map(str, self.channel_list))}")
        print("="*60 + "\n")
    
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
                current_channel = self.channel_list[self.current_idx]
                
                # Store unique SSIDs per channel
                if ssid and len(ssid) > 0:
                    if current_channel not in self.ssids_found:
                        self.ssids_found[current_channel] = set()
                    
                    if ssid not in self.ssids_found[current_channel]:
                        self.ssids_found[current_channel].add(ssid)
                        print(f"✅ Channel {current_channel} ({self.channels[current_channel]/1e9:.3f} GHz): '{ssid}'")
    
    def scan_loop(self):
        """Main scanning loop - changes channels periodically"""
        while self.scanning:
            time.sleep(0.1)  # Small sleep to avoid busy loop
            
            current_time = time.time()
            if current_time - self.last_scan >= self.scan_interval:
                # Move to next channel
                self.current_idx = (self.current_idx + 1) % len(self.channel_list)
                current_channel = self.channel_list[self.current_idx]
                freq = self.channels[current_channel]
                
                print(f"\n🔍 Scanning Channel {current_channel} ({freq/1e9:.3f} GHz)...")
                
                # Update frequency in flowgraph
                if self.flowgraph and hasattr(self.flowgraph, 'set_freq'):
                    self.flowgraph.set_freq(freq)
                
                self.last_scan = current_time
                
                # Print summary when cycle completes
                if self.current_idx == 0 and self.ssids_found:
                    self.print_summary()
    
    def print_summary(self):
        """Print scan results summary"""
        print("\n" + "="*60)
        print("SCAN SUMMARY - Networks Found:")
        print("="*60)
        
        total_ssids = 0
        for ch in sorted(self.ssids_found.keys()):
            ssids = self.ssids_found[ch]
            if ssids:
                freq_ghz = self.channels[ch] / 1e9
                print(f"  Channel {ch:3d} ({freq_ghz:.3f} GHz): {len(ssids)} network(s)")
                for ssid in sorted(ssids):
                    print(f"    • {ssid}")
                total_ssids += len(ssids)
        
        print(f"\n  Total: {total_ssids} unique network(s) across {len(self.ssids_found)} channel(s)")
        print("="*60 + "\n")
    
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
