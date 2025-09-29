#!/usr/bin/env python3
"""
Enhanced Lotofacil Prediction using core BaseLotteryPredictor + ModelAdapter.

Alinhado à arquitetura unificada: usa registry por jogo, combinações via Base,
salvamento padronizado (prediction_TIMESTAMP.json/csv) e FAST_CI.
"""

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
        # Pesos padrão para Lotofácil (podem ser sobrescritos pelo registry/auto)
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
        self._merge_auto_weights()
        # Reaplica guard de FAST_CI/GitHub Actions porque redefinimos self.models
        try:
            if os.environ.get('FAST_CI', '').strip() == '1' or os.environ.get('GITHUB_ACTIONS', '') == 'true':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo (Lotofácil): modelos pesados desativados (monte_carlo, neural_ensemble).")
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
        """Parse Lotofácil data from DataFrame."""
        cols = [c for c in df.columns if 'Bola' in c or c.lower().startswith('bola')]
        if not cols:
            # fallback: primeiras 15 numéricas
            cols = df.select_dtypes(include=['int64', 'float64']).columns[:15]
        if len(cols) < 15:
            raise ValueError(f"Expected 15 columns for Lotofácil, found {len(cols)}")
        if 'Concurso' in df.columns:
            df = df.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
        games = df[cols[:15]].values.tolist()
        # Validação simples
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
        """Run a specific model using the shared adapter or direct implementations."""
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
        
        return all_results
    
    def display_summary(self, results: Dict[str, Any]):
        """Display summary of results."""
        ensemble = results['ensemble_result']
        analysis = results['comprehensive_analysis']
        
        print("\n" + "="*80)
        print("🎯 RESUMO DA ANÁLISE PROBABILÍSTICA APRIMORADA")
        print("="*80)
        
        print(f"\n🏆 PREDIÇÃO ENSEMBLE FINAL:")
        print(f"   Números: {ensemble['ensemble_prediction']}")
        print(f"   Confiança: {ensemble['ensemble_confidence']:.4f}")
        print(f"   Modelos utilizados: {ensemble['model_count']}")
        
        print(f"\n📊 TOP 10 NÚMEROS COM MAIOR CONSENSO:")
        consensus = sorted(analysis['consensus_strength'].items(), 
                         key=lambda x: x[1], reverse=True)
        for i, (num, strength) in enumerate(consensus[:10]):
            print(f"   {i+1:2d}. Número {num:2d}: {strength:.3f} ({strength*100:.1f}% dos modelos)")
        
        print(f"\n🔥 NÚMEROS DE ALTA CONFIANÇA (>50% consenso):")
        high_conf = analysis['high_confidence_numbers']
        if high_conf:
            print(f"   {sorted(high_conf)}")
        else:
            print("   Nenhum número com consenso > 50%")
        
        print(f"\n📈 ANÁLISE DE PADRÕES:")
        patterns = analysis['pattern_analysis']
        print(f"   Média de números consecutivos: {patterns['avg_consecutive']:.2f}")
        print(f"   Soma média dos jogos: {patterns['avg_sum']:.1f} ± {patterns['sum_std']:.1f}")
        
        print(f"\n🎲 PREDIÇÕES POR MODELO:")
        for model_name, result in results['model_results'].items():
            if 'prediction' in result:
                pred = result['prediction']
                conf = result.get('confidence', 0.5)
                weight = results['model_weights'].get(model_name, 0)
                print(f"   {model_name:15s}: {pred} (conf: {conf:.3f}, peso: {weight:.2f})")
        
        print("\n" + "="*80)


def main():
    """Main execution function."""
    predictor = EnhancedLotofacilPredictor()
    
    try:
        results = predictor.run_complete_analysis()
        return results
    except KeyboardInterrupt:
        print("\n⏹️ Análise interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    results = main()