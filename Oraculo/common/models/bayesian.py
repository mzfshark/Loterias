import pandas as pd
import numpy as np
import math
from collections import Counter
from typing import Dict, List, Tuple


class BayesianLotofacilPredictor:
    """Advanced Bayesian predictor for Lotofacil using Beta-Binomial conjugate priors."""

    def __init__(self, alpha_prior: float = 1.0, beta_prior: float = 1.0):
        """Initialize predictor with Beta priors.

        Args:
            alpha_prior: Alpha parameter for Beta prior (success count)
            beta_prior: Beta parameter for Beta prior (failure count)
        """
        self.alpha_prior = alpha_prior
        self.beta_prior = beta_prior
        self.numbers_range = range(1, 26)  # Lotofacil numbers 1-25
        self.combination_size = 15

        # Initialize priors for each number
        self.priors = {num: {'alpha': alpha_prior, 'beta': beta_prior} for num in self.numbers_range}

        # Store historical data for analysis
        self.historical_data = []

    def update_priors(self, historical_games: List[List[int]]):
        """
        Update prior distributions based on historical data using Bayesian updating.

        Args:
            historical_games: List of historical lottery games, each containing 15 numbers
        """
        self.historical_data = historical_games
        total_games = len(historical_games)

        # Count occurrences of each number
        number_counts = Counter()
        for game in historical_games:
            for number in game:
                number_counts[number] += 1

        # Update Beta distribution parameters
        for number in self.numbers_range:
            successes = number_counts.get(number, 0)
            failures = total_games - successes

            self.priors[number]['alpha'] = self.alpha_prior + successes
            self.priors[number]['beta'] = self.beta_prior + failures

    def calculate_number_probabilities(self) -> Dict[int, float]:
        """
        Calculate the probability of each number being drawn based on Beta posterior.

        Returns:
            Dictionary mapping each number to its probability
        """
        probabilities = {}

        for number in self.numbers_range:
            alpha = self.priors[number]['alpha']
            beta = self.priors[number]['beta']

            # Expected value of Beta distribution
            prob = alpha / (alpha + beta)
            probabilities[number] = prob

        return probabilities

    def calculate_credible_intervals(self, confidence: float = 0.95) -> Dict[int, Tuple[float, float]]:
        """Calcula intervalos de credibilidade aproximados para cada número.

        Usa aproximação normal da Beta (adequada quando alpha,beta > ~1). Evita dependência SciPy.
        Para casos extremos (alpha ou beta muito pequenos), aplica ajuste simples com multiplicador conservador.
        """
        intervals: Dict[int, Tuple[float, float]] = {}
        z = 1.96 if abs(confidence - 0.95) < 1e-6 else 1.0 * math.sqrt(2)  # fallback grosseiro para outros níveis

        for number in self.numbers_range:
            alpha = self.priors[number]['alpha']
            beta = self.priors[number]['beta']
            total = alpha + beta
            # Média e variância da Beta
            mean = alpha / total
            var = (alpha * beta) / (total * total * (total + 1.0))
            std = math.sqrt(max(var, 1e-12))

            # Ajuste conservador para bordas (quando parâmetros pequenos)
            adj = 1.0
            if alpha < 1.5 or beta < 1.5:
                adj = 1.25

            lower = max(0.0, mean - z * std * adj)
            upper = min(1.0, mean + z * std * adj)
            intervals[number] = (lower, upper)

        return intervals

    def generate_prediction_mcmc(self, n_samples: int = 1000) -> List[int]:
        """
        Generate prediction using Monte Carlo Markov Chain sampling.

        Args:
            n_samples: Number of MCMC samples to generate

        Returns:
            List of 15 predicted numbers
        """
        # Sample probabilities from posterior distributions
        sampled_probs = []

        for _ in range(n_samples):
            sample_probs = {}
            for number in self.numbers_range:
                alpha = self.priors[number]['alpha']
                beta = self.priors[number]['beta']

                # Sample from Beta posterior
                prob = np.random.beta(alpha, beta)
                sample_probs[number] = prob

            sampled_probs.append(sample_probs)

        # Average probabilities across samples
        avg_probs = {}
        for number in self.numbers_range:
            avg_probs[number] = np.mean([sample[number] for sample in sampled_probs])

        # Select top 15 numbers based on averaged probabilities
        sorted_numbers = sorted(avg_probs.items(), key=lambda x: x[1], reverse=True)
        prediction = [num for num, _ in sorted_numbers[:self.combination_size]]

        return sorted(prediction)

    def generate_prediction_map(self) -> List[int]:
        """
        Generate prediction using Maximum A Posteriori (MAP) estimation.

        Returns:
            List of 15 predicted numbers
        """
        probabilities = self.calculate_number_probabilities()

        # Select top 15 numbers based on MAP probabilities
        sorted_numbers = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        prediction = [num for num, _ in sorted_numbers[:self.combination_size]]

        return sorted(prediction)

    def calculate_model_evidence(self) -> float:
        """
        Calculate the marginal likelihood (model evidence) for model comparison.

        Returns:
            Log marginal likelihood
        """
        # Usa math.lgamma para evitar SciPy; soma log-evidências parciais
        log_evidence = 0.0
        for number in self.numbers_range:
            alpha = self.priors[number]['alpha']
            beta = self.priors[number]['beta']
            log_evidence += math.lgamma(alpha) + math.lgamma(beta) - math.lgamma(alpha + beta)
        return log_evidence

    def predict_with_uncertainty(self) -> Dict:
        """
        Generate prediction with uncertainty quantification.

        Returns:
            Dictionary containing prediction, probabilities, and confidence intervals
        """
        probabilities = self.calculate_number_probabilities()
        credible_intervals = self.calculate_credible_intervals()
        map_prediction = self.generate_prediction_map()
        mcmc_prediction = self.generate_prediction_mcmc()

        return {
            'map_prediction': map_prediction,
            'mcmc_prediction': mcmc_prediction,
            'probabilities': probabilities,
            'credible_intervals': credible_intervals,
            'model_evidence': self.calculate_model_evidence(),
        }

    # ---- Stubs mínimos para compatibilidade com o ModelAdapter ----
    def predict_next_game(self, method: str = "map"):
        """
        Retorna uma predição única compatível com outros jogos via adapter.
        method: 'map' (padrão) ou 'mcmc'.
        """
        if method == "mcmc":
            return self.generate_prediction_mcmc()

        # Default: MAP
        return self.generate_prediction_map()

    def analyze_historical_patterns(self) -> Dict:
        """
        Analyze historical patterns in the data.

        Returns:
            Dictionary containing various statistical analyses
        """
        if not self.historical_data:
            return {}

        # Calculate basic statistics
        all_numbers = [num for game in self.historical_data for num in game]
        number_freq = Counter(all_numbers)

        # Calculate hot and cold numbers
        mean_freq = len(all_numbers) / len(self.numbers_range)
        hot_numbers = [num for num, freq in number_freq.items() if freq > mean_freq * 1.1]
        cold_numbers = [num for num, freq in number_freq.items() if freq < mean_freq * 0.9]

        # Calculate consecutive number patterns
        consecutive_patterns = []
        for game in self.historical_data:
            sorted_game = sorted(game)
            consecutive_count = 0
            for i in range(len(sorted_game) - 1):
                if sorted_game[i + 1] - sorted_game[i] == 1:
                    consecutive_count += 1
            consecutive_patterns.append(consecutive_count)

        # Calculate sum patterns
        game_sums = [sum(game) for game in self.historical_data]

        return {
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'number_frequencies': dict(number_freq),
            'avg_consecutive_numbers': np.mean(consecutive_patterns),
            'avg_game_sum': np.mean(game_sums),
            'game_sum_std': np.std(game_sums),
        }



