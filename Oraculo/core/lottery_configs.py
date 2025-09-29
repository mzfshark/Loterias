#!/usr/bin/env python3
"""
Lottery Game Configurations

This module contains configuration definitions for all supported lottery games.
Each configuration specifies the rules, data paths, and parameters for a specific lottery type.

Author: Enhanced AI System
"""

from .base_predictor import LotteryConfig


# Lotofacil Configuration
LOTOFACIL_CONFIG = LotteryConfig(
    name="Lotofacil",
    numbers_per_game=15,
    number_range=(1, 25),
    data_path="Oraculo/Lotofacil/data/Lotofacil.csv",
    predictions_path="Oraculo/Lotofacil/predictions"
)

# MegaSena Configuration
MEGASENA_CONFIG = LotteryConfig(
    name="MegaSena",
    numbers_per_game=6,
    number_range=(1, 60),
    data_path="Oraculo/MegaSena/data/MegaSena.csv",
    predictions_path="Oraculo/MegaSena/predictions"
)

# Quina Configuration  
QUINA_CONFIG = LotteryConfig(
    name="Quina",
    numbers_per_game=5,
    number_range=(1, 80),
    data_path="Oraculo/Quina/data/Quina.csv",
    predictions_path="Oraculo/Quina/predictions"
)

# +Milionaria Configuration (6 numbers + 2 clovers)
MILIONARIA_CONFIG = LotteryConfig(
    name="Milionaria",
    numbers_per_game=6,
    number_range=(1, 50),
    data_path="Oraculo/Milionaria/data/Milionaria.csv",
    predictions_path="Oraculo/Milionaria/predictions",
    has_bonus_numbers=True,
    bonus_count=2,
    bonus_range=(1, 6)
)

# SuperSete Configuration (7 columns with digits 0-9)
SUPERSETE_CONFIG = LotteryConfig(
    name="SuperSete",
    numbers_per_game=7,
    number_range=(0, 9),
    data_path="Oraculo/SuperSete/data/SuperSete.csv",
    predictions_path="Oraculo/SuperSete/predictions"
)

# Configuration registry
LOTTERY_CONFIGS = {
    'lotofacil': LOTOFACIL_CONFIG,
    'megasena': MEGASENA_CONFIG,
    'quina': QUINA_CONFIG,
    'milionaria': MILIONARIA_CONFIG,
    'supersete': SUPERSETE_CONFIG
}


def get_config(lottery_name: str) -> LotteryConfig:
    """
    Get configuration for a specific lottery game.
    
    Args:
        lottery_name: Name of the lottery game (case insensitive)
        
    Returns:
        LotteryConfig object for the specified game
        
    Raises:
        ValueError: If lottery_name is not supported
    """
    name = lottery_name.lower()
    if name not in LOTTERY_CONFIGS:
        available = ', '.join(LOTTERY_CONFIGS.keys())
        raise ValueError(f"Unsupported lottery: {lottery_name}. Available: {available}")
    
    return LOTTERY_CONFIGS[name]


def list_supported_lotteries() -> list:
    """Return list of all supported lottery games."""
    return list(LOTTERY_CONFIGS.keys())