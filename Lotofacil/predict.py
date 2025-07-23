import pandas as pd
import numpy as np
import os

def gerar_palpite_simples(df):
    # Seleciona as 15 dezenas mais frequentes em todo o histórico, sem repetições
    all_vals = df.values.flatten()
    freq = pd.Series(all_vals).value_counts()
    top15 = freq.nlargest(15).index.tolist()
    return top15


def gerar_palpite_markov(df):
    # Cadeia de Markov integrada: considera sequência concatenada de todas as colunas
    series = pd.to_numeric(df.values.flatten(), errors='coerce')
    seq = series.dropna().astype(int).tolist()
    # mantém apenas valores válidos (1-25)
    seq = [s for s in seq if 1 <= s <= 25]
    if len(seq) < 2:
        return []
    mat = np.ones((26, 26))
    for a, b in zip(seq, seq[1:]):
        mat[a, b] += 1
    trans = mat / mat.sum(axis=1, keepdims=True)
    last = seq[-1]
    # pega top 15 dígitos com maior prob de transição
    probs = trans[last]
    # ignorar índice 0
    prob_series = pd.Series(probs[1:], index=range(1, 26))
    return prob_series.nlargest(15).index.tolist()


def gerar_palpites_beam(df, beam_width=3):
    # Beam search: cada path é uma cartela de 15 dezenas únicas
    if len(df) < 20:
        return []
    recent = df.tail(20)
    freq_norm = pd.DataFrame({col: recent[col].value_counts(normalize=True) for col in df.columns}).fillna(0)
    # sorted candidate digits overall
    global_freq = freq_norm.sum(axis=1).sort_values(ascending=False)
    candidates = global_freq.index.tolist()
    # inicia beam com combinações das 2 primeiras posições
    beam = []
    for combo in __import__('itertools').combinations(candidates[:beam_width*2], 15):
        beam.append((list(combo), np.prod([global_freq[num] if num in global_freq else 0.01 for num in combo])))
    beam.sort(key=lambda x: x[1], reverse=True)
    top_paths = [path for path, _ in beam[:beam_width]]
    return top_paths


def salvar_relatorio(p1, p2, p3, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
        f.write("## 🎯 Palpite Simples (Top 15 Frequências)\n")
        f.write(f"{p1}\n\n")
        f.write("## 🔁 Palpite Markov (Top 15 Transições)\n")
        f.write(f"{p2}\n\n")
        f.write("## 🤖 Palpites por Beam Search (Top Combinações)\n")
        for i, path in enumerate(p3, 1):
            f.write(f"{i}. {path}\n")

if __name__ == "__main__":
    path = "Lotofacil/data/lotofacil.csv"
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
