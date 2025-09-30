#!/usr/bin/env python3
"""Teste rápido do sistema de paralellização Monte Carlo"""

import sys
import os

# Adicionar path do Oraculo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Oraculo'))

from Oraculo.common.models.monte_carlo import MonteCarloLotofacil
import pandas as pd

def test_monte_carlo_parallel():
    # Carregar dados básicos
    csv_path = "Oraculo/Lotofacil/data/Lotofacil.csv"
    if not os.path.exists(csv_path):
        print("❌ Dados da Lotofacil não encontrados")
        return
    
    df = pd.read_csv(csv_path)
    recent_games = df.iloc[-100:].values[:, 1:16].tolist()  # Últimos 100 jogos
    
    print(f"🎯 Testando Monte Carlo com {len(recent_games)} jogos históricos...")
    
    # Teste do modelo
    model = MonteCarloLotofacil()
    
    try:
        prediction = model.predict_probabilities(recent_games, lookback=50)
        print(f"✅ Monte Carlo paralelo funcionou!")
        print(f"📊 Predição: {sorted(prediction)}")
        return True
    except Exception as e:
        print(f"❌ Erro no Monte Carlo: {e}")
        return False

if __name__ == "__main__":
    test_monte_carlo_parallel()