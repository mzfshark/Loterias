import pandas as pd
import numpy as np
import sys
import os
import random
import json
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path
from collections import Counter

# Adiciona raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.Lotofacil.models import beam_search
from Oraculo.Lotofacil.models import mutation
from Oraculo.Lotofacil.models import markov
from Oraculo.Lotofacil.models import poisson

def load_data(path='Oraculo/Lotofacil/data/Lotofacil.csv'):
    df_raw = pd.read_csv(path)
    df_raw = df_raw.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
    df = df_raw[[f'Bola{i}' for i in range(1, 16)]]
    return df_raw, df

def generate_heatmap(df):
    all_numbers = df.values.flatten()
    freq = pd.Series(all_numbers).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    freq_matrix = freq.values.reshape(5, 5)
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=freq_matrix,
        x=[1, 2, 3, 4, 5],
        y=[1, 2, 3, 4, 5],
        colorscale='YlGnBu',
        text=freq_matrix,
        hoverinfo="z"
    ))
    heatmap_fig.update_layout(title="Frequência das Dezenas (Histórico)", height=300)
    return pio.to_html(heatmap_fig, include_plotlyjs='cdn', full_html=False)

def save_predictions(predictions, path_prefix):
    os.makedirs(os.path.dirname(path_prefix), exist_ok=True)
    # Save JSON
    with open(path_prefix + ".json", 'w', encoding='utf-8') as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    # Save CSV
    df = pd.DataFrame([{**{f"dezena{i+1}": n for i, n in enumerate(p['jogo'])}, "modelo": p['modelo']} for p in predictions])
    df.to_csv(path_prefix + ".csv", index=False)

if __name__ == '__main__':
    print("\n📊 Carregando dados históricos...")
    df_raw, df = load_data()
    print(f"Total de concursos: {len(df)} | Último concurso: {df_raw['Concurso'].iloc[0]}")

    print("\n📈 Calculando estatísticas...")

    # Modelos
    beam = beam_search.beam_search(df)
    mut = mutation.gerar_mutacoes(df)
    markov_pred = markov.gerar_palpite(df)
    poisson_pred = poisson.gerar_combinacao_poisson(df)

    # Frequência (curto, médio, longo)
    short_freq = df.tail(5).values.flatten()
    mid_freq = df.tail(75).values.flatten()
    full_freq = df.values.flatten()

    def top_dezenas(data):
        c = Counter(data)
        return sorted([n for n, _ in c.most_common(15)])

    freq_short = top_dezenas(short_freq)
    freq_mid = top_dezenas(mid_freq)
    freq_long = top_dezenas(full_freq)

    # Palpite da Rodada baseado nas dezenas mais frequentes entre todos os palpites
    all_jogos = []
    for jogo in [beam, markov_pred, poisson_pred, freq_short, freq_mid, freq_long]:
        if isinstance(jogo, list) and all(isinstance(n, int) for n in jogo):
            all_jogos.append(jogo)
    if isinstance(mut, list):
        for jogo in mut:
            if isinstance(jogo, list) and all(isinstance(n, int) for n in jogo):
                all_jogos.append(jogo)

    # Gerar palpite da rodada com base nas dezenas mais comuns por posição
    dez_por_posicao = [Counter([jogo[i] for jogo in all_jogos if len(jogo) > i and isinstance(jogo[i], int)]).most_common(1)[0][0] for i in range(15)]
    palpite_rodada = sorted(dez_por_posicao)

    print("\n🎯 Palpites gerados:")
    print(f"Beam: {beam}\nMutation: {mut}\nMarkov: {markov_pred}\nPoisson: {poisson_pred}")
    print(f"Frequência Curto: {freq_short}\nMédio: {freq_mid}\nLongo: {freq_long}")
    print(f"Palpite da Rodada: {palpite_rodada}")

    # Salvamento
    print("\n💾 Salvando previsões...")
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    predictions = [
        {"modelo": "beam_search", "jogo": beam},
        {"modelo": "mutation", "jogo": mut},
        {"modelo": "markov", "jogo": markov_pred},
        {"modelo": "poisson", "jogo": poisson_pred},
        {"modelo": "frequencia_curto", "jogo": freq_short},
        {"modelo": "frequencia_medio", "jogo": freq_mid},
        {"modelo": "frequencia_longo", "jogo": freq_long},
        {"modelo": "palpite_rodada", "jogo": palpite_rodada},
    ]
    save_predictions(predictions, f"Lotofacil/predictions/prediction_{today}")

    # Heatmap
    heatmap_html = generate_heatmap(df)
    Path(f"Lotofacil/docs/heatmap.html").write_text(heatmap_html, encoding="utf-8")

    print("\n✅ Arquivos salvos com sucesso.")
