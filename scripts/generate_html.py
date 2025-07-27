import markdown2
from pathlib import Path
from jinja2 import Template

# Caminhos dos relatórios markdown gerados por cada jogo
jogos = {
    "Lotofácil": Path("Oraculo/Lotofacil/docs/index.md"),
    "Super Sete": Path("Oraculo/SuperSete/docs/index.md"),
    "Mega-Sena": Path("Oraculo/MegaSena/docs/index.md")
}

# Função para carregar e converter markdown em HTML
def read_and_convert(path: Path, title: str) -> str:
    if not path.exists():
        return f"<h2>{title}</h2><p><em>Relatório não encontrado.</em></p>"
    with path.open("r", encoding="utf-8") as f:
        md_content = f.read()
    return f"<div class='tabcontent' id='{title}'><h2>{title}</h2>" + markdown2.markdown(md_content) + "</div>"

# Coleta os conteúdos em abas
abas_html = "\n".join([
    read_and_convert(path, nome) for nome, path in jogos.items()
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
    img { max-width: 100%; margin-top: 1rem; }
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
