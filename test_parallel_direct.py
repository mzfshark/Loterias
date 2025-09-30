#!/usr/bin/env python3
"""Teste do sistema paralelo usando chamada direta"""

import os
import sys
import subprocess
import time

def test_parallel_system():
    """Testa o sistema paralelo chamando o orchestrator diretamente"""
    print("🎯 Testando sistema paralelo via orchestrator...")
    
    # Configurar para modo rápido e threads
    env = os.environ.copy()
    env.update({
        'MAX_WORKERS': '6',
        'USE_PROCESSES': '0',  # Threads
        'FAST_CI': '1',        # Modo rápido
        'PYTHONPATH': '/mnt/d/Rede/Github/mzfshark/Loterias'
    })
    
    start_time = time.time()
    
    try:
        # Executar o orchestrator com timeout
        result = subprocess.run([
            'python3', 'Oraculo/lottery_orchestrator.py', 
            '--game', 'lotofacil'
        ], 
        cwd='/mnt/d/Rede/Github/mzfshark/Loterias',
        env=env,
        timeout=30,  # 30 segundos timeout
        capture_output=True,
        text=True
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            output = result.stdout
            
            # Contar sucessos
            success_count = output.count('✅') - output.count('✅ Treinamento')
            if "sucessos" in output:
                # Extrair número de sucessos do formato "X/Y sucessos"
                import re
                match = re.search(r'(\d+)/(\d+) sucessos', output)
                if match:
                    success_count = int(match.group(1))
                    total_count = int(match.group(2))
                    
                    print(f"🎯 Sistema executado em {elapsed:.2f}s")
                    print(f"✅ Sucessos: {success_count}/{total_count} modelos")
                    
                    if success_count >= 4:  # Pelo menos 4 modelos funcionando
                        print("🎉 SISTEMA PARALELO FUNCIONANDO!")
                        return True
                    else:
                        print("⚠️ Poucos modelos funcionando")
                        return False
        
        print("❌ Erro na execução")
        print("STDOUT:", result.stdout[:500])  # Primeiras 500 chars
        print("STDERR:", result.stderr[:500])
        return False
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - sistema demorou mais de 30s")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = test_parallel_system()
    exit(0 if success else 1)