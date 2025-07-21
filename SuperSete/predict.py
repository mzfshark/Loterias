import pandas as pd
import numpy as np

def gerar_palpite_simples(df):
    # Frequência simples por coluna
    palpites = []
    for col in df.columns[1:]:
        freq = df[col].value_counts().sort_values(ascending=False)
        palpites.append(freq.index[0])
    return palpites

if __name__ == "__main__":
    df = pd.read_csv("supersete/data/latest_draws.csv")
    palpite = gerar_palpite_simples(df)
    with open("supersete/report.md", "w") as f:
        f.write("# Palpite Automático Super Sete\n")
        f.write("Palpite baseado em frequência histórica:\n")
        f.write(str(palpite))

