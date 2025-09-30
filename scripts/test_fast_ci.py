#!/usr/bin/env python3
"""
Script para testar se FAST_CI está funcionando corretamente em todos os jogos
"""

import subprocess
import os

def test_fast_ci():
    games = ['SuperSete', 'Lotofacil', 'MegaSena', 'Quina', 'Milionaria']
    
    print("🧪 Testando configuração FAST_CI em todos os jogos...\n")
    
    for game in games:
        print(f"📊 Testando {game}:")
        
        # Teste com FAST_CI=0 (modo completo)
        try:
            result = subprocess.run(
                [
                    'python3', 
                    f'Oraculo/{game}/scripts/enhanced_predict.py'
                ],
                env={**os.environ, 'FAST_CI': '0'},
                capture_output=True,
                text=True,
                timeout=30,
                cwd='/mnt/d/Rede/Github/mzfshark/Loterias'
            )
            
            if "🔍 Modo completo" in result.stdout:
                print(f"  ✅ FAST_CI=0: Modo completo detectado")
            else:
                print(f"  ❌ FAST_CI=0: Modo completo NÃO detectado")
                print(f"     Output: {result.stdout[:100]}...")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ FAST_CI=0: Timeout (normal - script completo)")
        except Exception as e:
            print(f"  ❌ FAST_CI=0: Erro: {e}")
        
        # Teste com FAST_CI=1 (modo rápido)
        try:
            result = subprocess.run(
                [
                    'python3', 
                    f'Oraculo/{game}/scripts/enhanced_predict.py'
                ],
                env={**os.environ, 'FAST_CI': '1'},
                capture_output=True,
                text=True,
                timeout=20,
                cwd='/mnt/d/Rede/Github/mzfshark/Loterias'
            )
            
            if "⚡ Modo FAST_CI ativo" in result.stdout:
                print(f"  ✅ FAST_CI=1: Modo rápido detectado")
            else:
                print(f"  ❌ FAST_CI=1: Modo rápido NÃO detectado")
                print(f"     Output: {result.stdout[:100]}...")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ FAST_CI=1: Timeout (pode indicar problema)")
        except Exception as e:
            print(f"  ❌ FAST_CI=1: Erro: {e}")
        
        print()

if __name__ == "__main__":
    test_fast_ci()
    print("🎯 Teste de FAST_CI concluído!")