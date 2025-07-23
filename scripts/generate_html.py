import markdown2
from pathlib import Path
from jinja2 import Template

# Caminhos
supersete_md = Path("SuperSete/docs/index.md")
lotofacil_md = Path("Lotofacil/docs/index.md")
output_html = Path("index.html")

# Função auxiliar para ler e converter markdown
def read_and_convert(path: Path, title: str):
    print(f"Verificando se o arquivo Markdown existe: {path}")
    if not path.exists():
        print(f"Aviso: {path} não encontrado.")
        return f"<h2>{title}</h2><p>Arquivo não encontrado.</p>"
    print(f"Lendo conteúdo de {path}")
    with path.open("r", encoding="utf-8") as f:
        md = f.read()
    print(f"Convertendo Markdown de {title} para HTML")
    return f"<h2>{title}</h2>" + markdown2.markdown(md)

# Coleta dos conteúdos
supersete_html = read_and_convert(supersete_md, "Super Sete")
lotofacil_html = read_and_convert(lotofacil_md, "Lotofácil")

print("Criando template HTML unificado")
html_template = Template("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Relatórios Loterias</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: system-ui, sans-serif;
      max-width: 1000px;
      margin: 2rem auto;
      padding: 1rem;
      background: #192532;
      color: #e3e3e3;
    }
    h1, h2 {
      color: #2fd39a;
      padding-bottom: 0.25rem;
    }
    cards{
      display: flex;
      flex-wrap: unset;
    }
    section {
      margin: 1rem;
      background: #000616;
      padding: 1rem;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
      width: 49%;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }
    th, td {
      border: 1px solid #ccc;
      padding: 0.5rem;
      text-align: center;
    }
    th {
      background-color: #e3f2fd;
    }
  </style>
</head>
<body>
  <h1>Relatórios de Loterias</h1>
  <cards>
  <section>
    {{ lotofacil | safe }}
  </section>
  <section>
    {{ supersete | safe }}
  </section>
  </cards>
</body>
</html>
""")

print("Renderizando HTML final")
html_output = html_template.render(lotofacil=lotofacil_html, supersete=supersete_html)

print(f"Salvando HTML em {output_html}")
output_html.write_text(html_output, encoding="utf-8")

print(f"HTML unificado gerado com sucesso em {output_html}")
