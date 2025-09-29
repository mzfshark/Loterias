import pandas as pd
import numpy as np
from typing import List, Dict
from collections import Counter, defaultdict
import random


class MonteCarloLotofacilSimulator:
    """
    Advanced Monte Carlo simulation for Lotofacil prediction with multiple sampling strategies.
    """
    
    def __init__(self, n_simulations: int = 10000, verbose: bool = False):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            n_simulations: Number of Monte Carlo simulations to run
        """
        self.n_simulations = n_simulations
        # Controla verbosidade de logs (progresso de simulação, etc.)
        self.verbose = verbose
        self.numbers_range = list(range(1, 26))
        self.combination_size = 15
        self.historical_data = []
        
        # Statistical models for sampling
        self.sampling_strategies = [
            'uniform',
            'frequency_weighted',
            'inverse_frequency',
            'recency_weighted',
            'pattern_based',
            'gaussian_kernel'
        ]
    
    def load_historical_data(self, historical_games: List[List[int]]):
        """Load historical data for analysis."""
        self.historical_data = historical_games
        self._analyze_patterns()
    
    def _analyze_patterns(self):
        """Analyze historical patterns for informed sampling."""
        if not self.historical_data:
            return
        
        # Calculate frequency statistics
        all_numbers = [num for game in self.historical_data for num in game]
        self.number_frequencies = Counter(all_numbers)
        self.total_numbers = len(all_numbers)
        
        # Calculate recency weights
        self.recency_weights = {}
        for num in self.numbers_range:
            # Find the most recent occurrence
            last_seen = -1
            for i, game in enumerate(reversed(self.historical_data)):
                if num in game:
                    last_seen = i
                    break
            self.recency_weights[num] = 1 / (last_seen + 1) if last_seen != -1 else 0.001
        
        # Calculate positional patterns
        self.positional_probs = defaultdict(lambda: defaultdict(int))
        for game in self.historical_data:
            sorted_game = sorted(game)
            for pos, num in enumerate(sorted_game):
                self.positional_probs[pos][num] += 1
        
        # Normalize positional probabilities
        for pos in self.positional_probs:
            total = sum(self.positional_probs[pos].values())
            for num in self.positional_probs[pos]:
                self.positional_probs[pos][num] /= total
        
    # Calculate sum statistics
        self.game_sums = [sum(game) for game in self.historical_data]
        self.sum_mean = np.mean(self.game_sums)
        self.sum_std = np.std(self.game_sums)
        
        # Calculate consecutive patterns
        self.consecutive_stats = []
        for game in self.historical_data:
            sorted_game = sorted(game)
            consecutive_count = 0
            for i in range(len(sorted_game) - 1):
                if sorted_game[i+1] - sorted_game[i] == 1:
                    consecutive_count += 1
            self.consecutive_stats.append(consecutive_count)
        
        self.avg_consecutive = np.mean(self.consecutive_stats)
    
    def sample_uniform(self) -> List[int]:
        """Sample using uniform distribution."""
        return sorted(random.sample(self.numbers_range, self.combination_size))
    
    def sample_frequency_weighted(self) -> List[int]:
        """Sample using frequency-based weights."""
        if not hasattr(self, 'number_frequencies'):
            return self.sample_uniform()
        
        weights = [self.number_frequencies.get(num, 1) for num in self.numbers_range]
        selected = np.random.choice(
            self.numbers_range, 
            size=self.combination_size, 
            replace=False, 
            p=np.array(weights) / sum(weights)
        )
        return sorted(selected.tolist())
    
    def sample_inverse_frequency(self) -> List[int]:
        """Sample using inverse frequency weights (favor less frequent numbers)."""
        if not hasattr(self, 'number_frequencies'):
            return self.sample_uniform()
        
        max_freq = max(self.number_frequencies.values()) if self.number_frequencies else 1
        inv_weights = [max_freq - self.number_frequencies.get(num, 0) + 1 for num in self.numbers_range]
        selected = np.random.choice(
            self.numbers_range,
            size=self.combination_size,
            replace=False,
            p=np.array(inv_weights) / sum(inv_weights)
        )
        return sorted(selected.tolist())
    
    def sample_recency_weighted(self) -> List[int]:
        """Sample using recency-based weights."""
        if not hasattr(self, 'recency_weights'):
            return self.sample_uniform()
        
        weights = [self.recency_weights.get(num, 0.001) for num in self.numbers_range]
        selected = np.random.choice(
            self.numbers_range,
            size=self.combination_size,
            replace=False,
            p=np.array(weights) / sum(weights)
        )
        return sorted(selected.tolist())
    
    def sample_pattern_based(self) -> List[int]:
        """Sample based on historical patterns (sum, consecutive numbers, etc.)."""
        if not hasattr(self, 'sum_mean'):
            return self.sample_uniform()
        
        # Generate multiple candidates and select based on pattern similarity
        candidates = []
        for _ in range(100):  # Generate 100 candidates
            candidate = sorted(random.sample(self.numbers_range, self.combination_size))
            
            # Calculate pattern scores
            candidate_sum = sum(candidate)
            sum_score = -abs(candidate_sum - self.sum_mean) / self.sum_std
            
            # Calculate consecutive score
            consecutive_count = sum(1 for i in range(len(candidate) - 1) 
                                  if candidate[i+1] - candidate[i] == 1)
            consecutive_score = -abs(consecutive_count - self.avg_consecutive)
            
            # Distribution score (balanced across low, mid, high)
            low_count = sum(1 for num in candidate if num <= 8)
            mid_count = sum(1 for num in candidate if 9 <= num <= 17)
            high_count = sum(1 for num in candidate if num >= 18)
            balance_score = -abs(low_count - 5) - abs(mid_count - 5) - abs(high_count - 5)
            
            total_score = sum_score + consecutive_score + balance_score
            candidates.append((candidate, total_score))
        
        # Select best candidate
        best_candidate = max(candidates, key=lambda x: x[1])[0]
        return best_candidate
    
    def sample_gaussian_kernel(self) -> List[int]:
        """Sample using Gaussian kernel density estimation."""
        if not self.historical_data:
            return self.sample_uniform()
        
        # Use kernel density estimation on historical numbers
        selected_numbers = []
        
        # For each position, use KDE to estimate probability density
        all_games_matrix = np.array([sorted(game) for game in self.historical_data])
        
        for i in range(self.combination_size):
            if i < all_games_matrix.shape[1]:
                position_data = all_games_matrix[:, i]
                
                # Simple Gaussian KDE approximation
                mean_pos = np.mean(position_data)
                std_pos = np.std(position_data)
                
                # Sample from Gaussian and round to nearest valid number
                sample = int(np.clip(np.random.normal(mean_pos, std_pos), 1, 25))
                
                # Ensure uniqueness
                while sample in selected_numbers:
                    sample = int(np.clip(np.random.normal(mean_pos, std_pos), 1, 25))
                
                selected_numbers.append(sample)
            else:
                # Fallback for additional numbers
                remaining = [n for n in self.numbers_range if n not in selected_numbers]
                if remaining:
                    selected_numbers.append(random.choice(remaining))
        
        return sorted(selected_numbers)
    
    def run_monte_carlo_simulation(self, strategy: str = 'frequency_weighted') -> Dict:
        """
        Run Monte Carlo simulation with specified strategy.
        
        Args:
            strategy: Sampling strategy to use
            
        Returns:
            Dictionary containing simulation results
        """
        if strategy not in self.sampling_strategies:
            strategy = 'frequency_weighted'
        
        sampling_method = getattr(self, f'sample_{strategy}')
        
        # Run simulations
        all_simulations = []
        number_appearance_count = Counter()
        
        if self.verbose:
            print(f"🎲 Executando {self.n_simulations} simulações Monte Carlo ({strategy})...")
        
        for i in range(self.n_simulations):
            if self.verbose and self.n_simulations >= 10 and i % max(1, (self.n_simulations // 10)) == 0:
                print(f"  Progresso: {i/self.n_simulations*100:.0f}%")
            
            simulation = sampling_method()
            all_simulations.append(simulation)
            
            # Count appearances
            for num in simulation:
                number_appearance_count[num] += 1
        
        # Calculate statistics
        appearance_probabilities = {
            num: count / self.n_simulations 
            for num, count in number_appearance_count.items()
        }
        
        # Fill in zeros for numbers that never appeared
        for num in self.numbers_range:
            if num not in appearance_probabilities:
                appearance_probabilities[num] = 0.0
        
        # Generate final prediction based on most frequent appearances
        most_frequent = sorted(appearance_probabilities.items(), 
                             key=lambda x: x[1], reverse=True)
        prediction = [num for num, _ in most_frequent[:self.combination_size]]
        
        # Calculate confidence metrics
        top_15_probs = [prob for _, prob in most_frequent[:self.combination_size]]
        confidence = np.mean(top_15_probs)
        prob_variance = np.var(top_15_probs)
        
        return {
            'prediction': sorted(prediction),
            'appearance_probabilities': appearance_probabilities,
            'confidence': confidence,
            'probability_variance': prob_variance,
            'strategy_used': strategy,
            'n_simulations': self.n_simulations,
            'top_numbers': most_frequent[:self.combination_size]
        }
    
    def run_ensemble_simulation(self) -> Dict:
        """
        Run ensemble of different Monte Carlo strategies.
        
        Returns:
            Dictionary containing ensemble results
        """
        if self.verbose:
            print("🎯 Executando ensemble de simulações Monte Carlo...")
        
        strategy_results = {}
        ensemble_predictions = []
        
        # Run each strategy
        for strategy in self.sampling_strategies:
            if self.verbose:
                print(f"\n📊 Estratégia: {strategy}")
            result = self.run_monte_carlo_simulation(strategy)
            strategy_results[strategy] = result
            ensemble_predictions.append(result['prediction'])
        
        # Combine predictions using voting
        number_votes = Counter()
        for prediction in ensemble_predictions:
            for num in prediction:
                number_votes[num] += 1
        
        # Select top numbers based on votes
        most_voted = sorted(number_votes.items(), key=lambda x: x[1], reverse=True)
        ensemble_prediction = [num for num, _ in most_voted[:self.combination_size]]
        
        # Calculate ensemble confidence
        total_votes = sum(number_votes.values())
        ensemble_confidence = sum(votes for _, votes in most_voted[:self.combination_size]) / total_votes
        
        return {
            'ensemble_prediction': sorted(ensemble_prediction),
            'strategy_results': strategy_results,
            'ensemble_confidence': ensemble_confidence,
            'voting_results': most_voted,
            'strategies_used': self.sampling_strategies
        }
    
    def analyze_convergence(self, strategy: str = 'frequency_weighted', 
                          step_size: int = 1000) -> Dict:
        """
        Analyze convergence of Monte Carlo simulation.
        
        Args:
            strategy: Strategy to analyze
            step_size: Step size for convergence analysis
            
        Returns:
            Dictionary containing convergence analysis
        """
        sampling_method = getattr(self, f'sample_{strategy}')
        
        convergence_data = []
        running_predictions = []
        
        current_count = Counter()
        
        for i in range(1, self.n_simulations + 1):
            simulation = sampling_method()
            for num in simulation:
                current_count[num] += 1
            
            if i % step_size == 0:
                # Calculate current prediction
                current_probs = {num: count / i for num, count in current_count.items()}
                most_frequent = sorted(current_probs.items(), 
                                     key=lambda x: x[1], reverse=True)
                current_prediction = [num for num, _ in most_frequent[:self.combination_size]]
                
                convergence_data.append({
                    'simulation_count': i,
                    'prediction': sorted(current_prediction),
                    'top_prob': most_frequent[0][1] if most_frequent else 0,
                    'prob_entropy': -sum(p * np.log(p) for p in current_probs.values() if p > 0)
                })
                
                running_predictions.append(current_prediction)
        
        return {
            'convergence_data': convergence_data,
            'final_prediction': convergence_data[-1]['prediction'] if convergence_data else [],
            'strategy_analyzed': strategy
        }


def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv') -> List[List[int]]:
    """Load historical Lotofacil data."""
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col]
    return df[colunas].values.tolist()


def gerar_predicao_monte_carlo(dados: List[List[int]], 
                             n_simulations: int = 10000,
                             strategy: str = 'ensemble') -> Dict:
    """
    Generate Monte Carlo prediction for Lotofacil.
    
    Args:
        dados: Historical lottery data
        n_simulations: Number of simulations to run
        strategy: Strategy to use ('ensemble' or specific strategy name)
        
    Returns:
        Dictionary containing prediction and analysis
    """
    simulator = MonteCarloLotofacilSimulator(n_simulations=n_simulations)
    simulator.load_historical_data(dados)
    
    if strategy == 'ensemble':
        resultado = simulator.run_ensemble_simulation()
    else:
        resultado = simulator.run_monte_carlo_simulation(strategy)
    
    return resultado


if __name__ == '__main__':
    print("🎲 Executando simulação Monte Carlo avançada para Lotofacil...")
    
    # Load data
    dados = carregar_dados()
    print(f"📊 Dados carregados: {len(dados)} jogos históricos")
    
    # Generate Monte Carlo prediction
    resultado = gerar_predicao_monte_carlo(dados, n_simulations=5000, strategy='ensemble')
    
    print("\n🎯 Predição do Ensemble Monte Carlo:")
    print(f"Números previstos: {resultado['ensemble_prediction']}")
    print(f"Confiança do ensemble: {resultado['ensemble_confidence']:.4f}")
    
    print("\n📊 Resultados por estratégia:")
    for strategy, result in resultado['strategy_results'].items():
        print(f"{strategy:20s}: {result['prediction']} (conf: {result['confidence']:.4f})")
    
    print(f"\n🗳️ Top 20 números mais votados:")
    for i, (num, votes) in enumerate(resultado['voting_results'][:20]):
        print(f"{i+1:2d}. Número {num:2d}: {votes} votos")


# Backwards-compatible canonical alias expected by ModelAdapter
MonteCarloSimulator = MonteCarloLotofacilSimulator