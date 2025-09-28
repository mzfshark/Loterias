#!/usr/bin/env python3
"""
Wrapper de execução para a Mega-Sena.

Este script apenas instancia o EnhancedMegaSenaPredictor e executa a
análise completa, salvando os resultados em JSON/CSV no diretório
Oraculo/MegaSena/predictions, conforme esperado pelos workflows e pelo
gerador de HTML unificado.
"""

import os
import sys
import traceback
from math import ceil
from collections import Counter
from typing import List, Tuple

import pandas as pd
import plotly.graph_objects as go

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.MegaSena.scripts.enhanced_predict import EnhancedMegaSenaPredictor

# Caminhos de dados/saída para relatórios
DATA_PATH = os.path.join("Oraculo", "MegaSena", "data", "MegaSena.csv")
DOCS_PATH = os.path.join("Oraculo", "MegaSena", "docs")

def _coletar_dezenas(df: pd.DataFrame) -> List[int]:
    cand_cols = [
        c for c in df.columns
        if any(k in c.lower() for k in ["bola", "dezena", "numero"]) or c.lower().startswith("n")
    ]
    if not cand_cols:
        cand_cols = [c for c in df.select_dtypes(include=["int64", "float64"]).columns if c.lower() != "concurso"]
    vals: List[int] = []
    for c in cand_cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna().astype(int)
        s = s[(s >= 1) & (s <= 60)]
        vals.extend(s.tolist())
    return vals


def _matriz_heatmap(vetor: List[int], total: int = 60, cols: int = 10) -> Tuple[List[List[int]], List[List[str]]]:
    rows = ceil(total / cols)
    z, text = [], []
    for r in range(rows):
        zr, tr = [], []
        for c in range(cols):
            n = r * cols + c + 1
            if n <= total:
                zr.append(vetor[n - 1])
                tr.append(str(n))
            else:
                zr.append(None)
                tr.append("")
        z.append(zr)
        text.append(tr)
    return z, text


def gerar_heatmap_megasena():
    try:
        if not os.path.isfile(DATA_PATH):
            print(f"ℹ️ Heatmap: arquivo de dados não encontrado em {DATA_PATH}")
            return
        df = pd.read_csv(DATA_PATH)
        vals = _coletar_dezenas(df)
        if not vals:
            print("ℹ️ Heatmap: nenhuma dezena válida encontrada (1..60).")
            return
        freq = Counter(vals)
        vetor = [freq.get(i, 0) for i in range(1, 61)]
        z, text = _matriz_heatmap(vetor, total=60, cols=10)
        os.makedirs(DOCS_PATH, exist_ok=True)
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=[f"Col {i}" for i in range(1, 11)],
            y=[f"Linha {i}" for i in range(1, 7)],
            colorscale=[[0, '#f7fbec'], [0.5, '#afd355'], [1, '#6b8c21']],
            text=text,
            texttemplate="%{text}",
            hovertemplate="Dezena %{text}: %{z} ocorrências<extra></extra>"
        ))
        fig.update_layout(
            title="Heatmap de Frequência das Dezenas (1 a 60)",
            xaxis_title="Colunas",
            yaxis_title="Linhas",
            height=500,
            paper_bgcolor="#0b0f14",
            plot_bgcolor="#0f1720",
            font=dict(color="#e8eef5"),
            margin=dict(l=40, r=20, t=60, b=40)
        )
        out_path = os.path.join(DOCS_PATH, "heatmap.html")
        fig.write_html(out_path)
        print(f"📊 Heatmap gerado em {out_path}")
    except Exception as e:
        print(f"⚠️ Falha ao gerar heatmap Mega-Sena: {e}")


def main() -> int:
    print("\n🚀 Iniciando pipeline de previsão - Mega-Sena")
    predictor = EnhancedMegaSenaPredictor()
    try:
        results = predictor.run_complete_analysis()
        if not results:
            print("⚠️ Nenhum resultado foi gerado.")
            return 2
        # Gera heatmap após previsões
        gerar_heatmap_megasena()
        print("\n✅ Pipeline Mega-Sena finalizada com sucesso.")
        return 0
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida pelo usuário.")
        return 130
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
