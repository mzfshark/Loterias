#!/usr/bin/env python3
"""
Model Adapter - Adapts Lotofacil models to work with different lottery formats

This module provides a unified interface to adapt the existing sophisticated
Lotofacil models (Bayesian, Neural Ensemble, Monte Carlo, etc.) to work with
different lottery games by adjusting parameters and data formats.

Author: Enhanced AI System
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from .base_predictor import LotteryConfig


class ModelAdapter:
    """Adapts existing Lotofacil models to work with different lottery configurations."""
    
    def __init__(self, config: LotteryConfig):
        """
        Initialize model adapter with lottery configuration.
        
        Args:
            config: LotteryConfig object specifying the lottery rules
        """
        self.config = config
        
    def adapt_bayesian_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Bayesian model for current lottery configuration."""
        try:
            # Import shared Bayesian predictor (backed by Lotofacil implementation)
            from Oraculo.common.models.bayesian import BayesianPredictor as BayesianLotofacilPredictor
            
            # Create predictor with standard parameters
            predictor = BayesianLotofacilPredictor()
            
            # Adapt configuration
            predictor.numbers_range = self.config.get_number_list()
            predictor.combination_size = self.config.numbers_per_game
            
            # Re-initialize priors for new range
            predictor.priors = {num: {'alpha': 1.0, 'beta': 1.0} 
                               for num in predictor.numbers_range}
            
            # Update with historical data
            predictor.update_priors(data)
            
            # Run prediction
            prediction = predictor.predict_next_game()
            confidence = predictor.calculate_model_evidence()
            
            # Normalize confidence
            normalized_confidence = max(0.1, min(0.95, abs(confidence) / 100000))
            
            return {
                'prediction': prediction,
                'confidence': normalized_confidence,
                'model_evidence': confidence
            }
            
        except Exception as e:
            print(f"⚠️ Bayesian model adaptation failed: {e}")
            return None
    
    def adapt_neural_ensemble_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Neural Ensemble model for current lottery configuration."""
        try:
            from Oraculo.common.models.neural_ensemble import NeuralEnsemblePredictor as NeuralEnsembleLotofacil
            
            # Create predictor
            predictor = NeuralEnsembleLotofacil()
            
            # Train and predict
            prediction, confidence = predictor.train_and_predict(data)
            
            # Adapt prediction to current lottery format
            valid_prediction = []
            for num in prediction:
                if self.config.min_number <= num <= self.config.max_number:
                    valid_prediction.append(int(num))
            
            # Fill to required count if needed
            while len(valid_prediction) < self.config.numbers_per_game:
                candidates = [n for n in self.config.get_number_list() if n not in valid_prediction]
                if candidates:
                    valid_prediction.append(np.random.choice(candidates))
                else:
                    break
            
            # Truncate if too many
            valid_prediction = sorted(valid_prediction[:self.config.numbers_per_game])
            
            return {
                'prediction': valid_prediction,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"⚠️ Neural Ensemble model adaptation failed: {e}")
            return None
    
    def adapt_monte_carlo_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Monte Carlo model for current lottery configuration."""
        try:
            from Oraculo.common.models.monte_carlo import MonteCarloSimulator as MonteCarloLotofacilSimulator
            
            # Create simulator
            # Usa verbose=False para silenciar logs de progresso
            simulator = MonteCarloLotofacilSimulator(verbose=False)
            
            # Adapt configuration
            simulator.numbers_range = self.config.get_number_list()
            simulator.combination_size = self.config.numbers_per_game
            
            # Load historical data
            simulator.load_historical_data(data)
            
            # Run simulation
            result = simulator.run_ensemble_simulation()
            
            # Chaves retornadas pelo ensemble
            return {
                'prediction': result.get('ensemble_prediction', []),
                'confidence': result.get('ensemble_confidence', 0.0),
                'all_strategies': result.get('strategy_results', {})
            }
            
        except Exception as e:
            print(f"⚠️ Monte Carlo model adaptation failed: {e}")
            return None
    
    def adapt_time_series_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Time Series model for current lottery configuration."""
        try:
            from Oraculo.common.models.time_series import TimeSeriesPredictor as TimeSeriesLotofacilPredictor
            
            # Create predictor
            predictor = TimeSeriesLotofacilPredictor()
            
            # Adapt configuration
            predictor.numbers_range = self.config.get_number_list()
            predictor.combination_size = self.config.numbers_per_game
            
            # Load historical data
            predictor.load_historical_data(data)
            
            # Run prediction
            result = predictor.predict_next_game()
            
            return {
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'cycles_detected': result.get('cycles_detected', [])
            }
            
        except Exception as e:
            print(f"⚠️ Time Series model adaptation failed: {e}")
            return None
    
    def adapt_markov_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Markov model for current lottery configuration."""
        try:
            from Oraculo.Lotofacil.models import markov
            
            # Use the existing gerar_palpite function with adapted data
            prediction = markov.gerar_palpite(data)
            
            # Ensure prediction is within valid range and correct count
            valid_prediction = []
            for num in prediction:
                if self.config.min_number <= num <= self.config.max_number:
                    valid_prediction.append(int(num))
            
            # Fill to required count if needed
            while len(valid_prediction) < self.config.numbers_per_game:
                candidates = [n for n in self.config.get_number_list() if n not in valid_prediction]
                if candidates:
                    valid_prediction.append(np.random.choice(candidates))
                else:
                    break
            
            # Truncate if too many
            valid_prediction = sorted(valid_prediction[:self.config.numbers_per_game])
            
            return {
                'prediction': valid_prediction,
                'confidence': 0.6  # Default confidence for Markov
            }
            
        except Exception as e:
            print(f"⚠️ Markov model adaptation failed: {e}")
            return None
    
    def adapt_poisson_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Poisson model for current lottery configuration."""
        try:
            from Oraculo.Lotofacil.models.poisson import gerar_combinacao_poisson
            
            # Convert data to DataFrame format
            df = pd.DataFrame(data)
            
            # Generate prediction with standard parameters  
            prediction = gerar_combinacao_poisson(df, self.config.numbers_per_game)
            
            # Ensure prediction is within valid range
            valid_prediction = []
            for num in prediction:
                if self.config.min_number <= num <= self.config.max_number:
                    valid_prediction.append(int(num))
            
            # Fill to required count if needed
            while len(valid_prediction) < self.config.numbers_per_game:
                candidates = [n for n in self.config.get_number_list() if n not in valid_prediction]
                if candidates:
                    # Use Poisson-like sampling
                    probs = np.random.poisson(3, len(candidates))
                    probs = probs / np.sum(probs) if np.sum(probs) > 0 else np.ones(len(candidates)) / len(candidates)
                    selected = np.random.choice(candidates, p=probs)
                    valid_prediction.append(selected)
                else:
                    break
            
            return {
                'prediction': sorted(valid_prediction[:self.config.numbers_per_game]),
                'confidence': 0.65  # Default confidence for Poisson
            }
            
        except Exception as e:
            print(f"⚠️ Poisson model adaptation failed: {e}")
            return None
    
    def adapt_mutation_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Genetic Algorithm (Mutation) model for current lottery configuration."""
        try:
            from Oraculo.Lotofacil.models import mutation
            
            # Create adapted mutation functions
            def adapted_gerar_mutacoes(jogos_hist, num_mutantes=5, taxa_mutacao=0.3):
                def calcular_probabilidades_adapted(jogos):
                    todas = [n for jogo in jogos for n in jogo]
                    from collections import Counter
                    freq = Counter(todas)
                    total = sum(freq.values())
                    probs = {n: freq[n] / total for n in self.config.get_number_list()}
                    return probs
                
                def gerar_populacao_base_adapted(jogos, n=10):
                    import random
                    return [sorted(random.sample(self.config.get_number_list(), self.config.numbers_per_game)) for _ in range(n)]
                
                def mutar_adapted(jogo_base, probs, taxa_mutacao=0.3):
                    import random
                    jogo = jogo_base[:]
                    for i in range(len(jogo)):
                        if random.random() < taxa_mutacao:
                            candidatos = [n for n in self.config.get_number_list() if n not in jogo]
                            pesos = [probs.get(n, 0) for n in candidatos]
                            if candidatos and sum(pesos) > 0:
                                novo = random.choices(candidatos, weights=pesos, k=1)[0]
                                jogo[i] = novo
                    
                    # Ensure unique numbers
                    jogo = sorted(set(jogo))
                    while len(jogo) < self.config.numbers_per_game:
                        candidatos = [n for n in self.config.get_number_list() if n not in jogo]
                        pesos = [probs.get(n, 0) for n in candidatos]
                        if candidatos and sum(pesos) > 0:
                            novo = random.choices(candidatos, weights=pesos, k=1)[0]
                            jogo.append(novo)
                    
                    return sorted(jogo[:self.config.numbers_per_game])
                
                probs = calcular_probabilidades_adapted(jogos_hist)
                base = gerar_populacao_base_adapted(jogos_hist, n=num_mutantes)
                mutantes = [mutar_adapted(jogo, probs, taxa_mutacao) for jogo in base]
                return mutantes
            
            # Generate mutations
            mutations = adapted_gerar_mutacoes(data, num_mutantes=5)
            primary_prediction = mutations[0] if mutations else []
            
            return {
                'prediction': primary_prediction,
                'confidence': 0.6,  # Default confidence
                'all_mutations': mutations
            }
            
        except Exception as e:
            print(f"⚠️ Mutation model adaptation failed: {e}")
            return None
    
    def adapt_beam_search_model(self, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Adapt Beam Search model for current lottery configuration."""
        try:
            from Oraculo.Lotofacil.models.beam_search import beam_search
            
            # Generate prediction using beam search
            results = beam_search(data, beam_width=50, top_candidates=1)
            prediction = results[0] if results else []
            
            # Ensure prediction is valid for current config
            valid_prediction = []
            for num in prediction:
                if self.config.min_number <= num <= self.config.max_number:
                    valid_prediction.append(int(num))
            
            # Fill to required count if needed
            while len(valid_prediction) < self.config.numbers_per_game:
                candidates = [n for n in self.config.get_number_list() if n not in valid_prediction]
                if candidates:
                    valid_prediction.append(np.random.choice(candidates))
                else:
                    break
            
            return {
                'prediction': sorted(valid_prediction[:self.config.numbers_per_game]),
                'confidence': 0.7  # Default confidence for Beam Search
            }
            
        except Exception as e:
            print(f"⚠️ Beam Search model adaptation failed: {e}")
            return None