#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Enhanced Lotofacil Prediction Models

This script provides extensive testing for all probabilistic models including:
- Unit tests for individual models
- Integration tests for the prediction pipeline
- Performance benchmarks
- Statistical validation
- Model accuracy assessment

Author: Enhanced AI System
"""

import unittest
import sys
import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import time
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import all models
from Oraculo.Lotofacil.models.bayesian import BayesianLotofacilPredictor, gerar_predicao_bayesiana
from Oraculo.Lotofacil.models.neural_ensemble import NeuralEnsembleLotofacil, gerar_predicao_neural_ensemble
from Oraculo.Lotofacil.models.monte_carlo import MonteCarloLotofacilSimulator, gerar_predicao_monte_carlo
from Oraculo.Lotofacil.models.time_series import TimeSeriesLotofacilPredictor, gerar_predicao_time_series
from Oraculo.Lotofacil.scripts.enhanced_predict import EnhancedLotofacilPredictor


class TestDataGenerator:
    """Generate synthetic test data for validation."""
    
    @staticmethod
    def generate_synthetic_games(n_games: int = 100, seed: int = 42) -> List[List[int]]:
        """Generate synthetic lottery games for testing."""
        np.random.seed(seed)
        games = []
        
        for _ in range(n_games):
            # Generate a game with some realistic patterns
            game = sorted(np.random.choice(range(1, 26), size=15, replace=False))
            games.append(game)
        
        return games
    
    @staticmethod
    def load_sample_data(n_games: int = 200) -> List[List[int]]:
        """Load a sample of real historical data."""
        try:
            df = pd.read_csv('Oraculo/Lotofacil/data/Lotofacil.csv')
            colunas = [col for col in df.columns if 'Bola' in col]
            all_games = df[colunas].values.tolist()
            return all_games[:n_games] if len(all_games) > n_games else all_games
        except FileNotFoundError:
            print("⚠️ Real data not found, using synthetic data")
            return TestDataGenerator.generate_synthetic_games(n_games)


class TestBayesianModel(unittest.TestCase):
    """Test cases for Bayesian model."""
    
    def setUp(self):
        self.test_data = TestDataGenerator.generate_synthetic_games(50)
        self.predictor = BayesianLotofacilPredictor()
    
    def test_initialization(self):
        """Test model initialization."""
        self.assertEqual(len(self.predictor.numbers_range), 25)
        self.assertEqual(self.predictor.combination_size, 15)
        self.assertGreater(self.predictor.alpha_prior, 0)
        self.assertGreater(self.predictor.beta_prior, 0)
    
    def test_prior_updates(self):
        """Test prior distribution updates."""
        initial_alpha = self.predictor.priors[1]['alpha']
        self.predictor.update_priors(self.test_data)
        updated_alpha = self.predictor.priors[1]['alpha']
        self.assertGreaterEqual(updated_alpha, initial_alpha)
    
    def test_probability_calculation(self):
        """Test probability calculations."""
        self.predictor.update_priors(self.test_data)
        probabilities = self.predictor.calculate_number_probabilities()
        
        # Check that probabilities are valid
        self.assertEqual(len(probabilities), 25)
        for prob in probabilities.values():
            self.assertGreaterEqual(prob, 0)
            self.assertLessEqual(prob, 1)
    
    def test_map_prediction(self):
        """Test MAP prediction."""
        self.predictor.update_priors(self.test_data)
        prediction = self.predictor.generate_prediction_map()
        
        self.assertEqual(len(prediction), 15)
        self.assertEqual(len(set(prediction)), 15)  # All unique
        self.assertTrue(all(1 <= num <= 25 for num in prediction))
    
    def test_mcmc_prediction(self):
        """Test MCMC prediction."""
        self.predictor.update_priors(self.test_data)
        prediction = self.predictor.generate_prediction_mcmc(n_samples=100)
        
        self.assertEqual(len(prediction), 15)
        self.assertEqual(len(set(prediction)), 15)  # All unique
        self.assertTrue(all(1 <= num <= 25 for num in prediction))
    
    def test_credible_intervals(self):
        """Test credible interval calculation."""
        self.predictor.update_priors(self.test_data)
        intervals = self.predictor.calculate_credible_intervals()
        
        self.assertEqual(len(intervals), 25)
        for lower, upper in intervals.values():
            self.assertLessEqual(lower, upper)
            self.assertGreaterEqual(lower, 0)
            self.assertLessEqual(upper, 1)


class TestNeuralEnsemble(unittest.TestCase):
    """Test cases for Neural Ensemble model."""
    
    def setUp(self):
        self.test_data = TestDataGenerator.generate_synthetic_games(100)
        self.ensemble = NeuralEnsembleLotofacil()
    
    def test_feature_extraction(self):
        """Test feature extraction."""
        features = self.ensemble.extract_features(self.test_data, lookback=10)
        
        self.assertGreater(features.shape[0], 0)
        self.assertGreater(features.shape[1], 0)
        self.assertFalse(np.any(np.isnan(features)))
    
    def test_target_preparation(self):
        """Test target preparation."""
        targets = self.ensemble.prepare_targets(self.test_data, lookback=10)
        
        self.assertEqual(len(targets), 25)  # One target per number
        for target in targets:
            self.assertTrue(all(val in [0, 1] for val in target))
    
    def test_prediction_generation(self):
        """Test prediction generation."""
        result = self.ensemble.generate_prediction(self.test_data)
        
        self.assertIn('prediction', result)
        self.assertEqual(len(result['prediction']), 15)
        self.assertTrue(all(1 <= num <= 25 for num in result['prediction']))
        self.assertIn('confidence', result)


class TestMonteCarloModel(unittest.TestCase):
    """Test cases for Monte Carlo model."""
    
    def setUp(self):
        self.test_data = TestDataGenerator.generate_synthetic_games(50)
        self.simulator = MonteCarloLotofacilSimulator(n_simulations=100)
    
    def test_data_loading(self):
        """Test data loading and analysis."""
        self.simulator.load_historical_data(self.test_data)
        
        self.assertEqual(len(self.simulator.historical_data), len(self.test_data))
        self.assertGreater(len(self.simulator.number_frequencies), 0)
    
    def test_sampling_strategies(self):
        """Test different sampling strategies."""
        self.simulator.load_historical_data(self.test_data)
        
        strategies = ['uniform', 'frequency_weighted', 'pattern_based']
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                sample = getattr(self.simulator, f'sample_{strategy}')()
                self.assertEqual(len(sample), 15)
                self.assertEqual(len(set(sample)), 15)  # All unique
                self.assertTrue(all(1 <= num <= 25 for num in sample))
    
    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation."""
        self.simulator.load_historical_data(self.test_data)
        result = self.simulator.run_monte_carlo_simulation('frequency_weighted')
        
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertEqual(len(result['prediction']), 15)
        self.assertGreaterEqual(result['confidence'], 0)
    
    def test_ensemble_simulation(self):
        """Test ensemble simulation."""
        self.simulator.load_historical_data(self.test_data)
        result = self.simulator.run_ensemble_simulation()
        
        self.assertIn('ensemble_prediction', result)
        self.assertIn('strategy_results', result)
        self.assertEqual(len(result['ensemble_prediction']), 15)


