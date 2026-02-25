#!/usr/bin/env python3
"""
Auto Calibrator - Ajuste fino de pesos por modelo usando:
 - backtest recente (histórico puro)
 - online (acertos observados das predições gravadas)
 - híbrido (combina os dois com fator alpha)

Uso (CLI):
    # Backtest puro
    python Oraculo/core/auto_calibrator.py --game all --mode backtest --lookback-history 20
    # Online puro (últimas 10 predições)
    python Oraculo/core/auto_calibrator.py --game megasena --mode online --lookback-preds 10
    # Híbrido (alpha = 0.6 para online)
    python Oraculo/core/auto_calibrator.py --game all --mode hybrid --alpha 0.6 --lookback-history 20 --lookback-preds 10

Autor: Enhanced AI System
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.lottery_configs import MEGASENA_CONFIG, QUINA_CONFIG, MILIONARIA_CONFIG, SUPERSETE_CONFIG, LOTOFACIL_CONFIG
from core.model_adapter import ModelAdapter


def _get_predictor_and_config(lottery: str):
    lot = lottery.lower()
    if lot == 'megasena':
        from MegaSena.scripts.enhanced_predict import EnhancedMegaSenaPredictor as P
        return P(), MEGASENA_CONFIG
    if lot == 'quina':
        from Quina.scripts.enhanced_predict import EnhancedQuinaPredictor as P
        return P(), QUINA_CONFIG
    if lot == 'milionaria':
        from Milionaria.scripts.enhanced_predict import EnhancedMilionariaPredictor as P
        return P(), MILIONARIA_CONFIG
    if lot == 'supersete':
        from SuperSete.scripts.enhanced_predict import EnhancedSuperSetePredictor as P
        return P(), SUPERSETE_CONFIG
    if lot == 'lotofacil':
        # Lotofácil enhanced usa caminho próprio
        from Lotofacil.scripts.enhanced_predict import EnhancedLotofacilPredictor as P
        return P(), LOTOFACIL_CONFIG
    raise ValueError(f"Unsupported lottery: {lottery}")


def _score_prediction(pred: List[int], actual: List[int], lottery: str, numbers_per_game: int) -> float:
    lot = lottery.lower()
    if lot == 'supersete':
        if not pred or not actual or len(pred) != 7 or len(actual) != 7:
            return 0.0
        return sum(1 for i in range(7) if pred[i] == actual[i]) / 7.0
    # Demais loterias: percentual de acertos no conjunto
    if not pred or not actual:
        return 0.0
    return len(set(pred).intersection(actual)) / float(numbers_per_game)


def backtest_models(lottery: str, lookback: int = 20) -> Dict[str, float]:
    """Executa backtest simples e retorna pesos normalizados por modelo."""
    predictor, config = _get_predictor_and_config(lottery)

    # Carrega DF bruto para ter ordem consistente
    df = pd.read_csv(config.data_path)
    if 'Concurso' in df.columns:
        df = df.sort_values(by='Concurso', ascending=True).reset_index(drop=True)

    # Reutiliza o parser específico do predictor para obter jogos
    # Garantindo ordem ascendente (antigo -> recente)
    parsed_desc = predictor._parse_data(df)
    data_asc = list(reversed(parsed_desc)) if parsed_desc else []

    if len(data_asc) < lookback + 5:
        lookback = max(1, len(data_asc) - 5)

    # Adaptador de modelos
    adapter = ModelAdapter(config)
    model_names = [m for m in predictor.models.keys()]
    scores = {m: [] for m in model_names}

    # Janela deslizante: para cada t, treina em [0..t-1] e avalia em t
    start = max(1, len(data_asc) - lookback)
    for t in range(start, len(data_asc)):
        train_data = data_asc[:t]
        actual = data_asc[t]

        for m in model_names:
            try:
                if m == 'bayesian':
                    res = adapter.adapt_bayesian_model(train_data)
                elif m == 'neural_ensemble':
                    res = adapter.adapt_neural_ensemble_model(train_data)
                elif m == 'monte_carlo':
                    res = adapter.adapt_monte_carlo_model(train_data)
                elif m == 'time_series':
                    res = adapter.adapt_time_series_model(train_data)
                elif m == 'markov':
                    res = adapter.adapt_markov_model(train_data)
                elif m == 'poisson':
                    res = adapter.adapt_poisson_model(train_data)
                elif m == 'mutation':
                    res = adapter.adapt_mutation_model(train_data)
                elif m == 'beam_search':
                    res = adapter.adapt_beam_search_model(train_data)
                else:
                    res = None

                if res and 'prediction' in res:
                    hit = _score_prediction(res['prediction'], actual, lottery, config.numbers_per_game)
                    scores[m].append(hit)
            except Exception:
                # ignora falhas pontuais de modelo
                continue

    # Média por modelo + suavização (pseudocontagem) para evitar zeros
    raw = {m: (np.mean(v) if v else 0.0) for m, v in scores.items()}
    # Suavização e normalização
    epsilon = 1e-3
    total = sum(raw.values()) + epsilon * len(raw)
    norm = {m: (raw[m] + epsilon) / total for m in raw}

    return norm


def _parse_date_str(s: str) -> pd.Timestamp:
    # Tenta formatos mais comuns (BR/PT-BR) e ISO
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            continue
    # Fallback genérico
    return pd.to_datetime(s, dayfirst=True, errors='coerce')


def _get_date_column(df: pd.DataFrame) -> str:
    for c in df.columns:
        lc = c.lower()
        if 'data' in lc:
            return c
    # fallback
    return 'Data Sorteio' if 'Data Sorteio' in df.columns else df.columns[0]


def _extract_actual_numbers(row: pd.Series, lottery: str, numbers_per_game: int) -> List[int]:
    lot = lottery.lower()
    if lot == 'supersete':
        cols = [c for c in row.index if 'coluna' in c.lower() or 'col' in c.lower()]
        cols = cols[:7]
        return [int(row[c]) for c in cols if pd.notna(row[c])][:7]
    # Demais: procurar bolas/dezenas
    bola_cols = [c for c in row.index if 'bola' in c.lower() or 'num' in c.lower() or 'dez' in c.lower()]
    if not bola_cols:
        # tenta primeiros numéricos
        bola_cols = [c for c in row.index if isinstance(row[c], (int, float))]
    # Garante tamanho
    bola_cols = bola_cols[:numbers_per_game]
    vals = []
    for c in bola_cols:
        try:
            vals.append(int(row[c]))
        except Exception:
            continue
    return sorted(vals)[:numbers_per_game]


def online_models(lottery: str, lookback_preds: int = 10) -> Dict[str, float]:
    """Calcula pesos com base em acertos reais das últimas N predições salvas."""
    predictor, config = _get_predictor_and_config(lottery)
    df = pd.read_csv(config.data_path)
    # Data por concurso
    date_col = _get_date_column(df)
    df['_data'] = df[date_col].apply(_parse_date_str)
    df = df.sort_values(by=['_data']).reset_index(drop=True)

    # Carregar predições salvas
    pred_dir = config.predictions_path
    if not os.path.isdir(pred_dir):
        return {}
    files = [f for f in os.listdir(pred_dir) if f.startswith('prediction_') and f.endswith('.json')]
    if not files:
        return {}
    # Ordenar por timestamp no nome ou no conteúdo
    def _parse_ts_from_name(name: str) -> pd.Timestamp:
        # formato: prediction_YYYY-MM-DD_HH-MM-SS.json
        try:
            base = name[len('prediction_'):-len('.json')]
            return pd.to_datetime(base, format='%Y-%m-%d_%H-%M-%S')
        except Exception:
            return pd.NaT

    files = sorted(files, key=_parse_ts_from_name)
    files = files[-lookback_preds:]

    # Mapear cada predição ao próximo concurso por data >= timestamp
    scores_sum: Dict[str, float] = {}
    scores_cnt: Dict[str, int] = {}

    for fname in files:
        try:
            fpath = os.path.join(pred_dir, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            ts = payload.get('timestamp')
            lotname = payload.get('lottery', '').lower()
            if lotname and lotname != lottery.lower():
                continue
            ts_pd = pd.to_datetime(ts) if ts else _parse_ts_from_name(fname)
            if pd.isna(ts_pd):
                continue
            # Próximo sorteio com data >= ts_pd.date()
            mask = df['_data'] >= ts_pd.normalize()
            next_rows = df[mask]
            if next_rows.empty:
                continue
            row = next_rows.iloc[0]
            actual = _extract_actual_numbers(row, lottery, config.numbers_per_game)
            # Avaliar cada modelo salvo
            for m in payload.get('models', []):
                mname = m.get('modelo')
                pred = m.get('jogo', [])
                hit = _score_prediction(pred, actual, lottery, config.numbers_per_game)
                scores_sum[mname] = scores_sum.get(mname, 0.0) + float(hit)
                scores_cnt[mname] = scores_cnt.get(mname, 0) + 1
        except Exception:
            continue

    if not scores_cnt:
        return {}

    raw = {m: (scores_sum.get(m, 0.0) / max(1, scores_cnt.get(m, 0))) for m in scores_cnt.keys()}
    epsilon = 1e-3
    total = sum(raw.values()) + epsilon * len(raw)
    norm = {m: (raw[m] + epsilon) / total for m in raw}
    return norm


def hybrid_weights(lottery: str, alpha: float = 0.6, lookback_history: int = 20, lookback_preds: int = 10) -> Dict[str, float]:
    online = online_models(lottery, lookback_preds=lookback_preds)
    back = backtest_models(lottery, lookback=lookback_history)
    # União de chaves
    keys = set(back.keys()) | set(online.keys())
    if not keys:
        return back  # fallback
    comb = {}
    for k in keys:
        b = back.get(k, 0.0)
        o = online.get(k, 0.0)
        val = alpha * o + (1 - alpha) * b
        comb[k] = val
    # Normalizar
    s = sum(comb.values()) or 1.0
    comb = {k: v / s for k, v in comb.items()}
    return comb


def save_weights(lottery: str, weights: Dict[str, float], meta: Dict[str, Any] = None):
    predictor, config = _get_predictor_and_config(lottery)
    # models dir ao lado de scripts
    base_dir = os.path.abspath(os.path.join(os.path.dirname(sys.modules[predictor.__module__].__file__), '..'))
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    path = os.path.join(models_dir, 'weights.auto.json')
    payload = {
        'lottery': lottery,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'lookback': None,
        'weights': weights,
    }
    if meta:
        payload.update(meta)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def calibrate_and_save(lottery: str, mode: str = 'hybrid', lookback_history: int = 20, lookback_preds: int = 10, alpha: float = 0.6) -> str:
    mode = mode.lower()
    if mode == 'backtest':
        weights = backtest_models(lottery, lookback=lookback_history)
        meta = {'mode': 'backtest', 'lookback_history': lookback_history}
    elif mode == 'online':
        weights = online_models(lottery, lookback_preds=lookback_preds)
        meta = {'mode': 'online', 'lookback_preds': lookback_preds}
    else:
        weights = hybrid_weights(lottery, alpha=alpha, lookback_history=lookback_history, lookback_preds=lookback_preds)
        meta = {'mode': 'hybrid', 'alpha': alpha, 'lookback_history': lookback_history, 'lookback_preds': lookback_preds}
    path = save_weights(lottery, weights, meta=meta)
    return path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Auto-calibrador de pesos por modelo')
    parser.add_argument('--game', '-g', choices=['all', 'megasena', 'quina', 'milionaria', 'supersete', 'lotofacil'], required=True)
    parser.add_argument('--mode', '-m', choices=['backtest', 'online', 'hybrid'], default='hybrid')
    parser.add_argument('--lookback-history', type=int, default=20)
    parser.add_argument('--lookback-preds', type=int, default=10)
    parser.add_argument('--alpha', type=float, default=0.6, help='Peso do componente online no modo híbrido')
    args = parser.parse_args()

    targets = ['megasena', 'quina', 'milionaria', 'supersete', 'lotofacil'] if args.game == 'all' else [args.game]

    for lot in targets:
        print(f"\n🔧 Calibrando pesos: {lot} (mode={args.mode})")
        path = calibrate_and_save(lot, mode=args.mode, lookback_history=args.lookback_history, lookback_preds=args.lookback_preds, alpha=args.alpha)
        print(f"✅ Pesos atualizados em: {path}")
