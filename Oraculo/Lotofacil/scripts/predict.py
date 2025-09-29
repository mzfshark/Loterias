import os
import sys
from pathlib import Path

# Adiciona raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.Lotofacil.scripts.enhanced_predict import EnhancedLotofacilPredictor
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio


def generate_heatmap_from_csv(csv_path: str) -> str:
    df_raw = pd.read_csv(csv_path)
    if 'Concurso' in df_raw.columns:
        df_raw = df_raw.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
    cols = [f'Bola{i}' for i in range(1, 16) if f'Bola{i}' in df_raw.columns]
    if not cols:
        return ""
    df = df_raw[cols]
    all_numbers = df.values.flatten()
    freq = pd.Series(all_numbers).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    freq_matrix = freq.values.reshape((5, 5), order='F')
    labels_matrix = np.arange(1, 26).reshape((5, 5), order='F')
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=freq_matrix,
        x=["Coluna 1", "Coluna 2", "Coluna 3", "Coluna 4", "Coluna 5"],
        y=["Dezena 1", "Dezena 2", "Dezena 3", "Dezena 4", "Dezena 5"],
        colorscale=[[0, '#0ea5e9'], [0.5, '#22d3ee'], [1, '#2FD39A']],
        text=labels_matrix,
        texttemplate="%{text}",
        hoverinfo="text+z",
        showscale=True
    ))
    heatmap_fig.update_layout(
        title="Heatmap de Frequência das Dezenas (1 a 25)",
        xaxis_title="Colunas",
        yaxis_title="Dezenas",
        height=500,
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0f1720",
        font=dict(color="#e8eef5"),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return pio.to_html(heatmap_fig, include_plotlyjs='cdn', full_html=False)


if __name__ == '__main__':
    predictor = EnhancedLotofacilPredictor()
    results = predictor.run_complete_analysis()

    # Heatmap: pular em FAST_CI
    if os.environ.get('FAST_CI', '').strip() == '1' or os.environ.get('GITHUB_ACTIONS', '') == 'true':
        print("⏭️ FAST_CI ativo: pulando geração de heatmap do Lotofácil.")
    else:
        csv_path = "Oraculo/Lotofacil/data/Lotofacil.csv"
        try:
            heatmap_html = generate_heatmap_from_csv(csv_path)
            if heatmap_html:
                Path("Oraculo/Lotofacil/docs").mkdir(parents=True, exist_ok=True)
                Path("Oraculo/Lotofacil/docs/heatmap.html").write_text(heatmap_html, encoding="utf-8")
                print("📈 Heatmap do Lotofácil gerado com sucesso.")
        except Exception as e:
            print(f"⚠️ Falha ao gerar heatmap do Lotofácil: {e}")

    print("✅ Concluído.")
