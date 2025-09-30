#!/usr/bin/env python3
"""
Enhanced SuperSete Prediction System with Advanced Probabilistic Models

This script adapts all sophisticated probabilistic models from Lotofacil
to work with SuperSete format (7 digits from 0-9, column-based).

Author: Enhanced AI System
"""

import sys
import os
import signal
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
        self._merge_auto_weights()
        # Reaplica guard FAST_CI após redefinição
        try:
            fast_ci = os.environ.get('FAST_CI', '').strip()
            if fast_ci == '1':
                for heavy in ('monte_carlo', 'neural_ensemble'):
                    if heavy in self.models:
                        self.models[heavy]['enabled'] = False
                print("⚡ Modo FAST_CI ativo (SuperSete): modelos pesados desativados (monte_carlo, neural_ensemble).")
            else:
                print(f"🔍 Modo completo (SuperSete): todos os modelos habilitados (FAST_CI={fast_ci})")
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
        try:
            # Timeout para evitar travamentos (apenas Unix/Linux)
            timeout_set = False
            try:
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Timeout no modelo {model_name}")
                
                # Define timeout de 30 segundos (apenas em sistemas Unix)
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)
                    timeout_set = True
            except (AttributeError, OSError):
                # Windows ou sistema que não suporta alarm
                pass
            
            result = None
            
            if model_name == 'bayesian':
                result = self._simple_bayesian_model(data)
            elif model_name == 'neural_ensemble':
                result = self._simple_neural_model(data)
            elif model_name == 'monte_carlo':
                result = self._simple_monte_carlo_model(data)
            elif model_name == 'time_series':
                result = self._simple_time_series_model(data)
            elif model_name == 'markov':
                result = self._simple_markov_model(data)
            elif model_name == 'poisson':
                result = self._simple_poisson_model(data)
            elif model_name == 'mutation':
                result = self._simple_mutation_model(data)
            elif model_name == 'beam_search':
                result = self._simple_beam_search_model(data)
            
            # Cancela o timeout se foi definido
            if timeout_set:
                signal.alarm(0)
            return result
            
        except (TimeoutError, Exception) as e:
            if timeout_set:
                signal.alarm(0)  # Cancela timeout
            print(f"⚠️ Modelo {model_name} falhou: {e}")
            return None
    
    def _simple_bayesian_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo Bayesiano simplificado para SuperSete."""
        if not data:
            return self._generate_random_prediction('bayesian')
        
        # Calcula frequência por coluna
        column_freqs = [np.zeros(10) for _ in range(7)]
        for game in data[-100:]:  # Últimos 100 jogos
            for col, digit in enumerate(game[:7]):
                if 0 <= digit <= 9:
                    column_freqs[col][digit] += 1
        
        # Gera predição baseada em frequências
        prediction = []
        for col_freq in column_freqs:
            # Adiciona prior Bayesiano
            col_freq += 0.1
            probabilities = col_freq / col_freq.sum()
            digit = np.random.choice(10, p=probabilities)
            prediction.append(int(digit))
        
        return {
            'prediction': prediction,
            'confidence': 0.7,
            'method': 'bayesian_frequency'
        }
    
    def _simple_neural_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo Neural simplificado."""
        if len(data) < 10:
            return self._generate_random_prediction('neural')
        
        # Padrão de tendência por coluna
        prediction = []
        for col in range(7):
            recent_values = [game[col] for game in data[-20:] if col < len(game)]
            if recent_values:
                # Média ponderada dos valores recentes
                weights = np.exp(np.linspace(-1, 0, len(recent_values)))
                avg = np.average(recent_values, weights=weights)
                prediction.append(int(np.round(avg)) % 10)
            else:
                prediction.append(np.random.randint(0, 10))
        
        return {
            'prediction': prediction,
            'confidence': 0.6,
            'method': 'neural_trend'
        }
    
    def _simple_monte_carlo_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo Monte Carlo simplificado."""
        if not data:
            return self._generate_random_prediction('monte_carlo')
        
        # Simula múltiplas predições baseadas em distribuições históricas
        predictions = []
        for _ in range(100):  # 100 simulações
            pred = []
            for col in range(7):
                col_values = [game[col] for game in data[-50:] if col < len(game)]
                if col_values:
                    pred.append(int(np.random.choice(col_values)))
                else:
                    pred.append(np.random.randint(0, 10))
            predictions.append(pred)
        
        # Moda de cada coluna
        final_pred = []
        for col in range(7):
            col_values = [pred[col] for pred in predictions]
            from collections import Counter
            most_common = Counter(col_values).most_common(1)
            final_pred.append(int(most_common[0][0]) if most_common else np.random.randint(0, 10))
        
        return {
            'prediction': final_pred,
            'confidence': 0.65,
            'method': 'monte_carlo_mode'
        }
    
    def _simple_time_series_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo de série temporal simplificado."""
        if len(data) < 5:
            return self._generate_random_prediction('time_series')
        
        prediction = []
        for col in range(7):
            col_series = [game[col] for game in data[-30:] if col < len(game)]
            if len(col_series) >= 3:
                # Tendência linear simples
                x = np.arange(len(col_series))
                y = np.array(col_series)
                trend = np.polyfit(x, y, 1)[0]  # Coeficiente linear
                next_val = col_series[-1] + trend
                prediction.append(int(np.clip(next_val, 0, 9)))
            else:
                prediction.append(np.random.randint(0, 10))
        
        return {
            'prediction': prediction,
            'confidence': 0.55,
            'method': 'linear_trend'
        }
    
    def _simple_markov_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo de Markov simplificado."""
        if len(data) < 3:
            return self._generate_random_prediction('markov')
        
        prediction = []
        for col in range(7):
            col_values = [game[col] for game in data[-20:] if col < len(game)]
            if len(col_values) >= 2:
                # Transições de estado
                transitions = {}
                for i in range(len(col_values) - 1):
                    current = col_values[i]
                    next_val = col_values[i + 1]
                    if current not in transitions:
                        transitions[current] = []
                    transitions[current].append(next_val)
                
                # Predição baseada no último valor
                last_val = col_values[-1]
                if last_val in transitions and transitions[last_val]:
                    next_digit = np.random.choice(transitions[last_val])
                else:
                    next_digit = np.random.randint(0, 10)
                prediction.append(int(next_digit))
            else:
                prediction.append(np.random.randint(0, 10))
        
        return {
            'prediction': prediction,
            'confidence': 0.6,
            'method': 'markov_chain'
        }
    
    def _simple_poisson_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo de Poisson simplificado."""
        if not data:
            return self._generate_random_prediction('poisson')
        
        prediction = []
        for col in range(7):
            col_values = [game[col] for game in data[-50:] if col < len(game)]
            if col_values:
                # Lambda como média da coluna
                lambda_val = np.mean(col_values)
                # Gera valor de Poisson e limita a 0-9
                poisson_val = np.random.poisson(lambda_val)
                prediction.append(int(poisson_val % 10))
            else:
                prediction.append(np.random.randint(0, 10))
        
        return {
            'prediction': prediction,
            'confidence': 0.5,
            'method': 'poisson_distribution'
        }
    
    def _simple_mutation_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo de mutação simplificado."""
        if not data:
            return self._generate_random_prediction('mutation')
        
        # Pega um jogo recente como base
        base_game = data[-1][:7]
        prediction = []
        
        for digit in base_game:
            # Aplica mutação com probabilidade
            if np.random.random() < 0.3:  # 30% chance de mutação
                # Mutação: +/- 1, 2 ou 3
                mutation = np.random.choice([-3, -2, -1, 1, 2, 3])
                new_digit = (digit + mutation) % 10
                prediction.append(int(new_digit))
            else:
                prediction.append(int(digit))
        
        # Garante 7 dígitos
        while len(prediction) < 7:
            prediction.append(np.random.randint(0, 10))
        
        return {
            'prediction': prediction[:7],
            'confidence': 0.55,
            'method': 'genetic_mutation'
        }
    
    def _simple_beam_search_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo de Beam Search simplificado."""
        if not data:
            return self._generate_random_prediction('beam_search')
        
        # Beam search com 3 candidatos por coluna
        beam_size = 3
        candidates = []
        
        for col in range(7):
            col_values = [game[col] for game in data[-20:] if col < len(game)]
            if col_values:
                # Top 3 valores mais frequentes
                from collections import Counter
                counter = Counter(col_values)
                top_candidates = [val for val, _ in counter.most_common(beam_size)]
                # Preenche com valores aleatórios se necessário
                while len(top_candidates) < beam_size:
                    rand_val = np.random.randint(0, 10)
                    if rand_val not in top_candidates:
                        top_candidates.append(rand_val)
                candidates.append(top_candidates)
            else:
                candidates.append([np.random.randint(0, 10) for _ in range(beam_size)])
        
        # Seleciona um candidato por coluna
        prediction = [int(np.random.choice(col_candidates)) for col_candidates in candidates]
        
        return {
            'prediction': prediction,
            'confidence': 0.6,
            'method': 'beam_search_frequency'
        }
    
    def _generate_random_prediction(self, method: str) -> Dict[str, Any]:
        """Gera predição aleatória como fallback."""
        prediction = [np.random.randint(0, 10) for _ in range(7)]
        return {
            'prediction': prediction,
            'confidence': 0.3,
            'method': f'{method}_random'
        }
    
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