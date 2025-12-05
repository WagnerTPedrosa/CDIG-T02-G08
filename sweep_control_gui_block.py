"""
Embedded Python Block: Sweep Control GUI
"""

from PyQt5 import Qt, QtCore
from gnuradio import gr
import pmt

class sweep_control_gui(gr.sync_block):
    """
    GUI para controlar o channel sweep
    """
    def __init__(self, sweeper_callback=None):
        gr.sync_block.__init__(
            self,
            name='Sweep Control GUI',
            in_sig=None,
            out_sig=None
        )
        
        self.sweeper_callback = sweeper_callback
        
        # Criar widget GUI
        self.widget = Qt.QWidget()
        self.layout = Qt.QVBoxLayout()
        self.widget.setLayout(self.layout)
        
        # Título
        title = Qt.QLabel("Channel Sweep Control")
        title.setStyleSheet("QLabel { font-weight: bold; font-size: 16px; }")
        self.layout.addWidget(title)
        
        # Botões
        button_layout = Qt.QHBoxLayout()
        self.start_btn = Qt.QPushButton("▶ Start Sweep")
        self.stop_btn = Qt.QPushButton("⏸ Stop Sweep")
        
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; }")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; font-weight: bold; }")
        
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        self.layout.addLayout(button_layout)
        
        # Status
        self.status_label = Qt.QLabel("Status: Stopped")
        self.status_label.setStyleSheet("QLabel { font-size: 14px; padding: 8px; background-color: #f0f0f0; border-radius: 4px; }")
        self.layout.addWidget(self.status_label)
        
        # Info
        info = Qt.QLabel("Varre canais 2.4GHz (1-11) e 5GHz (36-165)\n10 segundos por canal")
        info.setStyleSheet("QLabel { font-size: 11px; color: #666; padding: 4px; }")
        self.layout.addWidget(info)
        
    def on_start(self):
        """Callback para botão Start"""
        if self.sweeper_callback:
            self.sweeper_callback('start')
            self.status_label.setText("Status: ✓ Sweeping...")
            self.status_label.setStyleSheet("QLabel { font-size: 14px; padding: 8px; background-color: #4CAF50; color: white; border-radius: 4px; font-weight: bold; }")
    
    def on_stop(self):
        """Callback para botão Stop"""
        if self.sweeper_callback:
            self.sweeper_callback('stop')
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("QLabel { font-size: 14px; padding: 8px; background-color: #f0f0f0; border-radius: 4px; }")
    
    def get_widget(self):
        """Retorna o widget para ser adicionado ao GUI"""
        return self.widget
    
    def work(self, input_items, output_items):
        """Não processa samples"""
        return 0
