import pandas as pd
import numpy as np
import os
import random
import plotly.graph_objects as go
import plotly.io as pio


def load_data(path='Lotofacil/data/Lotofacil.csv'):
    if not os.path.exists(path):
        raise FileNotFoundError("CSV file not found at: " + path)
    df_raw = pd.read_csv(path)
    df_raw = df_raw.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
    df = df_raw[[f'Bola{i}' for i in range(1, 16)]]
    df.columns = [f'Numero{i}' for i in range(1, 16)]
    return df_raw, df


def generate_heatmap(df):
    all_numbers = df.values.flatten()
    freq = pd.Series(all_numbers).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    freq_df = pd.DataFrame({
        'Dezena': range(1, 26),
        'Frequência (%)': (freq.values * 100).round(2)
    })
    freq_matrix = freq.values.reshape(5, 5)
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=freq_matrix,
        x=[1, 2, 3, 4, 5],
        y=[1, 2, 3, 4, 5],
        colorscale='YlGnBu',
        text=freq_matrix,
        hoverinfo="z"
    ))
    heatmap_fig.update_layout(
        title="Frequência das Dezenas (Histórico)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    top_15 = sorted(freq.sort_values(ascending=False).head(15).index.tolist())
    return top_15, freq_df, pio.to_html(heatmap_fig, include_plotlyjs='cdn', full_html=False)


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


def track_performance(df, predictions):
    accuracy = []
    for idx in range(len(df)):
        draw = set(df.iloc[idx].values)
        acc = [len(draw & set(p)) for p in predictions]
        accuracy.append(acc)
    accuracy = np.array(accuracy[::-1])
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=accuracy[:, 0], name='Short'))
    fig.add_trace(go.Scatter(y=accuracy[:, 1], name='Mid'))
    fig.add_trace(go.Scatter(y=accuracy[:, 2], name='Long'))
    fig.update_layout(
        title="Histórico de Acertos por Estratégia",
        xaxis_title="Concursos Passados",
        yaxis_title="Acertos",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return accuracy, pio.to_html(fig, include_plotlyjs='cdn', full_html=False)


def generate_info_table(df_raw, freq_df):
    avg_numbers = df_raw[[f'Bola{i}' for i in range(1, 16)]].apply(pd.to_numeric).mean().to_dict()
    freq_df['Média de Ocorrência'] = freq_df['Dezena'].apply(lambda x: avg_numbers.get(x, 0))
    return freq_df.sort_values(by='Dezena')


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
    top_15, freq_df, heatmap_html = generate_heatmap(df)
    pred_short, pred_mid, pred_long = generate_predictions(df)
    acc_matrix, performance_html = track_performance(df, [pred_short, pred_mid, pred_long])
    info_table = generate_info_table(df_raw, freq_df)
    salvar_relatorio(df_raw, top_15, pred_short, pred_mid, pred_long, info_table)

    # Exporta gráficos para uso externo (ex: HTML)
    Path("Lotofacil/docs/heatmap.html").write_text(heatmap_html, encoding="utf-8")
    Path("Lotofacil/docs/performance.html").write_text(performance_html, encoding="utf-8")