def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv') -> List[List[int]]:
    """Load historical Lotofacil data."""
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col]
    return df[colunas].values.tolist()


def gerar_predicao_bayesiana(dados: List[List[int]], alpha_prior: float = 2.0, beta_prior: float = 23.0) -> Dict:
    """Generate Bayesian prediction for Lotofacil.

    Args:
        dados: Historical lottery data
        alpha_prior: Prior alpha parameter (reflects expected success rate)
        beta_prior: Prior beta parameter (reflects expected failure rate)

    Returns:
        Dictionary containing predictions and analysis
    """

    # Create predictor with informative priors
    # alpha_prior = 2.0, beta_prior = 23.0 reflects that each number has roughly
    # 15/25 = 0.6 probability of being selected in each game
    predictor = BayesianLotofacilPredictor(alpha_prior=alpha_prior, beta_prior=beta_prior)

    # Update with historical data
    predictor.update_priors(dados)

    # Generate predictions with uncertainty
    results = predictor.predict_with_uncertainty()

    # Add historical pattern analysis
    results['historical_analysis'] = predictor.analyze_historical_patterns()

    return results


if __name__ == '__main__':
    print("🎯 Executando predição Bayesiana avançada para Lotofacil...")

    # Load data
    dados = carregar_dados()
    print(f"📊 Dados carregados: {len(dados)} jogos históricos")

    # Generate Bayesian prediction
    resultado = gerar_predicao_bayesiana(dados)

    print("\n🎲 Predições Bayesianas:")
    print(f"MAP (Maximum A Posteriori): {resultado['map_prediction']}")
    print(f"MCMC (Monte Carlo): {resultado['mcmc_prediction']}")

    print("\n📈 Top 10 números com maiores probabilidades:")
    probs_sorted = sorted(resultado['probabilities'].items(), key=lambda x: x[1], reverse=True)
    for i, (num, prob) in enumerate(probs_sorted[:10]):
        ci = resultado['credible_intervals'][num]
        print(f"{i+1:2d}. Número {num:2d}: {prob:.4f} (IC 95%: {ci[0]:.4f} - {ci[1]:.4f})")

    print(f"\n🔍 Evidência do modelo (log): {resultado['model_evidence']:.2f}")

    # Historical analysis
    hist_analysis = resultado['historical_analysis']
    print(f"\n📊 Análise de padrões históricos:")
    print(f"Números 'quentes': {hist_analysis['hot_numbers']}")
    print(f"Números 'frios': {hist_analysis['cold_numbers']}")
    print(f"Média de números consecutivos por jogo: {hist_analysis['avg_consecutive_numbers']:.2f}")
    print(f"Soma média dos jogos: {hist_analysis['avg_game_sum']:.1f} ± {hist_analysis['game_sum_std']:.1f}")