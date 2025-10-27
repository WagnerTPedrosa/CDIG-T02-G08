#!/usr/bin/env python3
"""
Capturador de pacotes WiFi GNU Radio para Wireshark
Conecta diretamente ao socket TCP e cria arquivo PCAP
"""
import socket
import sys
import time
import struct
import os

def create_pcap_header():
    """Criar cabeçalho PCAP válido"""
    # PCAP Global Header (24 bytes)
    magic = 0xa1b2c3d4        # Magic number (little endian)
    version_major = 2         # Version major
    version_minor = 4         # Version minor  
    thiszone = 0              # GMT offset
    sigfigs = 0               # Timestamp accuracy
    snaplen = 65535           # Max packet length
    network = 127             # Data link type (IEEE 802.11)
    
    return struct.pack('<LHHLLLL', magic, version_major, version_minor, 
                      thiszone, sigfigs, snaplen, network)

def create_packet_header(packet_data, timestamp):
    """Criar cabeçalho do pacote PCAP"""
    ts_sec = int(timestamp)
    ts_usec = int((timestamp - ts_sec) * 1000000)
    incl_len = len(packet_data)
    orig_len = len(packet_data)
    
    return struct.pack('<LLLL', ts_sec, ts_usec, incl_len, orig_len)

def capture_to_file(output_file):
    """Capturar pacotes do GNU Radio e salvar em arquivo PCAP"""
    
    print(f"🔗 Conectando ao GNU Radio (porta 12345)...")
    
    try:
        # Conectar ao GNU Radio
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Increased timeout
        print("📡 Tentando conectar...")
        sock.connect(('localhost', 12345))
        print("✅ Conectado com sucesso!")
        
        # Set socket to non-blocking after connection
        sock.settimeout(1.0)
        
        # Abrir arquivo de saída
        with open(output_file, 'wb') as f:
            # Escrever cabeçalho PCAP
            f.write(create_pcap_header())
            print(f"📁 Arquivo PCAP criado: {output_file}")
            
            packet_count = 0
            start_time = time.time()
            
            print("📦 Aguardando pacotes WiFi...")
            print("   (Pressione Ctrl+C para parar)")
            
            while True:
                try:
                    # Receber dados do GNU Radio
                    data = sock.recv(4096)
                    if not data:
                        print("❌ Conexão fechada pelo GNU Radio")
                        break
                    
                    # Skip if data is too small or looks like control data
                    if len(data) < 10:
                        print(f"⚠️  Dados muito pequenos ignorados: {len(data)} bytes")
                        continue
                    
                    # Timestamp atual
                    timestamp = time.time()
                    
                    # Escrever cabeçalho do pacote
                    packet_header = create_packet_header(data, timestamp)
                    f.write(packet_header)
                    
                    # Escrever dados do pacote
                    f.write(data)
                    f.flush()  # Forçar escrita no disco
                    
                    packet_count += 1
                    elapsed = time.time() - start_time
                    
                    print(f"📦 Pacote {packet_count}: {len(data)} bytes "
                          f"(tempo: {elapsed:.1f}s)")
                    
                except socket.timeout:
                    print("⏱️  Timeout - ainda aguardando pacotes...")
                    continue
                except KeyboardInterrupt:
                    print(f"\n🛑 Captura interrompida pelo usuário")
                    break
                except Exception as e:
                    print(f"❌ Erro ao processar dados: {e}")
                    continue
                    
        print(f"✅ Captura finalizada: {packet_count} pacotes salvos")
        
    except ConnectionRefusedError:
        print("❌ Erro: GNU Radio não está rodando na porta 12345")
        print("   Execute: python projeto.py &")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    finally:
        sock.close()
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 capture_wifi_pcap.py <arquivo_saida.pcap>")
        print("Exemplo: python3 capture_wifi_pcap.py wifi_capture.pcap")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    # Verificar se arquivo já existe (mas não para pipes)
    if os.path.exists(output_file) and not output_file.startswith('/tmp/'):
        response = input(f"⚠️  Arquivo {output_file} já existe. Sobrescrever? (s/N): ")
        if response.lower() != 's':
            print("❌ Operação cancelada")
            sys.exit(1)
    
    print("=" * 60)
    print("📡 Capturador WiFi GNU Radio → PCAP")
    print("=" * 60)
    
    if capture_to_file(output_file):
        print(f"\n🎉 Sucesso! Arquivo salvo: {output_file}")
        print(f"📊 Para abrir no Wireshark:")
        print(f"   wireshark {output_file}")
        print(f"   ou")
        print(f"   File → Open → {output_file}")

if __name__ == "__main__":
    main()
