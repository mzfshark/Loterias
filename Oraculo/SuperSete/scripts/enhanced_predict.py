#!/usr/bin/env python3
"""
Enhanced SuperSete Prediction System with Advanced Probabilistic Models

This script adapts all sophisticated probabilistic models from Lotofacil
to work with SuperSete format (7 digits from 0-9, column-based).

Author: Enhanced AI System
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import SUPERSETE_CONFIG
from Oraculo.core.model_adapter import ModelAdapter


class EnhancedSuperSetePredictor(BaseLotteryPredictor):
    """Enhanced SuperSete predictor using adapted Lotofacil models."""
    
    def __init__(self):
        """Initialize SuperSete predictor with configuration."""
        super().__init__(SUPERSETE_CONFIG)
        self.adapter = ModelAdapter(self.config)
        # Estratégia SuperSete: formato posicional (7 dígitos 0-9) favorece modelos
        # de transição (Markov) e distribuição de frequência (Poisson/Bayes).
        # Neural/MonteCarlo ajudam como suporte; TimeSeries/Beam/Mutation têm menor influência.
        self.models = {
            'bayesian': {'weight': 0.28, 'enabled': True},
            'neural_ensemble': {'weight': 0.10, 'enabled': True},
            'monte_carlo': {'weight': 0.12, 'enabled': True},
            'time_series': {'weight': 0.06, 'enabled': True},
            'beam_search': {'weight': 0.05, 'enabled': True},
            'markov': {'weight': 0.18, 'enabled': True},
            'poisson': {'weight': 0.16, 'enabled': True},
            'mutation': {'weight': 0.05, 'enabled': True},
        }
    
    def _parse_data(self, df: pd.DataFrame) -> List[List[int]]:
        """Parse SuperSete data from DataFrame."""
        # SuperSete has 7 columns with digits 0-9
        column_names = [f"Coluna {i}" for i in range(1, 8)]
        
        # Try different column naming patterns
        if not all(col in df.columns for col in column_names):
            # Try alternative patterns
            column_names = [col for col in df.columns if 'Col' in col or 'Coluna' in col]
            if len(column_names) < 7:
                # Fallback: use first 7 numeric columns
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                column_names = numeric_cols[:7]
        
        if len(column_names) < 7:
            raise ValueError(f"Expected 7 columns for SuperSete, found {len(column_names)}")
        
        # Extract games and sort by contest (newest first if Concurso column exists)
        if 'Concurso' in df.columns:
            df = df.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
        
        games = df[column_names[:7]].values.tolist()
        
        # Convert to integers and validate (digits 0-9)
        validated_games = []
        for game in games:
            try:
                int_game = [int(x) for x in game if pd.notna(x)]
                if len(int_game) == 7 and all(0 <= digit <= 9 for digit in int_game):
                    validated_games.append(int_game)  # Don't sort - order matters for SuperSete
            except (ValueError, TypeError):
                continue
        
        return validated_games
    
    def _run_model(self, model_name: str, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Run a specific adapted model for SuperSete."""
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
    
    def combine_predictions(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Override to handle SuperSete's column-based format."""
        if not model_results:
            return {}
        
        # For SuperSete, we need to generate predictions for each column position
        column_predictions = [[] for _ in range(7)]
        
        # Collect predictions from all models
        for model_name, result in model_results.items():
            if 'prediction' in result and self.models[model_name]['enabled']:
                prediction = result['prediction']
                weight = self.models[model_name]['weight']
                
                # Distribute prediction across columns
                for i, digit in enumerate(prediction[:7]):  # Take first 7 digits
                    if 0 <= digit <= 9:
                        column_predictions[i].append((digit, weight))
        
        # Generate ensemble prediction for each column
        ensemble_prediction = []
        for col_preds in column_predictions:
            if col_preds:
                # Weighted voting for each column
                digit_weights = {}
                for digit, weight in col_preds:
                    digit_weights[digit] = digit_weights.get(digit, 0) + weight
                
                # Select digit with highest weight
                best_digit = max(digit_weights.keys(), key=lambda d: digit_weights[d])
                ensemble_prediction.append(best_digit)
            else:
                # Fallback: random digit
                ensemble_prediction.append(np.random.randint(0, 10))
        
        # Calculate ensemble confidence
        total_models = len(model_results)
        confidence = 0.7 if total_models > 0 else 0.5  # Base confidence for SuperSete
        
        return {
            'ensemble_prediction': ensemble_prediction,
            'ensemble_confidence': confidence,
            'model_results': model_results,
            'column_analysis': column_predictions
        }
    
    def display_summary(self, results: Dict[str, Any]):
        """Override to display SuperSete-specific results."""
        print(f"\n{'='*80}")
        print(f"🎯 RESUMO DA ANÁLISE - {self.config.name.upper()}")
        print(f"{'='*80}")
        
        ensemble_pred = results.get('ensemble_prediction', [])
        ensemble_conf = results.get('ensemble_confidence', 0.0)
        
        print(f"🏆 Predição Final do Ensemble:")
        if len(ensemble_pred) == 7:
            print(f"   Col 1  Col 2  Col 3  Col 4  Col 5  Col 6  Col 7")
            print(f"    {ensemble_pred[0]}      {ensemble_pred[1]}      {ensemble_pred[2]}      {ensemble_pred[3]}      {ensemble_pred[4]}      {ensemble_pred[5]}      {ensemble_pred[6]}")
        else:
            print(f"   {ensemble_pred}")
        
        print(f"📊 Confiança do Ensemble: {ensemble_conf:.1%}")
        
        model_results = results.get('model_results', {})
        print(f"\n📋 Modelos Executados: {len(model_results)}")
        
        for model_name, result in model_results.items():
            prediction = result.get('prediction', [])
            confidence = result.get('confidence', 0.0)
            print(f"   • {model_name.upper()}: {prediction} (Conf: {confidence:.1%})")
        
        print(f"\n{'='*80}")


def main():
    """Main execution function."""
    predictor = EnhancedSuperSetePredictor()
    
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