from pathlib import Path
from jinja2 import Template
import pandas as pd
import json
from typing import Optional
from datetime import datetime
import math

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

def classificar_modelo(modelo: str):
  modelo = str(modelo).lower()
  if "bayes" in modelo:
    return "🔮", "tipo-bayes"
  if "monte" in modelo:
    return "🎲", "tipo-monte"
  if "markov" in modelo:
    return "🔗", "tipo-markov"
  if "gauss" in modelo or "galton" in modelo or "zscore" in modelo:
    return "📘", "tipo-galton"
  if "ml" in modelo or "neural" in modelo or "ensemble" in modelo:
    return "🤖", "tipo-ml"
  if "gen" in modelo or "genetic" in modelo or "evol" in modelo:
    return "🧬", "tipo-gen"
  if "poisson" in modelo or "freq" in modelo:
    return "📊", "tipo-pois"
  return "📐", "tipo-outro"


def gerar_modelos_individuais(df: pd.DataFrame) -> str:
  """Gera cards individuais para cada modelo, com suporte à Distribuição de Galton e sem timestamp."""
  if df is None or df.empty:
    return "<p class='muted'>Nenhuma previsão individual disponível.</p>"

  html = ["<div class='modelos-container'>"]

  for _, row in df.iterrows():
    modelo = row.get("modelo", row.get("model", "Desconhecido"))
    jogo = row.get("jogo") or row.get("prediction")
    conf = row.get("confidence", None)

    # Galton fields
    z = row.get("galton_zscore", None)
    dens = row.get("galton_density", None)

    # Format prediction
    try:
      jogo_fmt = " ".join(
        str(x)
        for x in str(jogo)
        .replace("[", "")
        .replace("]", "")
        .replace(",", " ")
        .split()
      )
    except Exception:
      jogo_fmt = str(jogo)

    try:
      conf_fmt = f"{float(conf)*100:.1f}%" if conf is not None else "--"
    except Exception:
      conf_fmt = "--"
    try:
      z_fmt = f"{float(z):.2f}" if z is not None else "--"
    except Exception:
      z_fmt = "--"
    try:
      dens_fmt = f"{float(dens):.4f}" if dens is not None else "--"
    except Exception:
      dens_fmt = "--"

    # Get icon + tipo class
    tipo_icon, tipo_class = classificar_modelo(modelo)

    card = f"""
    <div class='modelo-card {tipo_class}'>
      <div class='modelo-header'>
        <span class='modelo-icon'>{tipo_icon}</span>
            <h4 class='modelo-nome'>{modelo}</h4>
        </div>
        <div class='modelo-body'>
            <div class='modelo-pred'>🎯 {jogo_fmt}</div>
            <div class='modelo-metrics'>
                <span class='metric'>🔐 Confiança: {conf_fmt}</span>
                <span class='metric'>📉 Z-Score: {z_fmt}</span>
                <span class='metric'>📈 Densidade: {dens_fmt}</span>
            </div>
        </div>
    </div>
    """

    html.append(card)

  html.append("</div>")
  return "\n".join(html)


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
      view['confidence'] = df_csv[conf_col]
    # Galton: campos opcionais se existirem
    if 'galton_zscore' in df_csv.columns:
      view['galton_zscore'] = df_csv['galton_zscore']
    if 'galton_density' in df_csv.columns:
      view['galton_density'] = df_csv['galton_density']
  else:
    # Padrão para todos os demais jogos: modelo, jogo, confiança, timestamp (quando existirem)
    view = pd.DataFrame()
    if modelo_col:
      view['modelo'] = df_csv[modelo_col]
    else:
      view['modelo'] = df_csv.get('model', 'desconhecido')
    if jogo_col:
      view['jogo'] = df_csv[jogo_col].apply(_normalize_prediction)
    if conf_col:
      view['confidence'] = df_csv[conf_col]
    # Galton: campos opcionais
    if 'galton_zscore' in df_csv.columns:
      view['galton_zscore'] = df_csv['galton_zscore']
    if 'galton_density' in df_csv.columns:
      view['galton_density'] = df_csv['galton_density']

  # Substitui tabela por cards de modelos individuais (sem timestamp)
  models_table = f"""
  <div class='card'>
      <h3 class='card-title'>🧪 Modelos Individuais</h3>
      <p class='muted'>Resultados por estratégia estatística e IA.</p>
      {gerar_modelos_individuais(view.head(preview_rows))}
  </div>
  """
  
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

  # Nova sessão de Análise de Performance (ranking + detalhes por modelo)
  try:
    html.append(gerar_sessao_benchmark(slug, cfg))
  except Exception:
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


