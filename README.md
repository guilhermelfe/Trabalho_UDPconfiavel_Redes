# Trabalho_UDPconfiavel_Redes
Trabalho de Redes de Computadores sobre adicionar confiabilidade ao UDP

## Funcionalidades Implementadas

- Confiabilidade e Ordem: Uso de números de sequência e buffers para garantir a entrega ordenada e reenviar apenas pacotes perdidos (Repetição Seletiva).
- Controle de Congestionamento (TCP Reno): Implementação dos algoritmos Slow Start e Congestion Avoidance para ajuste dinâmico da janela de envio (cwnd).
- Controle de Fluxo: Monitoramento da janela de recepção (rwnd) informada nos ACKs para respeitar a capacidade do destinatário.
- Segurança (Handshake): Estabelecimento de conexão via 3-Way Handshake simplificado (SYN e SYN-ACK).
- Segurança (Criptografia): Ofuscamento de dados com cifra XOR e encapsulamento em Base64 para integridade.
- Simulação: Testes realizados com envio de 10.000 pacotes e taxa de perda de 2% no servidor.

## Arquivos do Projeto

- SERVIDOR-UDP.py: Recebe os pacotes, gerencia o buffer de reordenação, simula perdas aleatórias e envia confirmações (ACKs) com o tamanho da janela disponível.
- CLIENTE-UDP.py: Realiza o handshake, criptografa os dados, gerencia a janela deslizante e detecta timeouts.
- dados.py: Script responsável por plotar os gráficos de congestionamento, fluxo e perdas acumuladas.
