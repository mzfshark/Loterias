import pandas as pd
import os
import glob
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import json

# === CONFIGURAÇÃO ===
JOGO = "Milionaria"
DATASET_PATH = "../data/Milionaria.csv"
PRED_PATH = "../predictions"
RESULT_CSV = "../validation/benchmark_results.csv"
SUMMARY_MD = "../docs/benchmark_summary.md"
CHART_HTML = "../docs/charts/benchmark_interactive.html"

# === PARÂMETROS ===
N_VALID = 300
TEST_MODE = True  # Permite qualquer predição ser comparada com qualquer concurso

# Verificação de caminhos
def verificar_paths():
    """Verifica se os caminhos essenciais existem."""
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"📄 Procurando dataset: {DATASET_PATH}")
    
    if not os.path.exists(DATASET_PATH):
        # Tentar caminhos alternativos
        alt_paths = [
            "../data/Milionaria.csv",
            "data/Milionaria.csv", 
            "Oraculo/Milionaria/data/Milionaria.csv",
            "../Milionaria/data/Milionaria.csv"
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
    # +Milionária tem trevos; aqui contamos apenas acertos dos números principais se o CSV contiver apenas eles
    acertos = len(set(palpite) & set(real))
    return acertos


def _processar_concurso_milionaria(row):
    """Processa um concurso individual e retorna os dados validados."""
    data_conc = row.get("Data Sorteio")
    if not data_conc:
        return None

    # Extrair apenas os números principais (Bola1-Bola6)
    try:
        nums_reais = []
        for i in range(1, 7):  # Bola1 a Bola6
            bola = row.get(f"Bola{i}")
            if bola is not None:
                nums_reais.append(int(bola))
            else:
                return None
        
        if len(nums_reais) != 6:
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

def _filtrar_palpites_validos(preds, data_conc_dt):
    """Filtra palpites válidos anteriores ao concurso."""
    palpites_validos = []
    for p in preds:
        p_dt = parse_date_multi(p["data"])
        if TEST_MODE:
            # Em modo teste, aceita qualquer predição com data válida
            if p_dt:
                palpites_validos.append(p)
        else:
            # Modo normal: apenas predições anteriores ao concurso
            if p_dt and p_dt < data_conc_dt:
                palpites_validos.append(p)
    return palpites_validos

def _gerar_registro_milionaria(pmais_recente, concurso_data):
    """Gera um registro de benchmark para +Milionária."""
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
    
    debug_count = 0
    for _, row in df_real.iterrows():
        debug_count += 1
        if debug_count <= 3:  # Debug primeiros 3 concursos
            concurso = row.get('Concurso', '?')
            print(f"🔍 Debug concurso {debug_count}: {concurso}")
            print(f"   Colunas disponíveis: {list(row.index)}")
        
        concurso_data = _processar_concurso_milionaria(row)
        if not concurso_data:
            if debug_count <= 3:
                print(f"   ❌ Falha no processamento do concurso")
            continue
        
        if debug_count <= 3:
            print(f"   ✅ Concurso processado: {concurso_data['concurso']}")
            print(f"   📅 Data concurso: {concurso_data['data_conc_dt']}")

        palpites_validos = _filtrar_palpites_validos(preds, concurso_data["data_conc_dt"])
        if debug_count <= 3:
            print(f"   🎯 Palpites válidos encontrados: {len(palpites_validos)}")
        
        if not palpites_validos:
            continue

        pmais_recente = max(palpites_validos, key=lambda x: parse_date_multi(x["data"]))
        registro = _gerar_registro_milionaria(pmais_recente, concurso_data)
        registros.append(registro)

    print(f"📊 Gerados {len(registros)} registros de comparação")

    if not registros:
        print("⚠️ Nenhum registro válido para benchmarking.")
        return pd.DataFrame()

    os.makedirs(os.path.dirname(RESULT_CSV), exist_ok=True)
    df_benchmark = pd.DataFrame(registros)
    df_benchmark.to_csv(RESULT_CSV, index=False)
    return df_benchmark


def _calcular_faixas_acertos_milionaria(df):
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

def _gerar_relatorio_markdown_milionaria(resumo, faixas_acertos):
    """Gera o relatório markdown com as estatísticas."""
    melhor_modelo = resumo.loc[resumo["media_acertos"].idxmax()]
    
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("# 🎯 Benchmark Summary - +Milionária\n\n")
        f.write(f"**Período analisado:** Últimos {N_VALID} concursos\n")
        f.write(f"**Modelos testados:** {len(resumo)} modelos\n\n")
        
        f.write("## 📊 Performance Geral por Modelo\n\n")
        try:
            f.write(resumo.to_markdown(index=False))
        except Exception:
            f.write(resumo.to_string(index=False))
        
        f.write("\n\n## 🏆 Análise de Faixas de Premiação\n\n")
        f.write("| Modelo | 4+ acertos | 5+ acertos | 6 acertos |\n")
        f.write("|--------|------------|------------|----------|\n")
        
        for modelo, faixas in faixas_acertos.items():
            f.write(f"| {modelo} | {faixas['4_ou_mais']} | {faixas['5_ou_mais']} | {faixas['6_acertos']} |\n")
        
        f.write(f"\n## 🥇 Melhor Modelo: **{melhor_modelo['modelo']}**\n")
        f.write(f"- Média de acertos: **{melhor_modelo['media_acertos']:.2f}**\n")
        f.write(f"- Desvio padrão: {melhor_modelo['desvio_padrao']:.2f}\n")
    
    return melhor_modelo

def _gerar_grafico_interativo_milionaria(resumo, df):
    """Gera gráfico interativo de benchmark com múltiplas visualizações."""
    charts_dir = os.path.dirname(CHART_HTML)
    os.makedirs(charts_dir, exist_ok=True)

    # Cor oficial da +Milionária
    MILIONARIA_COLOR = "#2e307a"
    
    # Criar paleta de cores baseada na cor principal
    cores = [MILIONARIA_COLOR, "#252768", "#1c1e56", "#131544", "#0a0c32"]

    # Criar subplots 2x2
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("📊 Média de Acertos por Modelo", "📦 Distribuição de Acertos", 
                       "📈 Acertos por Concurso (Temporal)", "🥧 Proporção de Modelos"),
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
            marker_color=MILIONARIA_COLOR,
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

    # 4. Pie Chart - Proporção de uso dos modelos
    modelo_counts = df["modelo"].value_counts()
    fig.add_trace(
        go.Pie(
            labels=modelo_counts.index,
            values=modelo_counts.values,
            name="Proporção",
            marker_colors=cores[:len(modelo_counts)],
            visible=True
        ),
        row=2, col=2
    )

    # Configurar layout
    fig.update_layout(
        title={
            'text': "🎯 +Milionária - Análise Interativa de Performance dos Modelos",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': MILIONARIA_COLOR}
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
                    dict(label="🥧 Apenas Pizza", method="update",
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
    print(f"📈 Gráfico interativo +Milionária salvo em: {CHART_HTML}")

def gerar_summary(df):
    """Gera o relatório de benchmark com estatísticas e gráficos."""
    if df.empty:
        print("⚠️ DataFrame vazio. Sumário não gerado.")
        return

    resumo = df.groupby("modelo")["acertos_totais"].agg(["mean", "std", "count"]).reset_index()
    resumo.columns = ["modelo", "media_acertos", "desvio_padrao", "n"]
    
    os.makedirs(os.path.dirname(SUMMARY_MD), exist_ok=True)
    
    faixas_acertos = _calcular_faixas_acertos_milionaria(df)
    melhor_modelo = _gerar_relatorio_markdown_milionaria(resumo, faixas_acertos)
    _gerar_grafico_interativo_milionaria(resumo, df)
    
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
