# benchmark.py - Benchmark interativo para Lotofácil com gráficos Plotly

import pandas as pd
import os
import glob
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# === CONFIGURAÇÃO ===
JOGO = "Lotofacil"
DATASET_PATH = "../data/Lotofacil.csv"
PRED_PATH = "../predictions"
RESULT_CSV = "../validation/benchmark_results.csv"
SUMMARY_MD = "../docs/benchmark_summary.md"
CHART_HTML = "../docs/charts/benchmark_interactive.html"

# Verificação de caminhos
def verificar_paths():
    """Verifica se os caminhos essenciais existem."""
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"📄 Procurando dataset: {DATASET_PATH}")
    
    if not os.path.exists(DATASET_PATH):
        # Tenta caminhos alternativos se executado do diretório raiz
        alt_paths = [
            f"Oraculo/{JOGO}/data/{JOGO}.csv",
            f"Oraculo/Lotofacil/data/Lotofacil.csv",
            "data/Lotofacil.csv"
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                print(f"✅ Dataset encontrado em: {alt_path}")
                return alt_path
                
        print(f"❌ Dataset não encontrado em nenhum dos caminhos:")
        print(f"   - {DATASET_PATH}")
        for path in alt_paths:
            print(f"   - {path}")
        return None
    
    print(f"✅ Dataset encontrado: {DATASET_PATH}")
    return DATASET_PATH

# === PARÂMETROS ===
N_VALID = 300
TEST_MODE = False  # Quando False, só usa predições anteriores ao concurso

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

# === FUNÇÕES ===
def load_dataset():
    """Carrega o dataset com verificação de caminhos."""
    dataset_path = verificar_paths()
    if not dataset_path:
        raise FileNotFoundError(f"Dataset {JOGO}.csv não encontrado em nenhum dos caminhos esperados")
    
    print(f"📊 Carregando dados de {dataset_path}...")
    df = pd.read_csv(dataset_path)
    print(f"📊 Carregadas {len(df)} linhas do dataset")
    print(f"🔍 Colunas disponíveis: {list(df.columns)}")
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
    """Processa conteúdo no formato de dicionário.
    Aceita dois formatos:
    - {"models": [{"modelo":..., "jogo": [...]}, ...]}
    - {"modelo": ..., "jogo": [...]} (único)
    Retorna lista homogênea de entradas.
    """
    if not isinstance(conteudo, dict):
        return []
    if "models" in conteudo and isinstance(conteudo["models"], list):
        return [
            {"data": data, "modelo": m["modelo"], "jogo": m["jogo"]}
            for m in conteudo["models"]
            if isinstance(m, dict) and "modelo" in m and "jogo" in m
        ]
    if "modelo" in conteudo and "jogo" in conteudo:
        return [{"data": data, "modelo": conteudo["modelo"], "jogo": conteudo["jogo"]}]
    return []

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

def _processar_concurso_lotofacil(row):
    """Processa um concurso individual e retorna os dados validados."""
    data_conc = row.get("Data Sorteio") or row.get("Data")
    if not data_conc:
        return None

    # Para Lotofácil: Bola1 até Bola15
    colunas_bolas = [col for col in row.index if col.startswith('Bola')]
    if len(colunas_bolas) < 15:
        return None
        
    real_series = row[colunas_bolas[:15]]
    real_series = pd.to_numeric(real_series, errors="coerce")
    if real_series.isna().any():
        return None
    
    nums_reais = sorted(real_series.astype(int).tolist())
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

def _gerar_registro_lotofacil(pred, concurso_data):
    """Gera um registro de benchmark para Lotofácil."""
    acertos = comparar(pred["jogo"], concurso_data["nums_reais"])
    
    return {
        "modelo": pred["modelo"],
        "data_palpite": pred["data"],
        "data_concurso": concurso_data["data_conc"],
        "concurso": concurso_data["concurso"],
        "acertos_totais": acertos,
        "acertos_por_coluna": "-",
        "nums_reais": concurso_data["nums_reais"],
        "nums_preditos": pred["jogo"],
        "simulada": pred.get("simulada", False)
    }

def _predicao_baseline_random(data_palpite):
    import random
    nums = sorted(random.sample(range(1, 26), 15))
    return {"data": data_palpite, "modelo": "baseline_random", "jogo": nums, "simulada": True}

def _predicao_baseline_freq(concurso_data, historico_df, data_palpite):
    import random
    if str(concurso_data["concurso"]).isdigit():
        conc_num = int(concurso_data["concurso"])
        historico_prev = historico_df[historico_df["Concurso"] < conc_num]
    else:
        historico_prev = historico_df
    colunas_bolas = [c for c in historico_prev.columns if c.startswith("Bola")]
    freq_map = {}
    for _, row in historico_prev.iterrows():
        for c in colunas_bolas[:15]:
            try:
                num = int(row.get(c))
            except Exception:
                continue
            freq_map[num] = freq_map.get(num, 0) + 1
    ordenados = sorted(freq_map.items(), key=lambda x: (-x[1], x[0]))
    freq_nums = [n for n, _ in ordenados[:15]]
    if len(freq_nums) < 15:
        restantes = [n for n in range(1, 26) if n not in freq_nums]
        freq_nums.extend(sorted(random.sample(restantes, 15 - len(freq_nums))))
    return {"data": data_palpite, "modelo": "baseline_freq", "jogo": sorted(freq_nums), "simulada": True}

def _gerar_predicoes_simuladas(concurso_data, historico_df):
    from datetime import timedelta
    from random import seed
    try:
        seed(int(concurso_data["concurso"]))
    except Exception:
        pass
    data_palpite = (concurso_data["data_conc_dt"] - timedelta(hours=1)).strftime("%Y-%m-%d")
    return [
        _predicao_baseline_random(data_palpite),
        _predicao_baseline_freq(concurso_data, historico_df, data_palpite)
    ]

def benchmark():
    """Executa o benchmark comparando predições com resultados históricos."""
    df_real = load_dataset()
    preds = load_predictions()
    registros = []

    print(f"🔍 Processando {N_VALID} concursos...")

    for _, row in df_real.iterrows():
        concurso_data = _processar_concurso_lotofacil(row)
        if not concurso_data:
            continue
        # Ignorar concursos sem ID
        if not concurso_data.get("concurso") or concurso_data.get("concurso") == "?":
            continue

        if TEST_MODE:
            palpites_validos = preds
        else:
            palpites_validos = _filtrar_palpites_validos(preds, concurso_data["data_conc_dt"])

        if not palpites_validos:
            palpites_validos = _gerar_predicoes_simuladas(concurso_data, df_real)

        for pred in palpites_validos:
            registro = _gerar_registro_lotofacil(pred, concurso_data)
            registros.append(registro)

    print(f"📊 Gerados {len(registros)} registros de comparação")

    if not registros:
        print("⚠️ Nenhum registro válido para benchmarking.")
        return pd.DataFrame()

    os.makedirs(os.path.dirname(RESULT_CSV), exist_ok=True)
    df_benchmark = pd.DataFrame(registros)
    df_benchmark.to_csv(RESULT_CSV, index=False)
    return df_benchmark

def _calcular_faixas_acertos_lotofacil(df):
    """Calcula análise por faixas de acertos para cada modelo."""
    faixas_acertos = {}
    for modelo in df["modelo"].unique():
        dados_modelo = df[df["modelo"] == modelo]["acertos_totais"]
        faixas_acertos[modelo] = {
            "11_ou_mais": sum(dados_modelo >= 11),
            "12_ou_mais": sum(dados_modelo >= 12),
            "13_ou_mais": sum(dados_modelo >= 13),
            "14_ou_mais": sum(dados_modelo >= 14),
            "15_acertos": sum(dados_modelo == 15)
        }
    return faixas_acertos

def _gerar_relatorio_markdown_lotofacil(resumo, faixas_acertos, df_full):
    """Gera o relatório markdown com as estatísticas."""
    melhor_modelo = resumo.loc[resumo["media_acertos"].idxmax()]
    
    with open(SUMMARY_MD, "w") as f:
        f.write("# 🎯 Benchmark Summary - Lotofácil\n\n")
        f.write(f"**Período analisado:** Últimos {N_VALID} concursos\n")
        f.write(f"**Modelos testados:** {len(resumo)} modelos\n\n")
        
        f.write("## 📊 Performance Geral por Modelo\n\n")
        f.write(resumo.to_markdown(index=False))
        
        f.write("\n\n## 🏆 Análise de Faixas de Premiação\n\n")
        f.write("| Modelo | 11+ acertos | 12+ acertos | 13+ acertos | 14+ acertos | 15 acertos |\n")
        f.write("|--------|-------------|-------------|-------------|-------------|------------|\n")
        
        for modelo, faixas in faixas_acertos.items():
            f.write(f"| {modelo} | {faixas['11_ou_mais']} | {faixas['12_ou_mais']} | {faixas['13_ou_mais']} | {faixas['14_ou_mais']} | {faixas['15_acertos']} |\n")

        f.write("\n## 🧪 Predições Simuladas\n\n")
        simuladas_group = df_full[df_full.get("simulada", False)].groupby("modelo").size().reset_index(name="predicoes_simuladas")
        if not simuladas_group.empty:
            f.write(simuladas_group.to_markdown(index=False))
        else:
            f.write("Nenhuma predição simulada necessária no período.\n")
        
        f.write(f"\n## 🥇 Melhor Modelo: **{melhor_modelo['modelo']}**\n")
        f.write(f"- Média de acertos: **{melhor_modelo['media_acertos']:.2f}**\n")
        f.write(f"- Desvio padrão: {melhor_modelo['desvio_padrao']:.2f}\n")
    
    return melhor_modelo

def _gerar_grafico_interativo_lotofacil(resumo, df):
    """Gera gráfico interativo de benchmark com múltiplas visualizações."""
    charts_dir = os.path.dirname(CHART_HTML)
    os.makedirs(charts_dir, exist_ok=True)

    # Cor oficial da Lotofácil
    LOTOFACIL_COLOR = "#c2318f"
    
    # Criar paleta de cores baseada na cor principal
    cores = [LOTOFACIL_COLOR, "#a8287c", "#8e1f69", "#741656", "#5a0d43"]

    # Criar subplots 2x2
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("📊 Média de Acertos por Modelo", "📦 Distribuição de Acertos", 
                       "📈 Acertos por Concurso (Temporal)", "🥧 Faixas de Premiação"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "domain"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # 1. Gráfico de Barras - Média de Acertos
    fig.add_trace(
        go.Bar(
            x=resumo["modelo"],
            y=resumo["media_acertos"],
            error_y=dict(type='data', array=resumo["desvio_padrao"]),
            name="Média de Acertos",
            marker_color=LOTOFACIL_COLOR,
            text=[f'{v:.2f}' for v in resumo["media_acertos"]],
            textposition='outside',
            visible=True
        ),
        row=1, col=1
    )

    # 2. Box Plot - Distribuição
    for i, modelo in enumerate(resumo["modelo"]):
        dados_modelo = df[df["modelo"] == modelo]["acertos_totais"]
        fig.add_trace(
            go.Box(
                y=dados_modelo,
                name=modelo,
                marker_color=cores[i % len(cores)],
                visible=True
            ),
            row=1, col=2
        )

    # 3. Scatter Plot Temporal
    for i, modelo in enumerate(resumo["modelo"]):
        dados_modelo = df[df["modelo"] == modelo]
        fig.add_trace(
            go.Scatter(
                x=list(range(len(dados_modelo))),
                y=dados_modelo["acertos_totais"],
                mode='markers+lines',
                name=f"{modelo} - Temporal",
                marker_color=cores[i % len(cores)],
                visible=True
            ),
            row=2, col=1
        )

    # 4. Pie Chart - Faixas de Premiação (11, 12, 13, 14, 15 acertos)
    faixas_labels = []
    faixas_values = []
    
    for modelo in resumo["modelo"]:
        dados_modelo = df[df["modelo"] == modelo]["acertos_totais"]
        for acertos in [11, 12, 13, 14, 15]:
            count = sum(dados_modelo == acertos)
            if count > 0:
                faixas_labels.append(f"{modelo} - {acertos} acertos")
                faixas_values.append(count)
    
    if faixas_values:  # Só adiciona se houver dados
        fig.add_trace(
            go.Pie(
                labels=faixas_labels,
                values=faixas_values,
                name="Faixas de Premiação",
                marker_colors=cores * (len(faixas_labels) // len(cores) + 1),
                visible=True
            ),
            row=2, col=2
        )

    # Configurar layout
    fig.update_layout(
        title={
            'text': "🎯 Lotofácil - Análise Interativa de Performance dos Modelos",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': LOTOFACIL_COLOR}
        },
        showlegend=True,
        height=800,
        font=dict(size=10),
        # Botões para alternar tipos de gráfico
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(label="📊 Visão Completa", method="update",
                         args=[{"visible": [True] * len(fig.data)}]),
                    dict(label="📊 Apenas Barras", method="update",
                         args=[{"visible": [True if i < 1 else False for i in range(len(fig.data))]}]),
                    dict(label="📦 Apenas Distribuição", method="update",
                         args=[{"visible": [True if 1 <= i < 1 + len(resumo) else False for i in range(len(fig.data))]}]),
                    dict(label="📈 Apenas Temporal", method="update",
                         args=[{"visible": [True if 1 + len(resumo) <= i < 1 + 2*len(resumo) else False for i in range(len(fig.data))]}]),
                    dict(label="🥧 Faixas de Premiação", method="update",
                         args=[{"visible": [True if i >= len(fig.data)-1 else False for i in range(len(fig.data))]}])
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.05,
                yanchor="top"
            ),
        ]
    )

    # Configurar eixos dos subplots
    fig.update_xaxes(title_text="Modelos", row=1, col=1)
    fig.update_yaxes(title_text="Média de Acertos", row=1, col=1)
    
    fig.update_xaxes(title_text="Modelos", row=1, col=2)
    fig.update_yaxes(title_text="Acertos", row=1, col=2)
    
    fig.update_xaxes(title_text="Concursos", row=2, col=1)
    fig.update_yaxes(title_text="Acertos", row=2, col=1)

    # Salvar gráfico
    fig.write_html(CHART_HTML, include_plotlyjs='cdn')
    print(f"📈 Gráfico interativo Lotofácil salvo em: {CHART_HTML}")

def gerar_summary(df):
    """Gera o relatório de benchmark com estatísticas e gráficos."""
    if df.empty:
        print("⚠️ DataFrame vazio. Sumário não gerado.")
        return

    resumo = df.groupby("modelo")["acertos_totais"].agg(["mean", "std", "count"]).reset_index()
    resumo.columns = ["modelo", "media_acertos", "desvio_padrao", "n"]
    
    faixas_acertos = _calcular_faixas_acertos_lotofacil(df)
    melhor_modelo = _gerar_relatorio_markdown_lotofacil(resumo, faixas_acertos, df)
    _gerar_grafico_interativo_lotofacil(resumo, df)
    
    print(f"📈 Gráfico interativo salvo em: {CHART_HTML}")
    print(f"📝 Relatório salvo em: {SUMMARY_MD}")
    print(f"\n🏆 RESUMO DO BENCHMARK:")
    print(f"Melhor modelo: {melhor_modelo['modelo']} ({melhor_modelo['media_acertos']:.2f} acertos em média)")
    print(f"Range de performance: {resumo['media_acertos'].min():.2f} - {resumo['media_acertos'].max():.2f} acertos")

if __name__ == "__main__":
    print("\n🔍 Executando benchmark...")
    df = benchmark()
    gerar_summary(df)
    print("✅ Benchmark concluído.")
