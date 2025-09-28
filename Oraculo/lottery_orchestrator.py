#!/usr/bin/env python3
"""
Unified Lottery Prediction Orchestrator

This script provides a unified interface to run predictions across all supported
lottery games using the modular architecture.

Usage:
    python lottery_orchestrator.py --game megasena
    python lottery_orchestrator.py --game all
    python lottery_orchestrator.py --game lotofacil --models bayesian,monte_carlo

Author: Enhanced AI System
"""

import sys
import os
import argparse
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.lottery_configs import list_supported_lotteries, get_config


def run_lottery_prediction(lottery_name: str, selected_models: List[str] = None) -> Dict[str, Any]:
    """
    Run prediction for a specific lottery game.
    
    Args:
        lottery_name: Name of the lottery game
        selected_models: List of specific models to run (optional, runs all if None)
        
    Returns:
        Dictionary with prediction results
    """
    print(f"\n🎯 Executando predições para {lottery_name.upper()}...")
    
    try:
        if lottery_name.lower() == 'lotofacil':
            from Lotofacil.scripts.enhanced_predict import EnhancedLotofacilPredictor
            predictor = EnhancedLotofacilPredictor()
        elif lottery_name.lower() == 'megasena':
            from MegaSena.scripts.enhanced_predict import EnhancedMegaSenaPredictor
            predictor = EnhancedMegaSenaPredictor()
        elif lottery_name.lower() == 'quina':
            from Quina.scripts.enhanced_predict import EnhancedQuinaPredictor
            predictor = EnhancedQuinaPredictor()
        elif lottery_name.lower() == 'milionaria':
            from Milionaria.scripts.enhanced_predict import EnhancedMilionariaPredictor
            predictor = EnhancedMilionariaPredictor()
        elif lottery_name.lower() == 'supersete':
            from SuperSete.scripts.enhanced_predict import EnhancedSuperSetePredictor
            predictor = EnhancedSuperSetePredictor()
        else:
            raise ValueError(f"Unsupported lottery: {lottery_name}")
        
        # Disable specific models if requested
        if selected_models:
            for model_name in predictor.models:
                if model_name not in selected_models:
                    predictor.models[model_name]['enabled'] = False
        
        # Run prediction
        results = predictor.run_complete_analysis()
        
        return {
            'lottery': lottery_name,
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erro ao executar {lottery_name}: {e}")
        return {
            'lottery': lottery_name,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_all_lotteries(selected_models: List[str] = None) -> Dict[str, Any]:
    """
    Run predictions for all supported lottery games.
    
    Args:
        selected_models: List of specific models to run (optional)
        
    Returns:
        Dictionary with all prediction results
    """
    print("🚀 Executando predições para todas as loterias...")
    
    results = {}
    supported_lotteries = list_supported_lotteries()
    
    for lottery in supported_lotteries:
        result = run_lottery_prediction(lottery, selected_models)
        results[lottery] = result
    
    # Summary
    successful = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMO GERAL - {successful}/{total} LOTERIAS EXECUTADAS COM SUCESSO")
    print(f"{'='*80}")
    
    for lottery, result in results.items():
        status = "✅" if result.get('success') else "❌"
        print(f"{status} {lottery.upper()}")
        
        if result.get('success') and 'results' in result:
            ensemble_pred = result['results'].get('ensemble_prediction', [])
            ensemble_conf = result['results'].get('ensemble_confidence', 0.0)
            print(f"   🎯 Predição: {ensemble_pred}")
            print(f"   📊 Confiança: {ensemble_conf:.1%}")
        elif not result.get('success'):
            print(f"   ❌ Erro: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*80}")
    
    return results


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Unified Lottery Prediction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --game megasena
    %(prog)s --game all
    %(prog)s --game lotofacil --models bayesian,monte_carlo
    %(prog)s --list-games
    %(prog)s --list-models
        """
    )
    
    parser.add_argument(
        '--game', '-g',
        choices=list_supported_lotteries() + ['all'],
        help='Lottery game to run predictions for'
    )
    
    parser.add_argument(
        '--models', '-m',
        type=str,
        help='Comma-separated list of models to run (e.g., bayesian,monte_carlo)'
    )
    
    parser.add_argument(
        '--list-games',
        action='store_true',
        help='List all supported lottery games'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all available prediction models'
    )
    
    args = parser.parse_args()
    
    if args.list_games:
        print("🎲 Supported lottery games:")
        for game in list_supported_lotteries():
            config = get_config(game)
            print(f"   • {game.upper()}: {config.numbers_per_game} numbers from {config.min_number}-{config.max_number}")
            if config.has_bonus_numbers:
                print(f"     + {config.bonus_count} bonus numbers from {config.bonus_range[0]}-{config.bonus_range[1]}")
        return
    
    if args.list_models:
        print("🧠 Available prediction models:")
        models = ['bayesian', 'neural_ensemble', 'monte_carlo', 'time_series', 
                 'markov', 'poisson', 'mutation', 'beam_search']
        for model in models:
            print(f"   • {model}")
        return
    
    if not args.game:
        parser.print_help()
        return
    
    # Parse selected models
    selected_models = None
    if args.models:
        selected_models = [m.strip() for m in args.models.split(',')]
        print(f"🎯 Modelos selecionados: {selected_models}")
    
    # Run predictions
    if args.game == 'all':
        results = run_all_lotteries(selected_models)
    else:
        result = run_lottery_prediction(args.game, selected_models)
        results = {args.game: result}
    
    return results


if __name__ == "__main__":
    main()