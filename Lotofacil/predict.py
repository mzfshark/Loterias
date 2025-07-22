import pandas as pd
import numpy as np
import os

def gerar_palpite_simples(df):
    # Para cada posição (coluna), escolhe o valor mais frequente
    palpites = []
    for col in df.columns:
        freq = df[col].value_counts().sort_values(ascending=False)
        if not freq.empty:
            palpites.append(int(freq.index[0]))
        else:
            palpites.append(-1)
    return palpites


def gerar_palpite_markov(df):
    # Cadeia de Markov de 1ª ordem por coluna
    palpites = []
    for col in df.columns:
        series = pd.to_numeric(df[col], errors='coerce').dropna().astype(int)
        # valid digits between 1-25
        series = [s for s in series if 1 <= s <= 25]
        if len(series) < 2:
            palpites.append(-1)
            continue
        # matriz de transição
        mat = np.ones((26, 26))  # índices 0-25
        for i in range(len(series) - 1):
            mat[series[i], series[i+1]] += 1
        # normaliza
        transition = mat / mat.sum(axis=1, keepdims=True)
        last = series[-1]
        # escolhe próximo mais provável
        palpite = int(np.argmax(transition[last]))
        palpites.append(palpite)
    return palpites


def gerar_palpites_beam(df, beam_width=3):
    # Beam search usando última janela de 20 concursos
    if len(df) < 20:
        return [[-1]*15]
    recent = df.tail(20)
    # calcular frequências normalizadas por coluna
    freq_df = {
        col: recent[col].value_counts(normalize=True)
        for col in df.columns
    }
    sorted_digits = {
        col: freq_df[col].sort_values(ascending=False).index.tolist()
        for col in df.columns
    }
    # inicia beam com primeiros beam_width dígitos da primeira coluna
    beam = [[d] for d in sorted_digits[df.columns[0]][:beam_width]]
    # expande para as demais colunas
    for col in df.columns[1:]:
        new_beam = []
        for path in beam:
            for d in sorted_digits[col][:beam_width]:
                new_path = path + [d]
                # probabilidade aproximada como produto das freq
                prob = np.prod([
                    freq_df[c].get(val, 0.01)
                    for c, val in zip(df.columns[:len(new_path)], new_path)
                ])
                new_beam.append((new_path, prob))
        # mantém top beam_width paths
        new_beam = sorted(new_beam, key=lambda x: x[1], reverse=True)[:beam_width]
        beam = [b for b, _ in new_beam]
    return beam


def salvar_relatorio(p1, p2, p3, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Palpite Automático Lotofácil\n\n")
        f.write("## 🎯 Palpite Simples (Frequência Histórica)\n")
        f.write(f"{p1}\n\n")

        f.write("## 🔁 Palpite Markov 1ª Ordem\n")
        f.write(f"{p2}\n\n")

        f.write("## 🤖 Top Palpites por Beam Search (base 20 concursos)\n")
        for i, beam in enumerate(p3):
            f.write(f"{i+1}. {beam}\n")

if __name__ == "__main__":
    path = "Lotofacil/data/Lotofacil.csv"
    if not os.path.exists(path):
        print("Arquivo de dados não encontrado.")
        exit(1)

    df_raw = pd.read_csv(path)
    # Assume colunas: primeira coluna data/id, próximas 15 dezenas
    # Seleciona apenas as colunas numéricas (dezenas)
df = df_raw.select_dtypes(include=[np.number])
# Se por acaso existir coluna de índice com valores altos, renomeie colunas para garantir as últimas 15
if df.shape[1] > 15:
    df = df.iloc[:, -15:]

    if df.empty or df.shape[1] < 15:
    print("Dados insuficientes para gerar palpites.")
    salvar_relatorio([], [], [])
    exit(0)
        print("Dados insuficientes para gerar palpites.")
        salvar_relatorio([], [], [])
        exit(0)

    palpite_simples = gerar_palpite_simples(df)
    palpite_markov = gerar_palpite_markov(df)
    palpites_beam = gerar_palpites_beam(df)

    salvar_relatorio(palpite_simples, palpite_markov, palpites_beam)
