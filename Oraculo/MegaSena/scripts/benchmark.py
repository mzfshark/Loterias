import pandas as pd
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import json

# === CONFIGURAÇÃO ===
JOGO = "MegaSena"
DATASET_PATH = "../data/MegaSena.csv"
PRED_PATH = "../predictions"
RESULT_CSV = "../validation/benchmark_results.csv"
SUMMARY_MD = "../docs/benchmark_summary.md"
CHART_IMG = "../docs/charts/benchmark_summary.png"

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


def _carregar_arquivo_predicao(arq):
    """Carrega um arquivo de predição JSON."""
    nome_arquivo = os.path.basename(arq)
    data = nome_arquivo.replace("prediction_", "").replace(".json", "")
    
    try:
        with open(arq, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                return None
            return json.loads(raw), data
    except Exception as e:
        print(f"⚠️ Ignorando arquivo inválido de previsão: {nome_arquivo} ({e})")
        return None

def _processar_conteudo_list(conteudo, data):
    """Processa conteúdo no formato de lista."""
    dados = []
    for entrada in conteudo:
        if isinstance(entrada, dict) and "modelo" in entrada and "jogo" in entrada:
            dados.append({"data": data, "modelo": entrada["modelo"], "jogo": entrada["jogo"]})
    return dados

def _processar_conteudo_dict(conteudo, data):
    """Processa conteúdo no formato de dicionário."""
    dados = []
    if "models" in conteudo and isinstance(conteudo["models"], list):
        for m in conteudo["models"]:
            if isinstance(m, dict) and "modelo" in m and "jogo" in m:
                dados.append({"data": data, "modelo": m["modelo"], "jogo": m["jogo"]})
    elif "modelo" in conteudo and "jogo" in conteudo:
        dados.append({"data": data, "modelo": conteudo["modelo"], "jogo": conteudo["jogo"]})
    return dados

def load_predictions():
    """Carrega todas as predições dos arquivos JSON."""
    arquivos = sorted(glob.glob(f"{PRED_PATH}/prediction_*.json"))
    print(f"📁 Encontrados {len(arquivos)} arquivos de predição")
    dados = []
    
    for arq in arquivos:
        resultado = _carregar_arquivo_predicao(arq)
        if not resultado:
            continue
            
        conteudo, data = resultado
        
        if isinstance(conteudo, list):
            dados.extend(_processar_conteudo_list(conteudo, data))
        elif isinstance(conteudo, dict):
            dados.extend(_processar_conteudo_dict(conteudo, data))
    
    print(f"🎯 Processadas {len(dados)} predições válidas")
    return dados


def comparar(palpite, real):
    acertos = len(set(palpite) & set(real))
    return acertos


def _processar_concurso_megasena(row):
    """Processa um concurso individual e retorna os dados validados."""
    data_conc = row.get("Data") or row.get("Data Sorteio")
    if not data_conc:
        return None

    real_series = row.drop(["Data", "Data Sorteio", "Concurso"], errors="ignore")
    real_series = pd.to_numeric(real_series, errors="coerce")
    if real_series.isna().any():
        return None
    
    nums_reais = real_series.astype(int).tolist()
    data_conc_dt = parse_date_multi(data_conc)
    
    if not data_conc_dt:
        return None
    
    return {
        "data_conc": data_conc,
        "data_conc_dt": data_conc_dt,
        "nums_reais": nums_reais,
        "concurso": row.get('Concurso', '?')
    }

def _filtrar_palpites_validos(preds, data_conc_dt):
    """Filtra palpites válidos anteriores ao concurso."""
    palpites_validos = []
    for p in preds:
        p_dt = parse_date_multi(p["data"])
        if p_dt and p_dt < data_conc_dt:
            palpites_validos.append(p)
    return palpites_validos

def _gerar_registro_megasena(pmais_recente, concurso_data):
    """Gera um registro de benchmark para MegaSena."""
    acertos = comparar(pmais_recente["jogo"], concurso_data["nums_reais"])
    
    return {
        "modelo": pmais_recente["modelo"],
        "data_palpite": pmais_recente["data"],
        "data_concurso": concurso_data["data_conc"],
        "acertos_totais": acertos,
    }

def benchmark():
    """Executa o benchmark comparando predições com resultados históricos."""
    df_real = load_dataset()
    preds = load_predictions()
    registros = []

    print(f"🔍 Processando {len(df_real)} concursos...")

    for _, row in df_real.iterrows():
        concurso_data = _processar_concurso_megasena(row)
        if not concurso_data:
            continue

        palpites_validos = _filtrar_palpites_validos(preds, concurso_data["data_conc_dt"])
        if not palpites_validos:
            continue

        pmais_recente = max(palpites_validos, key=lambda x: parse_date_multi(x["data"]))
        registro = _gerar_registro_megasena(pmais_recente, concurso_data)
        registros.append(registro)

    print(f"📊 Gerados {len(registros)} registros de comparação")

    if not registros:
        print("⚠️ Nenhum registro válido para benchmarking.")
        return pd.DataFrame()

    os.makedirs(os.path.dirname(RESULT_CSV), exist_ok=True)
    df_benchmark = pd.DataFrame(registros)
    df_benchmark.to_csv(RESULT_CSV, index=False)
    return df_benchmark


def _calcular_faixas_acertos_megasena(df):
    """Calcula análise por faixas de acertos para cada modelo."""
    faixas_acertos = {}
    for modelo in df["modelo"].unique():
        dados_modelo = df[df["modelo"] == modelo]["acertos_totais"]
        faixas_acertos[modelo] = {
            "4_ou_mais": sum(dados_modelo >= 4),
            "5_ou_mais": sum(dados_modelo >= 5),
            "6_acertos": sum(dados_modelo == 6)
        }
    return faixas_acertos

def _gerar_relatorio_markdown_megasena(resumo, faixas_acertos):
    """Gera o relatório markdown com as estatísticas."""
    melhor_modelo = resumo.loc[resumo["media_acertos"].idxmax()]
    
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("# 🎯 Benchmark Summary - MegaSena\n\n")
        f.write(f"**Período analisado:** Últimos {N_VALID} concursos\n")
        f.write(f"**Modelos testados:** {len(resumo)} modelos\n\n")
        
        f.write("## 📊 Performance Geral por Modelo\n\n")
        try:
            f.write(resumo.to_markdown(index=False))
        except Exception:
            f.write(resumo.to_string(index=False))
        
        f.write("\n\n## 🏆 Análise de Faixas de Premiação\n\n")
        f.write("| Modelo | 4+ acertos | 5+ acertos | 6 acertos (Sena) |\n")
        f.write("|--------|------------|------------|------------------|\n")
        
        for modelo, faixas in faixas_acertos.items():
            f.write(f"| {modelo} | {faixas['4_ou_mais']} | {faixas['5_ou_mais']} | {faixas['6_acertos']} |\n")
        
        f.write(f"\n## 🥇 Melhor Modelo: **{melhor_modelo['modelo']}**\n")
        f.write(f"- Média de acertos: **{melhor_modelo['media_acertos']:.2f}**\n")
        f.write(f"- Desvio padrão: {melhor_modelo['desvio_padrao']:.2f}\n")
    
    return melhor_modelo

def _gerar_grafico_megasena(resumo):
    """Gera o gráfico de benchmark."""
    charts_dir = os.path.dirname(CHART_IMG)
    os.makedirs(charts_dir, exist_ok=True)

    plt.figure(figsize=(12,8))
    plt.bar(resumo["modelo"], resumo["media_acertos"], yerr=resumo["desvio_padrao"], 
             capsize=5, color='green', alpha=0.7)
    plt.title("📊 Benchmark - Média de Acertos por Modelo (MegaSena)", fontsize=14, pad=20)
    plt.ylabel("Média de Acertos")
    plt.xlabel("Modelo")
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(resumo["media_acertos"]):
        plt.text(i, v + 0.05, f'{v:.2f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(CHART_IMG, dpi=300, bbox_inches='tight')
    plt.close()

def gerar_summary(df):
    """Gera o relatório de benchmark com estatísticas e gráficos."""
    if df.empty:
        print("⚠️ DataFrame vazio. Sumário não gerado.")
        return

    resumo = df.groupby("modelo")["acertos_totais"].agg(["mean", "std", "count"]).reset_index()
    resumo.columns = ["modelo", "media_acertos", "desvio_padrao", "n"]
    
    os.makedirs(os.path.dirname(SUMMARY_MD), exist_ok=True)
    
    faixas_acertos = _calcular_faixas_acertos_megasena(df)
    melhor_modelo = _gerar_relatorio_markdown_megasena(resumo, faixas_acertos)
    _gerar_grafico_megasena(resumo)
    
    print(f"📈 Gráfico salvo em: {CHART_IMG}")
    print(f"📝 Relatório salvo em: {SUMMARY_MD}")
    print(f"\n🏆 RESUMO DO BENCHMARK:")
    print(f"Melhor modelo: {melhor_modelo['modelo']} ({melhor_modelo['media_acertos']:.2f} acertos em média)")
    print(f"Range de performance: {resumo['media_acertos'].min():.2f} - {resumo['media_acertos'].max():.2f} acertos")


if __name__ == "__main__":
    print("\n🔍 Executando benchmark...")
    df = benchmark()
    gerar_summary(df)
    print("✅ Benchmark concluído.")
