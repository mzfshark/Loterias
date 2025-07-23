import pandas as pd
import numpy as np
import os


def gerar_palpite_simples(df):
    palpites = []
    for col in df.columns:
        freq = df[col].value_counts()
        palpites.append(int(freq.idxmax()) if not freq.empty else -1)
    return palpites


def gerar_palpite_markov(df):
    palpites = []
    for col in df.columns:
        series = pd.to_numeric(df[col], errors='coerce').dropna().astype(int).tolist()
        if len(series) < 2:
            palpites.append(-1)
            continue
        mat = np.ones((26, 26))
        for i in range(len(series) - 1):
            mat[series[i], series[i+1]] += 1
        transition = (mat.T / mat.sum(axis=1)).T
        last = series[-1]
        palpites.append(int(np.argmax(transition[last][1:]) + 1))
    return palpites


def gerar_palpites_beam(df, beam_width=3):
    if len(df) < 20:
        return []
    recent = df.tail(20)
    freq_norm = {col: recent[col].value_counts(normalize=True).sort_index() for col in df.columns}
    sorted_digits = {col: list(freq_norm[col].index) for col in df.columns}
    beam = [[d] for d in sorted_digits[df.columns[0]][:beam_width]]
    for col in df.columns[1:]:
        new_beam = []
        for path in beam:
            for d in sorted_digits[col][:beam_width]:
                new_beam.append(path + [int(d)])
        beam = new_beam[:beam_width]
    return beam


def salvar_relatorio(p1, p2, p3, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("## 🎯 Palpite Simples\n")
        f.write(f"{p1}\n\n")
        f.write("## 🔁 Palpite Markov 1ª Ordem\n")
        f.write(f"{p2}\n\n")
        f.write("## 🤖 Beam Search (últimos 20 concursos)\n")
        for i, beam in enumerate(p3, start=1):
            f.write(f"{i}. {beam}\n")

if __name__ == "__main__":
    path = "Lotofacil/data/Lotofacil.csv"
    if not os.path.exists(path):
        print("Arquivo de dados não encontrado.")
        exit(1)
    df_raw = pd.read_csv(path)
    df = df_raw.iloc[:, 2:17]
    df.columns = [f"Coluna {i}" for i in range(1, 16)]
    if df.shape[1] != 15:
        print("Dados insuficientes para gerar palpites.")
        salvar_relatorio([], [], [])
        exit(0)
    p1 = gerar_palpite_simples(df)
    p2 = gerar_palpite_markov(df)
    p3 = gerar_palpites_beam(df)
    salvar_relatorio(p1, p2, p3)