class TestTimeSeriesModel(unittest.TestCase):
    """Test cases for Time Series model."""
    
    def setUp(self):
        self.test_data = TestDataGenerator.generate_synthetic_games(100)
        self.predictor = TimeSeriesLotofacilPredictor()
    
    def test_data_preparation(self):
        """Test time series data preparation."""
        self.predictor.load_historical_data(self.test_data)
        
        self.assertEqual(len(self.predictor.historical_data), len(self.test_data))
        self.assertEqual(len(self.predictor.number_time_series), 25)
    
    def test_time_series_decomposition(self):
        """Test time series decomposition."""
        self.predictor.load_historical_data(self.test_data)
        
        for num in range(1, 26):
            self.assertIn(num, self.predictor.trend_data)
            self.assertIn(num, self.predictor.seasonal_data)
            self.assertIn(num, self.predictor.residual_data)
    
    def test_autocorrelation(self):
        """Test autocorrelation calculation."""
        series = np.random.randn(50)
        autocorr = self.predictor.calculate_autocorrelation(series, max_lag=10)
        
        self.assertLessEqual(len(autocorr), 10)
        for lag, corr in autocorr.items():
            self.assertGreaterEqual(lag, 1)
            self.assertGreaterEqual(corr, -1)
            self.assertLessEqual(corr, 1)
    
    def test_prediction_methods(self):
        """Test different prediction methods."""
        self.predictor.load_historical_data(self.test_data)
        
        methods = ['trend_continuation', 'seasonal_component', 'mean_reversion', 'momentum']
        for method in methods:
            with self.subTest(method=method):
                pred_func = getattr(self.predictor, f'predict_{method}')
                predictions = pred_func()
                
                self.assertEqual(len(predictions), 25)
                for prob in predictions.values():
                    self.assertGreaterEqual(prob, 0)
                    self.assertLessEqual(prob, 1)


