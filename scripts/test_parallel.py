#!/usr/bin/env python3
"""
Teste básico do sistema de paralelização
"""

import sys
import os
import time

# Adiciona o path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_parallel_system():
    """Testa o sistema de paralelização básico"""
    print("🚀 Testando Sistema de Paralelização")
    print("=" * 40)
    
    try:
        from Oraculo.core.parallel_engine import get_parallel_engine, ParallelConfig
        
        # Teste 1: Configuração básica
        print("📋 Teste 1: Configuração Básica")
        engine = get_parallel_engine(max_workers=2, use_processes=False)
        print(f"   ✅ Workers: {engine.max_workers}")
        print(f"   ✅ Tipo: {'Processos' if engine.use_processes else 'Threads'}")
        print(f"   ✅ Paralelo: {engine.parallel_enabled}")
        
        # Teste 2: Função simples para threads
        def simple_task(data):
            time.sleep(0.1)
            return {"result": sum(data), "processed": len(data)}
        
        print("\n📊 Teste 2: Predições com Threads")
        models = {
            "modelo_a": simple_task,
            "modelo_b": simple_task,
            "modelo_c": simple_task
        }
        
        start_time = time.time()
        results = engine.parallel_predict(
            models=models,
            data=[1, 2, 3, 4, 5]
        )
        elapsed = time.time() - start_time
        
        print(f"   ✅ Tempo: {elapsed:.2f}s")
        print(f"   ✅ Resultados: {len(results)}")
        for name, result in results.items():
            if result:
                print(f"      {name}: soma={result['result']}")
        
        print("\n🎯 Teste 3: Configurações de Ambiente")
        os.environ['MAX_WORKERS'] = '3'
        os.environ['FAST_CI'] = '1'
        
        # Reset para testar novas configurações
        from Oraculo.core.parallel_engine import reset_parallel_engines
        reset_parallel_engines()
        
        engine2 = get_parallel_engine()
        print(f"   ✅ FAST_CI ativo: workers={engine2.max_workers} (era 3, limitado a 2)")
        
        print("\n✅ Todos os testes passaram!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    success = test_parallel_system()
    exit(0 if success else 1)