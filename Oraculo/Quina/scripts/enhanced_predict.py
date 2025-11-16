#!/usr/bin/env python3
"""
Enhanced Quina         try:
            fast_ci = os.environ.get('FAST_CI', '').strip()
            if fast_ci == '1':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo (Quina): modelos pesados desativados (monte_carlo, neural_ensemble).")
            else:
                print(f"🔍 Modo completo (Quina): todos os modelos habilitados (FAST_CI={fast_ci})")
        except Exception:
            passon System with Advanced Probabilistic Models

This script adapts all sophisticated probabilistic models from Lotofacil
to work with Quina format (5 numbers from 1-80).

Author: Enhanced AI System
"""

import sys
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import QUINA_CONFIG
from Oraculo.core.model_adapter import ModelAdapter
from Oraculo.core.metrics_engine import (
    safe_probs,
    normalized_entropy,
    rolling_stability,
    volatility_chunks,
    dynamic_confidence,
)


class EnhancedQuinaPredictor(BaseLotteryPredictor):
    """Enhanced Quina predictor using adapted Lotofacil models."""
    
    def __init__(self):
        """Initialize Quina predictor with configuration."""
        super().__init__(QUINA_CONFIG)
        self.adapter = ModelAdapter(self.config)
        # Estratégia Quina: foco em bayesian/monte_carlo/poisson, reforço moderado em markov;
        # menor influência de time_series/beam/mutation.
        self.models = {
            'bayesian': {'weight': 0.24, 'enabled': True},
            'neural_ensemble': {'weight': 0.14, 'enabled': True},
            'monte_carlo': {'weight': 0.20, 'enabled': True},
            'time_series': {'weight': 0.07, 'enabled': True},
            'beam_search': {'weight': 0.05, 'enabled': True},
            'markov': {'weight': 0.12, 'enabled': True},
            'poisson': {'weight': 0.15, 'enabled': True},
            'mutation': {'weight': 0.03, 'enabled': True},
        }
        self._merge_auto_weights()
        # Reaplica FAST_CI/GitHub Actions guard, já que redefinimos self.models
        try:
            if os.environ.get('FAST_CI', '').strip() == '1' or os.environ.get('GITHUB_ACTIONS', '') == 'true':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo (Quina): modelos pesados desativados (monte_carlo, neural_ensemble).")
        except Exception:
            pass

    def _merge_auto_weights(self):
        import json
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        path = os.path.join(base_dir, 'models', 'weights.auto.json')
        try:
            if os.path.isfile(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                w = data.get('weights', {})
                for k, v in w.items():
                    if k in self.models and isinstance(v, (int, float)):
                        self.models[k]['weight'] = float(v)
        except Exception:
            pass
    
    def _parse_data(self, df: pd.DataFrame) -> List[List[int]]:
        """Parse Quina data from DataFrame."""
        # Look for Quina-specific column patterns
        numero_cols = [col for col in df.columns if 'Bola' in col or 'Numero' in col or col.startswith('N')]
        
        if not numero_cols:
            # Try numbered columns (1st Ball, 2nd Ball, etc.)
            numero_cols = [col for col in df.columns if any(word in col.lower() for word in ['ball', 'dezena', 'num'])]
        
        if not numero_cols:
            # Fallback: assume first 5 numeric columns are the numbers
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            numero_cols = numeric_cols[:5]
        
        if len(numero_cols) < 5:
            raise ValueError(f"Expected at least 5 number columns, found {len(numero_cols)}")
        
        # Extract games and sort by contest (newest first if Concurso column exists)
        if 'Concurso' in df.columns:
            df = df.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
        
        games = df[numero_cols[:5]].values.tolist()
        
        # Convert to integers and validate
        validated_games = []
        for game in games:
            try:
                int_game = [int(x) for x in game if pd.notna(x)]
                if len(int_game) == 5 and all(1 <= num <= 80 for num in int_game):
                    validated_games.append(sorted(int_game))
            except (ValueError, TypeError):
                continue
        
        return validated_games
    
    def _run_model(self, model_name: str, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Run a specific adapted model for Quina."""
        if model_name == 'bayesian':
            return self.adapter.adapt_bayesian_model(data)
        elif model_name == 'neural_ensemble':
            return self.adapter.adapt_neural_ensemble_model(data)
        elif model_name == 'monte_carlo':
            return self.adapter.adapt_monte_carlo_model(data)
        elif model_name == 'time_series':
            return self.adapter.adapt_time_series_model(data)
        elif model_name == 'markov':
            return self.adapter.adapt_markov_model(data)
        elif model_name == 'poisson':
            return self.adapter.adapt_poisson_model(data)
        elif model_name == 'mutation':
            return self.adapter.adapt_mutation_model(data)
        elif model_name == 'beam_search':
            return self.adapter.adapt_beam_search_model(data)
        else:
            return None

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


def main():
    """Main execution function."""
    predictor = EnhancedQuinaPredictor()
    
    try:
        results = predictor.run_complete_analysis()
        return results
    except KeyboardInterrupt:
        print("\n⏹️ Análise interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()