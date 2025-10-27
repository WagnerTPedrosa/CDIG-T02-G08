#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Test version using baseband recordings
#

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio import pdu
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
import time
from gnuradio.mywifi.ofdm_decode_mac import ofdm_decode_mac
from gnuradio.mywifi.ofdm_decode_signal import ofdm_decode_signal
from gnuradio.mywifi.ofdm_equalize_symbols import ofdm_equalize_symbols
from gnuradio.mywifi.ofdm_parse_mac import ofdm_parse_mac
from gnuradio.mywifi.ofdm_sync_long import ofdm_sync_long
from gnuradio.mywifi.ofdm_sync_short import ofdm_sync_short
import threading

class test_with_samples(gr.top_block, Qt.QWidget):

    def __init__(self, sample_file="./Wifi_Project_Baseband_recordings/Sample1_20MHz_Channel36.bin"):
        gr.top_block.__init__(self, "WiFi Test with Samples", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("WiFi Test with Samples")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "test_with_samples")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.window_size = window_size = 32000
        self.samp_rate = samp_rate = int(20e6)  # 20 MHz
        self.sample_file = sample_file

        ##################################################
        # Blocks
        ##################################################
        
        # File source instead of Pluto
        print(f"Loading WiFi sample file: {self.sample_file}")
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, self.sample_file, True)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate, True)
        
        # Network output for packet capture
        self.network_socket_pdu_0 = network.socket_pdu('TCP_SERVER', '', '12345', 10000, False)
        
        # WiFi processing blocks
        self.mywifi_ofdm_sync_short_0 = ofdm_sync_short(threshold=0.56, max_samples=8000, min_plateau=2, debug=True)
        self.mywifi_ofdm_sync_long_0 = ofdm_sync_long(sync_length=320, freq_est=128, debug=True)
        self.mywifi_ofdm_parse_mac_0 = ofdm_parse_mac(debug=True)
        self.mywifi_ofdm_equalize_symbols_0 = ofdm_equalize_symbols(debug=True)
        self.mywifi_ofdm_decode_signal_0 = ofdm_decode_signal(debug=True)
        self.mywifi_ofdm_decode_mac_0 = ofdm_decode_mac(debug=True)
        
        # Signal processing blocks
        self.fir_filter_xxx_1 = filter.fir_filter_fff(1, [1]*window_size)
        self.fir_filter_xxx_1.declare_sample_delay(0)
        self.fir_filter_xxx_0 = filter.fir_filter_ccc(1, [1]*window_size)
        self.fir_filter_xxx_0.declare_sample_delay(0)
        self.fft_vxx_0 = fft.fft_vcc(64, True, window.rectangular(64), True, 1)
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_gr_complex*1, 64)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 64)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_divide_xx_0 = blocks.divide_ff(1)
        self.blocks_delay_1 = blocks.delay(gr.sizeof_gr_complex*1, 240)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, 16)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.mywifi_ofdm_decode_mac_0, 'out'), (self.mywifi_ofdm_parse_mac_0, 'in'))
        self.msg_connect((self.mywifi_ofdm_parse_mac_0, 'out'), (self.network_socket_pdu_0, 'pdus'))
        
        # File source chain
        self.connect((self.blocks_file_source_0, 0), (self.blocks_throttle_0, 0))
        
        # Signal processing connections
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.fir_filter_xxx_1, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.mywifi_ofdm_sync_short_0, 0))
        self.connect((self.blocks_delay_1, 0), (self.mywifi_ofdm_sync_long_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.mywifi_ofdm_sync_short_0, 1))
        self.connect((self.blocks_multiply_xx_0, 0), (self.fir_filter_xxx_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.mywifi_ofdm_equalize_symbols_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.fir_filter_xxx_1, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.mywifi_ofdm_decode_signal_0, 0), (self.mywifi_ofdm_decode_mac_0, 0))
        self.connect((self.mywifi_ofdm_equalize_symbols_0, 0), (self.mywifi_ofdm_decode_signal_0, 0))
        self.connect((self.mywifi_ofdm_sync_long_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.mywifi_ofdm_sync_short_0, 0), (self.blocks_delay_1, 0))
        self.connect((self.mywifi_ofdm_sync_short_0, 0), (self.mywifi_ofdm_sync_long_0, 1))
        
        # Connect throttled source to processing chain
        self.connect((self.blocks_throttle_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_multiply_xx_0, 1))

    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "test_with_samples")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()
        event.accept()

    def get_window_size(self):
        return self.window_size

    def set_window_size(self, window_size):
        self.window_size = window_size
        self.fir_filter_xxx_0.set_taps([1]*self.window_size)
        self.fir_filter_xxx_1.set_taps([1]*self.window_size)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(samp_rate)

def main(top_block_cls=test_with_samples, options=None):
    parser = ArgumentParser()
    parser.add_argument("--sample-file", dest="sample_file", type=str, 
                       default="./Wifi_Project_Baseband_recordings/Sample1_20MHz_Channel36.bin",
                       help="Path to the WiFi sample file")
    args = parser.parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(sample_file=args.sample_file)

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
