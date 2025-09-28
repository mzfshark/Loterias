#!/usr/bin/env python3
"""
Wrapper de execução para a +Milionária.

Instancia o EnhancedMilionariaPredictor e executa a análise completa, salvando
JSON/CSV em Oraculo/Milionaria/predictions.
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

from Oraculo.Milionaria.scripts.enhanced_predict import EnhancedMilionariaPredictor

DATA_PATH = os.path.join("Oraculo", "+Milionária".replace("+", "Milionaria"), "data", "Milionaria.csv")
DOCS_PATH = os.path.join("Oraculo", "+Milionária".replace("+", "Milionaria"), "docs")


def _plotly_dark_layout(fig: go.Figure, title: str, height: int = 500):
    fig.update_layout(
        title=title,
        xaxis_title="Colunas",
        yaxis_title="Linhas",
        height=height,
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0f1720",
        font=dict(color="#e8eef5"),
        margin=dict(l=40, r=20, t=60, b=40)
    )


def gerar_heatmap_milionaria():
    try:
        # Ajuste de caminho (pasta chama Milionaria sem '+')
        data_path = os.path.join("Oraculo", "Milionaria", "data", "Milionaria.csv")
        docs_path = os.path.join("Oraculo", "Milionaria", "docs")
        if not os.path.isfile(data_path):
            print(f"ℹ️ Heatmap: arquivo de dados não encontrado em {data_path}")
            return

        df = pd.read_csv(data_path)
        # Colunas de números principais (1..50). Ignorar trevos (1..6)
        main_cols = [
            c for c in df.columns
            if any(k in c.lower() for k in ["bola", "dezena", "numero"]) or c.lower().startswith("n")
        ]
        if not main_cols:
            main_cols = [c for c in df.select_dtypes(include=["int64", "float64"]).columns if c.lower() != "concurso"]

        vals: list[int] = []
        for c in main_cols:
            try:
                s = pd.to_numeric(df[c], errors="coerce").dropna().astype(int)
                # Filtra apenas dezenas principais 1..50
                s = s[(s >= 1) & (s <= 50)]
                if not s.empty:
                    vals.extend(s.tolist())
            except Exception:
                continue

        if not vals:
            print("ℹ️ Heatmap: nenhuma dezena válida encontrada (1..50).")
            return

        freq = Counter(vals)
        vetor = [freq.get(i, 0) for i in range(1, 51)]

        cols = 10
        rows = ceil(50 / cols)
        z, text = [], []
        for r in range(rows):
            zr, tr = [], []
            for c in range(cols):
                n = r * cols + c + 1
                if n <= 50:
                    zr.append(vetor[n - 1])
                    tr.append(str(n))
                else:
                    zr.append(None)
                    tr.append("")
            z.append(zr)
            text.append(tr)

        os.makedirs(docs_path, exist_ok=True)
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=[f"Col {i}" for i in range(1, cols + 1)],
            y=[f"Linha {i}" for i in range(1, rows + 1)],
            colorscale=[[0, '#f7fbec'], [0.5, '#afd355'], [1, '#6b8c21']],
            text=text,
            texttemplate="%{text}",
            hovertemplate="Dezena %{text}: %{z} ocorrências<extra></extra>"
        ))
        _plotly_dark_layout(fig, title="Heatmap de Frequência das Dezenas (1 a 50)")
        out_path = os.path.join(docs_path, "heatmap.html")
        fig.write_html(out_path)
        print(f"📊 Heatmap gerado em {out_path}")
    except Exception as e:
        print(f"⚠️ Falha ao gerar heatmap +Milionária: {e}")


def gerar_mini_heatmap_trevos():
    """Gera um mini-heatmap (ou barra) com as frequências dos trevos 1..6."""
    try:
        data_path = os.path.join("Oraculo", "Milionaria", "data", "Milionaria.csv")
        docs_path = os.path.join("Oraculo", "Milionaria", "docs")
        if not os.path.isfile(data_path):
            return
        df = pd.read_csv(data_path)
        # Tenta detectar colunas de trevos
        trevo_cols = [c for c in df.columns if "trevo" in c.lower()]
        if not trevo_cols:
            # Heurística alternativa
            poss = [c for c in df.columns if any(k in c.lower() for k in ["trevo", "clover"]) or c.lower().startswith("t")]
            trevo_cols = poss[:2]
        if not trevo_cols:
            return
        vals = []
        for c in trevo_cols:
            s = pd.to_numeric(df[c], errors="coerce").dropna().astype(int)
            s = s[(s >= 1) & (s <= 6)]
            vals.extend(s.tolist())
        if not vals:
            return
        freq = Counter(vals)
        x = list(range(1, 7))
        y = [freq.get(i, 0) for i in x]
        os.makedirs(docs_path, exist_ok=True)
        # Usar heatmap 1x6 para manter consistência visual
        fig = go.Figure(data=go.Heatmap(
            z=[y],
            x=[str(i) for i in x],
            y=["Trevos"],
            colorscale=[[0, '#0ea5e9'], [0.5, '#22d3ee'], [1, '#2FD39A']],
            text=[x],
            texttemplate="%{x}",
            hovertemplate="Trevo %{x}: %{z} ocorrências<extra></extra>"
        ))
        # Layout compacto
        fig.update_layout(
            title="Frequência dos Trevos (1 a 6)",
            height=220,
            paper_bgcolor="#0b0f14",
            plot_bgcolor="#0f1720",
            font=dict(color="#e8eef5"),
            margin=dict(l=40, r=20, t=50, b=30),
            xaxis_title="Trevo",
            yaxis_title=""
        )
        out_path = os.path.join(docs_path, "heatmap_trevos.html")
        fig.write_html(out_path)
        print(f"📊 Mini-heatmap de trevos gerado em {out_path}")
    except Exception as e:
        print(f"⚠️ Falha ao gerar mini-heatmap de trevos: {e}")


def main() -> int:
    print("\n🚀 Iniciando pipeline de previsão - +Milionária")
    predictor = EnhancedMilionariaPredictor()
    try:
        results = predictor.run_complete_analysis()
        if not results:
            print("⚠️ Nenhum resultado foi gerado.")
            return 2
        gerar_heatmap_milionaria()
        gerar_mini_heatmap_trevos()
        print("\n✅ Pipeline +Milionária finalizada com sucesso.")
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
