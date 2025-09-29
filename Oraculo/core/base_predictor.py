#!/usr/bin/env python3
"""
Base Lottery Predictor Class - Core Architecture for Modular Lottery System

This module provides the foundational architecture for lottery prediction systems
that can be adapted to different lottery formats (Lotofacil, MegaSena, Quina, etc.)

Author: Enhanced AI System
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import os


class LotteryConfig:
    """Configuration class for different lottery types."""
    
    def __init__(self, 
                 name: str,
                 numbers_per_game: int,
                 number_range: Tuple[int, int],
                 data_path: str,
                 predictions_path: str,
                 has_bonus_numbers: bool = False,
                 bonus_count: int = 0,
                 bonus_range: Tuple[int, int] = (0, 0)):
        """
        Initialize lottery configuration.
        
        Args:
            name: Name of the lottery game
            numbers_per_game: How many numbers to select per game
            number_range: (min, max) range for main numbers
            data_path: Path to historical data CSV
            predictions_path: Path to save predictions
            has_bonus_numbers: Whether this lottery has bonus numbers
            bonus_count: Number of bonus numbers to select
            bonus_range: (min, max) range for bonus numbers
        """
        self.name = name
        self.numbers_per_game = numbers_per_game
        self.number_range = number_range
        self.data_path = data_path
        self.predictions_path = predictions_path
        self.has_bonus_numbers = has_bonus_numbers
        self.bonus_count = bonus_count
        self.bonus_range = bonus_range
        
        # Derived properties
        self.min_number = number_range[0]
        self.max_number = number_range[1]
        self.total_numbers = number_range[1] - number_range[0] + 1
        
    def get_number_list(self) -> List[int]:
        """Get list of all possible main numbers."""
        return list(range(self.min_number, self.max_number + 1))
    
    def get_bonus_list(self) -> List[int]:
        """Get list of all possible bonus numbers."""
        if not self.has_bonus_numbers:
            return []
        return list(range(self.bonus_range[0], self.bonus_range[1] + 1))
    
    def validate_game(self, game: List[int], bonus: List[int] = None) -> bool:
        """Validate if a game follows the lottery rules."""
        # Check main numbers
        if len(game) != self.numbers_per_game:
            return False
        if not all(self.min_number <= num <= self.max_number for num in game):
            return False
        if len(set(game)) != len(game):  # Check for duplicates
            return False
            
        # Check bonus numbers
        if self.has_bonus_numbers:
            if bonus is None or len(bonus) != self.bonus_count:
                return False
            if not all(self.bonus_range[0] <= num <= self.bonus_range[1] for num in bonus):
                return False
            if len(set(bonus)) != len(bonus):  # Check for duplicates
                return False
        
        return True


class BaseLotteryPredictor(ABC):
    """Abstract base class for lottery predictors."""
    
    def __init__(self, config: LotteryConfig):
        """
        Initialize base predictor.
        
        Args:
            config: Lottery configuration object
        """
        self.config = config
        # Inicializa modelos com base em um registry por jogo (pesos/ativação)
        try:
            from .model_registry import get_models_for
            self.models = get_models_for(self.config.name.lower())
        except Exception:
            # Fallback seguro
            self.models = {
                'bayesian': {'weight': 0.20, 'enabled': True},
                'neural_ensemble': {'weight': 0.18, 'enabled': True},
                'monte_carlo': {'weight': 0.15, 'enabled': True},
                'time_series': {'weight': 0.15, 'enabled': True},
                'beam_search': {'weight': 0.10, 'enabled': True},
                'markov': {'weight': 0.08, 'enabled': True},
                'poisson': {'weight': 0.07, 'enabled': True},
                'mutation': {'weight': 0.07, 'enabled': True}
            }
        self.results = {}
        self.ensemble_confidence = 0.0

        # Modo rápido para CI: desabilita modelos mais pesados por padrão
        try:
            if os.environ.get('FAST_CI', '').strip() == '1' or os.environ.get('GITHUB_ACTIONS', '') == 'true':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo: modelos pesados desativados (monte_carlo, neural_ensemble).")
        except Exception:
            pass
        
    def load_data(self) -> List[List[int]]:
        """Load historical lottery data from CSV file."""
        try:
            df = pd.read_csv(self.config.data_path)
            return self._parse_data(df)
        except FileNotFoundError:
            print(f"⚠️ Data file not found: {self.config.data_path}")
            return self._generate_synthetic_data()
    
    @abstractmethod
    def _parse_data(self, df: pd.DataFrame) -> List[List[int]]:
        """Parse lottery data from DataFrame. Must be implemented by subclasses."""
        raise NotImplementedError()
    
    def _generate_synthetic_data(self, n_games: int = 100) -> List[List[int]]:
        """Generate synthetic data for testing when real data is not available."""
        print(f"🧪 Generating {n_games} synthetic games for {self.config.name}")
        np.random.seed(42)
        games = []
        
        for _ in range(n_games):
            game = sorted(np.random.choice(
                self.config.get_number_list(), 
                size=self.config.numbers_per_game, 
                replace=False
            ))
            games.append(game)
        
        return games
    
    def run_all_models(self, data: List[List[int]]) -> Dict[str, Any]:
        """Run all enabled prediction models."""
        print(f"🧠 Executando todos os modelos probabilísticos para {self.config.name}...")
        
        model_results = {}
        
        # Run each model if available and enabled
        for model_name, model_config in self.models.items():
            if model_config['enabled']:
                try:
                    result = self._run_model(model_name, data)
                    if result:
                        model_results[model_name] = result
                        print(f"   ✅ {model_name}: {result.get('prediction', [])}")
                except Exception as e:
                    print(f"   ❌ {model_name} erro: {e}")
                    self.models[model_name]['enabled'] = False
        
        return model_results
    
    @abstractmethod
    def _run_model(self, model_name: str, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Run a specific model. Must be implemented by subclasses."""
        raise NotImplementedError()
    
    def combine_predictions(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine predictions from multiple models using weighted ensemble."""
        if not model_results:
            return {}
        
        # Get all predictions
        predictions = []
        weights = []
        confidences = []
        
        for model_name, result in model_results.items():
            if 'prediction' in result and self.models[model_name]['enabled']:
                predictions.append(result['prediction'])
                weights.append(self.models[model_name]['weight'])
                confidences.append(result.get('confidence', 0.5))
        
        if not predictions:
            return {}
        
        # Create frequency matrix for ensemble
        frequency_matrix = np.zeros(self.config.total_numbers + 1)  # +1 for 1-based indexing
        
        for i, prediction in enumerate(predictions):
            weight = weights[i]
            confidence = confidences[i]
            combined_weight = weight * confidence
            
            for num in prediction:
                if self.config.min_number <= num <= self.config.max_number:
                    frequency_matrix[num] += combined_weight
        
        # Select top numbers based on weighted frequency
        top_indices = np.argsort(frequency_matrix)[-self.config.numbers_per_game:]
        ensemble_prediction = sorted([int(idx) for idx in top_indices if idx >= self.config.min_number])
        
        # Calculate ensemble confidence
        total_weight = sum(weights)
        weighted_confidence = sum(w * c for w, c in zip(weights, confidences)) / total_weight if total_weight > 0 else 0.5
        
        return {
            'ensemble_prediction': ensemble_prediction,
            'ensemble_confidence': weighted_confidence,
            'model_results': model_results,
            'individual_predictions': predictions
        }
    
    def save_predictions(self, results: Dict[str, Any], timestamp: str = None) -> Tuple[str, str]:
        """Save predictions to JSON and CSV files."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Ensure predictions directory exists
        predictions_dir = Path(self.config.predictions_path)
        predictions_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for saving
        save_data = {
            'lottery': self.config.name,
            'timestamp': timestamp,
            'ensemble_prediction': self._serialize_prediction(results.get('ensemble_prediction', [])),
            'ensemble_confidence': float(results.get('ensemble_confidence', 0.0)),
            'models': []
        }
        
        # Add individual model results
        for model_name, result in results.get('model_results', {}).items():
            save_data['models'].append({
                'modelo': model_name,
                'jogo': self._serialize_prediction(result.get('prediction', [])),
                'confidence': float(result.get('confidence', 0.0))
            })
        
        # Save JSON
        json_path = predictions_dir / f"prediction_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        # Save CSV
        csv_data = []
        for model_data in save_data['models']:
            csv_data.append({
                'lottery': self.config.name,
                'timestamp': timestamp,
                'model': model_data['modelo'],
                'prediction': str(model_data['jogo']),
                'confidence': model_data['confidence']
            })
        
        csv_df = pd.DataFrame(csv_data)
        csv_path = predictions_dir / f"prediction_{timestamp}.csv"
        csv_df.to_csv(csv_path, index=False)
        
        return str(json_path), str(csv_path)
    
    def _serialize_prediction(self, prediction: List[Any]) -> List[int]:
        """Convert prediction to JSON-serializable format."""
        if not prediction:
            return []
        
        serialized = []
        for item in prediction:
            if hasattr(item, 'item'):  # numpy types
                serialized.append(int(item.item()))
            elif isinstance(item, (int, np.integer)):
                serialized.append(int(item))
            elif isinstance(item, (float, np.floating)):
                serialized.append(int(item))
            else:
                try:
                    serialized.append(int(item))
                except (ValueError, TypeError):
                    serialized.append(0)  # fallback
        
        return serialized
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete prediction analysis."""
        print(f"🚀 Iniciando análise completa para {self.config.name}...")
        
        # Load data
        data = self.load_data()
        print(f"📊 Dados carregados: {len(data)} jogos históricos")
        
        if not data:
            print("❌ Nenhum dado disponível para análise.")
            return {}
        
        # Run all models
        model_results = self.run_all_models(data)
        
        # Combine predictions
        combined_results = self.combine_predictions(model_results)
        
        # Save results
        if combined_results:
            json_path, csv_path = self.save_predictions(combined_results)
            print(f"💾 Predições salvas:")
            print(f"   📄 JSON: {json_path}")
            print(f"   📊 CSV: {csv_path}")
            
            # Display summary
            self.display_summary(combined_results)
        
        return combined_results
    
    def display_summary(self, results: Dict[str, Any]):
        """Display summary of prediction results."""
        print(f"\n{'='*80}")
        print(f"🎯 RESUMO DA ANÁLISE - {self.config.name.upper()}")
        print(f"{'='*80}")
        
        ensemble_pred = results.get('ensemble_prediction', [])
        ensemble_conf = results.get('ensemble_confidence', 0.0)
        
        print(f"🏆 Predição Final do Ensemble: {ensemble_pred}")
        print(f"📊 Confiança do Ensemble: {ensemble_conf:.1%}")
        
        model_results = results.get('model_results', {})
        print(f"\n📋 Modelos Executados: {len(model_results)}")
        
        for model_name, result in model_results.items():
            prediction = result.get('prediction', [])
            confidence = result.get('confidence', 0.0)
            print(f"   • {model_name.upper()}: {prediction} (Conf: {confidence:.1%})")
        
        print(f"\n{'='*80}")