def _safe_mean(series: pd.Series) -> float:
  try:
    return float(series.mean())
  except Exception:
    return float('nan')


def _safe_std(series: pd.Series) -> float:
  try:
    val = float(series.std())
    if math.isnan(val):
      return 0.0
    return val
  except Exception:
    return 0.0


def _normalize_benchmark_df(df: pd.DataFrame) -> pd.DataFrame:
  """Normaliza o DataFrame de benchmark para conter colunas padrão:
  - 'modelo' (fallback de 'model')
  - 'acertos' (fallback de 'acertos_totais' ou 'hits')
  - Converte 'acertos' para numérico e remove NaN.
  """
  if df is None or df.empty:
    return pd.DataFrame()

  out = df.copy()

  # Mapeia renomeações em lote para reduzir ramificações
  rename_map = {}
  if 'modelo' not in out.columns and 'model' in out.columns:
    rename_map['model'] = 'modelo'

  if 'acertos' not in out.columns:
    for cand in ('acertos_totais', 'hits'):
      if cand in out.columns:
        rename_map[cand] = 'acertos'
        break

  if rename_map:
    out = out.rename(columns=rename_map)

  # Garante tipo numérico
  if 'acertos' in out.columns:
    out['acertos'] = pd.to_numeric(out['acertos'], errors='coerce')
    out = out.dropna(subset=['acertos'])

  return out


def gerar_ranking_benchmark(df: pd.DataFrame, colors: dict) -> str:
  if df is None or df.empty or 'modelo' not in df.columns or 'acertos' not in df.columns:
    return """
    <div class='card'>
      <h3 class='card-title'>🏁 Ranking de Modelos</h3>
      <p class='muted'>Dados em preparação.</p>
    </div>
    """

  grp = df.groupby('modelo', dropna=False)
  stats = grp['acertos'].agg(['mean', 'std', 'count', 'min', 'max']).reset_index()
  stats = stats.sort_values('mean', ascending=False).reset_index(drop=True)

  if 'galton_density' in df.columns:
    dens = grp['galton_density'].mean().reset_index(name='galton_density_mean')
    stats = stats.merge(dens, on='modelo', how='left')
  else:
    stats['galton_density_mean'] = None

  # Monta tabela HTML com cabeçalho fixo e estilos existentes
  header = (
    "<thead><tr>"
    "<th>Posição</th>"
    "<th>Modelo</th>"
    "<th>Média</th>"
    "<th>±DP</th>"
    "<th>n</th>"
    "<th>Mín</th>"
    "<th>Máx</th>"
    "<th>Galton Density</th>"
    "</tr></thead>"
  )

  rows = []
  for i, row in stats.iterrows():
    pos = i + 1
    medal = '🥇' if pos == 1 else ('🥈' if pos == 2 else ('🥉' if pos == 3 else str(pos)))
    nome = row['modelo']
    mean_acc = 0.0 if pd.isna(row['mean']) else float(row['mean'])
    std_acc = 0.0 if pd.isna(row['std']) else float(row['std'])
    cnt = int(row['count']) if not pd.isna(row['count']) else 0
    min_acc = 0.0 if pd.isna(row['min']) else float(row['min'])
    max_acc = 0.0 if pd.isna(row['max']) else float(row['max'])
    dens_mean = row.get('galton_density_mean', None)
    dens_str = f"{dens_mean:.4f}" if dens_mean is not None and not pd.isna(dens_mean) else "—"
    rows.append(
      f"<tr>"
      f"<td class='pos'>{medal}</td>"
      f"<td class='model'><strong>{nome}</strong></td>"
      f"<td>{mean_acc:.2f}</td>"
      f"<td>{std_acc:.2f}</td>"
      f"<td>{cnt}</td>"
      f"<td>{min_acc:.2f}</td>"
      f"<td>{max_acc:.2f}</td>"
      f"<td>{dens_str}</td>"
      f"</tr>"
    )

  table_html = f"<div class='table-wrap'><table class='table ranking-table'>{header}<tbody>{''.join(rows)}</tbody></table></div>"

  return f"""
  <div class='card'>
    <h3 class='card-title'>🏁 Ranking de Modelos</h3>
    {table_html}
  </div>
  """


