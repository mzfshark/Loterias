from pathlib import Path
from jinja2 import Template
import pandas as pd
import json
from typing import Optional
from datetime import datetime

# Configuração dos relatórios por jogo (ids em slug, títulos para exibição)
jogos = {
  "lotofacil": {
    "predictions": Path("Oraculo/Lotofacil/predictions"),
    "heatmap": Path("Oraculo/Lotofacil/docs/heatmap.html"),
    "title": "Lotofácil",
    "logo": "Oraculo/Lotofacil/docs/lotofacil.png"
  },
  "supersete": {
    "predictions": Path("Oraculo/SuperSete/predictions"),
    "heatmap": Path("Oraculo/SuperSete/docs/heatmap.html"),
    "title": "Super Sete",
    "logo": "Oraculo/SuperSete/docs/supersete.png"
  },
  "megasena": {
    "predictions": Path("Oraculo/MegaSena/predictions"),
    "heatmap": Path("Oraculo/MegaSena/docs/heatmap.html"),
    "title": "Mega-Sena",
    "logo": "Oraculo/MegaSena/docs/megasena.png"
  },
  "quina": {
    "predictions": Path("Oraculo/Quina/predictions"),
    "heatmap": Path("Oraculo/Quina/docs/heatmap.html"),
    "title": "Quina",
    "logo": "Oraculo/Quina/docs/quina.png"
  },
  "milionaria": {
    "predictions": Path("Oraculo/Milionaria/predictions"),
    "heatmap": Path("Oraculo/Milionaria/docs/heatmap.html"),
    "heatmap_trevos": Path("Oraculo/Milionaria/docs/heatmap_trevos.html"),
    "title": "+Milionária",
    "logo": "Oraculo/Milionaria/docs/milionaria.webp"
  }
}

def _arquivo_recente(prediction_dir: Path) -> Optional[Path]:
  arquivos = sorted(
    list(prediction_dir.glob("*.csv")) + list(prediction_dir.glob("*.json")),
    reverse=True
  )
  return arquivos[0] if arquivos else None

def _df_de_arquivo(path: Path) -> pd.DataFrame:
  try:
    if path.suffix.lower() == ".csv":
      return pd.read_csv(path)
    # JSON: tentar com pandas primeiro
    try:
      return pd.read_json(path, lines=True)
    except Exception:
      try:
        return pd.read_json(path)
      except Exception:
        with path.open("r", encoding="utf-8") as f:
          data = json.load(f)
        if isinstance(data, list):
          return pd.DataFrame(data)
        if isinstance(data, dict):
          # Se houver listas de tamanhos diferentes, alinhar pelo menor comprimento
          list_keys = [k for k, v in data.items() if isinstance(v, list)]
          if list_keys:
            min_len = min((len(data[k]) for k in list_keys if len(data[k]) > 0), default=0)
            rows = []
            for i in range(min_len):
              row = {}
              for k, v in data.items():
                if isinstance(v, list):
                  if i < len(v):
                    row[k] = v[i]
                else:
                  row[k] = v
              rows.append(row)
            return pd.DataFrame(rows)
          # Dicionário escalar -> uma linha
          return pd.DataFrame([data])
  except Exception:
    return pd.DataFrame()

