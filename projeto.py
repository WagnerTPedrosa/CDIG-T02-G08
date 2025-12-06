#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import blocks
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
from gnuradio import iio
import foo
import ieee802_11
import projeto_epy_block_1 as epy_block_1  # embedded python block
import threading


def snipfcn_snippet_0(self):
    # Sweep

    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit
    import projeto_epy_block_1 as epy_block_1

    # Import matplotlib for graphing
    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt
        matplotlib_available = True
    except ImportError:
        print("[GRAPH] Matplotlib not available. Install with: pip install matplotlib")
        matplotlib_available = False

    # Channel sweep setup
    channels = [
        2412000000, 2417000000, 2422000000, 2427000000, 2432000000, 2437000000,
        2442000000, 2447000000, 2452000000, 2457000000, 2462000000, 2467000000,
        2472000000, 2484000000, 5160000000, 5180000000, 5200000000, 5220000000,
        5240000000, 5260000000, 5280000000, 5300000000, 5320000000, 5340000000,
        5480000000, 5500000000, 5520000000, 5540000000, 5560000000, 5580000000,
        5600000000, 5620000000, 5640000000, 5660000000, 5680000000, 5700000000,
        5720000000, 5745000000, 5765000000, 5785000000, 5805000000, 5825000000,
        5845000000, 5865000000, 5885000000
    ]
    channel_index = [0]
    sweep_active = [True]
    sweep_changing = [False]  # Flag to indicate sweep is changing frequency
    tb = self
    time = 60000

    # Create status label
    status_label = QLabel(" SWEEP MODE - Scanning all channels...")
    status_label.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; font-size: 14px; }")
    tb.top_layout.addWidget(status_label)

    # Create statistics display widgets
    stats_widget = QWidget()
    stats_layout = QVBoxLayout()

    activity_label = QLabel("CHANNEL ACTIVITY - No data yet")
    activity_label.setStyleSheet("QLabel { background-color: #2196F3; color: white; padding: 8px; font-weight: bold; font-size: 13px; }")
    stats_layout.addWidget(activity_label)

    occupancy_label = QLabel("TOP CHANNELS BY NETWORK COUNT - No data yet")
    occupancy_label.setStyleSheet("QLabel { background-color: #9C27B0; color: white; padding: 8px; font-weight: bold; font-size: 13px; }")
    stats_layout.addWidget(occupancy_label)

    rssi_label = QLabel("BEST CHANNELS BY SIGNAL STRENGTH - No data yet")
    rssi_label.setStyleSheet("QLabel { background-color: #FF5722; color: white; padding: 8px; font-weight: bold; font-size: 13px; }")
    stats_layout.addWidget(rssi_label)

    stats_widget.setLayout(stats_layout)
    tb.top_layout.addWidget(stats_widget)

    # Create matplotlib graph widget
    if matplotlib_available:
        graph_widget = QWidget()
        graph_layout = QVBoxLayout()

        graph_label = QLabel("REAL-TIME CHANNEL ANALYSIS")
        graph_label.setStyleSheet("QLabel { background-color: #607D8B; color: white; padding: 8px; font-weight: bold; font-size: 13px; }")
        graph_layout.addWidget(graph_label)

        # Create figure with two subplots
        fig = Figure(figsize=(12, 6), dpi=80)
        canvas = FigureCanvas(fig)

        ax1 = fig.add_subplot(121)  # Left: Networks per channel
        ax2 = fig.add_subplot(122)  # Right: Average RSSI per channel

        graph_layout.addWidget(canvas)
        graph_widget.setLayout(graph_layout)
        tb.top_layout.addWidget(graph_widget)

        def update_graph():
            """Update the real-time graphs"""
            try:
                stats = epy_block_1.get_channel_stats()

                # Clear previous plots
                ax1.clear()
                ax2.clear()

                # Plot 1: Networks per channel
                if stats['networks_per_channel'] and len(stats['networks_per_channel']) > 0:
                    channels_list = sorted(stats['networks_per_channel'].keys())
                    network_counts = [len(stats['networks_per_channel'][ch]) for ch in channels_list]

                    if channels_list and network_counts:
                        ax1.bar(range(len(channels_list)), network_counts, color='#2196F3', alpha=0.7)
                        ax1.set_xticks(range(len(channels_list)))
                        ax1.set_xticklabels([str(ch) for ch in channels_list], rotation=45, ha='right', fontsize=8)
                        ax1.set_xlabel('Channel', fontweight='bold')
                        ax1.set_ylabel('Number of Networks', fontweight='bold')
                        ax1.set_title('Networks Detected per Channel', fontweight='bold', fontsize=11)
                        ax1.grid(axis='y', alpha=0.3)

                        # Highlight most active channel
                        if network_counts:
                            max_idx = network_counts.index(max(network_counts))
                            ax1.bar(max_idx, network_counts[max_idx], color='#4CAF50', alpha=0.9)
                else:
                    # Show "waiting for data" message
                    ax1.text(0.5, 0.5, 'Waiting for network detections...',
                            ha='center', va='center', transform=ax1.transAxes, fontsize=12)
                    ax1.set_title('Networks Detected per Channel', fontweight='bold', fontsize=11)

                # Plot 2: Average RSSI per channel
                if stats['rssi_per_channel']:
                    rssi_channels = sorted([ch for ch, rssi_list in stats['rssi_per_channel'].items() if rssi_list])

                    if rssi_channels and len(rssi_channels) > 0:
                        avg_rssi = [sum(stats['rssi_per_channel'][ch])/len(stats['rssi_per_channel'][ch])
                                   for ch in rssi_channels]

                        colors = ['#4CAF50' if rssi > -60 else '#FF9800' if rssi > -75 else '#F44336'
                                 for rssi in avg_rssi]

                        ax2.bar(range(len(rssi_channels)), avg_rssi, color=colors, alpha=0.7)
                        ax2.set_xticks(range(len(rssi_channels)))
                        ax2.set_xticklabels([str(ch) for ch in rssi_channels], rotation=45, ha='right', fontsize=8)
                        ax2.set_xlabel('Channel', fontweight='bold')
                        ax2.set_ylabel('Average RSSI (dBm)', fontweight='bold')
                        ax2.set_title('Signal Strength per Channel', fontweight='bold', fontsize=11)
                        ax2.grid(axis='y', alpha=0.3)
                        ax2.axhline(y=-60, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Excellent')
                        ax2.axhline(y=-75, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='Good')
                        ax2.legend(fontsize=8, loc='lower right')
                    else:
                        # Show "waiting for data" message
                        ax2.text(0.5, 0.5, 'Waiting for RSSI data...',
                                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
                        ax2.set_title('Signal Strength per Channel', fontweight='bold', fontsize=11)
                else:
                    # Show "waiting for data" message
                    ax2.text(0.5, 0.5, 'Waiting for RSSI data...',
                            ha='center', va='center', transform=ax2.transAxes, fontsize=12)
                    ax2.set_title('Signal Strength per Channel', fontweight='bold', fontsize=11)

                fig.tight_layout()
                canvas.draw()
            except Exception as e:
                # Silently handle errors when no data is available yet
                pass

        # Store update function and canvas for later use
        tb._graph_update = update_graph
        tb._graph_canvas = canvas

    # Save original set_freq
    original_set_freq = tb.set_freq

    def update_status_label():
        if sweep_active[0]:
            status_label.setText(" SWEEP MODE - Scanning all channels...")
            status_label.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; font-size: 14px; }")
        else:
            status_label.setText(" MANUAL MODE - Fixed channel selected")
            status_label.setStyleSheet("QLabel { background-color: #FF9800; color: white; padding: 10px; font-weight: bold; font-size: 14px; }")

    def custom_set_freq(freq):
        # Only pause if this is a manual change (not from sweep itself)
        if sweep_active[0] and not sweep_changing[0]:
            sweep_active[0] = False
            tb._sweep_timer.stop()
            update_status_label()
            print(f"[SWEEP] Paused! Manual change detected.")
            print("[SWEEP] Click 'Resume Sweep' button to continue.")
        original_set_freq(freq)

    tb.set_freq = custom_set_freq

    def update_statistics_display():
        """Update the GUI with latest statistics"""
        try:
            # Get top channels by network count
            top_channels = epy_block_1.get_top_channels(5)
            if top_channels:
                most_active_ch, most_active_count = top_channels[0]
                activity_label.setText(f" MOST ACTIVE CHANNEL: {most_active_ch} with {most_active_count} networks")

                occupancy_text = "TOP CHANNELS BY NETWORK COUNT:\n"
                for i, (ch, count) in enumerate(top_channels, 1):
                    occupancy_text += f"  {i}. Channel {ch}: {count} networks\n"
                occupancy_label.setText(occupancy_text.strip())

            # Get best channels by RSSI
            best_rssi_channels = epy_block_1.get_best_channels_by_rssi(5)
            if best_rssi_channels:
                rssi_text = " BEST CHANNELS BY SIGNAL STRENGTH:\n"
                for i, (ch, avg_rssi, sample_count) in enumerate(best_rssi_channels, 1):
                    rssi_text += f"  {i}. Channel {ch}: {avg_rssi:.1f} dBm avg ({sample_count} samples)\n"
                rssi_label.setText(rssi_text.strip())

            # Update graph if matplotlib is available
            if matplotlib_available and hasattr(tb, '_graph_update'):
                tb._graph_update()
        except Exception as e:
            print(f"[STATS] Error updating display: {e}")

    def sweep_channel():
        if sweep_active[0]:
            try:
                print(f"[SWEEP] Switching to channel {channel_index[0]+1}/{len(channels)}...")
                sweep_changing[0] = True  # Set flag before changing
                original_set_freq(channels[channel_index[0]])
                sweep_changing[0] = False  # Clear flag after changing
                print(f"[SWEEP] Now at: {channels[channel_index[0]]/1e9:.3f} GHz")
                channel_index[0] = (channel_index[0] + 1) % len(channels)

                # Update statistics display
                update_statistics_display()
            except Exception as e:
                sweep_changing[0] = False  # Clear flag on error
                print(f"[SWEEP] ERROR: {e}")

    def resume_sweep():
        if not sweep_active[0]:
            sweep_active[0] = True
            tb._sweep_timer.start(time)
            update_status_label()
            print(f"[SWEEP] Resumed! Continuing sweep from channel {channel_index[0]+1}/{len(channels)}.")
        else:
            print("[SWEEP] Sweep is already active!")

    resume_button = QPushButton("Resume Sweep")
    resume_button.clicked.connect(resume_sweep)
    tb.top_layout.addWidget(resume_button)

    # Create statistics update timer (updates every 2 seconds)
    tb._stats_timer = QtCore.QTimer(tb)
    tb._stats_timer.timeout.connect(update_statistics_display)
    tb._stats_timer.start(2000)

    print("[SWEEP] Starting automatic WiFi channel sweep...")
    print(f"[SWEEP] Initial channel: {tb.freq / 1e9:.3f} GHz")
    print("[SWEEP] Use dropdown to pause or 'Resume Sweep' button to continue.")
    tb._sweep_timer = QtCore.QTimer(tb)
    tb._sweep_timer.timeout.connect(sweep_channel)
    tb._sweep_timer.start(time)
    print(f"[SWEEP] Timer started! Changing channel every {time / 1000} seconds...")
    print("[STATS] Statistics display updating every 2 seconds...")

def snipfcn_snippet_0_0(self):
    # Snippet for wireshark

    import os
    import subprocess
    import time

    # Path to the pipe
    pipe_path = '/tmp/gnuradio_wireshark.fifo'

    # Remove old pipe if exists
    if os.path.exists(pipe_path):
        os.remove(pipe_path)

    # Create named pipe
    os.mkfifo(pipe_path)
    print(f"[WIRESHARK] Pipe created: {pipe_path}")

    # Launch Wireshark in background
    try:
        subprocess.Popen(['wireshark', '-k', '-i', pipe_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        print("[WIRESHARK] Wireshark launched! Wait for window to open...")
        time.sleep(2)  # Give Wireshark time to start
    except FileNotFoundError:
        print("[WIRESHARK] ERROR: Wireshark not found! Install with: sudo apt install wireshark")
    except Exception as e:
        print(f"[WIRESHARK] ERROR launching: {e}")


def snippets_main_after_init(tb):
    snipfcn_snippet_0(tb)

def snippets_init_before_blocks(tb):
    snipfcn_snippet_0_0(tb)

class projeto(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "projeto")

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
        self.window_size = window_size = 48
        self.threshold = threshold = 0.8
        self.samp_rate = samp_rate = 20000000
        self.freq = freq = 2412000000
        self.algorithm = algorithm = 0

        ##################################################
        # Blocks
        ##################################################
        snippets_init_before_blocks(self)
        self._threshold_range = qtgui.Range(0.1, 0.99, 0.01, 0.8, 200)
        self._threshold_win = qtgui.RangeWidget(self._threshold_range, self.set_threshold, "Sync Short Threshold", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._threshold_win)
        # Create the options list
        self._freq_options = [2412000000, 2417000000, 2422000000, 2427000000, 2432000000, 2437000000, 2442000000, 2447000000, 2452000000, 2457000000, 2462000000, 2467000000, 2472000000, 2484000000, 5160000000, 5180000000, 5200000000, 5220000000, 5240000000, 5260000000, 5280000000, 5300000000, 5320000000, 5340000000, 5480000000, 5500000000, 5520000000, 5540000000, 5560000000, 5580000000, 5600000000, 5620000000, 5640000000, 5660000000, 5680000000, 5700000000, 5720000000, 5745000000, 5765000000, 5785000000, 5805000000, 5825000000, 5845000000, 5865000000, 5885000000]
        # Create the labels list
        self._freq_labels = ['CH1(2.412GHz)', 'CH2(2.417GHz)', 'CH3(2.422GHz)', 'CH4(2.427GHz)', 'CH5(2.432GHz)', 'CH6(2.437GHz)', 'CH7(2.442GHz)', 'CH8(2.447GHz)', 'CH9(2.452GHz)', 'CH10(2.457GHz)', 'CH11(2.462GHz)', 'CH12(2.467GHz)', 'CH13(2.472GHz)', 'CH14(2.484GHz)', 'CH32(5.16e9)', 'CH36(5.18e9)', 'CH40(5.20e9)', 'CH44(5.22e9)', 'CH48(5.24e9)', 'CH52(5.26e9)', 'CH56(5.28e9)', 'CH60(5.30e9)', 'CH64(5.32e9)', 'CH68(5.34e9)', 'CH96(5.48e9)', 'CH100(5.50e9)', 'CH104(5.52e9)', 'CH108(5.54e9)', 'CH112(5.56e9)', 'CH116(5.58e9)', 'CH120(5.60e9)', 'CH124(5.62e9)', 'CH128(5.64e9)', 'CH132(5.66e9)', 'CH136(5.68e9)', 'CH140(5.70e9)', 'CH144(5.72e9)', 'CH149(5.745e9)', 'CH153(5.765e9)', 'CH157(5.785e9)', 'CH161(5.805e9)', 'CH165(5.825e9)', 'CH169(5.845e9)', 'CH173(5.865e9)', 'CH177(5.885e9)']
        # Create the combo box
        self._freq_tool_bar = Qt.QToolBar(self)
        self._freq_tool_bar.addWidget(Qt.QLabel("WiFi Channel" + ": "))
        self._freq_combo_box = Qt.QComboBox()
        self._freq_tool_bar.addWidget(self._freq_combo_box)
        for _label in self._freq_labels: self._freq_combo_box.addItem(_label)
        self._freq_callback = lambda i: Qt.QMetaObject.invokeMethod(self._freq_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._freq_options.index(i)))
        self._freq_callback(self.freq)
        self._freq_combo_box.currentIndexChanged.connect(
            lambda i: self.set_freq(self._freq_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._freq_tool_bar, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._algorithm_options = [0, 1, 2, 3]
        # Create the labels list
        self._algorithm_labels = ['ieee802_11.LS', 'ieee802_11.LMS', 'ieee802_11.Linear Comb', 'ieee802_11.STA']
        # Create the combo box
        # Create the radio buttons
        self._algorithm_group_box = Qt.QGroupBox("algorithm" + ": ")
        self._algorithm_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._algorithm_button_group = variable_chooser_button_group()
        self._algorithm_group_box.setLayout(self._algorithm_box)
        for i, _label in enumerate(self._algorithm_labels):
            radio_button = Qt.QRadioButton(_label)
            self._algorithm_box.addWidget(radio_button)
            self._algorithm_button_group.addButton(radio_button, i)
        self._algorithm_callback = lambda i: Qt.QMetaObject.invokeMethod(self._algorithm_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._algorithm_options.index(i)))
        self._algorithm_callback(self.algorithm)
        self._algorithm_button_group.buttonClicked[int].connect(
            lambda i: self.set_algorithm(self._algorithm_options[i]))
        self.top_layout.addWidget(self._algorithm_group_box)
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('' if '' else iio.get_pluto_uri(), [True, True], 20000000)
        self.iio_pluto_source_0.set_len_tag_key('packet_len')
        self.iio_pluto_source_0.set_frequency(freq)
        self.iio_pluto_source_0.set_samplerate(samp_rate)
        self.iio_pluto_source_0.set_gain_mode(0, 'slow_attack')
        self.iio_pluto_source_0.set_gain(0, 64)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)
        self.ieee802_11_sync_short_0 = ieee802_11.sync_short(threshold, 2, False, False)
        self.ieee802_11_sync_long_0 = ieee802_11.sync_long(240, False, False)
        self.ieee802_11_parse_mac_0 = ieee802_11.parse_mac(True, False)
        self.ieee802_11_frame_equalizer_0 = ieee802_11.frame_equalizer(algorithm, freq, samp_rate, False, False)
        self.ieee802_11_decode_mac_0 = ieee802_11.decode_mac(True, False)
        self.foo_wireshark_connector_0 = foo.wireshark_connector(127, False)
        self.fir_filter_xxx_0_0 = filter.fir_filter_fff(1, [1] * window_size)
        self.fir_filter_xxx_0_0.declare_sample_delay(0)
        self.fir_filter_xxx_0 = filter.fir_filter_ccc(1, [1] * window_size)
        self.fir_filter_xxx_0.declare_sample_delay(0)
        self.fft_vxx_0 = fft.fft_vcc(64, True, [], True, 1)
        self.epy_block_1 = epy_block_1.wifi_info_printer()
        self.blocks_stream_to_vector_1 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 64)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, '/tmp/gnuradio_wireshark.fifo', False)
        self.blocks_file_sink_0.set_unbuffered(True)
        self.blocks_divide_xx_0 = blocks.divide_ff(1)
        self.blocks_delay_0_0 = blocks.delay(gr.sizeof_gr_complex*1, 240)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, 16)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.ieee802_11_decode_mac_0, 'out'), (self.ieee802_11_parse_mac_0, 'in'))
        self.msg_connect((self.ieee802_11_parse_mac_0, 'out'), (self.epy_block_1, 'in'))
        self.msg_connect((self.ieee802_11_parse_mac_0, 'out'), (self.foo_wireshark_connector_0, 'in'))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.fir_filter_xxx_0_0, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.ieee802_11_sync_short_0, 0))
        self.connect((self.blocks_delay_0_0, 0), (self.ieee802_11_sync_long_0, 1))
        self.connect((self.blocks_divide_xx_0, 0), (self.ieee802_11_sync_short_0, 2))
        self.connect((self.blocks_multiply_xx_0, 0), (self.fir_filter_xxx_0, 0))
        self.connect((self.blocks_stream_to_vector_1, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.ieee802_11_frame_equalizer_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.ieee802_11_sync_short_0, 1))
        self.connect((self.fir_filter_xxx_0_0, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.foo_wireshark_connector_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.ieee802_11_frame_equalizer_0, 0), (self.ieee802_11_decode_mac_0, 0))
        self.connect((self.ieee802_11_sync_long_0, 0), (self.blocks_stream_to_vector_1, 0))
        self.connect((self.ieee802_11_sync_short_0, 0), (self.blocks_delay_0_0, 0))
        self.connect((self.ieee802_11_sync_short_0, 0), (self.ieee802_11_sync_long_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.blocks_multiply_xx_0, 1))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "projeto")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_window_size(self):
        return self.window_size

    def set_window_size(self, window_size):
        self.window_size = window_size
        self.fir_filter_xxx_0.set_taps([1] * self.window_size)
        self.fir_filter_xxx_0_0.set_taps([1] * self.window_size)

    def get_threshold(self):
        return self.threshold

    def set_threshold(self, threshold):
        self.threshold = threshold

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.ieee802_11_frame_equalizer_0.set_bandwidth(self.samp_rate)
        self.iio_pluto_source_0.set_samplerate(self.samp_rate)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self._freq_callback(self.freq)
        self.ieee802_11_frame_equalizer_0.set_frequency(self.freq)
        self.iio_pluto_source_0.set_frequency(self.freq)

    def get_algorithm(self):
        return self.algorithm

    def set_algorithm(self, algorithm):
        self.algorithm = algorithm
        self._algorithm_callback(self.algorithm)
        self.ieee802_11_frame_equalizer_0.set_algorithm(self.algorithm)




def main(top_block_cls=projeto, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    snippets_main_after_init(tb)
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
