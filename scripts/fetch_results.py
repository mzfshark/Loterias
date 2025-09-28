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
        "api": "lotofacil",
    },
    "megasena": {
        "url": "https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx",
        "csv_path": Path("Oraculo/MegaSena/data/MegaSena.csv"),
        "api": "megasena",
    },
    "quina": {
        "url": "https://loterias.caixa.gov.br/Paginas/Quina.aspx",
        "csv_path": Path("Oraculo/Quina/data/Quina.csv"),
        "api": "quina",
    },
    "milionaria": {
        "url": "https://loterias.caixa.gov.br/Paginas/Mais-Milionaria.aspx",
        "csv_path": Path("Oraculo/Milionaria/data/Milionaria.csv"),
        "api": "maismilionaria",
    },
    "supersete": {
        "url": "https://loterias.caixa.gov.br/Paginas/Super-Sete.aspx",
        "csv_path": Path("Oraculo/SuperSete/data/SuperSete.csv"),
        "api": "supersete",
    },
}


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

API_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/"


def api_url_for(game_key: str, concurso: int | None = None) -> str:
    slug = GAMES[game_key]["api"]
    url = urljoin(API_BASE, slug)
    if concurso is not None:
        return f"{url}?concurso={concurso}"
    return url


def api_get_json(game_key: str, concurso: int | None = None) -> dict | None:
    url = api_url_for(game_key, concurso)
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


def _to_int_list(seq) -> list[int]:
    out = []
    for x in (seq or []):
        try:
            out.append(int(str(x).strip()))
        except Exception:
            pass
    return out


def _infer_number_columns(game_key: str, df: pd.DataFrame | None) -> list[str]:
    if df is not None:
        # priorizar padrão existente
        bola_cols = [c for c in df.columns if c.lower().startswith("bola")]
        if bola_cols:
            return bola_cols
        if game_key == "supersete":
            col_cols = [c for c in df.columns if c.lower().startswith("coluna")]
            if col_cols:
                return col_cols
        # fallback: primeiras N colunas numéricas
    # padrão por jogo
    counts = {"lotofacil": 15, "megasena": 6, "quina": 5, "milionaria": 6, "supersete": 7}
    if game_key == "supersete":
        return [f"Coluna {i}" for i in range(1, counts[game_key] + 1)]
    return [f"Bola{i}" for i in range(1, counts[game_key] + 1)]


def _parse_api_row(game_key: str, data: dict, df_existing: pd.DataFrame | None) -> dict | None:
    if not data:
        return None
    numero = data.get("numero") or data.get("numero_concurso") or data.get("concurso")
    if not numero:
        return None
    try:
        concurso = int(numero)
    except Exception:
        return None
    data_apuracao = data.get("dataApuracao") or data.get("dtApuracao") or data.get("data")
    dezenas = data.get("listaDezenas") or data.get("dezenasOrdemSorteio") or data.get("dezenas")
    dezenas = _to_int_list(dezenas)

    row: dict = {"Concurso": concurso}
    if data_apuracao:
        row["Data"] = data_apuracao

    cols = _infer_number_columns(game_key, df_existing)

    if game_key == "supersete":
        # 7 dígitos 0-9
        if len(dezenas) == 7:
            for i, n in enumerate(dezenas[:7], start=1):
                key = cols[i - 1] if i - 1 < len(cols) else f"Coluna {i}"
                row[key] = n
        else:
            return row
    elif game_key == "milionaria":
        # 6 dezenas 1-50 + 2 trevos 1-6
        if len(dezenas) >= 6:
            for i, n in enumerate(dezenas[:6], start=1):
                key = cols[i - 1] if i - 1 < len(cols) else f"Bola{i}"
                row[key] = n
        # tenta trevos
        trevos = data.get("listaTrevos") or data.get("listaSorteioTrevos") or []
        trevos = _to_int_list(trevos)
        if len(trevos) >= 2:
            row["Trevo1"] = trevos[0]
            row["Trevo2"] = trevos[1]
    else:
        # Jogos padrão por dezenas
        expected = 15 if game_key == "lotofacil" else 6 if game_key == "megasena" else 5 if game_key == "quina" else len(dezenas)
        if len(dezenas) >= expected:
            for i, n in enumerate(dezenas[:expected], start=1):
                key = cols[i - 1] if i - 1 < len(cols) else f"Bola{i}"
                row[key] = n
    return row


