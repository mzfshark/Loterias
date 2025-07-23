import pandas as pd
import numpy as np
import os
import itertools


def gerar_palpite_simples(df):
    print("[DEBUG] gerar_palpite_simples: start")
    print(f"[DEBUG] DataFrame shape: {df.shape}")
    all_vals = df.values.flatten()
    print(f"[DEBUG] Number of total values: {len(all_vals)}")
    freq = pd.Series(all_vals).value_counts()
    top15 = freq.nlargest(15).index.astype(int).tolist()
    print(f"[DEBUG] Top15 simples: {top15}")
    return top15


def gerar_palpite_markov(df):
    print("[DEBUG] gerar_palpite_markov: start")
    series_vals = pd.Series(df.values.flatten())
    seq = pd.to_numeric(series_vals, errors='coerce').dropna().astype(int).tolist()
    seq = [s for s in seq if 1 <= s <= 25]
    print(f"[DEBUG] Sequence length after filter: {len(seq)}")
    if len(seq) < 2:
        print("[DEBUG] Sequence too short for Markov, returning []")
        return []
    mat = np.ones((26, 26))
    for a, b in zip(seq, seq[1:]):
        mat[a, b] += 1
    trans = mat / mat.sum(axis=1, keepdims=True)
    last = seq[-1]
    probs = trans[last][1:]
    top15 = list(pd.Series(probs, index=range(1, 26)).nlargest(15).index.astype(int))
    print(f"[DEBUG] Top15 markov for last={last}: {top15}")
    return top15


def gerar_palpites_beam(df, beam_width=3):
    print("[DEBUG] gerar_palpites_beam: start")
    if len(df) < 20:
        print(f"[DEBUG] Not enough data for beam search (len={len(df)}), returning []")
        return []
    recent = df.tail(20)
    print(f"[DEBUG] Recent window shape: {recent.shape}")
    freq_norm = recent.apply(lambda col: col.value_counts(normalize=True)).fillna(0)
    global_freq = freq_norm.sum(axis=1).sort_values(ascending=False)
    print(f"[DEBUG] Global freq head: {global_freq.head().to_dict()}")
    candidates = list(global_freq.index.astype(int))
    combos = itertools.combinations(candidates[:beam_width*2], 15)
    scored = []
    for combo in combos:
        score = np.prod([global_freq.get(num, 0.01) for num in combo])
        scored.append((list(combo), score))
    top = sorted(scored, key=lambda x: x[1], reverse=True)[:beam_width]
    print(f"[DEBUG] Beam top paths: {[path for path, _ in top]}")
    return [path for path, _ in top]


def salvar_relatorio(p1, p2, p3, path="Lotofacil/docs/index.md"):
    print(f"[DEBUG] salvar_relatorio: path={path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("## 🎯 Palpite Simples (Top 15 Frequências)\n")
        f.write(f"{p1}\n\n")
        f.write("## 🔁 Palpite Markov (Top 15 Transições)\n")
        f.write(f"{p2}\n\n")
        f.write("## 🤖 Palpites por Beam Search (Top Combinações)\n")
        for i, comb in enumerate(p3, start=1):
            f.write(f"{i}. {comb}\n")
    print("[DEBUG] Report saved successfully")


if __name__ == "__main__":
    path = "Lotofacil/data/Lotofacil.csv"
    print(f"[DEBUG] Loading data from {path}")
    if not os.path.exists(path):
        print("Arquivo de dados não encontrado.")
        exit(1)
    df_raw = pd.read_csv(path)
    print(f"[DEBUG] Raw data shape: {df_raw.shape}")
    df = df_raw.iloc[:, 2:17]
    df.columns = [f"Coluna {i}" for i in range(1, 16)]
    print(f"[DEBUG] Processed DataFrame columns: {df.columns.tolist()}")
    if df.shape[1] < 15:
        print("Dados insuficientes para gerar palpites.")
        salvar_relatorio([], [], [])
        exit(0)
    p1 = gerar_palpite_simples(df)
    p2 = gerar_palpite_markov(df)
    p3 = gerar_palpites_beam(df)
    salvar_relatorio(p1, p2, p3)
