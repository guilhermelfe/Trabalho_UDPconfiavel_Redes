import pandas as pd
import matplotlib.pyplot as plt

ARQUIVO_LOG = "log_dados.csv"
TOTAL_PACOTES = 10000

def main():
    try:
        df = pd.read_csv(ARQUIVO_LOG)
    except FileNotFoundError:
        print(f"Arquivo '{ARQUIVO_LOG}' não encontrado.")
        return

    plt.style.use('ggplot')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15), sharex=True)

    #1: Vazão 
    # sem e com perdas
    ax1.plot(df['Tempo'], df['Acked'], label='Vazão Real (Com Controle + Perdas)', color='blue', linewidth=2)
    
    # sem perdas
    tempo_final = df['Tempo'].iloc[-1]
    ax1.plot([0, tempo_final], [0, TOTAL_PACOTES], label='Vazão Teórica Ideal (Sem Perdas)', color='green', linestyle='--', alpha=0.7)
    
    ax1.set_title('Vazão: Pacotes Entregues x Tempo')
    ax1.set_ylabel('Pacotes Confirmados (Acked)')
    ax1.legend()
    ax1.grid(True)

    #2: Congestionamento 
    # Atende: "Sem e com controle de congestionamento"
    ax2.plot(df['Tempo'], df['CWND'], label='CWND Real (TCP Reno)', color='blue')
    ax2.plot(df['Tempo'], df['SSTHRESH'], label='SSTHRESH', color='red', linestyle='--')
    

    # Sem controle
    ax2.plot(df['Tempo'], df['RWND'], label='Sem Controle (Envia Max RWND)', color='grey', linestyle=':', alpha=0.5)

    ax2.set_title('Janela de Congestionamento (Controle Dinâmico vs Fixo)')
    ax2.set_ylabel('Tamanho da Janela')
    ax2.legend()
    ax2.grid(True)

    # 3: Perdas
    ax3.plot(df['Tempo'], df['Perdas'], label='Perdas Acumuladas (Real)', color='black')
    ax3.set_title('Impacto das Perdas na Rede')
    ax3.set_xlabel('Tempo (s)')
    ax3.set_ylabel('Total de Pacotes Perdidos')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    plt.savefig("graficos_finais_relatorio.png", dpi=300)
    print("Gráfico gerado: graficos_finais_relatorio.png")
    plt.show()

if __name__ == "__main__":
    main()