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
import math
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import SUPERSETE_CONFIG
from Oraculo.core.model_adapter import ModelAdapter
from Oraculo.core.metrics_engine import (
    safe_probs,
    normalized_entropy,
    rolling_stability,
    volatility_chunks,
    dynamic_confidence,
)


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

    # ===== Confiança dinâmica (por dígitos 0-9 agregados nas 7 colunas) =====
    def _digit_counts_from_history(self, data: List[List[int]], limit: Optional[int] = None) -> List[int]:
        if limit is not None:
            subset = data[:max(0, int(limit))]
        else:
            subset = data
        counts = [0] * 10
        for game in subset:
            for d in game[:7]:
                try:
                    di = int(d)
                except Exception:
                    continue
                if 0 <= di <= 9:
                    counts[di] += 1
        return counts

    def _calc_stability_volatility(self, data: List[List[int]]) -> Tuple[float, float]:
        n = len(data)
        if n < 40:
            return 0.7, 0.2
        w = min(200, n // 2)
        counts_a = self._digit_counts_from_history(data, limit=w)
        counts_b = self._digit_counts_from_history(data[w: 2 * w])
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
                mats.append(self._digit_counts_from_history(data[start:end]))
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

        counts_recent = self._digit_counts_from_history(data, limit=min(300, len(data)))
        probs_all = safe_probs(counts_recent, alpha=0.5)  # tamanho 10, dígitos 0..9
        stab, vol = self._calc_stability_volatility(data)

        for m, res in list(model_results.items()):
            try:
                pred_digits = res.get('prediction', []) or []  # 7 dígitos 0..9
                base_conf = float(res.get('confidence', 0.5))
                # Mapear para 1..10 para o helper de confiança
                pred_map = [int(d) + 1 for d in pred_digits if 0 <= int(d) <= 9]
                idx = [int(d) for d in pred_digits if 0 <= int(d) <= 9]  # índices 0..9
                h_norm = normalized_entropy(probs_all[idx]) if idx else normalized_entropy(probs_all)
                new_conf = dynamic_confidence(base_conf, pred_map, probs_all, stab, vol)
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
    
    def _run_model(self, model_name: str, data: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Run a specific adapted model for SuperSete."""
        try:
            # Timeout para evitar travamentos (apenas Unix/Linux)
            timeout_set = False
            try:
                # Só usa signals se estivermos na thread principal
                import threading
                is_main_thread = threading.current_thread() is threading.main_thread()
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Timeout no modelo {model_name}")
                
                # Define timeout de 30 segundos (apenas em sistemas Unix e thread principal)
                if hasattr(signal, 'SIGALRM') and is_main_thread:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)
                    timeout_set = True
            except (AttributeError, OSError, RuntimeError):
                # Windows, sistema que não suporta alarm, ou não é thread principal
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
            
            # Cancela o timeout se foi definido e estamos na thread principal
            if timeout_set and hasattr(signal, 'alarm'):
                try:
                    signal.alarm(0)
                except RuntimeError:
                    pass  # Ignora se não estivermos na thread principal
            return result
            
        except (TimeoutError, Exception) as e:
            if timeout_set and hasattr(signal, 'alarm'):
                try:
                    signal.alarm(0)  # Cancela timeout
                except RuntimeError:
                    pass  # Ignora se não estivermos na thread principal
            print(f"⚠️ Modelo {model_name} falhou: {e}")
            return None
    
    def _simple_bayesian_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo Bayesiano simplificado para SuperSete."""
        if not data:
            return self._generate_random_prediction('bayesian')

        window = data[-100:]  # janela de histórico
        column_freqs = [np.zeros(10, dtype=float) for _ in range(7)]
        for game in window:
            for col, digit in enumerate(game[:7]):
                if 0 <= digit <= 9:
                    column_freqs[col][digit] += 1.0

        prediction = []
        entropies = []
        variances = []
        for col_freq in column_freqs:
            col_freq += 0.5  # smoothing bayesiano (prior > 0.1 para maior regularização)
            probs = col_freq / col_freq.sum()
            # entropia
            entropy = -np.sum(probs * np.log(probs))
            entropies.append(float(entropy))
            variances.append(float(np.var(probs)))
            digit = np.random.choice(10, p=probs)
            prediction.append(int(digit))

        mean_entropy = float(np.mean(entropies))
        norm_entropy = mean_entropy / np.log(10)
        base_conf = 0.70
        dynamic_conf = base_conf * (1 - norm_entropy)
        dispersion = float(np.mean([abs(prediction[i] - np.mean([g[i] for g in window])) for i in range(7)])) if window else 0.0

        return {
            'prediction': prediction,
            'confidence': dynamic_conf,
            'method': 'bayesian_frequency',
            'metrics': {
                'column_entropies': entropies,
                'mean_entropy': mean_entropy,
                'column_variances': variances,
                'prediction_dispersion': dispersion
            }
        }
    
    def _simple_neural_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo Neural simplificado."""
        if len(data) < 10:
            return self._generate_random_prediction('neural')

        window = data[-20:]
        prediction = []
        entropies = []
        variances = []
        for col in range(7):
            recent_values = [game[col] for game in window if col < len(game)]
            if recent_values:
                weights = np.exp(np.linspace(-1, 0, len(recent_values)))
                avg = np.average(recent_values, weights=weights)
                pred_digit = int(np.round(avg)) % 10
                prediction.append(pred_digit)
                # distribuição aproximada via kernel gaussiano discreto centralizado na média
                centers = np.arange(10)
                dist = np.exp(-0.5 * ((centers - avg) ** 2) / (1.5 ** 2)) + 1e-9
                dist /= dist.sum()
                entropy = -np.sum(dist * np.log(dist))
                entropies.append(float(entropy))
                variances.append(float(np.var(dist)))
            else:
                rd = np.random.randint(0, 10)
                prediction.append(rd)
                entropies.append(np.log(10))
                variances.append(0.0)

        mean_entropy = float(np.mean(entropies))
        norm_entropy = mean_entropy / np.log(10)
        base_conf = 0.60
        dynamic_conf = base_conf * (1 - norm_entropy)
        dispersion = float(np.mean([abs(prediction[i] - np.mean([g[i] for g in window])) for i in range(7)])) if window else 0.0

        return {
            'prediction': prediction,
            'confidence': dynamic_conf,
            'method': 'neural_trend',
            'metrics': {
                'column_entropies': entropies,
                'mean_entropy': mean_entropy,
                'column_variances': variances,
                'prediction_dispersion': dispersion
            }
        }
    
    def _simple_monte_carlo_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo Monte Carlo simplificado."""
        if not data:
            return self._generate_random_prediction('monte_carlo')

        window = data[-50:]
        sims = 150  # número de simulações
        alpha = 0.8  # smoothing para escassez
        column_probs = []
        for col in range(7):
            col_values = [game[col] for game in window if col < len(game)]
            counts = np.zeros(10, dtype=float)
            for v in col_values:
                if 0 <= v <= 9:
                    counts[v] += 1
            probs = (counts + alpha) / (counts.sum() + alpha * 10)
            column_probs.append(probs)

        sim_matrix = np.zeros((sims, 7), dtype=int)
        for s in range(sims):
            for col in range(7):
                sim_matrix[s, col] = int(np.random.choice(10, p=column_probs[col]))

        final_pred = []
        entropies = []
        variances = []
        for col in range(7):
            col_samples = sim_matrix[:, col]
            counts = np.zeros(10, dtype=float)
            for v in col_samples:
                counts[v] += 1
            dist = counts / counts.sum()
            entropy = -np.sum(dist * np.log(dist + 1e-12))
            entropies.append(float(entropy))
            variances.append(float(np.var(dist)))
            final_pred.append(int(np.argmax(dist)))

        mean_entropy = float(np.mean(entropies))
        norm_entropy = mean_entropy / np.log(10)
        base_conf = 0.65
        dynamic_conf = base_conf * (1 - norm_entropy)
        dispersion = float(np.mean([abs(final_pred[i] - np.mean([g[i] for g in window])) for i in range(7)])) if window else 0.0

        return {
            'prediction': final_pred,
            'confidence': dynamic_conf,
            'method': 'monte_carlo_multinomial',
            'metrics': {
                'column_entropies': entropies,
                'mean_entropy': mean_entropy,
                'column_variances': variances,
                'prediction_dispersion': dispersion
            }
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

        window = data[-30:]
        alpha = 0.5  # regularização
        prediction = []
        entropies = []
        variances = []
        for col in range(7):
            col_values = [game[col] for game in window if col < len(game)]
            if len(col_values) >= 3:
                # matriz de transições regularizada
                trans_counts = np.zeros((10, 10), dtype=float)
                for i in range(len(col_values) - 1):
                    a = col_values[i]
                    b = col_values[i + 1]
                    if 0 <= a <= 9 and 0 <= b <= 9:
                        trans_counts[a, b] += 1
                last_val = col_values[-1]
                row = trans_counts[last_val] if 0 <= last_val <= 9 else np.zeros(10)
                probs = (row + alpha) / (row.sum() + alpha * 10)
                entropy = -np.sum(probs * np.log(probs))
                entropies.append(float(entropy))
                variances.append(float(np.var(probs)))
                next_digit = int(np.random.choice(10, p=probs))
                prediction.append(next_digit)
            else:
                rd = np.random.randint(0, 10)
                prediction.append(rd)
                entropies.append(np.log(10))
                variances.append(0.0)

        mean_entropy = float(np.mean(entropies))
        norm_entropy = mean_entropy / np.log(10)
        base_conf = 0.60
        dynamic_conf = base_conf * (1 - norm_entropy)
        dispersion = float(np.mean([abs(prediction[i] - np.mean([g[i] for g in window])) for i in range(7)])) if window else 0.0

        return {
            'prediction': prediction,
            'confidence': dynamic_conf,
            'method': 'markov_chain_regularized',
            'metrics': {
                'column_entropies': entropies,
                'mean_entropy': mean_entropy,
                'column_variances': variances,
                'prediction_dispersion': dispersion
            }
        }
    
    def _simple_poisson_model(self, data: List[List[int]]) -> Dict[str, Any]:
        """Modelo de Poisson simplificado."""
        if not data:
            return self._generate_random_prediction('poisson')

        window = data[-50:]
        prediction = []
        entropies = []
        variances = []
        for col in range(7):
            col_values = [game[col] for game in window if col < len(game)]
            if col_values:
                lambda_val = max(0.01, min(9.0, float(np.mean(col_values))))
                k = np.arange(10)
                pmf = np.exp(-lambda_val) * (lambda_val ** k) / np.maximum(1, np.array([math.factorial(int(x)) for x in k]))
                pmf /= pmf.sum()  # truncada e normalizada
                entropy = -np.sum(pmf * np.log(pmf + 1e-12))
                entropies.append(float(entropy))
                variances.append(float(np.var(pmf)))
                digit = int(np.random.choice(10, p=pmf))
                prediction.append(digit)
            else:
                rd = np.random.randint(0, 10)
                prediction.append(rd)
                entropies.append(np.log(10))
                variances.append(0.0)

        mean_entropy = float(np.mean(entropies))
        norm_entropy = mean_entropy / np.log(10)
        base_conf = 0.50
        dynamic_conf = base_conf * (1 - norm_entropy)
        dispersion = float(np.mean([abs(prediction[i] - np.mean([g[i] for g in window])) for i in range(7)])) if window else 0.0

        return {
            'prediction': prediction,
            'confidence': dynamic_conf,
            'method': 'poisson_truncated',
            'metrics': {
                'column_entropies': entropies,
                'mean_entropy': mean_entropy,
                'column_variances': variances,
                'prediction_dispersion': dispersion
            }
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
        
        window = data[-30:]
        entropies = []
        variances = []
        for col in range(7):
            col_values = [game[col] for game in window if col < len(game)]
            counts = np.zeros(10, dtype=float)
            for v in col_values:
                if 0 <= v <= 9:
                    counts[v] += 1
            dist = (counts + 0.3) / (counts.sum() + 0.3 * 10)
            entropy = -np.sum(dist * np.log(dist))
            entropies.append(float(entropy))
            variances.append(float(np.var(dist)))

        mean_entropy = float(np.mean(entropies))
        norm_entropy = mean_entropy / np.log(10)
        base_conf = 0.55
        dynamic_conf = base_conf * (1 - norm_entropy)
        dispersion = float(np.mean([abs(prediction[i] - np.mean([g[i] for g in window])) for i in range(7)])) if window else 0.0

        return {
            'prediction': prediction[:7],
            'confidence': dynamic_conf,
            'method': 'genetic_mutation',
            'metrics': {
                'column_entropies': entropies,
                'mean_entropy': mean_entropy,
                'column_variances': variances,
                'prediction_dispersion': dispersion
            }
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