def gerar_detalhes_benchmark(df: pd.DataFrame, modelo: str, colors: dict) -> str:
  try:
    df_m = df[df['modelo'] == modelo].copy()
    if df_m.empty:
      return ""

    # Eixos do gráfico (concursos x acertos)
    if 'concurso' in df_m.columns:
      x_vals = df_m['concurso'].astype(str).tolist()
    else:
      x_vals = list(range(1, len(df_m) + 1))
    y_vals = df_m['acertos'].tolist()

    # Métricas
    mean_acc = _safe_mean(df_m['acertos'])
    std_acc = _safe_std(df_m['acertos'])
    best = float(df_m['acertos'].max())
    worst = float(df_m['acertos'].min())
    n = int(df_m.shape[0])

    dens_mean = None
    if 'galton_density' in df_m.columns:
      dens_mean = _safe_mean(df_m['galton_density'])

    # Z-score médio da performance (em relação ao global dos acertos)
    if 'acertos' in df.columns and df['acertos'].std() not in (0, None) and not pd.isna(df['acertos'].std()):
      global_mean = float(df['acertos'].mean())
      global_std = float(df['acertos'].std())
      if global_std == 0 or pd.isna(global_std):
        z_mean = 0.0
      else:
        z_vals = (df_m['acertos'] - global_mean) / global_std
        z_mean = _safe_mean(z_vals)
    else:
      z_mean = 0.0

    x_json = json.dumps(x_vals)
    y_json = json.dumps(y_vals)
    color = colors.get('primary', '#2FD39A')

    dens_html = f"<span class='metric'>📈 Galton Density (média): {dens_mean:.4f}</span>" if dens_mean is not None and not pd.isna(dens_mean) else ""

    return f"""
    <details class='card'>
      <summary class='card-title'>📘 {modelo} — Ver detalhes</summary>
      <div class='benchmark-model'>
        <div class='modelo-metrics'>
          <span class='metric'>📊 Média de acertos: {mean_acc:.2f}</span>
          <span class='metric'>📉 Desvio-padrão: {std_acc:.2f}</span>
          <span class='metric'>🎯 Melhor/Pior: {best:.2f} / {worst:.2f}</span>
          <span class='metric'>🧮 Amostra (n): {n}</span>
          <span class='metric'>📈 Z-Score médio: {z_mean:.2f}</span>
          {dens_html}
        </div>
        <div class='benchmark-chart-wrapper'>
          <div class='plotly-model' data-x='{x_json}' data-y='{y_json}' data-color='{color}'></div>
        </div>
      </div>
      <div class='table-wrap'>
        {df_m.head(300).to_html(index=False, classes='table')}
      </div>
    </details>
    """
  except Exception:
    return ""


