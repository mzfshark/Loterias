#!/usr/bin/env python3
"""
Enhanced +Miliona        try:
            fast_ci = os.environ.get('FAST_CI', '').strip()
            if fast_ci == '1':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo (Milionária): modelos pesados desativados (monte_carlo, neural_ensemble).")
            else:
                print(f"🔍 Modo completo (Milionária): todos os modelos habilitados (FAST_CI={fast_ci})")
        except Exception:
            passiction System with Advanced Probabilistic Models

This script adapts all sophisticated probabilistic models from Lotofacil
to work with +Milionaria format (6 numbers from 1-50 + 2 clovers from 1-6).

Author: Enhanced AI System
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import MILIONARIA_CONFIG
from Oraculo.core.model_adapter import ModelAdapter


class EnhancedMilionariaPredictor(BaseLotteryPredictor):
    """Enhanced +Milionaria predictor using adapted Lotofacil models with dual number system."""
    
    def __init__(self):
        """Initialize +Milionaria predictor with configuration."""
        super().__init__(MILIONARIA_CONFIG)
        self.adapter = ModelAdapter(self.config)
        # Estratégia +Milionária (números principais):
        # Dar ênfase a bayesian/monte_carlo/poisson e bom peso a markov/neural.
        # Heurísticas e séries temporais com menor influência.
        self.models = {
            'bayesian': {'weight': 0.24, 'enabled': True},
            'neural_ensemble': {'weight': 0.14, 'enabled': True},
            'monte_carlo': {'weight': 0.20, 'enabled': True},
            'time_series': {'weight': 0.06, 'enabled': True},
            'beam_search': {'weight': 0.06, 'enabled': True},
            'markov': {'weight': 0.12, 'enabled': True},
            'poisson': {'weight': 0.14, 'enabled': True},
            'mutation': {'weight': 0.04, 'enabled': True},
        }
        self._merge_auto_weights()
        # Reaplica FAST_CI/GitHub Actions guard, já que redefinimos self.models
        try:
            if os.environ.get('FAST_CI', '').strip() == '1' or os.environ.get('GITHUB_ACTIONS', '') == 'true':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo (+Milionária): modelos pesados desativados (monte_carlo, neural_ensemble).")
        except Exception:
            pass

    def _merge_auto_weights(self):
        import json, os
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
        """Parse +Milionaria data from DataFrame."""
        # Look for main numbers (should be 6 columns)
        main_cols = [col for col in df.columns if 'Bola' in col or 'Numero' in col or col.startswith('N')]
        
        # Look for clover columns
        clover_cols = [col for col in df.columns if 'Trevo' in col or 'Clover' in col or 'C' in col]
        
        if not main_cols:
            # Fallback: assume first 6 numeric columns are main numbers
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            main_cols = numeric_cols[:6]
            
        if not clover_cols and len(df.columns) >= 8:
            # Assume last 2 columns are clovers if not found explicitly
            clover_cols = df.columns[-2:]
        
        if len(main_cols) < 6:
            raise ValueError(f"Expected at least 6 main number columns, found {len(main_cols)}")
        
        if len(clover_cols) < 2:
            raise ValueError(f"Expected at least 2 clover columns, found {len(clover_cols)}")
        
        # Extract games and sort by contest (newest first if Concurso column exists)
        if 'Concurso' in df.columns:
            df = df.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
        
        # For model compatibility, we'll combine main numbers and clovers into single games
        # This is a simplification - in a more advanced version, we'd handle them separately
        combined_games = []
        
        for _, row in df.iterrows():
            try:
                main_numbers = [int(row[col]) for col in main_cols[:6] if pd.notna(row[col])]
                clovers = [int(row[col]) for col in clover_cols[:2] if pd.notna(row[col])]
                
                # Validate main numbers (1-50)
                if len(main_numbers) == 6 and all(1 <= num <= 50 for num in main_numbers):
                    # Validate clovers (1-6)  
                    if len(clovers) == 2 and all(1 <= clover <= 6 for clover in clovers):
                        # For now, just use main numbers for model compatibility
                        # In a more sophisticated implementation, we'd handle dual systems
                        combined_games.append(sorted(main_numbers))
            except (ValueError, TypeError):
                continue
        
        return combined_games
    
    def _run_model(self, model_name: str, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Run a specific adapted model for +Milionaria."""
        # Run models on main numbers only for now
        result = None
        
        if model_name == 'bayesian':
            result = self.adapter.adapt_bayesian_model(data)
        elif model_name == 'neural_ensemble':
            result = self.adapter.adapt_neural_ensemble_model(data)
        elif model_name == 'monte_carlo':
            result = self.adapter.adapt_monte_carlo_model(data)
        elif model_name == 'time_series':
            result = self.adapter.adapt_time_series_model(data)
        elif model_name == 'markov':
            result = self.adapter.adapt_markov_model(data)
        elif model_name == 'poisson':
            result = self.adapter.adapt_poisson_model(data)
        elif model_name == 'mutation':
            result = self.adapter.adapt_mutation_model(data)
        elif model_name == 'beam_search':
            result = self.adapter.adapt_beam_search_model(data)
        
        # Add clover prediction if main prediction was successful
        if result and 'prediction' in result:
            # Generate clovers using simple frequency-based approach
            clovers = self._predict_clovers(data)
            result['clovers'] = clovers
            result['full_prediction'] = {
                'main_numbers': result['prediction'],
                'clovers': clovers
            }
        
        return result
    
    def _predict_clovers(self, data: List[List[int]]) -> List[int]:
        """Generate clover predictions using simple frequency analysis."""
        # For this implementation, we'll use a simple random approach
        # In a more sophisticated version, we'd analyze historical clover patterns
        np.random.seed(42)  # For reproducible results
        return sorted(np.random.choice(range(1, 7), size=2, replace=False))
    
    def display_summary(self, results: Dict[str, Any]):
        """Override to display +Milionaria specific results."""
        print(f"\n{'='*80}")
        print(f"🎯 RESUMO DA ANÁLISE - {self.config.name.upper()}")
        print(f"{'='*80}")
        
        ensemble_pred = results.get('ensemble_prediction', [])
        ensemble_conf = results.get('ensemble_confidence', 0.0)
        
        print(f"🏆 Predição Final do Ensemble (Números): {ensemble_pred}")
        print(f"🍀 Trevos Preditos: {self._predict_clovers([])}")  # Simple approach for display
        print(f"📊 Confiança do Ensemble: {ensemble_conf:.1%}")
        
        model_results = results.get('model_results', {})
        print(f"\n📋 Modelos Executados: {len(model_results)}")
        
        for model_name, result in model_results.items():
            prediction = result.get('prediction', [])
            clovers = result.get('clovers', [])
            confidence = result.get('confidence', 0.0)
            print(f"   • {model_name.upper()}: {prediction} + Trevos: {clovers} (Conf: {confidence:.1%})")
        
        print(f"\n{'='*80}")


def main():
    """Main execution function."""
    predictor = EnhancedMilionariaPredictor()
    
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