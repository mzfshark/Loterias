import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

def fetch_latest_draws(url="https://asloterias.com.br/super-sete", path="SuperSete/data/SuperSete.csv"):
    response = requests.get(url)
    if response.status_code != 200:
        print("Erro ao acessar a página de resultados.")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        print("Nenhuma tabela encontrada na página.")
        return

    table = tables[0]  # Assume que a primeira tabela contém os dados relevantes
    rows = table.find_all("tr")[1:]  # Pula o cabeçalho

    dados = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 7:
            dados.append([int(c.text.strip()) for c in cols[:7]])

    df = pd.DataFrame(dados, columns=[f"col_{c}" for c in "abcdefg"])
    df.insert(0, "contest", range(1, len(df) + 1))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Dados salvos em {path}")

if __name__ == "__main__":
    fetch_latest_draws()
