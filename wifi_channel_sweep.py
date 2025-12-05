"""
WiFi Channel Sweep - Varre canais WiFi 2.4 GHz automaticamente
"""
import time
from gnuradio import gr

class channel_sweeper(gr.hier_block2):
    """
    Faz sweep automático entre canais WiFi
    """
    def __init__(self, pluto_source, frame_equalizer, top_block, interval_seconds=10):
        gr.hier_block2.__init__(
            self, "WiFi Channel Sweeper",
            gr.io_signature(0, 0, 0),
            gr.io_signature(0, 0, 0),
        )
        
        self.pluto_source = pluto_source
        self.frame_equalizer = frame_equalizer
        self.top_block = top_block
        self.interval = interval_seconds
        self.running = False
        self.sweep_thread = None
        
        # Canais WiFi 2.4 GHz (1-11) e 5 GHz (36-165)
        self.channels_24ghz = {
            1: (2.412e9, '2.4GHz'),
            2: (2.417e9, '2.4GHz'),
            3: (2.422e9, '2.4GHz'),
            4: (2.427e9, '2.4GHz'),
            5: (2.432e9, '2.4GHz'),
            6: (2.437e9, '2.4GHz'),
            7: (2.442e9, '2.4GHz'),
            8: (2.447e9, '2.4GHz'),
            9: (2.452e9, '2.4GHz'),
            10: (2.457e9, '2.4GHz'),
            11: (2.462e9, '2.4GHz'),
        }
        
        # Canais 5 GHz mais comuns (802.11a/n/ac)
        self.channels_5ghz = {
            36: (5.180e9, '5GHz'),
            40: (5.200e9, '5GHz'),
            44: (5.220e9, '5GHz'),
            48: (5.240e9, '5GHz'),
            52: (5.260e9, '5GHz'),
            56: (5.280e9, '5GHz'),
            60: (5.300e9, '5GHz'),
            64: (5.320e9, '5GHz'),
            149: (5.745e9, '5GHz'),
            153: (5.765e9, '5GHz'),
            157: (5.785e9, '5GHz'),
            161: (5.805e9, '5GHz'),
            165: (5.825e9, '5GHz'),
        }
        
        self.current_channel_idx = 0
        
    def start_sweep(self):
        """Inicia o sweep automático"""
        if not self.running:
            self.running = True
            import threading
            self.sweep_thread = threading.Thread(target=self._sweep_loop, daemon=True)
            self.sweep_thread.start()
            print("[SWEEP] Iniciado - varrendo 2.4 GHz (canais 1-11) e 5 GHz (canais 36-165)")
    
    def stop_sweep(self):
        """Para o sweep"""
        self.running = False
        if self.sweep_thread:
            self.sweep_thread.join(timeout=2)
        print("[SWEEP] Parado")
    
    def _sweep_loop(self):
        """Loop principal do sweep"""
        
        while self.running:
            # Varre canais 2.4 GHz
            print(f"\n{'#'*60}")
            print(f"# Varrendo banda 2.4 GHz (802.11b/g/n)")
            print(f"{'#'*60}")
            
            for ch in sorted(self.channels_24ghz.keys()):
                if not self.running:
                    break
                    
                freq, band = self.channels_24ghz[ch]
                try:
                    # Atualizar PlutoSDR
                    self.pluto_source.set_frequency(int(freq))
                    # Atualizar variável freq no flowgraph
                    self.top_block.set_freq(freq)
                    # Atualizar frame equalizer com nova frequência
                    # (o equalizer usa freq internamente)
                    
                    print(f"\n{'='*60}")
                    print(f"[SWEEP] Canal {ch} ({band}) - {freq/1e9:.3f} GHz")
                    print(f"{'='*60}")
                    
                    time.sleep(self.interval)
                    
                except Exception as e:
                    print(f"[SWEEP ERROR] Erro ao mudar para canal {ch}: {e}")
            
            # Varre canais 5 GHz
            if self.running:
                print(f"\n{'#'*60}")
                print(f"# Varrendo banda 5 GHz (802.11a/n/ac)")
                print(f"{'#'*60}")
                
                for ch in sorted(self.channels_5ghz.keys()):
                    if not self.running:
                        break
                        
                    freq, band = self.channels_5ghz[ch]
                    try:
                        # Atualizar PlutoSDR
                        self.pluto_source.set_frequency(int(freq))
                        # Atualizar variável freq no flowgraph
                        self.top_block.set_freq(freq)
                        
                        print(f"\n{'='*60}")
                        print(f"[SWEEP] Canal {ch} ({band}) - {freq/1e9:.3f} GHz")
                        print(f"{'='*60}")
                        
                        time.sleep(self.interval)
                        
                    except Exception as e:
                        print(f"[SWEEP ERROR] Erro ao mudar para canal {ch}: {e}")
            
            if self.running:
                print(f"\n[SWEEP] Ciclo completo (2.4GHz + 5GHz) - reiniciando...")
