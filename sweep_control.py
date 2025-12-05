"""
Channel Sweep Control Module
Add this to your GNU Radio flowgraph to enable channel sweeping functionality
"""

from PyQt5 import Qt
from PyQt5 import QtCore

def setup_sweep_control(tb):
    """
    Setup channel sweep control on a top_block instance.
    Call this after all GUI elements are created.
    
    Args:
        tb: The top_block (flowgraph) instance
    """
    # Initialize sweep state
    tb.current_channel_index = 0
    tb.sweep_enable = True
    tb.scan_interval = 2.0  # seconds
    
    # Disconnect original freq callback and reconnect with sweep pause
    tb._freq_combo_box.currentIndexChanged.disconnect()
    tb._freq_combo_box.currentIndexChanged.connect(
        lambda i: manual_channel_select(tb, i))
    
    # Add sweep control button
    tb._sweep_button = Qt.QPushButton("Pause Sweep")
    tb._sweep_button.clicked.connect(lambda: toggle_sweep(tb))
    tb.top_layout.addWidget(tb._sweep_button)
    
    # Setup channel sweep timer
    tb.channel_sweep_timer = Qt.QTimer()
    tb.channel_sweep_timer.timeout.connect(lambda: sweep_next_channel(tb))
    if tb.sweep_enable:
        tb.channel_sweep_timer.start(int(tb.scan_interval * 1000))
    
    print("\n*** Channel Sweep Control initialized ***")
    print(f"*** Sweeping {len(tb._freq_options)} channels every {tb.scan_interval} seconds ***\n")


def sweep_next_channel(tb):
    """Advance to next channel in the list"""
    tb.current_channel_index = (tb.current_channel_index + 1) % len(tb._freq_options)
    new_freq = tb._freq_options[tb.current_channel_index]
    channel_label = tb._freq_labels[tb.current_channel_index]
    print(f"\n=== Scanning {channel_label} ===")
    tb.set_freq(new_freq)


def toggle_sweep(tb):
    """Toggle sweep on/off via button"""
    if tb.sweep_enable:
        # Pausing
        tb.channel_sweep_timer.stop()
        tb.sweep_enable = False
        tb._sweep_button.setText("Resume Sweep")
        print("\n*** Channel sweep PAUSED ***")
    else:
        # Resuming
        tb.sweep_enable = True
        tb._sweep_button.setText("Pause Sweep")
        tb.channel_sweep_timer.start(int(tb.scan_interval * 1000))
        print("\n*** Channel sweep RESUMED ***")


def manual_channel_select(tb, index):
    """Handle manual channel selection from dropdown"""
    # Pause sweep when user manually selects a channel
    if tb.sweep_enable:
        tb.channel_sweep_timer.stop()
        tb.sweep_enable = False
        tb._sweep_button.setText("Resume Sweep")
        print("\n*** Channel sweep PAUSED (manual selection) ***")
    
    tb.current_channel_index = index
    tb.set_freq(tb._freq_options[index])
    print(f"\n=== Manual: {tb._freq_labels[index]} ===")
