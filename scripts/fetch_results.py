from __future__ import annotations

import re
import sys
import argparse
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd


GAMES = {
    "lotofacil": {
        "url": "https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx",
        "csv_path": Path("Oraculo/Lotofacil/data/Lotofacil.csv"),
    },
    "megasena": {
        "url": "https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx",
        "csv_path": Path("Oraculo/MegaSena/data/MegaSena.csv"),
    },
    "quina": {
        "url": "https://loterias.caixa.gov.br/Paginas/Quina.aspx",
        "csv_path": Path("Oraculo/Quina/data/Quina.csv"),
    },
    "milionaria": {
        "url": "https://loterias.caixa.gov.br/Paginas/Mais-Milionaria.aspx",
        "csv_path": Path("Oraculo/Milionaria/data/Milionaria.csv"),
    },
    "supersete": {
        "url": "https://loterias.caixa.gov.br/Paginas/Super-Sete.aspx",
        "csv_path": Path("Oraculo/SuperSete/data/SuperSete.csv"),
    },
}


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _find_xlsx_link(soup: BeautifulSoup, base_url: str) -> str | None:
    # 1) Procura <a> com href direto para .xlsx
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".xlsx" in href.lower():
            return urljoin(base_url, href)

    # 2) Procura <a> que pareça o botão de download (texto)
    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").strip().lower()
        if "download" in text and ("resultado" in text or "resultados" in text):
            href = a["href"]
            if href.startswith("http"):
                return href
            if href.lower().endswith(".xlsx"):
                return urljoin(base_url, href)
            # Caso seja um __doPostBack
            if href.lower().startswith("javascript:__dopostback"):
                return href
    return None


def _extract_postback_target(js: str) -> str | None:
    # javascript:__doPostBack('ctl00$conteudo$btnDownload','')
    m = re.search(r"__doPostBack\('([^']+)'\s*,\s*'([^']*)'\)", js)
    if not m:
        return None
    event_target, event_argument = m.group(1), m.group(2)
    return event_target


def download_results_xlsx(page_url: str) -> bytes | None:
    s = requests.Session()
    r = s.get(page_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    link = _find_xlsx_link(soup, page_url)
    if link is None:
        return None

    # Link direto
    if link.lower().endswith(".xlsx"):
        dl = s.get(link, headers=HEADERS, timeout=60)
        if dl.status_code == 200 and dl.content:
            return dl.content
        return None

    # Postback
    if link.lower().startswith("javascript:__dopostback"):
        target = _extract_postback_target(link)
        if not target:
            return None

        form = soup.find("form")
        action = form.get("action") if form else page_url
        post_url = urljoin(page_url, action)

        data = {}
        # Campos ASP.NET padrão
        for name in ["__EVENTTARGET", "__EVENTARGUMENT", "__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]:
            inp = soup.find("input", attrs={"name": name})
            if inp is not None:
                data[name] = inp.get("value", "")
        data["__EVENTTARGET"] = target
        data["__EVENTARGUMENT"] = data.get("__EVENTARGUMENT", "")

        dl = s.post(post_url, data=data, headers=HEADERS, timeout=60, allow_redirects=True)
        if dl.status_code == 200 and dl.content:
            # Verifica se é um arquivo (Content-Disposition)
            cd = dl.headers.get("Content-Disposition", "").lower()
            if ".xlsx" in cd or dl.headers.get("Content-Type", "").lower().endswith("excel"):
                return dl.content
            # Alguns servidores retornam HTML com um link real; tenta extrair novamente
            if "<html" in dl.text.lower():
                soup2 = BeautifulSoup(dl.text, "lxml")
                link2 = _find_xlsx_link(soup2, page_url)
                if link2 and link2.lower().endswith(".xlsx"):
                    dl2 = s.get(link2, headers=HEADERS, timeout=60)
                    if dl2.status_code == 200 and dl2.content:
                        return dl2.content
        return None

    # Caso o link não seja direto nem postback
    return None


def xlsx_bytes_to_csv(xlsx_bytes: bytes, out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    # Tenta detectar a planilha com dados (primeira com linhas)
    import io
    with pd.ExcelFile(io.BytesIO(xlsx_bytes)) as xls:
        sheet_name = None
        for name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=name)
            if not df.empty:
                sheet_name = name
                break
        if sheet_name is None:
            sheet_name = xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet_name)
    # Normalização suave: remove colunas totalmente vazias
    df = df.dropna(axis=1, how='all')
    df.to_csv(out_csv, index=False)


def main():
    parser = argparse.ArgumentParser(description="Baixa resultados oficiais (.xlsx) e converte para CSV.")
    parser.add_argument("--game", choices=list(GAMES.keys()) + ["all"], default="all", help="Jogo a sincronizar")
    args = parser.parse_args()

    games = GAMES.keys() if args.game == "all" else [args.game]
    any_success = False
    for key in games:
        cfg = GAMES[key]
        print(f"Sincronizando {key}: {cfg['url']}")
        try:
            content = download_results_xlsx(cfg["url"])
            if not content:
                print(f"[WARN] Não foi possível obter o arquivo para {key}.")
                continue
            xlsx_path = cfg["csv_path"].with_suffix(".xlsx")
            xlsx_path.parent.mkdir(parents=True, exist_ok=True)
            xlsx_path.write_bytes(content)
            xlsx_bytes_to_csv(content, cfg["csv_path"])
            print(f"[OK] Atualizado: {cfg['csv_path']}")
            any_success = True
        except Exception as e:
            print(f"[ERRO] {key}: {e}")
    if not any_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
