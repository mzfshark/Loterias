import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

# Adiciona raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.SuperSete.scripts.enhanced_predict import EnhancedSuperSetePredictor


def generate_supersete_heatmap(csv_path: str) -> str:
    df_full = pd.read_csv(csv_path)
    if 'Concurso' in df_full.columns:
        df_full = df_full.sort_values(by='Concurso').reset_index(drop=True)
    cols = [c for c in df_full.columns if c.startswith('Coluna')]
    if len(cols) < 7:
        return ""
    df = df_full[cols[:7]]
    # Frequência por coluna
    counts = {i: {} for i in range(7)}
    for i in range(7):
        col_vals = df.iloc[:, i].dropna().astype(int).values
        for d in range(10):
            counts[i][d] = int((col_vals == d).sum())
    table = pd.DataFrame(counts).fillna(0).astype(int).T
    table.columns = list(range(10))
    fig = go.Figure(data=go.Heatmap(
        z=table.values,
        x=table.columns,
        y=[f"Coluna {i+1}" for i in table.index],
        colorscale=[[0, '#f7fbec'], [0.5, '#afd355'], [1, '#6b8c21']],
        hoverinfo='x+y+z'
    ))
    fig.update_layout(
        title='Heatmap de Frequência por Coluna (0 a 9)',
        xaxis_title='Dígitos',
        yaxis_title='Colunas',
        height=500,
        paper_bgcolor='#0b0f14',
        plot_bgcolor='#0f1720',
        font=dict(color='#e8eef5'),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return pio.to_html(fig, include_plotlyjs='cdn', full_html=False)


if __name__ == '__main__':
    predictor = EnhancedSuperSetePredictor()
    results = predictor.run_complete_analysis()

    # Heatmap: pular em FAST_CI
    fast_ci = os.environ.get('FAST_CI', '').strip()
    if fast_ci == '1':
        print("⏭️ FAST_CI ativo: pulando geração de heatmap do SuperSete.")
    else:
        csv_path = "Oraculo/SuperSete/data/SuperSete.csv"
        try:
            html = generate_supersete_heatmap(csv_path)
            if html:
                Path("Oraculo/SuperSete/docs").mkdir(parents=True, exist_ok=True)
                Path("Oraculo/SuperSete/docs/heatmap.html").write_text(html, encoding='utf-8')
                print("📈 Heatmap do SuperSete gerado com sucesso.")
        except Exception as e:
            print(f"⚠️ Falha ao gerar heatmap do SuperSete: {e}")

    print("✅ Concluído.")
