#!/usr/bin/env python3
"""Enhanced Lotofacil Prediction using core BaseLotteryPredictor + ModelAdapter."""

import sys
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import LOTOFACIL_CONFIG
from Oraculo.core.model_adapter import ModelAdapter
from Oraculo.core.metrics_engine import (
    safe_probs,
    normalized_entropy,
    rolling_stability,
    volatility_chunks,
    dynamic_confidence,
)


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

    # ===== Confiança dinâmica baseada no histórico =====
    def _counts_from_history(self, data: List[List[int]], limit: Optional[int] = None) -> List[int]:
        max_n = self.config.total_numbers
        if limit is not None:
            subset = data[:max(0, int(limit))]
        else:
            subset = data
        counts = [0] * max_n
        for game in subset:
            for n in game:
                n = int(n)
                if self.config.min_number <= n <= self.config.max_number:
                    counts[n - self.config.min_number] += 1
        return counts

    def _calc_stability_volatility(self, data: List[List[int]]) -> Tuple[float, float]:
        n = len(data)
        if n < 40:
            return 0.7, 0.2
        w = min(200, n // 2)
        counts_a = self._counts_from_history(data, limit=w)
        counts_b = self._counts_from_history(data[w: 2 * w])
        stab = rolling_stability(counts_a, counts_b)
        k = min(4, max(1, n // 60))
        if k <= 1:
            vol = 0.2
        else:
            chunk_size = n // k
            mats = []
            for i in range(k):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < k - 1 else n
                mats.append(self._counts_from_history(data[start:end]))
            vol = volatility_chunks(mats)
        return float(stab), float(vol)

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

    def run_complete_analysis(self) -> Dict[str, Any]:
        print(f"\n🧮 Confiança dinâmica ativada - {self.config.name}")
        data = self.load_data()
        if not data:
            print("❌ Nenhum dado disponível para análise.")
            return {}
        try:
            self._init_gaussian_baseline(data)
        except Exception:
            pass

        model_results = self.run_all_models(data)
        if not model_results:
            return {}

        counts_recent = self._counts_from_history(data, limit=min(300, len(data)))
        probs_all = safe_probs(counts_recent, alpha=0.5)
        stab, vol = self._calc_stability_volatility(data)

        for m, res in list(model_results.items()):
            try:
                pred = res.get('prediction', []) or []
                base_conf = float(res.get('confidence', 0.5))
                idx = []
                for n in pred:
                    n = int(n)
                    if self.config.min_number <= n <= self.config.max_number:
                        idx.append(n - self.config.min_number)
                h_norm = normalized_entropy(probs_all[idx]) if idx else normalized_entropy(probs_all)
                new_conf = dynamic_confidence(base_conf, pred, probs_all, stab, vol)
                res['confidence'] = float(new_conf)
                res['metrics'] = {
                    'entropy_norm_pred': float(h_norm),
                    'stability': float(stab),
                    'volatility': float(vol),
                }
                model_results[m] = res
            except Exception:
                pass

        combined_results = self.combine_predictions(model_results)
        if combined_results:
            from datetime import datetime
            ts = datetime.now().strftime('%Y-%m-%d')
            self.save_predictions(combined_results, timestamp=ts)
            self.display_summary(combined_results)
        return combined_results
