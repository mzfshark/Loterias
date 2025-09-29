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
  tabela_html = df_csv.head(preview_rows).to_html(index=False, classes="table")
  link = f"<a class='btn' href='{csv_path.as_posix()}' download>📥 Baixar CSV</a>"
  count_info = f"<span class='muted'>Exibindo {preview_rows} de {len(df_csv)} linhas</span>" if len(df_csv) > preview_rows else ""
  return f"<div class='card'><h3 class='card-title'>Previsões Recentes</h3><div class='table-wrap'>{tabela_html}</div><div class='actions'>{link}{count_info}</div></div>"

def carregar_heatmap(path: Path) -> str:
  if path.exists():
    return path.read_text(encoding="utf-8")
  return "<p class='muted'>Heatmap não disponível.</p>"

def gerar_conteudo_jogo(slug: str, cfg: dict) -> str:
  html = [f"<section class='tabcontent' id='{slug}'>"]
  # Cabeçalho com logo como ícone (125px de largura)
  logo_path = cfg.get('logo', '')
  titulo = cfg.get('title', slug.title())
  cabecalho = (
    f"<header class='section-header'>"
    f"<img src='{logo_path}' alt='{titulo} logo' width='150' height='auto' />"
    f"</header>"
  )
  html.append(cabecalho)

  prediction_dir = cfg["predictions"]
  arquivos = sorted(prediction_dir.glob("*.csv"), reverse=True)
  if not arquivos:
    html.append("<p class='muted'>Sem dados disponíveis.</p>")
    html.append("</section>")
    return "".join(html)

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
    base = Path(cfg["predictions"]).parents[0]  # Oraculo/Jogo
    summary_md = base / "validation" / "benchmark_summary.md"
    result_csv = base / "validation" / "benchmark_results.csv"
    chart_img = base / "docs" / "charts" / "benchmark_summary.png"
    if summary_md.exists() or result_csv.exists() or chart_img.exists():
      html.append("<div class='card'><h3 class='card-title'>📈 Backtest / Acertos Reais</h3>")
      links = []
      if result_csv.exists():
        links.append(f"<a class='btn' href='{result_csv.as_posix()}' download>📥 Baixar resultados (CSV)</a>")
      if summary_md.exists():
        # Render simples do markdown como preformatado para evitar dependências
        md_text = summary_md.read_text(encoding='utf-8')
        html.append(f"<details open><summary>Sumário</summary><pre class='md'>{md_text}</pre></details>")
      if chart_img.exists():
        html.append(f"<div class='img-wrap'><img src='{chart_img.as_posix()}' alt='Resumo de acertos' /></div>")
      if links:
        html.append("<div class='actions'>" + " ".join(links) + "</div>")
      html.append("</div>")
  except Exception:
    pass

  # Resumo de estratégias (se coluna existir)
  try:
    mais_recente_misto = _arquivo_recente(prediction_dir)
    if mais_recente_misto is not None:
      df_resumo = _df_de_arquivo(mais_recente_misto)
      if not df_resumo.empty and 'modelo' in df_resumo.columns:
        modelo_counts = df_resumo['modelo'].value_counts().to_frame().reset_index()
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
Path("index.html").write_text(html_output, encoding="utf-8")
print("index.html gerado com sucesso.")
