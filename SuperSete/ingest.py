import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_latest_draws(n=50):
    url = "https://github.com/Axodus/CryptoDraw/SuperSete/data/SuperSete.csv"
    print(f"Fetching the last {n} Super Sete draws from: {url}")

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.select("table.tabela-resultado tbody")

    draws = []
    for table in tables[:n]:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 7:
                digits = [int(c.get_text(strip=True)) for c in cols[:7]]
                draws.append(digits)

    df = pd.DataFrame(draws[::-1], columns=["col_a", "col_b", "col_c", "col_d", "col_e", "col_f", "col_g"])
    df.insert(0, "contest", range(1, len(df) + 1))
    return df

if __name__ == "__main__":
    df = fetch_latest_draws(n=50)
    df.to_csv("SuperSete/data/SuperSete.csv", index=False)
