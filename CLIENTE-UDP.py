import socket
import time
import threading
import csv
import base64

#CONFIGS
serverAddressPort   = ("127.0.0.1", 20001)
bufferSize          = 4096
TIMEOUT_INTERVAL    = 1.0  
TOTAL_PACOTES       = 10000 
ARQUIVO_LOG         = "log_dados.csv"

#CRIPTOGRAFIA (XOR + BASE64) 
CHAVE_SECRETA = 123 

def criptografar(texto_plano):
    # 1- Aplica XOR
    cifrado = ''.join(chr(ord(c) ^ CHAVE_SECRETA) for c in texto_plano)
    # 2- Codifica para Base64
    return base64.b64encode(cifrado.encode('latin-1')).decode('utf-8')

def descriptografar(texto_cifrado_b64):
    try:
        # 1- Decodifica Base64
        texto_cifrado = base64.b64decode(texto_cifrado_b64).decode('latin-1')
        # 2- XOR Reverso
        return ''.join(chr(ord(c) ^ CHAVE_SECRETA) for c in texto_cifrado)
    except:
        return ""

# SOCKET 
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(("0.0.0.0", 0)) 

#CONTROLE DE FLUXO
cwnd = 1.0          
ssthresh = 64       
rwnd = 100          
estado_cong = 'SLOW_START'

base = 0                 
next_seq_num = 0         
ack_received = [False] * TOTAL_PACOTES 
packet_timers = {}       
lock = threading.Lock()
executando = True

# Prepara Log
with open(ARQUIVO_LOG, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Tempo", "CWND", "SSTHRESH", "InFlight", "RWND", "Perdas", "Acked"])

start_time_global = time.time()
perdas_contador = 0

def realizar_handshake():
    print("Tentando Handshake...")
    UDPClientSocket.settimeout(2)
    try:
        # Enviando SYN puro sem criptografia no handshake
        UDPClientSocket.sendto("SYN".encode('utf-8'), serverAddressPort)
        msg, _ = UDPClientSocket.recvfrom(bufferSize)
        if msg.decode('utf-8') == "SYN-ACK":
            print("Handshake OK! Iniciando transmissão segura.")
            UDPClientSocket.settimeout(None)
            return True
    except socket.timeout:
        print("Erro: Servidor offline ou IP incorreto.")
        return False
    return False

def thread_escuta_ack():
    global base, cwnd, ssthresh, rwnd, estado_cong, executando
    
    while base < TOTAL_PACOTES and executando:
        try:
            msg_bytes, _ = UDPClientSocket.recvfrom(bufferSize)
            msg_raw = msg_bytes.decode('utf-8').strip()
            
            # Tenta descriptografar
            msg_plana = descriptografar(msg_raw)
            
            if msg_plana.startswith("ACK"):
                partes = msg_plana.split("|")
                ack_seq = int(partes[1])
                rwnd_recebido = int(partes[2])
                
                with lock:
                    rwnd = rwnd_recebido
                    if 0 <= ack_seq < TOTAL_PACOTES:
                        if not ack_received[ack_seq]:
                            ack_received[ack_seq] = True
                            
                            # Reno Simplificado
                            if estado_cong == 'SLOW_START':
                                cwnd += 1 
                                if cwnd >= ssthresh:
                                    estado_cong = 'CONGESTION_AVOIDANCE'
                            elif estado_cong == 'CONGESTION_AVOIDANCE':
                                cwnd += 1.0 / int(cwnd) 
                            
                            if ack_seq in packet_timers:
                                del packet_timers[ack_seq]

                        while base < TOTAL_PACOTES and ack_received[base]:
                            base += 1

        except ConnectionResetError:
            pass #ignorar erro de porta do Windows
        except Exception as e:
            pass 

if realizar_handshake():
    t = threading.Thread(target=thread_escuta_ack, daemon=True)
    t.start()

    print(f"Enviando {TOTAL_PACOTES} pacotes...")

    while base < TOTAL_PACOTES:
        with lock:
            janela_efetiva = min(cwnd, rwnd)
            
            # ENVIA NOVOS PACOTES
            while next_seq_num < base + janela_efetiva and next_seq_num < TOTAL_PACOTES:
                if not ack_received[next_seq_num]:
                    if next_seq_num not in packet_timers:
                        
                        # Visualização de progresso.......
                        if next_seq_num < 20 or next_seq_num % 500 == 0:
                            print(f"[Enviando] Seq {next_seq_num}")
                        
                        payload = f"D{next_seq_num}" # Payload curto
                        msg_plain = f"{next_seq_num}|DATA|{payload}"
                        
                        # Criptografa e envia
                        msg_final = criptografar(msg_plain)
                        UDPClientSocket.sendto(msg_final.encode('utf-8'), serverAddressPort)
                        packet_timers[next_seq_num] = time.time()
                next_seq_num += 1

            # TIMEOUTS
            timeout_ocorreu = False
            # otimização - verifica apenas pacotes na janela
            limite = int(min(base + cwnd + 50, TOTAL_PACOTES))
            
            for seq in range(base, limite):
                if seq in packet_timers and not ack_received[seq]:
                    if (time.time() - packet_timers[seq] > TIMEOUT_INTERVAL):
                        print(f"[Timeout] Pacote {seq}. Reenviando...")
                        
                        msg_plain = f"{seq}|DATA|D{seq}"
                        msg_final = criptografar(msg_plain)
                        UDPClientSocket.sendto(msg_final.encode('utf-8'), serverAddressPort)
                        packet_timers[seq] = time.time() 
                        
                        timeout_ocorreu = True
                        perdas_contador += 1

            if timeout_ocorreu:
                ssthresh = max(2, cwnd / 2)
                cwnd = 1
                estado_cong = 'SLOW_START'
                # ajuste de janela após timeout

       # LOG
        tempo_atual = time.time() - start_time_global
        with open(ARQUIVO_LOG, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([f"{tempo_atual:.2f}", f"{cwnd:.2f}", ssthresh, (next_seq_num-base), rwnd, perdas_contador, base])
        
        if base % 500 == 0 and base > 0:
            print(f"Status: Base {base}/{TOTAL_PACOTES} | CWND {cwnd:.1f}")

        time.sleep(0.005) # Loop pequeno para evitar a CPU 100%

    executando = False
    print("Fim da transmissão!")
    UDPClientSocket.close()
else:
    print("Falha.")