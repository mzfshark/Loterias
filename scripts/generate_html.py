import markdown2
from pathlib import Path
from jinja2 import Template
import json
import pandas as pd

# Caminhos dos relatórios markdown gerados por cada jogo
jogos = {
    "Lotofácil": {
        "md": Path("Oraculo/Lotofacil/docs/index.md"),
        "extras": [
            Path("Oraculo/Lotofacil/docs/heatmap.html"),
            Path("Oraculo/Lotofacil/docs/performance.html")
        ],
        "predictions": Path("Oraculo/Lotofacil/predictions")
    },
    "Super Sete": {
        "md": Path("Oraculo/SuperSete/docs/index.md"),
        "extras": [],
        "predictions": Path("Oraculo/SuperSete/predictions")
    },
    "Mega-Sena": {
        "md": Path("Oraculo/MegaSena/docs/index.md"),
        "extras": [],
        "predictions": Path("Oraculo/MegaSena/predictions")
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
    df.to_csv(csv_path, index=False)

    tabela_html = df.to_html(index=False, classes="prediction-table")
    link = f"<a href='{csv_path.as_posix()}' download>📥 Baixar CSV</a>"

    return f"<h3>Previsões Recentes</h3>{tabela_html}<br>{link}"

# Função para carregar e converter markdown + extras em HTML
def read_and_convert(jogo: str, paths: dict) -> str:
    html = f"<div class='tabcontent' id='{jogo}'><h2>{jogo}</h2>"

    md_path = paths.get("md")
    if md_path.exists():
        with md_path.open("r", encoding="utf-8") as f:
            html += markdown2.markdown(f.read())
    else:
        html += f"<p><em>Relatório não encontrado.</em></p>"

    for extra_path in paths.get("extras", []):
        if extra_path.exists():
            html += f"<div class='plotly-container'>{extra_path.read_text(encoding='utf-8')}</div>"

    html += gerar_tabela_previsoes(paths["predictions"])
    html += "</div>"
    return html

# Coleta os conteúdos em abas
abas_html = "\n".join([
    read_and_convert(nome, paths) for nome, paths in jogos.items()
])

# Criar estrutura de navegação por abas e renderizar template final
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

# Renderiza HTML final e salva
html_output = html_template.render(
    abas_html=abas_html,
    jogos=jogos
)
Path("index.html").write_text(html_output, encoding="utf-8")
print("index.html gerado com sucesso.")
