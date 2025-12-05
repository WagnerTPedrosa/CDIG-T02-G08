"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import time
import threading

# Variável global para armazenar a última instância criada
_last_instance = None


class blk(gr.sync_block):
    """WiFi Channel Sweeper - Varre canais 2.4 GHz e 5 GHz automaticamente"""

    def __init__(self, pluto_source=None, interval_seconds=10):
        """
        pluto_source: Referência ao bloco PlutoSDR Source
        interval_seconds: Tempo em cada canal (default 10s)
        """
        gr.sync_block.__init__(
            self,
            name='WiFi Channel Sweeper',
            in_sig=None,
            out_sig=None
        )
        
        self.pluto_source = pluto_source
        
        # Armazena referência global APÓS gr.sync_block.__init__
        global _last_instance
        _last_instance = self
        self.top_block = None  # Será detectado automaticamente
        self.interval = interval_seconds
        self.running = False
        self.sweep_thread = None
        
        # Canais WiFi 2.4 GHz (1-11)
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
        
        # Inicia a thread de detecção e sweep com delay
        if pluto_source:
            self.sweep_thread = threading.Thread(target=self._init_and_sweep, daemon=True)
            self.sweep_thread.start()
    
    def _init_and_sweep(self):
        """Detecta o top_block e inicia o sweep (com delay para inicialização)"""
        # Aguarda 2 segundos para o flowgraph inicializar completamente
        time.sleep(2)
        
        # Tenta detectar o top_block
        try:
            import inspect
            frame = inspect.currentframe()
            for _ in range(15):  # Procura nos frames
                if frame is None:
                    break
                if 'self' in frame.f_locals:
                    obj = frame.f_locals['self']
                    if hasattr(obj, 'set_freq') and hasattr(obj, 'iio_pluto_source_0'):
                        self.top_block = obj
                        print(f"[SWEEP] Top block detectado: {type(obj).__name__}")
                        break
                frame = frame.f_back
        except Exception as e:
            print(f"[SWEEP] Erro ao detectar top_block: {e}")
        
        # Se não detectou, tenta obter do parent do pluto_source
        if self.top_block is None and self.pluto_source:
            try:
                # Navega na hierarquia do GNU Radio
                if hasattr(self.pluto_source, 'to_basic_block'):
                    basic_block = self.pluto_source.to_basic_block()
                    if hasattr(basic_block, 'detail'):
                        detail = basic_block.detail()
                        # Tenta acessar o flowgraph
                        if hasattr(detail, 'owner'):
                            parent = detail.owner()
                            if hasattr(parent, 'set_freq'):
                                self.top_block = parent
                                print(f"[SWEEP] Top block obtido via hierarquia GNU Radio")
            except Exception as e:
                print(f"[SWEEP] Não foi possível obter top_block via hierarquia: {e}")
        
        if self.top_block and self.pluto_source:
            self.start_sweep()
        else:
            print("[SWEEP ERRO] Não foi possível detectar o top_block automaticamente")
            print(f"[SWEEP DEBUG] pluto_source={self.pluto_source}, top_block={self.top_block}")
    
    def start_sweep(self):
        """Inicia o sweep automático"""
        if not self.running and self.pluto_source and self.top_block:
            self.running = True
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
                    # Atualizar variável freq no flowgraph (para o equalizer)
                    self.top_block.set_freq(freq)
                    
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
                        # Atualizar variável freq no flowgraph (para o equalizer)
                        self.top_block.set_freq(freq)
                        
                        print(f"\n{'='*60}")
                        print(f"[SWEEP] Canal {ch} ({band}) - {freq/1e9:.3f} GHz")
                        print(f"{'='*60}")
                        
                        time.sleep(self.interval)
                        
                    except Exception as e:
                        print(f"[SWEEP ERROR] Erro ao mudar para canal {ch}: {e}")
            
            if self.running:
                print(f"\n[SWEEP] Ciclo completo (2.4GHz + 5GHz) - reiniciando...")
    
    def stop(self):
        """Cleanup quando o flowgraph para"""
        self.stop_sweep()
        return True
    
    def work(self, input_items, output_items):
        """Não processa samples"""
        return 0
