import markdown2
from pathlib import Path
from jinja2 import Template

# Caminhos
markdown_file = Path("SuperSete/data/index.md")
output_html = Path("SuperSete/index.html")

# Leitura do conteúdo Markdown
if not markdown_file.exists():
    raise FileNotFoundError(f"{markdown_file} not found.")

with markdown_file.open("r", encoding="utf-8") as f:
    md_content = f.read()

# Conversão para HTML
html_body = markdown2.markdown(md_content)

# Template básico
html_template = Template("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Relatório Super Sete</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: system-ui, sans-serif;
      max-width: 800px;
      margin: 2rem auto;
      padding: 1rem;
      background: #f9f9f9;
      color: #333;
    }
    h1, h2, h3 {
      color: #2c3e50;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1.5rem;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 0.5rem;
      text-align: center;
    }
    th {
      background-color: #eee;
    }
  </style>
</head>
<body>
  <h1>Relatório Super Sete</h1>
  {{ content | safe }}
</body>
</html>
""")

# Geração final
html_output = html_template.render(content=html_body)
output_html.write_text(html_output, encoding="utf-8")

print(f"HTML gerado com sucesso em {output_html}")
