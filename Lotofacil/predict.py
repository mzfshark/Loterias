import pandas as pd
import numpy as np
import os

def gerar_palpite_simples(df):
    # Para cada posição (coluna), escolhe o valor mais frequente
    palpites = []
    for col in df.columns:
        freq = df[col].value_counts().sort_values(ascending=False)
        palpites.append(int(freq.index[0]) if not freq.empty else -1)
    return palpites


def gerar_palpite_markov(df):
    # Cadeia de Markov de 1ª ordem por coluna
    palpites = []
    for col in df.columns:
        seq = df[col].dropna().astype(int).tolist()
        if len(seq) < 2:
            palpites.append(-1)
            continue
        mat = np.ones((max(seq)+1, max(seq)+1))
        for a, b in zip(seq, seq[1:]):
            mat[a, b] += 1
        trans = mat / mat.sum(axis=1, keepdims=True)
        palpites.append(int(np.argmax(trans[seq[-1]])))
    return palpites


def gerar_palpites_beam(df, beam_width=3):
    # Beam search usando última janela de 20 concursos
    if len(df) < 20:
        return [[-1] * df.shape[1]]
    recent = df.tail(20)
    freq_norm = {col: recent[col].value_counts(normalize=True) for col in df.columns}
    sorted_vals = {col: list(freq_norm[col].sort_values(ascending=False).index) for col in df.columns}
    beam = [[v] for v in sorted_vals[df.columns[0]][:beam_width]]
    for col in df.columns[1:]:
        candidates = []
        for path in beam:
            for v in sorted_vals[col][:beam_width]:
                new_path = path + [v]
                prob = np.prod([freq_norm[c].get(val, 0.01) for c, val in zip(df.columns[:len(new_path)], new_path)])
                candidates.append((new_path, prob))
        candidates.sort(key=lambda x: x[1], reverse=True)
        beam = [p for p, _ in candidates[:beam_width]]
    return beam


def salvar_relatorio(p1, p2, p3, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("## 🎯 Palpite Simples (Frequência Histórica)\n")
        f.write(f"{p1}\n\n")
        f.write("## 🔁 Palpite Markov 1ª Ordem\n")
        f.write(f"{p2}\n\n")
        f.write("## 🤖 Top Palpites por Beam Search (base 20 concursos)\n")
        for i, beam in enumerate(p3, start=1):
            f.write(f"{i}. {beam}\n")


if __name__ == "__main__":
    path = "Lotofacil/data/Lotofacil.csv"
    if not os.path.exists(path):
        print("Arquivo de dados não encontrado.")
        exit(1)

    df_raw = pd.read_csv(path)
    # Mapear colunas 3 a 17 como Coluna 1..15
    df = df_raw.iloc[:, 2:17]
    df.columns = [f"Coluna {i}" for i in range(1, 16)]

    if df.shape[1] != 15:
        print("Dados insuficientes para gerar palpites.")
        salvar_relatorio([], [], [])
        exit(0)

    palpite_simples = gerar_palpite_simples(df)
    palpite_markov = gerar_palpite_markov(df)
    palpites_beam = gerar_palpites_beam(df)

    salvar_relatorio(palpite_simples, palpite_markov, palpites_beam)