class TestEnhancedPredictor(unittest.TestCase):
    """Test cases for Enhanced Predictor integration."""
    
    def setUp(self):
        self.test_data = TestDataGenerator.load_sample_data(100)
        self.predictor = EnhancedLotofacilPredictor()
    
    def test_model_configuration(self):
        """Test model configuration."""
        total_weight = sum(config['weight'] for config in self.predictor.models.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
    
    def test_data_loading(self):
        """Test data loading functionality."""
        # Create a temporary test file
        test_df = pd.DataFrame({
            'Concurso': range(1, 51),
            'Bola1': np.random.randint(1, 26, 50),
            'Bola2': np.random.randint(1, 26, 50),
            'Bola3': np.random.randint(1, 26, 50),
            'Bola4': np.random.randint(1, 26, 50),
            'Bola5': np.random.randint(1, 26, 50),
            'Bola6': np.random.randint(1, 26, 50),
            'Bola7': np.random.randint(1, 26, 50),
            'Bola8': np.random.randint(1, 26, 50),
            'Bola9': np.random.randint(1, 26, 50),
            'Bola10': np.random.randint(1, 26, 50),
            'Bola11': np.random.randint(1, 26, 50),
            'Bola12': np.random.randint(1, 26, 50),
            'Bola13': np.random.randint(1, 26, 50),
            'Bola14': np.random.randint(1, 26, 50),
            'Bola15': np.random.randint(1, 26, 50),
        })
        
        test_path = '/tmp/test_lotofacil.csv'
        test_df.to_csv(test_path, index=False)
        
        try:
            data = self.predictor.load_data(test_path)
            self.assertEqual(len(data), 50)
            self.assertEqual(len(data[0]), 15)
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)


