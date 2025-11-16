
import pandas as pd
import os
import glob
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# === CONFIGURAÇÃO ===
JOGO = "SuperSete"
DATASET_PATH = "../data/SuperSete.csv"
PRED_PATH = "../predictions"
RESULT_CSV = "../validation/benchmark_results.csv"
SUMMARY_MD = "../docs/benchmark_summary.md"
CHART_HTML = "../docs/charts/benchmark_interactive.html"

# === PARÂMETROS ===
N_VALID = 300
TEST_MODE = False  # Quando False, usa só predições anteriores ao concurso

# Verificação de caminhos
def verificar_paths():
    """Verifica se os caminhos essenciais existem."""
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"📄 Procurando dataset: {DATASET_PATH}")
    
    if not os.path.exists(DATASET_PATH):
        # Tentar caminhos alternativos
        alt_paths = [
            "../data/SuperSete.csv",
            "data/SuperSete.csv", 
            "Oraculo/SuperSete/data/SuperSete.csv",
            "../SuperSete/data/SuperSete.csv"
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                print(f"✅ Dataset encontrado: {alt_path}")
                return alt_path
        
        print(f"❌ Dataset não encontrado em nenhum caminho testado!")
        return None
    else:
        print(f"✅ Dataset encontrado: {DATASET_PATH}")
        return DATASET_PATH

# === FUNÇÕES ===
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
    dataset_path = verificar_paths()
    if not dataset_path:
        raise FileNotFoundError("Dataset não encontrado!")
    
    print(f"📊 Carregando dados de {dataset_path}...")
    df = pd.read_csv(dataset_path)
    print(f"📊 Carregadas {len(df)} linhas do dataset")
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

def _extrair_registro_modelo(item, data):
    """Extrai um registro de predição se o item possuir as chaves esperadas."""
    if isinstance(item, dict) and "modelo" in item and "jogo" in item:
        return {"data": data, "modelo": item["modelo"], "jogo": item["jogo"]}
    return None

def _processar_conteudo_dict(conteudo, data):
    """Processa conteúdo no formato de dicionário com baixa complexidade."""
    dados = []
    itens = []
    if isinstance(conteudo.get("models"), list):
        itens = conteudo["models"]
    else:
        itens = [conteudo]

    for item in itens:
        reg = _extrair_registro_modelo(item, data)
        if reg:
            dados.append(reg)
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

def _processar_concurso_supersete(row):
    """Processa um concurso individual e retorna os dados validados."""
    data_conc = row.get("Data Sorteio")
    if not data_conc:
        return None

    # Extrair apenas os números principais (Coluna 1-Coluna 7)
    try:
        nums_reais = []
        for i in range(1, 8):  # Coluna 1 a Coluna 7
            coluna = row.get(f"Coluna {i}")
            if coluna is not None:
                nums_reais.append(int(coluna))
            else:
                return None
        
        if len(nums_reais) != 7:
            return None
    except (ValueError, TypeError):
        return None
    data_conc_dt = parse_date_multi(data_conc)
    
    if not data_conc_dt:
        return None
    
    return {
        "data_conc": data_conc,
        "data_conc_dt": data_conc_dt,
        "nums_reais": nums_reais,
        "concurso": row.get('Concurso', '?')
    }

def _calcular_acertos_supersete(palpite, nums_reais):
    """Calcula acertos para SuperSete (posicional e total)."""
    acertos = comparar(palpite, nums_reais)
    acertos_por_coluna = sum([1 for i in range(7) if i < len(palpite) and i < len(nums_reais) and palpite[i] == nums_reais[i]])
    return acertos, acertos_por_coluna

def _filtrar_palpites_validos(preds, data_conc_dt):
    palpites_validos = []
    for p in preds:
        p_dt = parse_date_multi(p["data"])
        if p_dt and p_dt < data_conc_dt:
            palpites_validos.append(p)
    return palpites_validos

def _gerar_registro_supersete(pred, concurso_data):
    acertos, acertos_por_coluna = _calcular_acertos_supersete(pred["jogo"], concurso_data["nums_reais"])
    return {
        "modelo": pred["modelo"],
        "data_palpite": pred["data"],
        "data_concurso": concurso_data["data_conc"],
        "concurso": concurso_data["concurso"],
        "acertos_totais": acertos,
        "acertos_por_coluna": acertos_por_coluna,
        "nums_reais": concurso_data["nums_reais"],
        "nums_preditos": pred["jogo"],
        "simulada": pred.get("simulada", False)
    }

def _predicao_baseline_random_ss(data_palpite):
    import random
    nums = [random.randint(0, 9) for _ in range(7)]
    return {"data": data_palpite, "modelo": "baseline_random", "jogo": nums, "simulada": True}

def _historico_antes_concurso(historico_df, concurso_val):
    """Filtra o histórico para concursos anteriores ao informado (quando possível)."""
    if str(concurso_val).isdigit():
        try:
            conc = int(concurso_val)
            return historico_df[historico_df["Concurso"] < conc]
        except Exception:
            return historico_df
    return historico_df

def _contar_frequencias_por_coluna(hist_df):
    """Conta frequências 0..9 por coluna 1..7 no histórico informado."""
    contagens = {i: {d: 0 for d in range(10)} for i in range(1, 8)}
    for i in range(1, 8):
        col = f"Coluna {i}"
        if col not in hist_df.columns:
            continue
        for _, r in hist_df.iterrows():
            try:
                d = int(r.get(col))
            except Exception:
                continue
            if 0 <= d <= 9:
                contagens[i][d] += 1
    return contagens

def _mais_frequentes_por_coluna(contagens):
    """Seleciona o dígito mais frequente por coluna (desempate pelo menor dígito)."""
    nums = []
    for i in range(1, 8):
        pares = list(contagens.get(i, {}).items())
        if not pares:
            nums.append(0)
            continue
        mais_freq = sorted(pares, key=lambda x: (-x[1], x[0]))[0][0]
        nums.append(mais_freq)
    return nums

def _predicao_baseline_freq_ss(concurso_data, historico_df, data_palpite):
    hist = _historico_antes_concurso(historico_df, concurso_data.get("concurso"))
    contagens = _contar_frequencias_por_coluna(hist)
    nums = _mais_frequentes_por_coluna(contagens)
    return {"data": data_palpite, "modelo": "baseline_freq", "jogo": nums, "simulada": True}

def _gerar_predicoes_simuladas(concurso_data, historico_df):
    from datetime import timedelta
    from random import seed
    try:
        seed(int(concurso_data["concurso"]))
    except Exception:
        pass
    data_palpite = (concurso_data["data_conc_dt"] - timedelta(hours=1)).strftime("%Y-%m-%d")
    return [
        _predicao_baseline_random_ss(data_palpite),
        _predicao_baseline_freq_ss(concurso_data, historico_df, data_palpite)
    ]

def _obter_palpites_para_concurso(concurso_data, todos_preds, historico_df):
    """Obtém palpites válidos (pré-sorteio) ou simula caso não existam."""
    palpites_validos = todos_preds if TEST_MODE else _filtrar_palpites_validos(todos_preds, concurso_data["data_conc_dt"])
    if not palpites_validos:
        return _gerar_predicoes_simuladas(concurso_data, historico_df)
    return palpites_validos

def benchmark():
    """Executa o benchmark comparando predições com resultados históricos."""
    df_real = load_dataset()
    preds = load_predictions()
    registros = []

    print(f"🔍 Processando {len(df_real)} concursos...")
    for _, row in df_real.iterrows():
        concurso_data = _processar_concurso_supersete(row)
        if not concurso_data:
            continue
        conc_id = concurso_data.get("concurso")
        if not conc_id or conc_id == "?":
            continue

        palpites = _obter_palpites_para_concurso(concurso_data, preds, df_real)
        for pred in palpites:
            registros.append(_gerar_registro_supersete(pred, concurso_data))

    print(f"📊 Gerados {len(registros)} registros de comparação")

    if not registros:
        print("⚠️ Nenhum registro válido para benchmarking.")
        return pd.DataFrame()

    os.makedirs(os.path.dirname(RESULT_CSV), exist_ok=True)
    df_benchmark = pd.DataFrame(registros)
    df_benchmark.to_csv(RESULT_CSV, index=False)
    return df_benchmark

def _calcular_faixas_acertos_supersete(df):
    """Calcula análise por faixas de acertos para cada modelo."""
    faixas_acertos = {}
    for modelo in df["modelo"].unique():
        dados_modelo = df[df["modelo"] == modelo]["acertos_totais"]
        faixas_acertos[modelo] = {
            "4_ou_mais": sum(dados_modelo >= 4),
            "5_ou_mais": sum(dados_modelo >= 5),
            "6_ou_mais": sum(dados_modelo >= 6),
            "7_acertos": sum(dados_modelo == 7)
        }
    return faixas_acertos

def _gerar_relatorio_markdown_supersete(resumo, faixas_acertos, df_full):
    """Gera o relatório markdown com as estatísticas."""
    melhor_modelo = resumo.loc[resumo["media_acertos"].idxmax()]
    
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("# 🎯 Benchmark Summary - SuperSete\n\n")
        f.write(f"**Período analisado:** Últimos {N_VALID} concursos\n")
        f.write(f"**Modelos testados:** {len(resumo)} modelos\n\n")
        
        f.write("## 📊 Performance Geral por Modelo\n\n")
        f.write(resumo.to_markdown(index=False))
        
        f.write("\n\n## 🏆 Análise de Faixas de Premiação\n\n")
        f.write("| Modelo | 4+ acertos | 5+ acertos | 6+ acertos | 7 acertos |\n")
        f.write("|--------|------------|------------|------------|----------|\n")
        
        for modelo, faixas in faixas_acertos.items():
            f.write(f"| {modelo} | {faixas['4_ou_mais']} | {faixas['5_ou_mais']} | {faixas['6_ou_mais']} | {faixas['7_acertos']} |\n")
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

def _cores_supersete():
    super_color = "#a8cf45"
    paleta = [super_color, "#8fb535", "#76a025", "#5d8b15", "#447605"]
    return super_color, paleta

def _criar_subplots_supersete():
    return make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "📊 Média de Acertos por Modelo",
            "📦 Distribuição de Acertos",
            "📈 Acertos por Concurso (Temporal)",
            "🥧 Proporção de Modelos"
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "domain"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

def _adicionar_barras_media(fig, resumo, cor):
    fig.add_trace(
        go.Bar(
            x=resumo["modelo"],
            y=resumo["media_acertos"],
            error_y=dict(type='data', array=resumo["desvio_padrao"]),
            name="Média de Acertos",
            marker_color=cor,
            text=[f"{v:.2f}" for v in resumo["media_acertos"]],
            textposition='outside',
            visible=True
        ),
        row=1, col=1
    )

def _adicionar_box_distribuicao(fig, resumo, df, cores):
    for i, modelo in enumerate(resumo["modelo"]):
        dados_modelo = df[df["modelo"] == modelo]["acertos_totais"]
        fig.add_trace(
            go.Box(y=dados_modelo, name=modelo, marker_color=cores[i % len(cores)], visible=True),
            row=1, col=2
        )

def _adicionar_temporal(fig, resumo, df, cores):
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

def _adicionar_pizza(fig, df, cores):
    modelo_counts = df["modelo"].value_counts()
    fig.add_trace(
        go.Pie(labels=modelo_counts.index, values=modelo_counts.values, name="Proporção",
               marker_colors=cores[:len(modelo_counts)], visible=True),
        row=2, col=2
    )

def _configurar_layout_grafico(fig, resumo, super_color):
    fig.update_layout(
        title={
            'text': "🎯 SuperSete - Análise Interativa de Performance dos Modelos",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': super_color}
        },
        showlegend=True,
        height=800,
        font=dict(size=10),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(label="📊 Visão Completa", method="update",
                         args=[{"visible": [True] * len(fig.data)}]),
                    dict(label="📊 Apenas Barras", method="update",
                         args=[{"visible": [i < 1 for i in range(len(fig.data))]}]),
                    dict(label="📦 Apenas Distribuição", method="update",
                         args=[{"visible": [1 <= i < 1 + len(resumo) for i in range(len(fig.data))]}]),
                    dict(label="📈 Apenas Temporal", method="update",
                         args=[{"visible": [1 + len(resumo) <= i < 1 + 2*len(resumo) for i in range(len(fig.data))]}]),
                    dict(label="🥧 Apenas Pizza", method="update",
                         args=[{"visible": [i == len(fig.data)-1 for i in range(len(fig.data))]}])
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

def _atualizar_eixos(fig):
    fig.update_xaxes(title_text="Modelos", row=1, col=1)
    fig.update_yaxes(title_text="Média de Acertos", row=1, col=1)
    fig.update_xaxes(title_text="Modelos", row=1, col=2)
    fig.update_yaxes(title_text="Acertos", row=1, col=2)
    fig.update_xaxes(title_text="Concursos", row=2, col=1)
    fig.update_yaxes(title_text="Acertos", row=2, col=1)

def _gerar_grafico_interativo_supersete(resumo, df):
    """Gera gráfico interativo de benchmark com múltiplas visualizações (modular)."""
    charts_dir = os.path.dirname(CHART_HTML)
    os.makedirs(charts_dir, exist_ok=True)

    super_color, cores = _cores_supersete()
    fig = _criar_subplots_supersete()
    _adicionar_barras_media(fig, resumo, super_color)
    _adicionar_box_distribuicao(fig, resumo, df, cores)
    _adicionar_temporal(fig, resumo, df, cores)
    _adicionar_pizza(fig, df, cores)
    _configurar_layout_grafico(fig, resumo, super_color)
    _atualizar_eixos(fig)

    fig.write_html(CHART_HTML, include_plotlyjs='cdn')
    print(f"📈 Gráfico interativo SuperSete salvo em: {CHART_HTML}")

def gerar_summary(df):
    """Gera o relatório de benchmark com estatísticas e gráficos."""
    if df.empty:
        print("⚠️ DataFrame vazio. Sumário não gerado.")
        return

    resumo = df.groupby("modelo")["acertos_totais"].agg(["mean", "std", "count"]).reset_index()
    resumo.columns = ["modelo", "media_acertos", "desvio_padrao", "n"]
    
    faixas_acertos = _calcular_faixas_acertos_supersete(df)
    melhor_modelo = _gerar_relatorio_markdown_supersete(resumo, faixas_acertos, df)
    _gerar_grafico_interativo_supersete(resumo, df)
    
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