def gerar_tabela_previsoes(prediction_dir: Path) -> str:
  if not prediction_dir.exists():
    return "<p class='muted'>Nenhuma previsão encontrada.</p>"

  mais_recente = _arquivo_recente(prediction_dir)
  if not mais_recente:
    return "<p class='muted'>Sem arquivos de previsão.</p>"

  # Primeiro, tenta extrair a predição ensemble se for JSON
  ensemble_html = ""
  if mais_recente.suffix.lower() == ".json":
    try:
      with mais_recente.open("r", encoding="utf-8") as f:
        data = json.load(f)
      if isinstance(data, dict) and 'ensemble_prediction' in data:
        ensemble_pred = data['ensemble_prediction']
        ensemble_conf = data.get('ensemble_confidence', 0.0)
        timestamp = data.get('timestamp', 'N/A')
        
        def _format_prediction(pred):
          if isinstance(pred, list):
            return ' '.join(str(x) for x in pred)
          return str(pred)
        
        ensemble_html = f"""
        <div class='card highlight'>
          <h3 class='card-title'>🏆 Predição Final do Ensemble</h3>
          <div class='ensemble-result'>
            <div class='prediction'>{_format_prediction(ensemble_pred)}</div>
            <div class='confidence'>Confiança: {ensemble_conf:.1%}</div>
            <div class='timestamp'>Gerado em: {timestamp}</div>
          </div>
        </div>
        """
    except Exception:
      pass

  df = _df_de_arquivo(mais_recente)
  if df.empty:
    if ensemble_html:
      return ensemble_html + "<p class='muted'>Não foi possível interpretar os modelos individuais.</p>"
    return "<p class='muted'>Não foi possível interpretar as previsões.</p>"

  # Garante CSV correspondente
  if mais_recente.suffix.lower() == ".csv":
    csv_path = mais_recente
    df_csv = df
  else:
    csv_path = prediction_dir / (mais_recente.stem + ".csv")
    if csv_path.exists():
      df_csv = pd.read_csv(csv_path)
    else:
      df.to_csv(csv_path, index=False)
      df_csv = df

  # Limita visualização para mobile se muito grande
  preview_rows = 100 if len(df_csv) > 100 else len(df_csv)

  # Normaliza colunas comuns
  def _normalize_prediction(val):
    try:
      if isinstance(val, str):
        # remove colchetes e vírgulas, mantém apenas números e espaços
        s = val.replace('[', '').replace(']', '').replace(',', ' ')
        s = ' '.join(s.split())
        return s
      if isinstance(val, (list, tuple)):
        return ' '.join(str(int(x)) for x in val)
      return str(val)
    except Exception:
      return str(val)

  bola_cols = [c for c in df_csv.columns if c.lower().startswith('bola')]
  modelo_col = 'modelo' if 'modelo' in df_csv.columns else ('model' if 'model' in df_csv.columns else None)
  jogo_col = None
  if 'jogo' in df_csv.columns:
    jogo_col = 'jogo'
  elif 'prediction' in df_csv.columns:
    jogo_col = 'prediction'

  conf_col = 'confidence' if 'confidence' in df_csv.columns else None
  time_col = 'timestamp' if 'timestamp' in df_csv.columns else ('data' if 'data' in df_csv.columns else None)

  # Organização especial: Lotofácil (colunas Bola1..BolaN) em uma única coluna 'jogo'
  if bola_cols:
    cols_ordenadas = sorted(bola_cols, key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
    def _jogo_str(row):
      vals = []
      for c in cols_ordenadas:
        try:
          v = row.get(c)
          if pd.isna(v):
            continue
          vals.append(str(int(v)))
        except Exception:
          continue
      return ' '.join(vals)
    view = pd.DataFrame()
    if modelo_col:
      view['modelo'] = df_csv[modelo_col]
    else:
      view['modelo'] = 'desconhecido'
    view['jogo'] = df_csv.apply(_jogo_str, axis=1)
    if conf_col:
      view['confiança'] = df_csv[conf_col]
    if time_col:
      view['gerado_em'] = df_csv[time_col]
    tabela_html = view.head(preview_rows).to_html(index=False, classes="table")
  else:
    # Padrão para todos os demais jogos: modelo, jogo, confiança, timestamp (quando existirem)
    view = pd.DataFrame()
    if modelo_col:
      view['modelo'] = df_csv[modelo_col]
    if jogo_col:
      view['jogo'] = df_csv[jogo_col].apply(_normalize_prediction)
    if conf_col:
      view['confiança'] = df_csv[conf_col]
    if time_col:
      view['gerado_em'] = df_csv[time_col]
    # Se por algum motivo não identificamos colunas, caímos na tabela original
    if view.empty:
      tabela_html = df_csv.head(preview_rows).to_html(index=False, classes="table")
    else:
      tabela_html = view.head(preview_rows).to_html(index=False, classes="table")
  # Não mostrar botão de download CSV na interface gerada (não necessário)
  models_table = f"<div class='card'><h3 class='card-title'>Modelos Individuais</h3><div class='table-wrap'>{tabela_html}</div></div>"
  
  # Retorna ensemble primeiro (se existe) + tabela de modelos
  return ensemble_html + models_table if ensemble_html else models_table

def carregar_heatmap(path: Path) -> str:
  # Resolve caminhos relativos ao diretório raiz do projeto
  current_dir = Path.cwd()
  if current_dir.name == 'scripts':
    project_root = current_dir.parent
  else:
    project_root = current_dir
  
  full_path = project_root / path
  if full_path.exists():
    return full_path.read_text(encoding="utf-8")
  return "<p class='muted'>Heatmap não disponível.</p>"

def get_game_colors(slug: str) -> dict:
  """Retorna as cores específicas de cada jogo para charts e visualizações (cores oficiais)"""
  colors = {
    "lotofacil": {
      "primary": "#c2318f",    # Rosa oficial Lotofácil
      "secondary": "#d14ba3",  # Rosa claro
      "accent": "#e073b7",     # Rosa suave
      "gradient": ["#c2318f", "#d14ba3", "#e073b7"]
    },
    "supersete": {
      "primary": "#a8cf45",    # Verde-limão oficial SuperSete
      "secondary": "#b6d65c",  # Verde-limão claro
      "accent": "#c4dd73",     # Verde-limão suave
      "gradient": ["#a8cf45", "#b6d65c", "#c4dd73"]
    },
    "megasena": {
      "primary": "#009e4c",    # Verde oficial MegaSena
      "secondary": "#1fb160",  # Verde claro
      "accent": "#4fc474",     # Verde suave
      "gradient": ["#009e4c", "#1fb160", "#4fc474"]
    },
    "quina": {
      "primary": "#42338b",    # Roxo oficial Quina
      "secondary": "#5a4ca0",  # Roxo claro
      "accent": "#7265b4",     # Roxo suave
      "gradient": ["#42338b", "#5a4ca0", "#7265b4"]
    },
    "milionaria": {
      "primary": "#2e307a",    # Azul oficial +Milionária
      "secondary": "#454891",  # Azul claro
      "accent": "#5c60a8",     # Azul suave
      "gradient": ["#2e307a", "#454891", "#5c60a8"]
    }
  }
  return colors.get(slug, colors["lotofacil"])  # Fallback para lotofacil

def gerar_conteudo_jogo(slug: str, cfg: dict) -> str:
  html = [f"<section class='tabcontent' id='{slug}'>"]
  # Cabeçalho com logo como ícone (125px de largura)
  logo_path = cfg.get('logo', '')
  titulo = cfg.get('title', slug.title())
  cabecalho = (
    f"<header class='section-header'>"
    f"<img src='{logo_path}' alt='{titulo} logo' width='220' height='auto' />"
    f"</header>"
  )
  html.append(cabecalho)

  prediction_dir = cfg["predictions"]

  # Heatmap / frequência
  html.append("<div class='card'><h3 class='card-title'>📊 Frequência Histórica</h3>")
  html.append("<div class='heatmap-wrap'>" + carregar_heatmap(cfg["heatmap"]) + "</div></div>")

  # Mini-heatmap de trevos (apenas +Milionária)
  if 'heatmap_trevos' in cfg:
    trevos_path = cfg['heatmap_trevos']
    if trevos_path.exists():
      html.append("<div class='card'><h3 class='card-title'>🍀 Trevos (1–6)</h3>")
      html.append("<div class='heatmap-wrap'>" + carregar_heatmap(trevos_path) + "</div></div>")

  # Tabela de palpites
  html.append(gerar_tabela_previsoes(prediction_dir))

  # Backtest / Acertos reais (se existir) - Versão melhorada
  try:
    # Resolve caminhos relativos ao diretório raiz do projeto
    current_dir = Path.cwd()
    if current_dir.name == 'scripts':
      project_root = current_dir.parent  # Estamos em /scripts, volta para raiz
    else:
      project_root = current_dir  # Já estamos na raiz
    base = project_root / cfg["predictions"].parents[0]  # Oraculo/Jogo
    summary_md = base / "docs" / "benchmark_summary.md"
    result_csv = base / "validation" / "benchmark_results.csv"
    chart_html = base / "docs" / "benchmark.html"
    chart_png = base / "docs" / "charts" / "benchmark_summary.png"
    
    # Obter cores do jogo
    game_colors = get_game_colors(slug)
    
  if summary_md.exists() or result_csv.exists() or chart_html.exists() or chart_png.exists():
      html.append(f"""
      <div class='card benchmark-card' data-game='{slug}'>
        <div class='benchmark-header' style='border-left: 4px solid {game_colors["primary"]}'>
          <h3 class='card-title'>
            <span class='benchmark-icon' style='color: {game_colors["primary"]}'>📈</span>
            Análise de Performance
          </h3>
          <p class='benchmark-subtitle'>Backtest em dados históricos reais</p>
        </div>
      """)
      
      # Sumário do benchmark com melhor formatação e embedding do gráfico interativo
      # Preferir: HTML interativo (chart_html) + tabela de resultados (result_csv)
      # Fallback: summary_md ou imagem estática
      # 1) Chart interativo
      if chart_html.exists():
        try:
          benchmark_content = chart_html.read_text(encoding='utf-8')
          styled_content = f"""
          <div class='benchmark-chart-container' data-game='{slug}'>
            <div class='chart-header'>
              <h4 style='color: {game_colors['primary']}'>📊 Gráfico Interativo</h4>
              <span class='chart-info'>Interaja com o gráfico: zoom, pan e tooltip.</span>
            </div>
            <div class='benchmark-chart-wrapper' style='--game-primary: {game_colors['primary']}; --game-secondary: {game_colors['secondary']};'>
              {benchmark_content}
            </div>
          </div>
          """
          html.append(styled_content)
        except Exception:
          pass

      # 2) Tabela de resultados (CSV de benchmark)
      if result_csv.exists():
        try:
          df_res = pd.read_csv(result_csv)
          # Limitar e formatar para exibição
          preview = df_res.head(200)
          tabela_bench = preview.to_html(index=False, classes='table table-striped')
          html.append(f"<div class='card'><h3 class='card-title'>Tabela de Benchmark (Top 200)</h3><div class='table-wrap'>{tabela_bench}</div></div>")
        except Exception:
          # fallback para summary_md
          if summary_md.exists():
            try:
              md_text = summary_md.read_text(encoding='utf-8')
              html.append(f"<div class='benchmark-summary'><pre class='md-content'>{md_text}</pre></div>")
            except Exception:
              pass
      else:
        # 3) Fallback para markdown summary se não houver CSV
        if summary_md.exists():
          try:
            md_text = summary_md.read_text(encoding='utf-8')
            html.append(f"<div class='benchmark-summary'><pre class='md-content'>{md_text}</pre></div>")
          except Exception:
            pass
      
      # Seção de ações com melhor visual
      actions_html = []
      if result_csv.exists():
        rel_csv = result_csv.relative_to(project_root)
        actions_html.append(f"""
        <a class='btn btn-download' href='{rel_csv.as_posix()}' download 
           style='background: linear-gradient(45deg, {game_colors["primary"]}, {game_colors["secondary"]}); color: white;'>
          📥 Baixar Dados (CSV)
        </a>
        """)
      
      # Não exibimos ações de download direto na página; usuários podem acessar os artefatos no repositório
      
      html.append("</div>")  # Fecha benchmark-card
      
    else:
      # Indica ausência de artefatos de benchmark para dar visibilidade
      html.append(f"""
      <div class='card benchmark-card benchmark-empty' data-game='{slug}'>
        <div class='benchmark-header' style='border-left: 4px solid {game_colors["primary"]}'>
          <h3 class='card-title'>
            <span class='benchmark-icon' style='color: {game_colors["primary"]}'>📈</span>
            Análise de Performance
          </h3>
        </div>
        <div class='benchmark-empty-state'>
          <div class='empty-icon' style='color: {game_colors["secondary"]}'>📊</div>
          <p class='empty-message'>Análise de benchmark em preparação</p>
          <p class='muted'>Os dados de performance histórica serão exibidos aqui após a próxima execução.</p>
        </div>
      </div>
      """)
  except Exception:
    # Em caso de erro, não mostra a seção
    pass

  # Resumo de estratégias (se coluna existir)
  try:
    mais_recente_misto = _arquivo_recente(prediction_dir)
    if mais_recente_misto is not None:
      df_resumo = _df_de_arquivo(mais_recente_misto)
      if not df_resumo.empty:
        col_modelo = 'modelo' if 'modelo' in df_resumo.columns else ('model' if 'model' in df_resumo.columns else None)
        if col_modelo:
          modelo_counts = df_resumo[col_modelo].value_counts().to_frame().reset_index()
        modelo_counts.columns = ['Modelo', 'Total']
        resumo_html = modelo_counts.to_html(index=False, classes="table")
        html.append(f"<div class='card'><h3 class='card-title'>Resumo de Estratégias</h3><div class='table-wrap'>{resumo_html}</div></div>")
  except Exception:
    pass

  html.append("</section>")
  return "".join(html)

# Coleta conteúdo por aba
abas_html = "\n".join([
  gerar_conteudo_jogo(slug, cfg) for slug, cfg in jogos.items()
])

html_template = Template("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Loterias • Relatórios Probabilísticos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header class="site-header">
    <div class="container">
      <h1>Relatórios Probabilísticos</h1>
      <p class="subtitle">Análises e palpites gerados por modelos estatísticos e ML. <span class="muted">Atualizado em {{ atualizado_em }}</span></p>
    </div>
  </header>

  <nav class="tabs container" aria-label="Seleção de jogo">
    {% for slug, cfg in jogos.items() %}
    <button class="tab-button" data-target="{{ slug }}">{{ cfg.title }}</button>
    {% endfor %}
  </nav>

  <main class="container">
    {{ abas_html | safe }}
  </main>

  <footer class="site-footer">
    <div class="container">
      <p class="muted small">Nota: resultados de loteria são aleatórios. Utilize as análises de forma responsável.</p>
    </div>
  </footer>

  <script>
    // Cores específicas de cada jogo (cores oficiais)
    const gameColors = {
      'lotofacil': { primary: '#c2318f', secondary: '#d14ba3', accent: '#e073b7' },
      'supersete': { primary: '#a8cf45', secondary: '#b6d65c', accent: '#c4dd73' },
      'megasena': { primary: '#009e4c', secondary: '#1fb160', accent: '#4fc474' },
      'quina': { primary: '#42338b', secondary: '#5a4ca0', accent: '#7265b4' },
      'milionaria': { primary: '#2e307a', secondary: '#454891', accent: '#5c60a8' }
    };

    function activateTab(targetId, btn){
      document.querySelectorAll('.tabcontent').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
      const section = document.getElementById(targetId);
      if(section) section.classList.add('active');
      if(btn) btn.classList.add('active');
      
      // Aplicar cores nos gráficos Plotly quando a aba for ativada
      setTimeout(() => applyGameColorsToCharts(targetId), 100);
    }

    function applyGameColorsToCharts(gameId) {
      const colors = gameColors[gameId];
      if (!colors) return;

      // Encontrar gráficos Plotly na aba ativa
      const activeSection = document.getElementById(gameId);
      if (!activeSection) return;

      const plotlyDivs = activeSection.querySelectorAll('.plotly-graph-div');
      plotlyDivs.forEach(div => {
        if (window.Plotly && div.layout) {
          try {
            // Atualizar cores do layout
            const update = {
              'paper_bgcolor': 'rgba(0,0,0,0)',
              'plot_bgcolor': 'rgba(0,0,0,0)',
              'font.color': '#e8eef5',
              'xaxis.gridcolor': colors.primary + '20',
              'yaxis.gridcolor': colors.primary + '20',
              'xaxis.zerolinecolor': colors.primary + '40',
              'yaxis.zerolinecolor': colors.primary + '40'
            };

            // Atualizar cores das séries de dados
            const dataUpdate = div.data?.map(trace => ({
              ...trace,
              marker: {
                ...trace.marker,
                color: trace.marker?.color || colors.primary,
                line: {
                  ...trace.marker?.line,
                  color: colors.secondary
                }
              },
              line: {
                ...trace.line,
                color: colors.primary
              }
            }));

            if (dataUpdate) {
              window.Plotly.restyle(div, dataUpdate);
            }
            window.Plotly.relayout(div, update);
          } catch (e) {
            console.log('Could not update chart colors:', e);
          }
        }
      });
    }

    // Função para redimensionar gráficos quando necessário
    function resizePlotlyCharts() {
      const plotlyDivs = document.querySelectorAll('.plotly-graph-div');
      plotlyDivs.forEach(div => {
        if (window.Plotly && div.layout) {
          try {
            window.Plotly.Plots.resize(div);
          } catch (e) {
            console.log('Could not resize chart:', e);
          }
        }
      });
    }

    // Configuração responsiva para gráficos Plotly
    function configurePlotlyResponsive() {
      const plotlyDivs = document.querySelectorAll('.plotly-graph-div');
      plotlyDivs.forEach(div => {
        if (window.Plotly && div.layout) {
          try {
            const update = {
              autosize: true,
              responsive: true,
              'xaxis.automargin': true,
              'yaxis.automargin': true
            };
            window.Plotly.relayout(div, update);
          } catch (e) {
            console.log('Could not configure responsive chart:', e);
          }
        }
      });
    }

    // Event listeners para responsividade
    window.addEventListener('resize', () => {
      clearTimeout(window.resizeTimeout);
      window.resizeTimeout = setTimeout(() => {
        resizePlotlyCharts();
        configurePlotlyResponsive();
      }, 250);
    });

    // Configurar responsividade inicial
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        configurePlotlyResponsive();
      }, 500);
    });
    function resizeCharts() {
      document.querySelectorAll('.plotly-graph-div').forEach(div => {
        if (window.Plotly) {
          window.Plotly.Plots.resize(div);
        }
      });
    }

    document.addEventListener('DOMContentLoaded', () => {
      const buttons = document.querySelectorAll('.tab-button');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => activateTab(btn.dataset.target, btn));
      });
      if(buttons.length){ 
        activateTab(buttons[0].dataset.target, buttons[0]);
      }

      // Redimensionar gráficos quando a janela for redimensionada
      window.addEventListener('resize', resizeCharts);
      
      // Aplicar cores iniciais após carregar
      setTimeout(() => {
        const activeTab = document.querySelector('.tab-button.active');
        if (activeTab) {
          applyGameColorsToCharts(activeTab.dataset.target);
        }
      }, 500);
    });
  </script>
</body>
</html>
""")

html_output = html_template.render(
  abas_html=abas_html,
  jogos=jogos,
  atualizado_em=datetime.now().strftime('%d/%m/%Y %H:%M')
)

# Salvar no diretório raiz do projeto
current_dir = Path.cwd()
if current_dir.name == 'scripts':
  output_path = current_dir.parent / "index.html"  # Volta para raiz
else:
  output_path = current_dir / "index.html"  # Já está na raiz

output_path.write_text(html_output, encoding="utf-8")
print("index.html gerado com sucesso.")
