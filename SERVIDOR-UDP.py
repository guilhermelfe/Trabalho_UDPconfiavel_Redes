import socket
import random
import base64

#CONFIGS
localIP     = "127.0.0.1"
localPort   = 20001
bufferSize  = 4096 
MAX_APP_BUFFER = 100  
PROBABILIDADE_PERDA = 0.02 

# CRIPTOGRAFIA (XOR + BASE64) 
CHAVE_SECRETA = 123 

def descriptografar(texto_cifrado_b64):
    try:
        # 1- Decodifica Base64 de volta para string cifrada
        texto_cifrado = base64.b64decode(texto_cifrado_b64).decode('latin-1')
        # 2- Aplica XOR reverso
        return ''.join(chr(ord(c) ^ CHAVE_SECRETA) for c in texto_cifrado)
    except:
        return None

def criptografar(texto_plano):
    # 1- Aplica XOR
    cifrado = ''.join(chr(ord(c) ^ CHAVE_SECRETA) for c in texto_plano)
    # 2- codifica para Base64 pra viajar seguramente na rede
    return base64.b64encode(cifrado.encode('latin-1')).decode('utf-8')

# SCOKET SETUP 
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((localIP, localPort))

print(f"=== Servidor UDP (Base64 Safe) Rodando em {localIP}:{localPort} ===")

buffer_pacotes = {} 
proximo_esperado = 0 
handshake_feito = False

while True:
    try:
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        # Recebe bytes puros e tenta decodificar como string
        mensagem_raw = bytesAddressPair[0].decode('utf-8').strip()
        address = bytesAddressPair[1]

        # handshake
        if mensagem_raw == "SYN":
            print(f"[Handshake] Novo cliente conectado: {address}")
            UDPServerSocket.sendto("SYN-ACK".encode('utf-8'), address)
            handshake_feito = True
            buffer_pacotes = {} 
            proximo_esperado = 0
            continue

        if not handshake_feito:
            continue

        # descriptografia
        mensagem_plana = descriptografar(mensagem_raw)
        
        if mensagem_plana is None:
            print("[Erro] Falha na descriptografia. Pacote ignorado.")
            continue

        # SEQ/RWND/DADOS
        try:
            partes = mensagem_plana.split("|", 2)
            seq = int(partes[0])
            conteudo = partes[2]
        except:
            print("[Erro] Formato inválido após descriptografia.")
            continue

        # simulação de perda
        if random.random() < PROBABILIDADE_PERDA:
            continue 

        # CONTROLE DE FLUXO
        pacotes_pendentes = len(buffer_pacotes)
        rwnd = MAX_APP_BUFFER - pacotes_pendentes
        if rwnd < 0: rwnd = 0

        # envia ACK
        msg_ack_plain = f"ACK|{seq}|{rwnd}"
        msg_ack_cifrada = criptografar(msg_ack_plain)
        UDPServerSocket.sendto(msg_ack_cifrada.encode('utf-8'), address)

        # Entrega em ordem
        if seq == proximo_esperado:
            proximo_esperado += 1
            while proximo_esperado in buffer_pacotes:
                del buffer_pacotes[proximo_esperado]
                proximo_esperado += 1
            
            if proximo_esperado % 500 == 0:
                print(f"[Progresso] Recebidos corretamente: {proximo_esperado}")

        elif seq > proximo_esperado:
            if seq not in buffer_pacotes and len(buffer_pacotes) < MAX_APP_BUFFER:
                buffer_pacotes[seq] = conteudo
        
    except Exception as e:
        print(f"[Erro Fatal Servidor] {e}")