def sync_game_via_api(game_key: str, cfg: dict) -> bool:
    """Sincroniza incrementos via API oficial, fazendo append ao CSV existente."""
    csv_path: Path = cfg["csv_path"]
    df_existing: pd.DataFrame | None = None
    last_concurso = 0
    if csv_path.exists():
        try:
            df_existing = pd.read_csv(csv_path)
            if "Concurso" in df_existing.columns and not df_existing["Concurso"].empty:
                last_concurso = int(pd.to_numeric(df_existing["Concurso"], errors="coerce").max())
        except Exception:
            df_existing = None
            last_concurso = 0

    latest = api_get_json(game_key)
    if not latest:
        return False
    latest_num = latest.get("numero") or latest.get("concurso")
    try:
        latest_concurso = int(latest_num)
    except Exception:
        return False

    if last_concurso >= latest_concurso:
        print(f"[OK] {game_key}: CSV já está atualizado (Concurso {last_concurso}).")
        return True

    rows = []
    for c in range(last_concurso + 1, latest_concurso + 1):
        data = api_get_json(game_key, c)
        if not data:
            continue
        row = _parse_api_row(game_key, data, df_existing)
        if row:
            rows.append(row)

    if not rows:
        return False

    new_df = pd.DataFrame(rows)
    if df_existing is not None:
        # alinhar colunas ao existente
        for col in df_existing.columns:
            if col not in new_df.columns:
                new_df[col] = pd.NA
        new_df = new_df[df_existing.columns]
        out_df = pd.concat([df_existing, new_df], ignore_index=True)
    else:
        out_df = new_df

    out_df.sort_values(by="Concurso", inplace=True)
    out_df.to_csv(csv_path, index=False)
    print(f"[OK] {game_key}: acrescentados {len(rows)} concursos (até {latest_concurso}).")
    return True


def _candidate_xlsx_from_tags(soup: BeautifulSoup) -> list[str]:
    candidates = []
    for a in soup.find_all(["a", "button"]):
        href = a.get("href") or a.get("data-href") or ""
        if href and ".xlsx" in href.lower():
            candidates.append(href)
    return candidates


def _candidate_xlsx_from_attrs(soup: BeautifulSoup) -> list[str]:
    candidates = []
    for tag in soup.find_all(True):
        for _attr, value in tag.attrs.items():
            if isinstance(value, str) and ".xlsx" in value.lower():
                candidates.append(value)
    return candidates


def _candidate_xlsx_from_text(soup: BeautifulSoup) -> list[str]:
    candidates = []
    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").strip().lower()
        if any(t in text for t in ["download", "baixar", "planilha", "resultado", "resultados", "xlsx"]):
            candidates.append(a["href"])
    return candidates


def _find_xlsx_link(soup: BeautifulSoup, base_url: str) -> str | None:
    for href in _candidate_xlsx_from_tags(soup) + _candidate_xlsx_from_attrs(soup) + _candidate_xlsx_from_text(soup):
        if href.startswith("http"):
            return href
        if href.lower().endswith(".xlsx"):
            return urljoin(base_url, href)
        if href.lower().startswith("javascript:__dopostback"):
            return href
    return None


def _extract_postback_target(js: str) -> str | None:
    # javascript:__doPostBack('ctl00$conteudo$btnDownload','')
    m = re.search(r"__doPostBack\('([^']+)'\s*,\s*'([^']*)'\)", js)
    if not m:
        return None
    event_target, _event_argument = m.group(1), m.group(2)
    return event_target


def _try_known_paths(session: requests.Session, base_url: str) -> bytes | None:
    known_paths = [
        "_layouts/15/DownloadFile.ashx",
        "_layouts/15/download.aspx",
    ]
    for kp in known_paths:
        try:
            guess = urljoin(base_url, kp)
            dl = session.get(guess, headers=HEADERS, timeout=30)
            cd = dl.headers.get("Content-Disposition", "").lower()
            if dl.status_code == 200 and dl.content and (".xlsx" in cd or "excel" in dl.headers.get("Content-Type", "").lower()):
                return dl.content
        except Exception:
            continue
    return None


