import pandas as pd
import numpy as np


def gerar_palpite_simples(df):
    palpites = []
    for col in df.columns[1:]:
        freq = df[col].value_counts().sort_values(ascending=False)
        palpites.append(freq.index[0])
    return palpites

def gerar_palpite_markov(df):
    palpites = []
    for col in df.columns[1:]:
        series = df[col].tolist()
        mat = np.ones((10, 10))
        for i in range(len(series) - 1):
            mat[series[i]][series[i + 1]] += 1
        transition = (mat.T / mat.sum(axis=1)).T
        last = series[-1]
        palpites.append(int(np.argmax(transition[last])))
    return palpites

def gerar_palpites_beam(df, beam_width=3):
    recent = df.tail(20)
    freq_df = {
        col: recent[col].value_counts(normalize=True).sort_index()
        for col in df.columns[1:]
    }
    sorted_digits = {
        col: freq_df[col].sort_values(ascending=False).index.tolist()
        for col in freq_df
    }
    beam = [[d] for d in sorted_digits[df.columns[1]][:beam_width]]
    for col in df.columns[2:]:
        new_beam = []
        for path in beam:
            for d in sorted_digits[col][:beam_width]:
                new_path = path + [d]
                prob = np.prod([
                    freq_df[c][val] if val in freq_df[c] else 0.01
                    for c, val in zip(df.columns[1:], new_path)
                ])
                new_beam.append((new_path, prob))
        new_beam = sorted(new_beam, key=lambda x: x[1], reverse=True)[:beam_width]
        beam = [b for b, _ in new_beam]
    return beam

def salvar_relatorio(p1, p2, p3, path="supersete/report.md"):
    with open(path, "w") as f:
        f.write("# Palpite Automático Super Sete\n\n")
        f.write("## 🎯 Palpite Simples (Frequência Histórica)\n")
        f.write(f"{p1}\n\n")

        f.write("## 🔁 Palpite Markov 1ª Ordem\n")
        f.write(f"{p2}\n\n")

        f.write("## 🤖 Top Palpites por Beam Search (base 20 concursos)\n")
        for i, beam in enumerate(p3):
            f.write(f"{i+1}. {beam}\n")

if __name__ == "__main__":
    df = pd.read_csv("supersete/data/latest_draws.csv")

    palpite_simples = gerar_palpite_simples(df)
    palpite_markov = gerar_palpite_markov(df)
    palpites_beam = gerar_palpites_beam(df)

    salvar_relatorio(palpite_simples, palpite_markov, palpites_beam)
