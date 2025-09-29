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

  df = _df_de_arquivo(mais_recente)
  if df.empty:
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
  link = f"<a class='btn' href='{csv_path.as_posix()}' download>📥 Baixar CSV</a>"
  count_info = f"<span class='muted'>Exibindo {preview_rows} de {len(df_csv)} linhas</span>" if len(df_csv) > preview_rows else ""
  return f"<div class='card'><h3 class='card-title'>Previsões Recentes</h3><div class='table-wrap'>{tabela_html}</div><div class='actions'>{link}{count_info}</div></div>"

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

  # Backtest / Acertos reais (se existir)
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
    chart_img = base / "docs" / "charts" / "benchmark_summary.png"
    
    if summary_md.exists() or result_csv.exists() or chart_img.exists():
      html.append("<div class='card'><h3 class='card-title'>📈 Backtest / Acertos Reais</h3>")
      links = []
      if result_csv.exists():
        # Usar caminho relativo do CSV para o HTML
        rel_csv = result_csv.relative_to(project_root)
        links.append(f"<a class='btn' href='{rel_csv.as_posix()}' download>📥 Baixar resultados (CSV)</a>")
      if summary_md.exists():
        # Render simples do markdown como preformatado para evitar dependências
        md_text = summary_md.read_text(encoding='utf-8')
        html.append(f"<details open><summary>Sumário</summary><pre class='md'>{md_text}</pre></details>")
      if chart_img.exists():
        # Usar caminho relativo da imagem para o HTML
        rel_img = chart_img.relative_to(project_root)
        html.append(f"<div class='img-wrap'><img src='{rel_img.as_posix()}' alt='Resumo de acertos' /></div>")
      if links:
        html.append("<div class='actions'>" + " ".join(links) + "</div>")
      html.append("</div>")
    else:
      # Indica ausência de artefatos de benchmark para dar visibilidade
      html.append("<div class='card'><h3 class='card-title'>📈 Backtest / Acertos Reais</h3><p class='muted'>Nenhum artefato de benchmark encontrado.</p></div>")
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
    function activateTab(targetId, btn){
      document.querySelectorAll('.tabcontent').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
      const section = document.getElementById(targetId);
      if(section) section.classList.add('active');
      if(btn) btn.classList.add('active');
    }
    document.addEventListener('DOMContentLoaded', () => {
      const buttons = document.querySelectorAll('.tab-button');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => activateTab(btn.dataset.target, btn));
      });
      if(buttons.length){ activateTab(buttons[0].dataset.target, buttons[0]); }
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
