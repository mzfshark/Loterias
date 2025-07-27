import pandas as pd
import numpy as np
import os
import random
import seaborn as sns
import matplotlib.pyplot as plt


def load_data(path='Lotofacil/data/Lotofacil.csv'):
    if not os.path.exists(path):
        raise FileNotFoundError("CSV file not found at: " + path)
    df_raw = pd.read_csv(path)
    df_raw = df_raw.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
    df = df_raw[[f'Bola{i}' for i in range(1, 16)]]
    df.columns = [f'Numero{i}' for i in range(1, 16)]
    return df_raw, df


def generate_heatmap(df, save_path='Lotofacil/docs/heatmap.png'):
    all_numbers = df.values.flatten()
    freq = pd.Series(all_numbers).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    heatmap_data = freq.values.reshape(5, 5)
    plt.figure(figsize=(6, 4))
    sns.heatmap(heatmap_data, annot=True, fmt=".0%", cmap="YlGnBu", xticklabels=False, yticklabels=False)
    plt.title("Frequência das Dezenas (Histórico)")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    top_15 = sorted(freq.sort_values(ascending=False).head(15).index.tolist())
    return top_15, freq


def score_frequency(df, alpha=0.5, window=None):
    data = df.values.flatten() if window is None else df.tail(window).values.flatten()
    freq = pd.Series(data).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    return {i: freq[i] for i in range(1, 26)}


def monte_carlo_opt(scores, trials=100_000):
    p = np.array([scores[i] for i in range(1, 26)])
    p /= p.sum()
    best_set, best_score = None, -1
    for _ in range(trials):
        combo = np.random.choice(range(1, 26), 15, replace=False, p=p)
        score = sum(scores[i] for i in combo)
        if score > best_score:
            best_score, best_set = score, combo
    return sorted(best_set.tolist())


def generate_predictions(df):
    pred_short = monte_carlo_opt(score_frequency(df, window=5))
    pred_mid = monte_carlo_opt(score_frequency(df, alpha=0.6, window=75))
    pred_long = monte_carlo_opt(score_frequency(df))
    return pred_short, pred_mid, pred_long


def track_performance(df, predictions, save_path='Lotofacil/docs/performance.png'):
    accuracy = []
    for idx in range(len(df)):
        draw = set(df.iloc[idx].values)
        acc = [len(draw & set(p)) for p in predictions]
        accuracy.append(acc)
    accuracy = np.array(accuracy[::-1])  # invert to align with ascending Concurso
    plt.plot(accuracy[:, 0], label='Short')
    plt.plot(accuracy[:, 1], label='Mid')
    plt.plot(accuracy[:, 2], label='Long')
    plt.xlabel("Concursos Passados")
    plt.ylabel("Acertos")
    plt.title("Histórico de Acertos por Estratégia")
    plt.legend()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    return accuracy


def generate_info_table(df_raw, freq):
    total_games = len(df_raw)
    avg_numbers = df_raw[[f'Bola{i}' for i in range(1, 16)]].apply(pd.to_numeric).mean().to_dict()
    info = pd.DataFrame({
        'Dezena': list(freq.index),
        'Frequência (%)': (freq.values * 100).round(2),
        'Média de Ocorrência': [avg_numbers.get(i, 0) for i in range(1, 26)]
    })
    return info.sort_values(by='Dezena')


def salvar_relatorio(df_raw, top_15, pred_short, pred_mid, pred_long, info_table, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('## 🔥 Top 15 Dezenas Mais Frequentes (Histórico)\n')
        f.write(', '.join(map(str, top_15)) + '\n\n')
        f.write('## 🎯 Palpites Gerados\n')
        f.write(f"- Curto Prazo (últimos 5): {pred_short}\n")
        f.write(f"- Médio Prazo (últimos 75): {pred_mid}\n")
        f.write(f"- Longo Prazo (todos): {pred_long}\n\n")
        f.write('## 📊 Tabela Informacional\n')
        f.write(info_table.to_markdown(index=False))


if __name__ == '__main__':
    df_raw, df = load_data()
    top_15, freq = generate_heatmap(df)
    pred_short, pred_mid, pred_long = generate_predictions(df)
    acc_matrix = track_performance(df, [pred_short, pred_mid, pred_long])
    info_table = generate_info_table(df_raw, freq)
    salvar_relatorio(df_raw, top_15, pred_short, pred_mid, pred_long, info_table)
