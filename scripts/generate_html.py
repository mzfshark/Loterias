import markdown2
from pathlib import Path
from jinja2 import Template
import json
import pandas as pd
import plotly.express as px

# Caminhos dos relatórios por jogo
jogos = {
    "Lotofácil": {
        "predictions": Path("Oraculo/Lotofacil/predictions"),
        "title": "Lotofácil"
    },
    "Super Sete": {
        "predictions": Path("Oraculo/SuperSete/predictions"),
        "title": "Super Sete"
    },
    "Mega-Sena": {
        "predictions": Path("Oraculo/MegaSena/predictions"),
        "title": "Mega-Sena"
    }
}

def gerar_tabela_previsoes(prediction_dir: Path) -> str:
    if not prediction_dir.exists():
        return "<p><em>Nenhuma previsão encontrada.</em></p>"

    arquivos = sorted(prediction_dir.glob("*.json"), reverse=True)
    if not arquivos:
        return "<p><em>Sem arquivos de previsão.</em></p>"

    mais_recente = arquivos[0]
    df = pd.read_json(mais_recente)
    csv_path = prediction_dir / (mais_recente.stem + ".csv")
    if csv_path.exists():
        df_csv = pd.read_csv(csv_path)
    else:
        df.to_csv(csv_path, index=False)
        df_csv = df

    tabela_html = df_csv.to_html(index=False, classes="prediction-table")
    link = f"<a href='{csv_path.as_posix()}' download>📥 Baixar CSV</a>"
    return f"<h3>Previsões Recentes</h3>{tabela_html}<br>{link}"

def gerar_heatmap(df: pd.DataFrame) -> str:
    df_long = df.melt(var_name="Coluna", value_name="Dígito")
    freq = df_long.groupby(["Coluna", "Dígito"]).size().reset_index(name="Frequência")
    fig = px.density_heatmap(freq, x="Coluna", y="Dígito", z="Frequência",
                             color_continuous_scale="Viridis", 
                             labels={"Dígito": "Dígito", "Frequência": "Frequência"},
                             height=400)
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def gerar_conteudo_jogo(nome: str, paths: dict) -> str:
    html = f"<div class='tabcontent' id='{nome}'><h2>{paths['title']}</h2>"

    prediction_dir = paths["predictions"]
    arquivos = sorted(prediction_dir.glob("*.csv"), reverse=True)
    if not arquivos:
        html += "<p><em>Sem dados disponíveis.</em></p></div>"
        return html

    mais_recente = arquivos[0]
    df = pd.read_csv(mais_recente)

    html += "<h3>📊 Frequência Histórica</h3>"
    html += gerar_heatmap(df[[c for c in df.columns if c.startswith("col")]])

    html += "<h3>🧠 Palpites Gerados</h3>"
    html += gerar_tabela_previsoes(prediction_dir)

    # Exibir resumo de estratégias
    modelo_counts = df['modelo'].value_counts().to_frame().reset_index()
    modelo_counts.columns = ['Modelo', 'Total']
    html += f"<h4>Resumo de estratégias</h4>"
    html += modelo_counts.to_html(index=False, classes="prediction-table")

    html += "</div>"
    return html

# Coleta conteúdo por aba
abas_html = "\n".join([
    gerar_conteudo_jogo(nome, paths) for nome, paths in jogos.items()
])

html_template = Template("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Relatórios de Loterias</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #111; color: #eee; padding: 2rem; }
    h1 { color: #2fd39a; }
    .tabs { display: flex; gap: 1rem; margin-bottom: 1rem; }
    .tab-button {
      padding: 0.5rem 1rem;
      background: #222;
      border: none;
      color: #2fd39a;
      cursor: pointer;
    }
    .tab-button.active { background: #2fd39a; color: #000; }
    .tabcontent { display: none; animation: fadeIn 0.3s ease-in-out; }
    .tabcontent.active { display: block; }
    .plotly-container { margin-top: 1rem; }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    table, th, td {
      border: 1px solid #444;
      border-collapse: collapse;
      padding: 0.4rem;
    }
    th { background: #2fd39a; color: #000; }
    .prediction-table { margin-top: 1rem; background: #000; }
    .prediction-table th, .prediction-table td { text-align: center; }
    a { color: #2fd39a; text-decoration: none; }
  </style>
</head>
<body>
  <h1>Relatórios Probabilísticos - Loterias</h1>
  <div class="tabs">
    {% for nome in jogos.keys() %}
    <button class="tab-button" onclick="openTab('{{ nome }}')">{{ nome }}</button>
    {% endfor %}
  </div>
  {{ abas_html | safe }}

  <script>
    function openTab(tabName) {
      const contents = document.querySelectorAll('.tabcontent');
      contents.forEach(c => c.classList.remove('active'));
      const tabs = document.querySelectorAll('.tab-button');
      tabs.forEach(t => t.classList.remove('active'));
      document.getElementById(tabName).classList.add('active');
      event.currentTarget.classList.add('active');
    }
    document.addEventListener('DOMContentLoaded', () => {
      const firstTab = document.querySelector('.tab-button');
      if (firstTab) firstTab.click();
    });
  </script>
</body>
</html>
""")

html_output = html_template.render(
    abas_html=abas_html,
    jogos=jogos
)
Path("index.html").write_text(html_output, encoding="utf-8")
print("index.html gerado com sucesso.")
