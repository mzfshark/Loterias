#!/usr/bin/env python3
"""
Enhanced Lotofacil Prediction System with Advanced Probabilistic Models

This script integrates multiple sophisticated probabilistic models for lottery prediction:
- Advanced Bayesian inference with Beta-Binomial conjugate priors
- Neural ensemble with Random Forest, Gradient Boosting, and MLP
- Monte Carlo simulation with multiple sampling strategies
- Time series analysis with trend, seasonal, and cyclical decomposition
- Original models: Markov chains, Poisson, mutation, beam search

Author: Enhanced AI System
"""

import pandas as pd
import numpy as np
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Importação preguiçosa (lazy) dos modelos será feita dentro dos blocos try
# para permitir que a execução degrade graciosamente caso SciPy/sklearn
# não estejam instalados no ambiente local.


class EnhancedLotofacilPredictor:
    """Enhanced predictor combining multiple probabilistic models."""
    
    def __init__(self):
        self.models = {
            'bayesian': {'weight': 0.18, 'enabled': True},
            'neural_ensemble': {'weight': 0.14, 'enabled': True},
            'monte_carlo': {'weight': 0.12, 'enabled': True},
            'time_series': {'weight': 0.20, 'enabled': True},
            'beam_search': {'weight': 0.12, 'enabled': True},
            'markov': {'weight': 0.07, 'enabled': True},
            'poisson': {'weight': 0.05, 'enabled': True},
            'mutation': {'weight': 0.12, 'enabled': True}
        }
        
        self.results = {}
        self.ensemble_confidence = 0.0
        
    def load_data(self, path: str = 'Oraculo/Lotofacil/data/Lotofacil.csv') -> List[List[int]]:
        """Load historical Lotofacil data."""
        df = pd.read_csv(path)
        # Sort by contest number (newest first)
        df = df.sort_values(by='Concurso', ascending=False).reset_index(drop=True)
        colunas = [col for col in df.columns if 'Bola' in col]
        return df[colunas].values.tolist()
    
    def run_all_models(self, data: List[List[int]]) -> Dict[str, Any]:
        """Run all enabled prediction models."""
        print("🧠 Executando todos os modelos probabilísticos...")
        
        model_results = {}
        
        # Advanced Bayesian model
        if self.models['bayesian']['enabled']:
            print("\n🎯 Modelo Bayesiano Avançado...")
            try:
                from Oraculo.Lotofacil.models.bayesian import gerar_predicao_bayesiana
                result = gerar_predicao_bayesiana(data)
                model_results['bayesian'] = {
                    'prediction': result['map_prediction'],
                    'confidence': result.get('model_evidence', 0) / -100000,  # Normalize
                    'probabilities': result['probabilities'],
                    'mcmc_prediction': result['mcmc_prediction'],
                    'credible_intervals': result['credible_intervals']
                }
                print(f"   ✅ MAP: {result['map_prediction']}")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                self.models['bayesian']['enabled'] = False
        
        # Neural Ensemble model
        if self.models['neural_ensemble']['enabled']:
            print("\n🧠 Ensemble Neural...")
            try:
                from Oraculo.Lotofacil.models.neural_ensemble import gerar_predicao_neural_ensemble
                result = gerar_predicao_neural_ensemble(data)
                model_results['neural_ensemble'] = {
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'probabilities': result['probabilities'],
                    'model_scores': result.get('model_scores', [])
                }
                print(f"   ✅ Predição: {result['prediction']}")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                self.models['neural_ensemble']['enabled'] = False
        
        # Monte Carlo simulation
        if self.models['monte_carlo']['enabled']:
            print("\n🎲 Simulação Monte Carlo...")
            try:
                from Oraculo.Lotofacil.models.monte_carlo import gerar_predicao_monte_carlo
                result = gerar_predicao_monte_carlo(data, n_simulations=3000, strategy='ensemble')
                model_results['monte_carlo'] = {
                    'prediction': result['ensemble_prediction'],
                    'confidence': result['ensemble_confidence'],
                    'voting_results': result['voting_results'],
                    'strategy_results': result['strategy_results']
                }
                print(f"   ✅ Ensemble: {result['ensemble_prediction']}")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                self.models['monte_carlo']['enabled'] = False
        
        # Time Series analysis
        if self.models['time_series']['enabled']:
            print("\n📈 Análise de Séries Temporais...")
            try:
                from Oraculo.Lotofacil.models.time_series import gerar_predicao_time_series
                result = gerar_predicao_time_series(data, sequence_length=60)
                model_results['time_series'] = {
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'probabilities': result['ensemble_probabilities'],
                    'cycles_detected': result['cycles_detected']
                }
                print(f"   ✅ Predição: {result['prediction']}")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                self.models['time_series']['enabled'] = False
        
        # Traditional models
        print("\n🔧 Modelos Tradicionais...")
        
        # Beam Search
        if self.models['beam_search']['enabled']:
            try:
                from Oraculo.Lotofacil.models import beam_search
                result = beam_search.beam_search(data)
                model_results['beam_search'] = {
                    'prediction': result[0] if result else [],
                    'confidence': 0.7,  # Default confidence
                    'all_results': result
                }
                print(f"   ✅ Beam Search: {result[0] if result else 'N/A'}")
            except Exception as e:
                print(f"   ❌ Beam Search erro: {e}")
                self.models['beam_search']['enabled'] = False
        
        # Markov Chain
        if self.models['markov']['enabled']:
            try:
                from Oraculo.Lotofacil.models import markov
                result = markov.gerar_palpite(data)
                # Convert numpy integers to regular integers
                result = [int(x) for x in result]
                model_results['markov'] = {
                    'prediction': result,
                    'confidence': 0.6,  # Default confidence
                }
                print(f"   ✅ Markov: {result}")
            except Exception as e:
                print(f"   ❌ Markov erro: {e}")
                self.models['markov']['enabled'] = False
        
        # Poisson
        if self.models['poisson']['enabled']:
            try:
                from Oraculo.Lotofacil.models import poisson
                result = poisson.gerar_combinacao_poisson(pd.DataFrame(data))
                model_results['poisson'] = {
                    'prediction': result,
                    'confidence': 0.65,  # Default confidence
                }
                print(f"   ✅ Poisson: {result}")
            except Exception as e:
                print(f"   ❌ Poisson erro: {e}")
                self.models['poisson']['enabled'] = False
        
        # Mutation (Genetic Algorithm)
        if self.models['mutation']['enabled']:
            try:
                from Oraculo.Lotofacil.models import mutation
                result = mutation.gerar_mutacoes(data, num_mutantes=5)
                # Take the first mutation as the primary prediction
                primary_prediction = result[0] if result else []
                model_results['mutation'] = {
                    'prediction': primary_prediction,
                    'confidence': 0.6,  # Default confidence
                    'all_mutations': result
                }
                print(f"   ✅ Mutation: {primary_prediction}")
            except Exception as e:
                print(f"   ❌ Mutation erro: {e}")
                self.models['mutation']['enabled'] = False
        
        return model_results
    
    def calculate_ensemble_prediction(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weighted ensemble prediction."""
        print("\n🎯 Calculando predição ensemble...")
        
        # Collect all predictions with weights
        weighted_votes = Counter()
        total_weight = 0
        confidence_scores = []
        
        for model_name, result in model_results.items():
            if self.models[model_name]['enabled'] and 'prediction' in result:
                weight = self.models[model_name]['weight']
                prediction = result['prediction']
                confidence = result.get('confidence', 0.5)
                
                # Adjust weight by confidence
                adjusted_weight = weight * (0.5 + confidence * 0.5)
                
                # Vote for each number in the prediction
                for number in prediction:
                    weighted_votes[number] += adjusted_weight
                
                total_weight += adjusted_weight
                confidence_scores.append(confidence)
        
        # Select top 15 numbers based on weighted votes
        most_voted = weighted_votes.most_common(15)
        ensemble_prediction = sorted([num for num, _ in most_voted])
        
        # Calculate ensemble confidence
        ensemble_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        
        # Calculate voting strength
        voting_strength = {}
        for num, votes in weighted_votes.items():
            voting_strength[num] = votes / total_weight if total_weight > 0 else 0
        
        return {
            'ensemble_prediction': ensemble_prediction,
            'ensemble_confidence': ensemble_confidence,
            'voting_results': most_voted,
            'voting_strength': voting_strength,
            'total_weight': total_weight,
            'model_count': len([m for m in self.models.values() if m['enabled']])
        }
    
    def generate_comprehensive_analysis(self, data: List[List[int]], 
                                      model_results: Dict[str, Any],
                                      ensemble_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis of all results."""
        
        # Frequency analysis
        all_numbers = [num for game in data for num in game]
        frequency_analysis = Counter(all_numbers)
        total_appearances = sum(frequency_analysis.values())
        
        # Recent trends (last 50 games)
        recent_numbers = [num for game in data[:50] for num in game]
        recent_analysis = Counter(recent_numbers)
        
        # Pattern analysis
        consecutive_patterns = []
        sum_patterns = []
        
        for game in data[:100]:  # Analyze last 100 games
            sorted_game = sorted(game)
            
            # Consecutive numbers
            consecutive = sum(1 for i in range(len(sorted_game) - 1) 
                            if sorted_game[i+1] - sorted_game[i] == 1)
            consecutive_patterns.append(consecutive)
            
            # Game sum
            sum_patterns.append(sum(game))
        
        # Model agreement analysis
        all_predictions = [result['prediction'] for result in model_results.values() 
                         if 'prediction' in result]
        
        number_consensus = Counter()
        for prediction in all_predictions:
            for num in prediction:
                number_consensus[num] += 1
        
        # Calculate consensus strength
        max_consensus = len(all_predictions)
        consensus_strength = {num: count / max_consensus 
                            for num, count in number_consensus.items()}
        
        return {
            'frequency_analysis': dict(frequency_analysis),
            'recent_trends': dict(recent_analysis),
            'pattern_analysis': {
                'avg_consecutive': np.mean(consecutive_patterns),
                'avg_sum': np.mean(sum_patterns),
                'sum_std': np.std(sum_patterns)
            },
            'model_consensus': dict(number_consensus),
            'consensus_strength': consensus_strength, 
            'high_confidence_numbers': [num for num, strength in consensus_strength.items() 
                                      if strength >= 0.5],
            'total_games_analyzed': len(data)
        }
    
    def save_results(self, all_results: Dict[str, Any], output_path: str = 'Oraculo/Lotofacil/predictions'):
        """Save all results to files."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Create output directory
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_path = f"{output_path}/enhanced_prediction_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
        
        # Save CSV with predictions
        csv_path = f"{output_path}/enhanced_prediction_{timestamp}.csv"
        csv_data = []
        
        # Add ensemble prediction
        ensemble_pred = all_results['ensemble_result']['ensemble_prediction']
        row = {f'Bola{i+1}': num for i, num in enumerate(ensemble_pred)}
        row['modelo'] = 'enhanced_ensemble'
        row['confidence'] = all_results['ensemble_result']['ensemble_confidence']
        csv_data.append(row)
        
        # Add individual model predictions
        for model_name, result in all_results['model_results'].items():
            if 'prediction' in result and result['prediction']:
                pred = result['prediction']
                row = {f'Bola{i+1}': pred[i] if i < len(pred) else '' 
                      for i in range(15)}
                row['modelo'] = model_name
                row['confidence'] = result.get('confidence', 0.5)
                csv_data.append(row)
        
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)
        
        print(f"\n💾 Resultados salvos:")
        print(f"   📄 JSON: {json_path}")
        print(f"   📊 CSV: {csv_path}")
        
        return json_path, csv_path
    
    def run_complete_analysis(self, data_path: str = 'Oraculo/Lotofacil/data/Lotofacil.csv'):
        """Run complete enhanced analysis."""
        print("🚀 Iniciando análise completa aprimorada do Lotofácil...")
        
        # Load data
        data = self.load_data(data_path)
        print(f"📊 Dados carregados: {len(data)} jogos históricos")
        
        # Run all models
        model_results = self.run_all_models(data)
        
        # Calculate ensemble prediction
        ensemble_result = self.calculate_ensemble_prediction(model_results)
        
        # Generate comprehensive analysis
        comprehensive_analysis = self.generate_comprehensive_analysis(
            data, model_results, ensemble_result
        )
        
        # Compile all results
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'total_games': len(data),
                'latest_contest': 'N/A',  # Could be extracted from data
                'models_used': [name for name, config in self.models.items() if config['enabled']]
            },
            'ensemble_result': ensemble_result,
            'model_results': model_results,
            'comprehensive_analysis': comprehensive_analysis,
            'model_weights': {name: config['weight'] for name, config in self.models.items()}
        }
        
        # Save results
        json_path, csv_path = self.save_results(all_results)
        
        # Display summary
        self.display_summary(all_results)
        
        return all_results
    
    def display_summary(self, results: Dict[str, Any]):
        """Display summary of results."""
        ensemble = results['ensemble_result']
        analysis = results['comprehensive_analysis']
        
        print("\n" + "="*80)
        print("🎯 RESUMO DA ANÁLISE PROBABILÍSTICA APRIMORADA")
        print("="*80)
        
        print(f"\n🏆 PREDIÇÃO ENSEMBLE FINAL:")
        print(f"   Números: {ensemble['ensemble_prediction']}")
        print(f"   Confiança: {ensemble['ensemble_confidence']:.4f}")
        print(f"   Modelos utilizados: {ensemble['model_count']}")
        
        print(f"\n📊 TOP 10 NÚMEROS COM MAIOR CONSENSO:")
        consensus = sorted(analysis['consensus_strength'].items(), 
                         key=lambda x: x[1], reverse=True)
        for i, (num, strength) in enumerate(consensus[:10]):
            print(f"   {i+1:2d}. Número {num:2d}: {strength:.3f} ({strength*100:.1f}% dos modelos)")
        
        print(f"\n🔥 NÚMEROS DE ALTA CONFIANÇA (>50% consenso):")
        high_conf = analysis['high_confidence_numbers']
        if high_conf:
            print(f"   {sorted(high_conf)}")
        else:
            print("   Nenhum número com consenso > 50%")
        
        print(f"\n📈 ANÁLISE DE PADRÕES:")
        patterns = analysis['pattern_analysis']
        print(f"   Média de números consecutivos: {patterns['avg_consecutive']:.2f}")
        print(f"   Soma média dos jogos: {patterns['avg_sum']:.1f} ± {patterns['sum_std']:.1f}")
        
        print(f"\n🎲 PREDIÇÕES POR MODELO:")
        for model_name, result in results['model_results'].items():
            if 'prediction' in result:
                pred = result['prediction']
                conf = result.get('confidence', 0.5)
                weight = results['model_weights'].get(model_name, 0)
                print(f"   {model_name:15s}: {pred} (conf: {conf:.3f}, peso: {weight:.2f})")
        
        print("\n" + "="*80)


def main():
    """Main execution function."""
    predictor = EnhancedLotofacilPredictor()
    
    try:
        results = predictor.run_complete_analysis()
        return results
    except KeyboardInterrupt:
        print("\n⏹️ Análise interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    results = main()