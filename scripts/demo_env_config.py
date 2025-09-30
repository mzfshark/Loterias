#!/usr/bin/env python3
"""
Demonstração do Sistema de Configuração com .env

Este script mostra como usar arquivos .env para configurar
o sistema de paralelização.
"""

import sys
import os
from pathlib import Path

# Adiciona o path do projeto
sys.path.append(str(Path(__file__).parent.parent))

def demo_env_config():
    """Demonstra o carregamento de configurações do .env"""
    
    print("🔧 Sistema de Configuração com .env")
    print("=" * 50)
    
    try:
        from Oraculo.core.env_config import get_env_config, reload_config
        from Oraculo.core.parallel_engine import get_parallel_engine, ParallelConfig
        
        # Carrega configurações
        print("📋 Carregando configurações...")
        config = get_env_config()
        
        # Exibe configurações
        print(f"\n📁 Arquivo .env: {config.env_file or 'Não encontrado'}")
        config.print_config()
        
        # Valida configurações
        print(f"\n✅ Configurações válidas: {config.validate_config()}")
        
        # Testa engine paralelo
        print(f"\n🚀 Testando ParallelEngine...")
        engine = get_parallel_engine()
        
        print(f"   Workers: {engine.max_workers}")
        print(f"   Tipo: {'Processos' if engine.use_processes else 'Threads'}")
        print(f"   Paralelo: {engine.parallel_enabled}")
        print(f"   FAST_CI: {engine.fast_ci}")
        print(f"   Timeout Predição: {engine.timeout_predict}s")
        print(f"   Timeout Treinamento: {engine.timeout_train}s")
        
        # Teste com configurações específicas
        print(f"\n🎯 Valores específicos do .env:")
        print(f"   MAX_WORKERS: {config.get_int('MAX_WORKERS', 'auto')}")
        print(f"   USE_PROCESSES: {config.get_bool('USE_PROCESSES')}")
        print(f"   DISABLE_PARALLEL: {config.get_bool('DISABLE_PARALLEL')}")
        print(f"   FAST_CI: {config.get_bool('FAST_CI')}")
        print(f"   LOG_LEVEL: {config.get_str('LOG_LEVEL', 'INFO')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def create_sample_env_files():
    """Cria arquivos .env de exemplo"""
    
    project_root = Path(__file__).parent.parent
    
    # .env para desenvolvimento
    dev_env = project_root / '.env.development'
    dev_config = """# Configuração para Desenvolvimento Local
MAX_WORKERS=8
USE_PROCESSES=1
DISABLE_PARALLEL=0
FAST_CI=0
LOG_LEVEL=DEBUG
PARALLEL_DEBUG=1

# Monte Carlo com mais simulações
MONTE_CARLO_SIMULATIONS=5000

# Neural com configuração completa
NEURAL_MAX_ITER=2000
NEURAL_EARLY_STOPPING=1
"""
    
    # .env para CI/CD
    ci_env = project_root / '.env.ci'
    ci_config = """# Configuração para CI/CD (GitHub Actions)
MAX_WORKERS=2
USE_PROCESSES=0
DISABLE_PARALLEL=0
FAST_CI=1
LOG_LEVEL=INFO
PARALLEL_DEBUG=0

# Configurações rápidas
MONTE_CARLO_SIMULATIONS=100
NEURAL_MAX_ITER=200
PARALLEL_TIMEOUT_PREDICT=60
PARALLEL_TIMEOUT_TRAIN=120
"""
    
    # .env para produção
    prod_env = project_root / '.env.production'
    prod_config = """# Configuração para Produção
MAX_WORKERS=6
USE_PROCESSES=1
DISABLE_PARALLEL=0
FAST_CI=0
LOG_LEVEL=INFO
PARALLEL_DEBUG=0

# Configurações otimizadas
MONTE_CARLO_SIMULATIONS=10000
NEURAL_MAX_ITER=1000
PARALLEL_TIMEOUT_PREDICT=600
PARALLEL_TIMEOUT_TRAIN=1800
"""
    
    # Salva arquivos
    examples = [
        (dev_env, dev_config, "Desenvolvimento"),
        (ci_env, ci_config, "CI/CD"),
        (prod_env, prod_config, "Produção")
    ]
    
    print("\n📝 Criando arquivos .env de exemplo...")
    
    for file_path, content, desc in examples:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ {file_path.name} ({desc})")
        except Exception as e:
            print(f"   ❌ Erro criando {file_path.name}: {e}")
    
    print(f"\n💡 Para usar um arquivo específico:")
    print(f"   cp .env.development .env")
    print(f"   # ou")
    print(f"   ENV_FILE=.env.production python3 scripts/predict.py")

def demo_dynamic_config():
    """Demonstra mudança dinâmica de configuração"""
    
    print(f"\n🔄 Demonstração de Configuração Dinâmica")
    print("-" * 40)
    
    try:
        from Oraculo.core.env_config import reload_config
        from Oraculo.core.parallel_engine import reset_parallel_engines, get_parallel_engine
        
        # Configuração 1: Padrão
        print("1️⃣ Configuração padrão (.env)")
        engine1 = get_parallel_engine()
        print(f"   Workers: {engine1.max_workers}, Processos: {engine1.use_processes}")
        
        # Configuração 2: Forçar variável de ambiente
        print("\n2️⃣ Sobrescrevendo com variável de ambiente")
        os.environ['MAX_WORKERS'] = '12'
        os.environ['USE_PROCESSES'] = '1'
        
        # Reset necessário para aplicar mudanças
        reset_parallel_engines()
        reload_config()
        
        engine2 = get_parallel_engine()
        print(f"   Workers: {engine2.max_workers}, Processos: {engine2.use_processes}")
        
        # Configuração 3: Parâmetros diretos (sobrescreve tudo)
        print("\n3️⃣ Parâmetros diretos (prioridade máxima)")
        reset_parallel_engines()
        
        engine3 = get_parallel_engine(max_workers=4, use_processes=False)
        print(f"   Workers: {engine3.max_workers}, Processos: {engine3.use_processes}")
        
        print(f"\n📊 Ordem de prioridade:")
        print(f"   1. Parâmetros diretos da função")
        print(f"   2. Variáveis de ambiente do sistema")
        print(f"   3. Arquivo .env")
        print(f"   4. Valores padrão")
        
    except Exception as e:
        print(f"❌ Erro na demonstração dinâmica: {e}")

def main():
    """Executa todas as demonstrações"""
    
    # Demonstração principal
    success = demo_env_config()
    
    if success:
        # Cria arquivos de exemplo
        create_sample_env_files()
        
        # Demonstração dinâmica
        demo_dynamic_config()
        
        print(f"\n✅ Sistema de configuração .env funcionando!")
        print(f"\n📖 Documentação:")
        print(f"   - .env.example: Template completo")
        print(f"   - .env.development: Para desenvolvimento")
        print(f"   - .env.ci: Para GitHub Actions")
        print(f"   - .env.production: Para produção")
        
    else:
        print(f"\n❌ Falha na demonstração do sistema .env")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())