# benchmark.py (exemplo aplicável tanto a SuperSete quanto Lotofacil, com ajustes mínimos por jogo)

import pandas as pd
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import json

# === CONFIGURAÇÃO ===
JOGO = "Lotofacil"  # Ou "Lotofacil"
ROOT = f"Oraculo/{JOGO}"
DATASET_PATH = f"{ROOT}/data/{JOGO}.csv"
PRED_PATH = f"{ROOT}/predictions"
RESULT_CSV = f"{ROOT}/validation/benchmark_results.csv"
SUMMARY_MD = f"{ROOT}/validation/benchmark_summary.md"
CHART_IMG = f"{ROOT}/docs/charts/benchmark_summary.png"

# === PARÂMETROS ===
N_VALID = 300

# === FUNÇÕES ===
def load_dataset():
    df = pd.read_csv(DATASET_PATH)
    df = df.sort_values(by="Concurso")
    return df.tail(N_VALID)

def load_predictions():
    arquivos = sorted(glob.glob(f"{PRED_PATH}/prediction_*.json"))
    dados = []
    for arq in arquivos:
        nome_arquivo = os.path.basename(arq)
        data = nome_arquivo.replace("prediction_", "").replace(".json", "")
        with open(arq, "r") as f:
            conteudo = json.load(f)
            if isinstance(conteudo, list):
                for entrada in conteudo:
                    dados.append({"data": data, "modelo": entrada["modelo"], "jogo": entrada["jogo"]})
            elif isinstance(conteudo, dict):
                dados.append({"data": data, "modelo": conteudo["modelo"], "jogo": conteudo["jogo"]})
    return dados

def comparar(palpite, real):
    acertos = len(set(palpite) & set(real))
    return acertos

def benchmark():
    df_real = load_dataset()
    preds = load_predictions()
    registros = []

    for _, row in df_real.iterrows():
        data_conc = row["Data"] if "Data" in row else None
        if not data_conc:
            continue

        nums_reais = row.drop(["Data", "Concurso"], errors="ignore").astype(int).tolist()
        data_conc_dt = datetime.strptime(data_conc, "%d/%m/%y")

        palpites_validos = [p for p in preds if datetime.strptime(p["data"], "%d/%m/%y") < data_conc_dt]
        if not palpites_validos:
            continue

        pmais_recente = max(palpites_validos, key=lambda x: x["data"])
        acertos = comparar(pmais_recente["jogo"], nums_reais)
        acertos_por_coluna = "-"

        if JOGO == "SuperSete":
            acertos_por_coluna = sum([1 for i in range(7) if i < len(pmais_recente["jogo"]) and i < len(nums_reais) and pmais_recente["jogo"][i] == nums_reais[i]])

        registros.append({
            "modelo": pmais_recente["modelo"],
            "data_palpite": pmais_recente["data"],
            "data_concurso": data_conc,
            "acertos_totais": acertos,
            "acertos_por_coluna": acertos_por_coluna
        })

    if not registros:
        print("⚠️ Nenhum registro válido para benchmarking.")
        return pd.DataFrame()

    df_benchmark = pd.DataFrame(registros)
    df_benchmark.to_csv(RESULT_CSV, index=False)
    return df_benchmark

def gerar_summary(df):
    if df.empty:
        print("⚠️ DataFrame vazio. Sumário não gerado.")
        return

    resumo = df.groupby("modelo")["acertos_totais"].agg(["mean", "std", "count"]).reset_index()
    resumo.columns = ["modelo", "media_acertos", "desvio_padrao", "n"]

    with open(SUMMARY_MD, "w") as f:
        f.write("# Benchmark Summary\n\n")
        f.write(resumo.to_markdown(index=False))

    # Gráfico
    plt.figure(figsize=(10,6))
    plt.bar(resumo["modelo"], resumo["media_acertos"], yerr=resumo["desvio_padrao"], capsize=5)
    plt.title("Média de Acertos por Modelo")
    plt.ylabel("Acertos")
    plt.savefig(CHART_IMG)
    plt.close()

if __name__ == "__main__":
    print("\n🔍 Executando benchmark...")
    df = benchmark()
    gerar_summary(df)
    print("✅ Benchmark concluído.")
