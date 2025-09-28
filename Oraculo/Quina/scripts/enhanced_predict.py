#!/usr/bin/env python3
"""
Enhanced Quina Prediction System with Advanced Probabilistic Models

This script adapts all sophisticated probabilistic models from Lotofacil
to work with Quina format (5 numbers from 1-80).

Author: Enhanced AI System
"""

import sys
import os
import pandas as pd
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import QUINA_CONFIG
from Oraculo.core.model_adapter import ModelAdapter


class EnhancedQuinaPredictor(BaseLotteryPredictor):
    """Enhanced Quina predictor using adapted Lotofacil models."""
    
    def __init__(self):
        """Initialize Quina predictor with configuration."""
        super().__init__(QUINA_CONFIG)
        self.adapter = ModelAdapter(self.config)
    
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