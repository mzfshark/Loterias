import pandas as pd
import numpy as np
import os
import itertools

def gerar_palpite_simples(df):
    all_vals = df.values.flatten()
    freq = pd.Series(all_vals).value_counts()
    return freq.nlargest(15).index.astype(int).tolist()

def gerar_palpite_markov(df):
    seq = pd.to_numeric(df.values.flatten(), errors='coerce').dropna().astype(int)
    seq = [s for s in seq if 1 <= s <= 25]
    if len(seq) < 2:
        return []
    mat = np.ones((26, 26))
    for a, b in zip(seq, seq[1:]):
        mat[a, b] += 1
    trans = mat / mat.sum(axis=1, keepdims=True)
    probs = trans[seq[-1]][1:]
    return list(pd.Series(probs, index=range(1, 26)).nlargest(15).index.astype(int))

def gerar_palpites_beam(df, beam_width=3):
    if len(df) < 20:
        return []
    recent = df.tail(20)
    freq_norm = recent.apply(lambda col: col.value_counts(normalize=True)).fillna(0)
    global_freq = freq_norm.sum(axis=1).sort_values(ascending=False)
    candidates = list(global_freq.index.astype(int))
    combinations = itertools.combinations(candidates[:beam_width*2], 15)
    scored = []
    for combo in combinations:
        score = np.prod([global_freq.get(num, 0.01) for num in combo])
        scored.append((list(combo), score))
    top = sorted(scored, key=lambda x: x[1], reverse=True)[:beam_width]
    return [path for path, _ in top]

def salvar_relatorio(p1, p2, p3, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("## 🎯 Palpite Simples (Top 15 Frequências)\n")
        f.write(f"{p1}\n\n")
        f.write("## 🔁 Palpite Markov (Top 15 Transições)\n")
        f.write(f"{p2}\n\n")
        f.write("## 🤖 Palpites por Beam Search (Top Combinações)\n")
        for i, comb in enumerate(p3, start=1):
            f.write(f"{i}. {comb}\n")

if __name__ == "__main__":
    path = "Lotofacil/data/Lotofacil.csv"
    if not os.path.exists(path):
        print("Arquivo de dados não encontrado.")
        exit(1)
    df_raw = pd.read_csv(path)
    df = df_raw.iloc[:, 2:17]
    df.columns = [f"Coluna {i}" for i in range(1, 16)]
    if df.shape[1] < 15:
        salvar_relatorio([], [], [])
        exit(0)
    p1 = gerar_palpite_simples(df)
    p2 = gerar_palpite_markov(df)
    p3 = gerar_palpites_beam(df)
    salvar_relatorio(p1, p2, p3)