def gerar_sessao_benchmark(slug: str, cfg: dict) -> str:
  # Resolve caminhos relativos ao diretório raiz do projeto
  current_dir = Path.cwd()
  if current_dir.name == 'scripts':
    project_root = current_dir.parent
  else:
    project_root = current_dir

  base = project_root / cfg['predictions'].parents[0]  # Oraculo/Jogo
  result_csv = base / 'validation' / 'benchmark_results.csv'
  game_colors = get_game_colors(slug)

  if not result_csv.exists():
    return f"""
    <div class='card benchmark-card benchmark-empty' data-game='{slug}'>
      <div class='benchmark-header'>
        <h3 class='card-title'>
          <span class='benchmark-icon'>📈</span>
          Análise de Performance
        </h3>
      </div>
      <div class='benchmark-empty-state'>
        <div class='empty-icon'>📊</div>
        <p class='empty-message'>Análise de benchmark em preparação</p>
        <p class='muted'>Os dados de performance histórica serão exibidos aqui após a próxima execução.</p>
      </div>
    </div>
    """

  try:
    df_bench_raw = pd.read_csv(result_csv)
  except Exception:
    return f"""
    <div class='card'>
      <h3 class='card-title'>📈 Análise de Performance</h3>
      <p class='muted'>Não foi possível carregar os dados de benchmark.</p>
    </div>
    """

  # Normaliza colunas do benchmark para formato padrão
  df_bench = _normalize_benchmark_df(df_bench_raw)

  # Ranking geral
  ranking_html = gerar_ranking_benchmark(df_bench, game_colors)

  # Detalhes por modelo (ordenar pelo ranking)
  models_order = []
  try:
    order_df = df_bench.groupby('modelo')['acertos'].mean().sort_values(ascending=False).reset_index()
    models_order = order_df['modelo'].tolist()
  except Exception:
    models_order = sorted(df_bench['modelo'].dropna().unique().tolist()) if 'modelo' in df_bench.columns else []

  detalhes_blocks = []
  for m in models_order:
    detalhes_blocks.append(gerar_detalhes_benchmark(df_bench, m, game_colors))

  detalhes_html = "\n".join(block for block in detalhes_blocks if block)

  return f"""
  <div class='card benchmark-card' data-game='{slug}'>
    <div class='benchmark-header'>
      <h3 class='card-title'>
        <span class='benchmark-icon'>📈</span>
        Análise de Performance
      </h3>
      <p class='benchmark-subtitle'>Backtest em dados históricos reais</p>
    </div>
    {ranking_html}
    {detalhes_html}
  </div>
  """

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
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
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
            const palette = [colors.primary, colors.accent, colors.secondary];

            // Atualizar cores do layout e colorway
            const layoutUpdate = {
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: '#e8eef5' },
              colorway: palette,
              'xaxis.gridcolor': colors.primary + '20',
              'yaxis.gridcolor': colors.primary + '20',
              'xaxis.zerolinecolor': colors.primary + '40',
              'yaxis.zerolinecolor': colors.primary + '40'
            };

            // Atualizar cores de cada trace, forçando paleta do jogo
            if (Array.isArray(div.data)) {
              div.data.forEach((t, i) => {
                const c = palette[i % palette.length];
                const update = {};
                // Linhas e marcadores
                update['line.color'] = c;
                update['marker.color'] = c;
                // Heatmaps: aplicar colorscale coerente com a paleta
                if (t.type === 'heatmap' || t.type === 'contour') {
                  update['colorscale'] = [[0, colors.accent], [0.5, colors.secondary], [1, colors.primary]];
                  update['reversescale'] = false;
                  update['showscale'] = true;
                }
                window.Plotly.restyle(div, update, [i]);
              });
            }

            window.Plotly.relayout(div, layoutUpdate);
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

      // Renderizar gráficos de desempenho por modelo (Plotly)
      const plotDivs = document.querySelectorAll('.plotly-model');
      plotDivs.forEach(div => {
        try {
          const x = JSON.parse(div.dataset.x || '[]');
          const y = JSON.parse(div.dataset.y || '[]');
          const color = div.dataset.color || '#2FD39A';
          if (window.Plotly && Array.isArray(x) && Array.isArray(y) && x.length === y.length && x.length > 0) {
            const data = [{ x, y, mode: 'lines+markers', line: { color }, marker: { color } }];
            const layout = {
              margin: { t: 10, r: 10, b: 40, l: 40 },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: '#e8eef5' },
              xaxis: { automargin: true, gridcolor: color + '33' },
              yaxis: { automargin: true, gridcolor: color + '33' }
            };
            const config = { displayModeBar: false, responsive: true };
            window.Plotly.newPlot(div, data, layout, config);
          }
        } catch (e) {
          console.log('Plotly render error:', e);
        }
      });
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
