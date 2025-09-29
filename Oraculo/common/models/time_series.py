import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from collections import Counter
from scipy.fft import fft, fftfreq
import warnings
warnings.filterwarnings('ignore')


class TimeSeriesLotofacilPredictor:
    """
    Advanced time series analysis for Lotofacil prediction using multiple temporal patterns.
    """
    
    def __init__(self, sequence_length: int = 50):
        """
        Initialize time series predictor.
        
        Args:
            sequence_length: Length of sequence to analyze for patterns
        """
        self.sequence_length = sequence_length
        self.numbers_range = list(range(1, 26))
        self.combination_size = 15
        self.historical_data = []
        
        # Time series components
        self.trend_data = {}
        self.seasonal_data = {}
        self.cyclical_data = {}
        self.residual_data = {}
        
    def load_historical_data(self, historical_games: List[List[int]]):
        """Load and prepare historical data for time series analysis."""
        self.historical_data = historical_games
        self._prepare_time_series()
        self._decompose_time_series()
    
    def _prepare_time_series(self):
        """Convert lottery data into time series format."""
        # Create time series for each number
        self.number_time_series = {}
        
        for num in self.numbers_range:
            # Binary time series: 1 if number appears, 0 otherwise
            series = [1 if num in game else 0 for game in self.historical_data]
            self.number_time_series[num] = np.array(series)
        
        # Create aggregate time series
        self.game_sums = np.array([sum(game) for game in self.historical_data])
        self.consecutive_counts = []
        self.even_odd_ratios = []
        self.low_high_ratios = []
        
        for game in self.historical_data:
            sorted_game = sorted(game)
            
            # Consecutive numbers
            consecutive = sum(1 for i in range(len(sorted_game) - 1) 
                            if sorted_game[i+1] - sorted_game[i] == 1)
            self.consecutive_counts.append(consecutive)
            
            # Even/odd ratio
            even_count = sum(1 for num in game if num % 2 == 0)
            self.even_odd_ratios.append(even_count / len(game))
            
            # Low/high ratio (1-12 vs 13-25)
            low_count = sum(1 for num in game if num <= 12)
            self.low_high_ratios.append(low_count / len(game))
        
        self.consecutive_counts = np.array(self.consecutive_counts)
        self.even_odd_ratios = np.array(self.even_odd_ratios)
        self.low_high_ratios = np.array(self.low_high_ratios)
    
    def _decompose_time_series(self):
        """Decompose time series into trend, seasonal, and residual components."""
        # Simple trend analysis using moving averages
        window_size = min(20, len(self.historical_data) // 4)
        
        for num in self.numbers_range:
            series = self.number_time_series[num]
            
            if len(series) >= window_size:
                # Calculate trend using moving average
                trend = np.convolve(series, np.ones(window_size)/window_size, mode='same')
                
                # Calculate residuals
                residual = series - trend
                
                # Simple seasonal component (using FFT to find dominant frequencies)
                if len(series) > 10:
                    fft_vals = fft(residual)
                    freqs = fftfreq(len(residual))
                    # Find dominant frequency (excluding DC component)
                    dominant_freq_idx = np.argmax(np.abs(fft_vals[1:len(fft_vals)//2])) + 1
                    dominant_freq = freqs[dominant_freq_idx]
                    
                    # Simple seasonal approximation
                    seasonal = np.sin(2 * np.pi * dominant_freq * np.arange(len(series)))
                    seasonal = seasonal * (np.std(residual) / np.std(seasonal)) * 0.1  # Scale down
                else:
                    seasonal = np.zeros_like(series)
                
                self.trend_data[num] = trend
                self.seasonal_data[num] = seasonal
                self.residual_data[num] = residual - seasonal
            else:
                # Fallback for short series
                self.trend_data[num] = np.full_like(series, np.mean(series))
                self.seasonal_data[num] = np.zeros_like(series)
                self.residual_data[num] = series - self.trend_data[num]
    
    def calculate_autocorrelation(self, series: np.ndarray, max_lag: int = 20) -> Dict[int, float]:
        """Calculate autocorrelation for different lags."""
        autocorr = {}
        n = len(series)
        
        for lag in range(1, min(max_lag + 1, n // 2)):
            if n - lag > 0:
                # Calculate Pearson correlation with lagged version
                corr = np.corrcoef(series[:-lag], series[lag:])[0, 1]
                autocorr[lag] = corr if not np.isnan(corr) else 0.0
            else:
                autocorr[lag] = 0.0
        
        return autocorr
    
    def detect_cycles(self, min_cycle_length: int = 5, max_cycle_length: int = 50) -> Dict:
        """Detect cyclical patterns in the data."""
        cycles = {}
        
        # Analyze cycles in game sums
        sum_autocorr = self.calculate_autocorrelation(self.game_sums, max_cycle_length)
        
        # Find peaks in autocorrelation (potential cycle lengths)
        cycle_candidates = []
        for lag, corr in sum_autocorr.items():
            if abs(corr) > 0.1 and min_cycle_length <= lag <= max_cycle_length:
                cycle_candidates.append((lag, abs(corr)))
        
        # Sort by correlation strength
        cycle_candidates.sort(key=lambda x: x[1], reverse=True)
        
        cycles['sum_cycles'] = cycle_candidates[:5]  # Top 5 cycles
        
        # Analyze cycles for individual numbers
        number_cycles = {}
        for num in self.numbers_range:
            series = self.number_time_series[num]
            num_autocorr = self.calculate_autocorrelation(series, max_cycle_length)
            
            strong_cycles = [(lag, abs(corr)) for lag, corr in num_autocorr.items() 
                           if abs(corr) > 0.15 and min_cycle_length <= lag <= max_cycle_length]
            strong_cycles.sort(key=lambda x: x[1], reverse=True)
            
            if strong_cycles:
                number_cycles[num] = strong_cycles[:3]  # Top 3 cycles per number
        
        cycles['number_cycles'] = number_cycles
        
        return cycles
    
    def predict_trend_continuation(self) -> Dict[int, float]:
        """Predict future values based on trend continuation."""
        predictions = {}
        
        for num in self.numbers_range:
            trend_series = self.trend_data[num]
            
            if len(trend_series) >= 3:
                # Simple linear extrapolation
                recent_trend = trend_series[-3:]
                if len(recent_trend) > 1:
                    slope = (recent_trend[-1] - recent_trend[0]) / (len(recent_trend) - 1)
                    next_value = trend_series[-1] + slope
                    
                    # Clamp to [0, 1] range
                    predictions[num] = max(0, min(1, next_value))
                else:
                    predictions[num] = trend_series[-1]
            else:
                # Fallback to historical average
                series = self.number_time_series[num]
                predictions[num] = np.mean(series) if len(series) > 0 else 1/25
        
        return predictions
    
    def predict_seasonal_component(self) -> Dict[int, float]:
        """Predict seasonal component for next draw."""
        predictions = {}
        
        for num in self.numbers_range:
            seasonal_series = self.seasonal_data[num]
            
            if len(seasonal_series) > 0:
                # Use the last seasonal value as next prediction, but ensure it's non-negative
                seasonal_value = seasonal_series[-1]
                predictions[num] = max(0.0, seasonal_value)
            else:
                predictions[num] = 0.0
        
        return predictions
    
    def predict_mean_reversion(self, lookback_period: int = 20) -> Dict[int, float]:
        """Predict based on mean reversion hypothesis."""
        predictions = {}
        
        for num in self.numbers_range:
            series = self.number_time_series[num]
            
            if len(series) >= lookback_period:
                recent_avg = np.mean(series[-lookback_period:])
                long_term_avg = np.mean(series)
                
                # Mean reversion: if recent is below long-term, predict higher probability
                reversion_factor = long_term_avg - recent_avg
                predictions[num] = long_term_avg + 0.3 * reversion_factor
                
                # Clamp to reasonable range
                predictions[num] = max(0, min(1, predictions[num]))
            else:
                predictions[num] = np.mean(series) if len(series) > 0 else 1/25
        
        return predictions
    
    def predict_momentum(self, momentum_period: int = 10) -> Dict[int, float]:
        """Predict based on momentum in recent draws."""
        predictions = {}
        
        for num in self.numbers_range:
            series = self.number_time_series[num]
            
            if len(series) >= momentum_period * 2:
                recent_avg = np.mean(series[-momentum_period:])
                previous_avg = np.mean(series[-momentum_period*2:-momentum_period])
                
                # Momentum factor
                momentum = recent_avg - previous_avg
                predictions[num] = recent_avg + 0.5 * momentum
                
                # Clamp to reasonable range
                predictions[num] = max(0, min(1, predictions[num]))
            else:
                predictions[num] = np.mean(series) if len(series) > 0 else 1/25
        
        return predictions
    
    def generate_ensemble_prediction(self, weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        Generate ensemble prediction combining multiple time series methods.
        
        Args:
            weights: Weights for different prediction methods
            
        Returns:
            Dictionary containing ensemble prediction and components
        """
        if weights is None:
            weights = {
                'trend': 0.3,
                'seasonal': 0.1,
                'mean_reversion': 0.25,
                'momentum': 0.25,
                'frequency': 0.1
            }
        
        # Get predictions from different methods
        trend_pred = self.predict_trend_continuation()
        seasonal_pred = self.predict_seasonal_component()
        reversion_pred = self.predict_mean_reversion()
        momentum_pred = self.predict_momentum()
        
        # Frequency-based baseline
        all_numbers = [num for game in self.historical_data for num in game]
        frequency_counts = Counter(all_numbers)
        total_count = sum(frequency_counts.values())
        frequency_pred = {num: frequency_counts.get(num, 0) / total_count 
                         for num in self.numbers_range}
        
        # Ensemble combination
        ensemble_probs = {}
        for num in self.numbers_range:
            combined_prob = (
                weights['trend'] * trend_pred[num] +
                weights['seasonal'] * (seasonal_pred[num] + 0.5) +  # Shift seasonal
                weights['mean_reversion'] * reversion_pred[num] +
                weights['momentum'] * momentum_pred[num] +
                weights['frequency'] * frequency_pred[num]
            )
            ensemble_probs[num] = combined_prob
        
        # Normalize probabilities
        total_prob = sum(ensemble_probs.values())
        if total_prob > 0:
            ensemble_probs = {num: prob / total_prob for num, prob in ensemble_probs.items()}
        
        # Select top 15 numbers
        sorted_probs = sorted(ensemble_probs.items(), key=lambda x: x[1], reverse=True)
        prediction = [num for num, _ in sorted_probs[:self.combination_size]]
        
        # Calculate confidence
        top_15_probs = [prob for _, prob in sorted_probs[:self.combination_size]]
        confidence = np.mean(top_15_probs) / np.mean([prob for _, prob in sorted_probs])
        
        # Detect cycles
        cycles = self.detect_cycles()
        
        return {
            'prediction': sorted(prediction),
            'ensemble_probabilities': ensemble_probs,
            'confidence': confidence,
            'component_predictions': {
                'trend': trend_pred,
                'seasonal': seasonal_pred,
                'mean_reversion': reversion_pred,
                'momentum': momentum_pred,
                'frequency': frequency_pred
            },
            'cycles_detected': cycles,
            'weights_used': weights,
            'top_numbers_with_probs': sorted_probs[:self.combination_size]
        }
    
    def analyze_stationarity(self) -> Dict:
        """Analyze stationarity of time series."""
        stationarity_results = {}
        
        for num in self.numbers_range:
            series = self.number_time_series[num]
            
            if len(series) > 10:
                # Simple stationarity test: compare first and second half means
                mid_point = len(series) // 2
                first_half_mean = np.mean(series[:mid_point])
                second_half_mean = np.mean(series[mid_point:])
                
                # Calculate variance ratio
                first_half_var = np.var(series[:mid_point])
                second_half_var = np.var(series[mid_point:])
                var_ratio = second_half_var / first_half_var if first_half_var > 0 else 1
                
                mean_diff = abs(second_half_mean - first_half_mean)
                
                # Simple stationarity score
                stationarity_score = 1 / (1 + mean_diff + abs(var_ratio - 1))
                
                stationarity_results[num] = {
                    'stationarity_score': stationarity_score,
                    'mean_difference': mean_diff,
                    'variance_ratio': var_ratio
                }
            else:
                stationarity_results[num] = {
                    'stationarity_score': 0.5,
                    'mean_difference': 0,
                    'variance_ratio': 1.0
                }
        
        return stationarity_results

    # ---- Stub mínimo para compatibilidade com o ModelAdapter ----
    def predict_next_game(self) -> Dict:
        """
        Gera uma predição única usando o ensemble interno e retorna
        no formato esperado pelo adapter: {prediction, confidence, cycles_detected}.
        """
        resultado = self.generate_ensemble_prediction()
        return {
            'prediction': resultado.get('prediction', []),
            'confidence': float(resultado.get('confidence', 0.6)),
            'cycles_detected': resultado.get('cycles_detected', {})
        }


def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv') -> List[List[int]]:
    """Load historical Lotofacil data."""
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col]
    return df[colunas].values.tolist()


def gerar_predicao_time_series(dados: List[List[int]], 
                              sequence_length: int = 50,
                              custom_weights: Optional[Dict[str, float]] = None) -> Dict:
    """
    Generate time series prediction for Lotofacil.
    
    Args:
        dados: Historical lottery data
        sequence_length: Length of sequence for analysis
        custom_weights: Custom weights for ensemble methods
        
    Returns:
        Dictionary containing prediction and analysis
    """
    predictor = TimeSeriesLotofacilPredictor(sequence_length=sequence_length)
    predictor.load_historical_data(dados)
    
    resultado = predictor.generate_ensemble_prediction(weights=custom_weights)
    
    # Add stationarity analysis
    resultado['stationarity_analysis'] = predictor.analyze_stationarity()
    
    return resultado


if __name__ == '__main__':
    print("📈 Executando análise de séries temporais para Lotofacil...")
    
    # Load data
    dados = carregar_dados()
    print(f"📊 Dados carregados: {len(dados)} jogos históricos")
    
    # Generate time series prediction
    resultado = gerar_predicao_time_series(dados, sequence_length=60)
    
    print("\n🎯 Predição de Séries Temporais:")
    print(f"Números previstos: {resultado['prediction']}")
    print(f"Confiança do ensemble: {resultado['confidence']:.4f}")
    
    print(f"\n⚖️ Pesos utilizados:")
    for method, weight in resultado['weights_used'].items():
        print(f"  {method:15s}: {weight:.3f}")
    
    print("\n📈 Top 15 números com probabilidades:")
    for i, (num, prob) in enumerate(resultado['top_numbers_with_probs']):
        print(f"{i+1:2d}. Número {num:2d}: {prob:.6f}")
    
    print(f"\n🔄 Ciclos detectados:")
    cycles = resultado['cycles_detected']
    if 'sum_cycles' in cycles and cycles['sum_cycles']:
        print("  Ciclos nas somas:")
        for lag, strength in cycles['sum_cycles'][:3]:
            print(f"    Período {lag}: força {strength:.4f}")
    
    print(f"\n📊 Números com ciclos mais fortes:")
    if 'number_cycles' in cycles:
        strong_cycle_numbers = sorted(cycles['number_cycles'].items(), 
                                    key=lambda x: x[1][0][1] if x[1] else 0, 
                                    reverse=True)[:5]
        for num, cycle_info in strong_cycle_numbers:
            if cycle_info:
                lag, strength = cycle_info[0]
                print(f"    Número {num:2d}: período {lag}, força {strength:.4f}")