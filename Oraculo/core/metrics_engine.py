#!/usr/bin/env python3
"""
Metrics Engine - utilitários para métricas de incerteza e estabilidade

Fornece funções para calcular entropia normalizada, estabilidade entre janelas
e volatilidade simples a partir de séries/frequências históricas.
"""

from typing import List, Sequence
import numpy as np


def safe_probs(counts: Sequence[float], alpha: float = 0.0) -> np.ndarray:
    arr = np.asarray(counts, dtype=float)
    if alpha > 0:
        arr = arr + alpha
    s = arr.sum()
    if s <= 0:
        return np.ones_like(arr) / max(1, arr.size)
    return arr / s


def entropy(probs: Sequence[float]) -> float:
    p = np.asarray(probs, dtype=float)
    p = np.clip(p, 1e-12, 1.0)
    return float(-np.sum(p * np.log(p)))


def normalized_entropy(probs: Sequence[float]) -> float:
    h = entropy(probs)
    n = max(1, len(probs))
    return float(h / np.log(n))


def js_distance(p: Sequence[float], q: Sequence[float]) -> float:
    """Jensen-Shannon distance simplificada (raiz do JSD)."""
    p = safe_probs(p)
    q = safe_probs(q)
    m = 0.5 * (p + q)
    def _kl(a, b):
        a = np.clip(a, 1e-12, 1.0)
        b = np.clip(b, 1e-12, 1.0)
        return np.sum(a * np.log(a / b))
    jsd = 0.5 * (_kl(p, m) + _kl(q, m))
    return float(np.sqrt(max(0.0, jsd)))


def l1_distance_norm(p: Sequence[float], q: Sequence[float]) -> float:
    p = safe_probs(p)
    q = safe_probs(q)
    return float(0.5 * np.abs(p - q).sum())


def rolling_stability(window_a_counts: Sequence[float], window_b_counts: Sequence[float]) -> float:
    """Estabilidade: 1 - distância L1 normalizada entre duas janelas de contagens."""
    d = l1_distance_norm(window_a_counts, window_b_counts)
    return float(max(0.0, 1.0 - d))


def volatility_chunks(counts_matrix: List[Sequence[float]]) -> float:
    """Volatilidade baseada em chunks: coeficiente de variação da prob média por dezena.

    counts_matrix: lista de vetores de contagens (mesma dimensão) de janelas consecutivas.
    Retorna valor em [0, 1] aproximadamente, com clamps.
    """
    if not counts_matrix:
        return 0.0
    probs = [safe_probs(c) for c in counts_matrix]
    probs_arr = np.stack(probs, axis=0)  # (chunks, N)
    mean_per_num = probs_arr.mean(axis=0)
    std_per_num = probs_arr.std(axis=0)
    # coeficiente de variação médio por dezena
    with np.errstate(divide='ignore', invalid='ignore'):
        cv = std_per_num / np.clip(mean_per_num, 1e-9, None)
    cv_mean = float(np.nanmean(np.clip(cv, 0.0, 5.0)))  # clamp para robustez
    # normaliza por um fator (heurístico)
    return float(max(0.0, min(1.0, cv_mean / 2.0)))


def dynamic_confidence(base_conf: float,
                       pred_numbers: Sequence[int],
                       probs_all_numbers: Sequence[float],
                       stability_val: float,
                       volatility_val: float) -> float:
    """Confiança dinâmica: (1 - entropia_pred) * estabilidade * (1 - volatilidade) * base.

    entropia_pred é calculada como entropia das probabilidades associadas às dezenas previstas.
    """
    p_all = safe_probs(probs_all_numbers)
    # Probabilidades dos números previstos
    idx = [n - 1 for n in pred_numbers if 1 <= int(n) <= len(p_all)]
    if not idx:
        h_norm = normalized_entropy(p_all)
    else:
        p_pred = p_all[idx]
        h_norm = normalized_entropy(p_pred)
    factor = (1.0 - h_norm) * float(stability_val) * float(max(0.0, 1.0 - volatility_val))
    conf = float(base_conf) * max(0.1, min(1.2, factor))
    return float(max(0.1, min(0.95, conf)))
