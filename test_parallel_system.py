#!/usr/bin/env python3
"""Teste completo do sistema paralelo"""

import sys
import os
import time

# Configurar ambiente
os.environ['MAX_WORKERS'] = '6'
os.environ['USE_PROCESSES'] = '0'  # Use threads
os.environ['FAST_CI'] = '0'

# Adicionar path do Oraculo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Oraculo'))

from Oraculo.core.base_predictor import BaseLotteryPredictor
from Oraculo.core.lottery_configs import get_config
import pandas as pd

def test_all_models():
    """Teste todos os modelos disponíveis"""
    print("🎯 Testando sistema paralelo completo...")
    
    # Configurar loteria
    config = get_config('lotofacil')
    
    # Carregar dados
    csv_path = "Oraculo/Lotofacil/data/Lotofacil.csv"
    if not os.path.exists(csv_path):
        print("❌ Dados da Lotofacil não encontrados")
        return False
    
    df = pd.read_csv(csv_path)
    historical_data = df.iloc[:, 1:16].values.tolist()  # Todos os jogos
    
    print(f"📊 Dados carregados: {len(historical_data)} jogos históricos")
    
    # Usar diretamente a implementação da Lotofacil
    from Oraculo.Lotofacil.scripts.predict import LotofacilPredictor
    predictor = LotofacilPredictor()
    
    try:
        start_time = time.time()
        
        # Executar predições
        predictions = predictor.run_models_ensemble(historical_data)
        
        elapsed = time.time() - start_time
        
        # Contar sucessos
        successful_models = [name for name, pred in predictions.items() 
                           if pred is not None and len(pred) == config['numbers_per_game']]
        
        print(f"🎯 Predições concluídas em {elapsed:.2f}s")
        print(f"✅ Sucessos: {len(successful_models)}/{len(predictions)} modelos")
        print(f"🧠 Modelos bem-sucedidos: {', '.join(successful_models)}")
        
        if len(successful_models) >= 5:  # Pelo menos 5 modelos funcionando
            print("🎉 SISTEMA PARALELO FUNCIONANDO!")
            return True
        else:
            print("⚠️ Poucos modelos funcionando")
            return False
            
    except Exception as e:
        print(f"❌ Erro no sistema paralelo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_models()
    exit(0 if success else 1)