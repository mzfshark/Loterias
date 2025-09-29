#!/usr/bin/env python3
"""Enhanced Lotofacil Prediction using core BaseLotteryPredictor + ModelAdapter."""

import sys
import os
import pandas as pd
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import LOTOFACIL_CONFIG
from Oraculo.core.model_adapter import ModelAdapter


class EnhancedLotofacilPredictor(BaseLotteryPredictor):
    """Enhanced Lotofácil predictor using the shared core and adapters."""

    def __init__(self):
        super().__init__(LOTOFACIL_CONFIG)
        self.adapter = ModelAdapter(self.config)
        self.models = {
            'bayesian': {'weight': 0.20, 'enabled': True},
            'neural_ensemble': {'weight': 0.14, 'enabled': True},
            'monte_carlo': {'weight': 0.12, 'enabled': True},
            'time_series': {'weight': 0.18, 'enabled': True},
            'beam_search': {'weight': 0.10, 'enabled': True},
            'markov': {'weight': 0.10, 'enabled': True},
            'poisson': {'weight': 0.08, 'enabled': True},
            'mutation': {'weight': 0.08, 'enabled': True},
        }

    def _parse_data(self, df: pd.DataFrame) -> List[List[int]]:
        """Parse Lotofácil data from DataFrame."""
        cols = [c for c in df.columns if 'Bola' in c or c.lower().startswith('bola')]
        if not cols:
            cols = df.select_dtypes(include=['int64', 'float64']).columns[:15]
        if len(cols) < 15:
            raise ValueError(f"Expected 15 columns for Lotofácil, found {len(cols)}")
        if 'Concurso' in df.columns:
            df = df.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
        games = df[cols[:15]].values.tolist()
        out = []
        for g in games:
            try:
                ints = sorted(int(x) for x in g if pd.notna(x))
                if len(ints) == 15 and all(1 <= n <= 25 for n in ints):
                    out.append(ints)
            except Exception:
                continue
        return out

    def _run_model(self, model_name: str, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Run a specific model using the shared adapter."""
        if model_name == 'bayesian':
            return self.adapter.adapt_bayesian_model(data)
        if model_name == 'neural_ensemble':
            return self.adapter.adapt_neural_ensemble_model(data)
        if model_name == 'monte_carlo':
            return self.adapter.adapt_monte_carlo_model(data)
        if model_name == 'time_series':
            return self.adapter.adapt_time_series_model(data)
        if model_name == 'markov':
            return self.adapter.adapt_markov_model(data)
        if model_name == 'poisson':
            return self.adapter.adapt_poisson_model(data)
        if model_name == 'mutation':
            return self.adapter.adapt_mutation_model(data)
        if model_name == 'beam_search':
            return self.adapter.adapt_beam_search_model(data)
        return None

    def display_summary(self, results: Dict[str, Any]):
        """Display summary with compatibility for base predictor output."""
        model_results = results.get('model_results', {})
        ensemble_prediction = results.get('ensemble_prediction', [])
        ensemble_confidence = results.get('ensemble_confidence', 0.0)
        
        print("\n" + "=" * 80)
        print("🎯 RESUMO DA ANÁLISE PROBABILÍSTICA")
        print("=" * 80)
        
        print(f"\n🏆 PREDIÇÃO ENSEMBLE FINAL:")
        print(f"   Números: {ensemble_prediction}")
        print(f"   Confiança: {ensemble_confidence:.4f}")
        print(f"   Modelos utilizados: {len(model_results)}")
        
        print(f"\n🎲 PREDIÇÕES POR MODELO:")
        model_weights = results.get('model_weights', {})
        for model_name, result in model_results.items():
            if 'prediction' in result:
                pred = result['prediction']
                conf = result.get('confidence', 0.5)
                weight = model_weights.get(model_name, 0)
                print(f"   {model_name:15s}: {pred} (conf: {conf:.3f}, peso: {weight:.2f})")
        
        print("\n" + "=" * 80)
