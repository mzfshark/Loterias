#!/usr/bin/env python3
"""
Auto Calibrator - Ajuste fino de pesos por modelo usando backtest recente

Executa um backtest simples nos últimos N concursos para estimar a taxa de acerto
de cada modelo e gerar pesos normalizados para o ensemble.

Uso (CLI):
  python Oraculo/core/auto_calibrator.py --game all --lookback 20
  python Oraculo/core/auto_calibrator.py --game megasena --lookback 30

Autor: Enhanced AI System
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

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


def save_weights(lottery: str, weights: Dict[str, float]):
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
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def calibrate_and_save(lottery: str, lookback: int = 20) -> str:
    weights = backtest_models(lottery, lookback=lookback)
    path = save_weights(lottery, weights)
    return path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Auto-calibrador de pesos por modelo')
    parser.add_argument('--game', '-g', choices=['all', 'megasena', 'quina', 'milionaria', 'supersete', 'lotofacil'], required=True)
    parser.add_argument('--lookback', '-l', type=int, default=20)
    args = parser.parse_args()

    targets = ['megasena', 'quina', 'milionaria', 'supersete', 'lotofacil'] if args.game == 'all' else [args.game]

    for lot in targets:
        print(f"\n🔧 Calibrando pesos: {lot} (lookback={args.lookback})")
        path = calibrate_and_save(lot, lookback=args.lookback)
        print(f"✅ Pesos atualizados em: {path}")
