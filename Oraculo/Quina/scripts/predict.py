#!/usr/bin/env python3
"""
Wrapper de execução para a Quina.

Instancia o EnhancedQuinaPredictor e roda a análise completa, salvando
os resultados em Oraculo/Quina/predictions.
"""

import os
import sys
import traceback
from math import ceil
from collections import Counter

import pandas as pd
import plotly.graph_objects as go

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.Quina.scripts.enhanced_predict import EnhancedQuinaPredictor

DATA_PATH = os.path.join("Oraculo", "Quina", "data", "Quina.csv")
DOCS_PATH = os.path.join("Oraculo", "Quina", "docs")


def gerar_heatmap_quina():
    try:
        if not os.path.isfile(DATA_PATH):
            print(f"ℹ️ Heatmap: arquivo de dados não encontrado em {DATA_PATH}")
            return

        df = pd.read_csv(DATA_PATH)
        cand_cols = [
            c for c in df.columns
            if any(k in c.lower() for k in ["bola", "dezena", "numero"]) or c.lower().startswith("n")
        ]
        if not cand_cols:
            cand_cols = [c for c in df.select_dtypes(include=["int64", "float64"]).columns if c.lower() != "concurso"]

        vals: list[int] = []
        for c in cand_cols:
            try:
                s = pd.to_numeric(df[c], errors="coerce").dropna().astype(int)
                s = s[(s >= 1) & (s <= 80)]
                if not s.empty:
                    vals.extend(s.tolist())
            except Exception:
                continue

        if not vals:
            print("ℹ️ Heatmap: nenhuma dezena válida encontrada (1..80).")
            return

        freq = Counter(vals)
        vetor = [freq.get(i, 0) for i in range(1, 81)]

        cols = 10
        rows = ceil(80 / cols)
        z, text = [], []
        for r in range(rows):
            zr, tr = [], []
            for c in range(cols):
                n = r * cols + c + 1
                if n <= 80:
                    zr.append(vetor[n - 1])
                    tr.append(str(n))
                else:
                    zr.append(None)
                    tr.append("")
            z.append(zr)
            text.append(tr)

        os.makedirs(DOCS_PATH, exist_ok=True)
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=[f"Col {i}" for i in range(1, cols + 1)],
            y=[f"Linha {i}" for i in range(1, rows + 1)],
            colorscale=[[0, '#f7fbec'], [0.5, '#afd355'], [1, '#6b8c21']],
            text=text,
            texttemplate="%{text}",
            hovertemplate="Dezena %{text}: %{z} ocorrências<extra></extra>"
        ))
        fig.update_layout(
            title="Heatmap de Frequência das Dezenas (1 a 80)",
            xaxis_title="Colunas",
            yaxis_title="Linhas",
            height=500,
        )
        out_path = os.path.join(DOCS_PATH, "heatmap.html")
        fig.write_html(out_path)
        print(f"📊 Heatmap gerado em {out_path}")
    except Exception as e:
        print(f"⚠️ Falha ao gerar heatmap Quina: {e}")


def main() -> int:
    print("\n🚀 Iniciando pipeline de previsão - Quina")
    predictor = EnhancedQuinaPredictor()
    try:
        results = predictor.run_complete_analysis()
        if not results:
            print("⚠️ Nenhum resultado foi gerado.")
            return 2
        gerar_heatmap_quina()
        print("\n✅ Pipeline Quina finalizada com sucesso.")
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