def _download_direct(session: requests.Session, link: str) -> bytes | None:
    dl = session.get(link, headers=HEADERS, timeout=60)
    if dl.status_code == 200 and dl.content:
        return dl.content
    return None


def _download_via_postback(session: requests.Session, soup: BeautifulSoup, page_url: str, link: str) -> bytes | None:
    target = _extract_postback_target(link)
    if not target:
        return None
    form = soup.find("form")
    action = form.get("action") if form else page_url
    post_url = urljoin(page_url, action)
    data = {}
    for name in ["__EVENTTARGET", "__EVENTARGUMENT", "__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]:
        inp = soup.find("input", attrs={"name": name})
        if inp is not None:
            data[name] = inp.get("value", "")
    data["__EVENTTARGET"] = target
    data["__EVENTARGUMENT"] = data.get("__EVENTARGUMENT", "")

    dl = session.post(post_url, data=data, headers=HEADERS, timeout=60, allow_redirects=True)
    if dl.status_code == 200 and dl.content:
        cd = dl.headers.get("Content-Disposition", "").lower()
        if ".xlsx" in cd or dl.headers.get("Content-Type", "").lower().endswith("excel"):
            return dl.content
        if "<html" in dl.text.lower():
            soup2 = BeautifulSoup(dl.text, "lxml")
            link2 = _find_xlsx_link(soup2, page_url)
            if link2 and link2.lower().endswith(".xlsx"):
                return _download_direct(session, link2)
    return None


def download_results_xlsx(page_url: str) -> bytes | None:
    s = requests.Session()
    r = s.get(page_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    link = _find_xlsx_link(soup, page_url)
    if link is None:
        return _try_known_paths(s, page_url)

    link_l = link.lower()
    if link_l.endswith(".xlsx"):
        return _download_direct(s, link)
    if link_l.startswith("javascript:__dopostback"):
        return _download_via_postback(s, soup, page_url, link)
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
    parser = argparse.ArgumentParser(description="Sincroniza resultados oficiais e atualiza CSVs.")
    parser.add_argument("--game", choices=list(GAMES.keys()) + ["all"], default="all", help="Jogo a sincronizar")
    parser.add_argument("--mode", choices=["api", "aspx"], default="api", help="Fonte de dados a usar (padrão: api)")
    args = parser.parse_args()

    games = GAMES.keys() if args.game == "all" else [args.game]
    any_success = False
    any_existing = False
    for key in games:
        cfg = GAMES[key]
        print(f"Sincronizando {key} (modo {args.mode})...")
        if args.mode == "api":
            ok = sync_game_via_api(key, cfg)
            if ok:
                any_success = True
            elif cfg["csv_path"].exists():
                any_existing = True
        else:
            # modo legado via ASP.NET
            try:
                content = download_results_xlsx(cfg["url"])
                if not content:
                    print(f"[WARN] Não foi possível obter o arquivo para {key}.")
                    if cfg["csv_path"].exists():
                        print(f"[OK] CSV existente encontrado: {cfg['csv_path']} — mantendo dados atuais.")
                        any_existing = True
                        continue
                    else:
                        print(f"[WARN] Nenhum CSV existente encontrado para {key}.")
                        continue
                xlsx_path = cfg["csv_path"].with_suffix(".xlsx")
                xlsx_path.parent.mkdir(parents=True, exist_ok=True)
                xlsx_path.write_bytes(content)
                xlsx_bytes_to_csv(content, cfg["csv_path"])
                print(f"[OK] Atualizado: {cfg['csv_path']}")
                any_success = True
            except Exception as e:
                print(f"[ERRO] {key}: {e}")
                if cfg["csv_path"].exists():
                    print(f"[OK] CSV existente encontrado após erro: {cfg['csv_path']} — mantendo dados atuais.")
                    any_existing = True
    # Não falha o processo mesmo sem baixar: pipelines podem usar dados existentes ou gerar sintético.
    if not any_success and not any_existing:
        print("[INFO] Nenhum arquivo foi baixado e não há CSVs existentes; prosseguindo sem atualizar.")


if __name__ == "__main__":
    main()
