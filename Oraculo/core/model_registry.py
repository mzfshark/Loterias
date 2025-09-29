#!/usr/bin/env python3
"""
Model Registry per game.
Defines which models are enabled and their ensemble weights per game.
"""

from typing import Dict

DEFAULT_WEIGHTS: Dict[str, float] = {
    'bayesian': 0.20,
    'neural_ensemble': 0.14,
    'monte_carlo': 0.20,
    'time_series': 0.10,
    'beam_search': 0.06,
    'markov': 0.12,
    'poisson': 0.14,
    'mutation': 0.04,
}

REGISTRY: Dict[str, Dict[str, Dict[str, float]]] = {
    # Keys: model names; values: {'weight': float, 'enabled': bool}
    'lotofacil': {
        'bayesian':       {'weight': 0.22, 'enabled': True},
        'neural_ensemble':{'weight': 0.16, 'enabled': True},
        'monte_carlo':    {'weight': 0.18, 'enabled': True},
        'time_series':    {'weight': 0.12, 'enabled': True},
        'beam_search':    {'weight': 0.10, 'enabled': True},
        'markov':         {'weight': 0.10, 'enabled': True},
        'poisson':        {'weight': 0.08, 'enabled': True},
        'mutation':       {'weight': 0.04, 'enabled': True},
    },
    'megasena': {
        'bayesian':       {'weight': 0.25, 'enabled': True},
        'neural_ensemble':{'weight': 0.14, 'enabled': True},
        'monte_carlo':    {'weight': 0.22, 'enabled': True},
        'time_series':    {'weight': 0.08, 'enabled': True},
        'beam_search':    {'weight': 0.04, 'enabled': True},
        'markov':         {'weight': 0.10, 'enabled': True},
        'poisson':        {'weight': 0.15, 'enabled': True},
        'mutation':       {'weight': 0.02, 'enabled': True},
    },
    'quina': {
        'bayesian':       {'weight': 0.24, 'enabled': True},
        'neural_ensemble':{'weight': 0.14, 'enabled': True},
        'monte_carlo':    {'weight': 0.20, 'enabled': True},
        'time_series':    {'weight': 0.07, 'enabled': True},
        'beam_search':    {'weight': 0.05, 'enabled': True},
        'markov':         {'weight': 0.12, 'enabled': True},
        'poisson':        {'weight': 0.15, 'enabled': True},
        'mutation':       {'weight': 0.03, 'enabled': True},
    },
    'milionaria': {
        'bayesian':       {'weight': 0.20, 'enabled': True},
        'neural_ensemble':{'weight': 0.12, 'enabled': True},
        'monte_carlo':    {'weight': 0.22, 'enabled': True},
        'time_series':    {'weight': 0.08, 'enabled': True},
        'beam_search':    {'weight': 0.06, 'enabled': True},
        'markov':         {'weight': 0.10, 'enabled': True},
        'poisson':        {'weight': 0.18, 'enabled': True},
        'mutation':       {'weight': 0.04, 'enabled': True},
    },
    'supersete': {
        # Para Super Sete, os modelos por coluna podem ser específicos, mas
        # mantemos pesos para o ensemble quando forem aplicados globalmente.
        'bayesian':       {'weight': 0.18, 'enabled': True},
        'neural_ensemble':{'weight': 0.12, 'enabled': True},
        'monte_carlo':    {'weight': 0.16, 'enabled': True},
        'time_series':    {'weight': 0.12, 'enabled': True},
        'beam_search':    {'weight': 0.08, 'enabled': True},
        'markov':         {'weight': 0.18, 'enabled': True},
        'poisson':        {'weight': 0.12, 'enabled': True},
        'mutation':       {'weight': 0.04, 'enabled': True},
    },
}


def get_models_for(game_slug: str) -> Dict[str, Dict[str, float]]:
    return REGISTRY.get(game_slug.lower(), {k: {'weight': v, 'enabled': True} for k, v in DEFAULT_WEIGHTS.items()})
