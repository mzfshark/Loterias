import pandas as pd
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import json

# === CONFIGURAÇÃO ===
JOGO = "Milionaria"
ROOT = f"Oraculo/{JOGO}"
DATASET_PATH = f"{ROOT}/data/{JOGO}.csv"
PRED_PATH = f"{ROOT}/predictions"
RESULT_CSV = f"{ROOT}/validation/benchmark_results.csv"
SUMMARY_MD = f"{ROOT}/validation/benchmark_summary.md"
CHART_IMG = f"{ROOT}/docs/charts/benchmark_summary.png"

# === PARÂMETROS ===
N_VALID = 300


def parse_date_multi(s: str):
    """Tenta converter datas em múltiplos formatos comuns."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    formats = ["%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d_%H-%M-%S"]
    for fmt in formats:
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except Exception:
            continue
    return None


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
        try:
            with open(arq, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if not raw:
                    continue
                conteudo = json.loads(raw)
        except Exception as e:
            print(f"⚠️ Ignorando arquivo inválido de previsão: {nome_arquivo} ({e})")
            continue

        if isinstance(conteudo, list):
            for entrada in conteudo:
                if isinstance(entrada, dict) and "modelo" in entrada and "jogo" in entrada:
                    dados.append({"data": data, "modelo": entrada["modelo"], "jogo": entrada["jogo"]})
        elif isinstance(conteudo, dict):
            if "models" in conteudo and isinstance(conteudo["models"], list):
                for m in conteudo["models"]:
                    if isinstance(m, dict) and "modelo" in m and "jogo" in m:
                        dados.append({"data": data, "modelo": m["modelo"], "jogo": m["jogo"]})
            elif "modelo" in conteudo and "jogo" in conteudo:
                dados.append({"data": data, "modelo": conteudo["modelo"], "jogo": conteudo["jogo"]})
    return dados


def comparar(palpite, real):
    # +Milionária tem trevos; aqui contamos apenas acertos dos números principais se o CSV contiver apenas eles
    acertos = len(set(palpite) & set(real))
    return acertos


def benchmark():
    df_real = load_dataset()
    preds = load_predictions()
    registros = []

    for _, row in df_real.iterrows():
        data_conc = row["Data"] if "Data" in row else (row["Data Sorteio"] if "Data Sorteio" in row else None)
        if not data_conc:
            continue

        # Considera apenas colunas numéricas principais (ignora trevos se estiverem separados)
        real_series = row.drop(["Data", "Data Sorteio", "Concurso", "Trevo1", "Trevo2"], errors="ignore")
        real_series = pd.to_numeric(real_series, errors="coerce")
        if real_series.isna().any():
            continue
        nums_reais = real_series.astype(int).tolist()
        data_conc_dt = parse_date_multi(data_conc)
        if not data_conc_dt:
            continue

        palpites_validos = []
        for p in preds:
            p_dt = parse_date_multi(p["data"])  # tenta múltiplos formatos
            if p_dt and p_dt < data_conc_dt:
                palpites_validos.append(p)
        if not palpites_validos:
            continue

        pmais_recente = max(palpites_validos, key=lambda x: parse_date_multi(x["data"]))
        acertos = comparar(pmais_recente["jogo"], nums_reais)

        registros.append({
            "modelo": pmais_recente["modelo"],
            "data_palpite": pmais_recente["data"],
            "data_concurso": data_conc,
            "acertos_totais": acertos,
        })

    if not registros:
        print("⚠️ Nenhum registro válido para benchmarking.")
        return pd.DataFrame()

    os.makedirs(os.path.dirname(RESULT_CSV), exist_ok=True)
    df_benchmark = pd.DataFrame(registros)
    df_benchmark.to_csv(RESULT_CSV, index=False)
    return df_benchmark


def gerar_summary(df):
    if df.empty:
        print("⚠️ DataFrame vazio. Sumário não gerado.")
        return

    resumo = df.groupby("modelo")["acertos_totais"].agg(["mean", "std", "count"]).reset_index()
    resumo.columns = ["modelo", "media_acertos", "desvio_padrao", "n"]

    os.makedirs(os.path.dirname(SUMMARY_MD), exist_ok=True)
    charts_dir = os.path.dirname(CHART_IMG)
    os.makedirs(charts_dir, exist_ok=True)

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("# Benchmark Summary\n\n")
        try:
            f.write(resumo.to_markdown(index=False))
        except Exception:
            f.write(resumo.to_string(index=False))

    plt.figure(figsize=(10, 6))
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
