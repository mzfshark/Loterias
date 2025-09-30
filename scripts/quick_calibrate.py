#!/usr/bin/env python3
"""
Calibrador rápido para workflows de CI/CD
Versão otimizada do auto_calibrator apenas para ajustes básicos durante builds
"""

import os
import sys
import json
from pathlib import Path

# Adiciona raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def quick_calibrate():
    """Calibração rápida apenas para verificar se o sistema está funcionando"""
    
    print("⚡ Iniciando calibração rápida...")
    
    # Lista dos jogos
    games = ['Lotofacil', 'SuperSete', 'MegaSena', 'Quina', 'Milionaria']
    
    for game in games:
        game_dir = Path(f"Oraculo/{game}")
        weights_file = game_dir / "models" / "weights.auto.json"
        
        # Cria diretório se não existe
        weights_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Pesos padrão balanceados
        default_weights = {
            "bayesian": 0.15,
            "neural_ensemble": 0.12,
            "monte_carlo": 0.10,
            "time_series": 0.14,
            "beam_search": 0.13,
            "markov": 0.12,
            "poisson": 0.12,
            "mutation": 0.12
        }
        
        # Se arquivo já existe, apenas verifica
        if weights_file.exists():
            try:
                with open(weights_file, 'r') as f:
                    existing = json.load(f)
                print(f"  ✅ {game}: pesos existentes mantidos ({len(existing)} modelos)")
                continue
            except:
                pass
        
        # Salva pesos padrão
        with open(weights_file, 'w') as f:
            json.dump(default_weights, f, indent=2)
        
        print(f"  ✅ {game}: pesos padrão aplicados ({len(default_weights)} modelos)")
    
    print("⚡ Calibração rápida concluída!")
    return True

if __name__ == "__main__":
    try:
        quick_calibrate()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro na calibração rápida: {e}")
        sys.exit(1)