class PerformanceBenchmark:
    """Performance benchmarking for all models."""
    
    def __init__(self):
        self.test_data = TestDataGenerator.load_sample_data(500)
        self.results = {}
    
    def benchmark_model(self, model_name: str, model_func, *args, **kwargs):
        """Benchmark a specific model."""
        print(f"\n🔍 Benchmarking {model_name}...")
        
        start_time = time.time()
        try:
            result = model_func(self.test_data, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Extract prediction
            if isinstance(result, dict):
                prediction = result.get('prediction') or result.get('ensemble_prediction') or result.get('map_prediction')
            else:
                prediction = result
            
            # Basic validation
            is_valid = (
                isinstance(prediction, list) and
                len(prediction) == 15 and
                all(isinstance(x, (int, np.integer)) for x in prediction) and
                all(1 <= x <= 25 for x in prediction) and
                len(set(prediction)) == 15
            )
            
            self.results[model_name] = {
                'execution_time': execution_time,
                'prediction': prediction,
                'is_valid': is_valid,
                'confidence': result.get('confidence', 0.5) if isinstance(result, dict) else 0.5
            }
            
            print(f"   ✅ {model_name}: {execution_time:.2f}s, Valid: {is_valid}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results[model_name] = {
                'execution_time': execution_time,
                'prediction': None,
                'is_valid': False,
                'error': str(e),
                'confidence': 0.0
            }
            print(f"   ❌ {model_name}: {execution_time:.2f}s, Error: {str(e)[:50]}...")
    
    def run_all_benchmarks(self):
        """Run benchmarks for all models."""
        print("🚀 Starting performance benchmarks...")
        
        # Bayesian model
        self.benchmark_model('Bayesian', gerar_predicao_bayesiana)
        
        # Neural ensemble
        self.benchmark_model('Neural Ensemble', gerar_predicao_neural_ensemble)
        
        # Monte Carlo (with fewer simulations for speed)
        self.benchmark_model('Monte Carlo', gerar_predicao_monte_carlo, 1000, 'frequency_weighted')
        
        # Time series
        self.benchmark_model('Time Series', gerar_predicao_time_series)
        
        return self.results
    
    def generate_report(self):
        """Generate performance report."""
        print("\n" + "="*60)
        print("📊 PERFORMANCE BENCHMARK REPORT")
        print("="*60)
        
        # Sort by execution time
        sorted_results = sorted(self.results.items(), key=lambda x: x[1]['execution_time'])
        
        print(f"\n{'Model':<20} {'Time (s)':<10} {'Valid':<8} {'Confidence':<12}")
        print("-" * 50)
        
        for model_name, result in sorted_results:
            time_str = f"{result['execution_time']:.2f}"
            valid_str = "✅" if result['is_valid'] else "❌"
            conf_str = f"{result['confidence']:.3f}"
            
            print(f"{model_name:<20} {time_str:<10} {valid_str:<8} {conf_str:<12}")
        
        # Summary statistics
        valid_models = [r for r in self.results.values() if r['is_valid']]
        if valid_models:
            avg_time = np.mean([r['execution_time'] for r in valid_models])
            avg_confidence = np.mean([r['confidence'] for r in valid_models])
            
            print(f"\n📈 Summary:")
            print(f"   Valid models: {len(valid_models)}/{len(self.results)}")
            print(f"   Average execution time: {avg_time:.2f}s")
            print(f"   Average confidence: {avg_confidence:.3f}")


class StatisticalValidator:
    """Statistical validation of model predictions."""
    
    def __init__(self):
        self.test_data = TestDataGenerator.load_sample_data(200)
    
    def validate_prediction_distribution(self, predictions: List[List[int]]) -> Dict[str, float]:
        """Validate the distribution of predictions."""
        all_numbers = [num for pred in predictions for num in pred]
        number_freq = Counter(all_numbers)
        
        # Calculate statistics
        total_picks = len(all_numbers)
        expected_freq = total_picks / 25  # Expected frequency for uniform distribution
        
        # Chi-square goodness of fit test approximation
        chi_square = sum((freq - expected_freq) ** 2 / expected_freq 
                        for freq in number_freq.values())
        
        # Distribution entropy
        probs = [freq / total_picks for freq in number_freq.values()]
        entropy = -sum(p * np.log(p) for p in probs if p > 0)
        max_entropy = np.log(25)  # Maximum entropy for uniform distribution
        
        return {
            'chi_square': chi_square,
            'entropy': entropy,
            'normalized_entropy': entropy / max_entropy,
            'number_coverage': len(number_freq) / 25  # Fraction of numbers covered
        }
    
    def run_validation(self) -> Dict[str, Any]:
        """Run statistical validation."""
        print("\n🔬 Running statistical validation...")
        
        # Generate multiple predictions from different models
        predictions = []
        
        try:
            # Generate 10 predictions from Bayesian model
            for i in range(10):
                result = gerar_predicao_bayesiana(self.test_data)
                predictions.append(result['map_prediction'])
        except Exception as e:
            print(f"   ⚠️ Bayesian validation error: {e}")
        
        if predictions:
            stats = self.validate_prediction_distribution(predictions)
            
            print(f"   📊 Distribution Analysis:")
            print(f"      Chi-square statistic: {stats['chi_square']:.2f}")
            print(f"      Entropy (normalized): {stats['normalized_entropy']:.3f}")
            print(f"      Number coverage: {stats['number_coverage']:.3f}")
            
            return stats
        else:
            print("   ❌ No valid predictions for statistical analysis")
            return {}


def run_all_tests():
    """Run all test suites."""
    print("🧪 Starting comprehensive test suite...")
    
    # Unit tests
    print("\n" + "="*60)
    print("🔬 UNIT TESTS")
    print("="*60)
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestBayesianModel,
        TestNeuralEnsemble,
        TestMonteCarloModel,
        TestTimeSeriesModel,
        TestEnhancedPredictor
    ]
    
    for test_class in test_classes:
        tests = test_loader.loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run unit tests
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(test_suite)
    
    # Performance benchmarks
    print("\n" + "="*60)
    print("⚡ PERFORMANCE BENCHMARKS")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    benchmark_results = benchmark.run_all_benchmarks()
    benchmark.generate_report()
    
    # Statistical validation
    print("\n" + "="*60)
    print("📊 STATISTICAL VALIDATION")
    print("="*60)
    
    validator = StatisticalValidator()
    validation_results = validator.run_validation()
    
    # Final summary
    print("\n" + "="*60)
    print("✅ TEST SUMMARY")
    print("="*60)
    
    print(f"Unit tests: {test_result.testsRun} run, {len(test_result.failures)} failures, {len(test_result.errors)} errors")
    
    valid_benchmarks = sum(1 for r in benchmark_results.values() if r['is_valid'])
    print(f"Performance tests: {valid_benchmarks}/{len(benchmark_results)} models passed")
    
    if validation_results:
        print(f"Statistical validation: Completed")
        print(f"  - Entropy score: {validation_results.get('normalized_entropy', 0):.3f}")
        print(f"  - Coverage score: {validation_results.get('number_coverage', 0):.3f}")
    
    return {
        'unit_tests': test_result,
        'benchmarks': benchmark_results,
        'validation': validation_results
    }


if __name__ == '__main__':
    results = run_all_tests()