#!/usr/bin/env python3
"""Teste de validação das correções implementadas"""

import os
import sys
import time
import logging

# Configurar ambiente
os.environ['MAX_WORKERS'] = '4'
os.environ['USE_PROCESSES'] = '0'  # Threads
os.environ['FAST_CI'] = '0'       # Modo completo

# Adicionar path do Oraculo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Oraculo'))

from Oraculo.common.models.neural_ensemble import NeuralEnsembleLotofacil
from Oraculo.common.models.monte_carlo import MonteCarloLotofacilSimulator
import pandas as pd
import numpy as np

def test_neural_ensemble():
    """Teste do Neural Ensemble corrigido"""
    print("🧠 Testando Neural Ensemble...")
    
    try:
        model = NeuralEnsembleLotofacil()
        print(f"✅ Inicialização OK - model_scores: {hasattr(model, 'model_scores')}")
        
        # Dados sintéticos para teste
        historical_data = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] for _ in range(100)]
        
        # Varia alguns números para criar diversidade
        for i in range(len(historical_data)):
            # Varia até 3 números por jogo
            for _ in range(np.random.randint(1, 4)):
                pos = np.random.randint(0, 15)
                historical_data[i][pos] = np.random.randint(1, 26)
        
        result = model.predict_probabilities(historical_data, lookback=50)
        print(f"✅ Neural Ensemble funcionou! Resultado: {len(result)} números")
        return True
        
    except Exception as e:
        print(f"❌ Neural Ensemble falhou: {e}")
        return False

def test_monte_carlo():
    """Teste do Monte Carlo paralelo"""
    print("🎲 Testando Monte Carlo...")
    
    try:
        model = MonteCarloLotofacilSimulator(n_simulations=100)
        
        # Dados sintéticos
        historical_data = []
        for i in range(100):
            game = np.random.choice(range(1, 26), 15, replace=False).tolist()
            historical_data.append(sorted(game))
        
        model.load_historical_data(historical_data)
        result = model.run_monte_carlo_simulation('uniform')
        
        print(f"✅ Monte Carlo funcionou! Resultado: {len(result)} números")
        return True
        
    except Exception as e:
        print(f"❌ Monte Carlo falhou: {e}")
        return False

def main():
    """Teste completo das correções"""
    print("🔧 Validando correções implementadas...")
    
    results = []
    
    # Teste Neural Ensemble
    results.append(test_neural_ensemble())
    
    # Teste Monte Carlo  
    results.append(test_monte_carlo())
    
    success_count = sum(results)
    total_tests = len(results)
    
    print(f"\n📊 Resultado dos testes: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 TODAS AS CORREÇÕES FUNCIONANDO!")
        return True
    else:
        print("⚠️ Ainda há problemas pendentes")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)