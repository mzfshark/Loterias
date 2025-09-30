"""
Configurações e Exemplos do Sistema de Paralelização

Este arquivo demonstra como usar o sistema de paralelização implementado
para otimizar o desempenho dos modelos de loteria.
"""

import os
import sys
from typing import Dict, Any

# Adiciona o diretório raiz ao Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Oraculo.core.parallel_engine import get_parallel_engine, ParallelConfig, reset_parallel_engines
except ImportError:
    print("⚠️ Módulo parallel_engine não encontrado. Executando simulação básica...")
    
    # Mock functions para demonstração
    class MockParallelEngine:
        def __init__(self, max_workers=2, use_processes=False):
            self.max_workers = max_workers
            self.use_processes = use_processes
        
        def parallel_predict(self, models, data, progress_callback=None):
            import time
            results = {}
            for i, (name, func) in enumerate(models.items(), 1):
                result = func(data)
                if progress_callback:
                    progress_callback(name, result, i, len(models))
                results[name] = result
                time.sleep(0.05)  # Simula paralelização
            return results
        
        def parallel_train(self, training_jobs, progress_callback=None):
            import time
            results = []
            for i, job in enumerate(training_jobs, 1):
                result = job['train_func'](job['data'], **job['params'])
                if progress_callback:
                    progress_callback(job['name'], result, i, len(training_jobs))
                results.append(result)
                time.sleep(0.05)
            return results
    
    def get_parallel_engine(max_workers=None, use_processes=False):
        return MockParallelEngine(max_workers or 2, use_processes)
    
    def reset_parallel_engines():
        pass
    
    class ParallelConfig:
        @staticmethod
        def is_parallel_enabled():
            return True

def configure_parallel_environment():
    """
    Configura o ambiente de paralelização baseado em variáveis de ambiente
    """
    # Exemplo de configurações via environment variables
    configs = {
        # Número de workers (None = auto-detect)
        'MAX_WORKERS': '4',
        
        # Habilitar/desabilitar paralelização
        'DISABLE_PARALLEL': '0',  # 0 = habilitado, 1 = desabilitado
        
        # Usar processos ao invés de threads (CPU-bound tasks)
        'USE_PROCESSES': '1',  # 0 = threads, 1 = processos
        
        # Modo rápido para CI/CD
        'FAST_CI': '0',  # 0 = completo, 1 = rápido
    }
    
    # Aplicar configurações
    for key, value in configs.items():
        os.environ[key] = value
    
    print(f"🔧 Configurações aplicadas:")
    for key, value in configs.items():
        print(f"   {key}={value}")


def example_parallel_predictions():
    """
    Exemplo de como executar predições em paralelo
    """
    print("\n📊 Exemplo: Predições Paralelas")
    print("-" * 40)
    
    # Simula modelos de predição
    def mock_predict_bayesian(data):
        import time
        time.sleep(0.1)  # Simula processamento
        return {'prediction': [1, 2, 3, 4, 5], 'confidence': 0.85}
    
    def mock_predict_neural(data):
        import time
        time.sleep(0.2)
        return {'prediction': [6, 7, 8, 9, 10], 'confidence': 0.78}
    
    def mock_predict_monte_carlo(data):
        import time
        time.sleep(0.15)
        return {'prediction': [11, 12, 13, 14, 15], 'confidence': 0.72}
    
    # Configura modelos
    models = {
        'bayesian': mock_predict_bayesian,
        'neural_ensemble': mock_predict_neural,
        'monte_carlo': mock_predict_monte_carlo,
    }
    
    # Dados de entrada
    data = [1, 2, 3, 4, 5]
    
    # Engine paralelo
    engine = get_parallel_engine(max_workers=3)
    
    # Callback para progresso
    def progress_callback(model_name: str, result: Any, completed: int, total: int):
        print(f"   ✅ {model_name}: {result['prediction']} (confiança: {result['confidence']})")
    
    # Executa predições paralelas
    start_time = time.time()
    results = engine.parallel_predict(
        models=models,
        data=data,
        progress_callback=progress_callback
    )
    elapsed = time.time() - start_time
    
    print(f"\n🎯 Resultados obtidos em {elapsed:.2f}s:")
    for model_name, result in results.items():
        if result:
            print(f"   {model_name}: {result['prediction']}")


def example_parallel_training():
    """
    Exemplo de como executar treinamentos em paralelo
    """
    print("\n🧠 Exemplo: Treinamentos Paralelos")
    print("-" * 40)
    
    # Simula funções de treinamento
    def train_model_a(data, epochs=10, lr=0.01):
        import time
        time.sleep(0.2)
        return {'model': 'ModelA', 'accuracy': 0.85, 'epochs': epochs}
    
    def train_model_b(data, epochs=15, regularization=0.1):
        import time
        time.sleep(0.3)
        return {'model': 'ModelB', 'accuracy': 0.78, 'regularization': regularization}
    
    def train_model_c(data, depth=10):
        import time
        time.sleep(0.25)
        return {'model': 'ModelC', 'accuracy': 0.82, 'depth': depth}
    
    # Configura jobs de treinamento
    training_jobs = [
        {
            'name': 'RandomForest',
            'train_func': train_model_a,
            'data': [1, 2, 3],
            'params': {'epochs': 20, 'lr': 0.005}
        },
        {
            'name': 'GradientBoosting',
            'train_func': train_model_b,
            'data': [4, 5, 6],
            'params': {'epochs': 25, 'regularization': 0.05}
        },
        {
            'name': 'MLP',
            'train_func': train_model_c,
            'data': [7, 8, 9],
            'params': {'depth': 15}
        }
    ]
    
    # Engine paralelo
    engine = get_parallel_engine(use_processes=True)  # Processos para CPU-bound
    
    # Callback para progresso
    def training_progress(job_name: str, result: Any, completed: int, total: int):
        if result:
            print(f"   ✅ {job_name}: Acurácia {result.get('accuracy', 0):.3f}")
    
    # Executa treinamentos paralelos
    start_time = time.time()
    results = engine.parallel_train(
        training_jobs=training_jobs,
        progress_callback=training_progress
    )
    elapsed = time.time() - start_time
    
    print(f"\n🎯 Treinamentos concluídos em {elapsed:.2f}s:")
    for job, result in zip(training_jobs, results):
        if result:
            print(f"   {job['name']}: {result}")


def benchmark_performance():
    """
    Benchmark comparando execução sequencial vs paralela
    """
    print("\n⚡ Benchmark: Sequencial vs Paralelo")
    print("-" * 40)
    
    import time
    
    # Simula processamento pesado
    def heavy_computation(data, delay=0.1):
        time.sleep(delay)
        return sum(data) * len(data)
    
    # Dados de teste
    test_data = [[1, 2, 3, 4, 5] for _ in range(8)]
    
    # Teste sequencial
    print("🔄 Executando sequencialmente...")
    start = time.time()
    sequential_results = []
    for i, data in enumerate(test_data):
        result = heavy_computation(data)
        sequential_results.append(result)
    sequential_time = time.time() - start
    
    # Teste paralelo
    print("🚀 Executando em paralelo...")
    
    # Prepara jobs
    parallel_jobs = []
    for i, data in enumerate(test_data):
        job = {
            'name': f'Job_{i+1}',
            'train_func': heavy_computation,
            'data': data,
            'params': {'delay': 0.1}
        }
        parallel_jobs.append(job)
    
    # Executa em paralelo
    engine = get_parallel_engine(max_workers=4)
    start = time.time()
    parallel_results = engine.parallel_train(parallel_jobs)
    parallel_time = time.time() - start
    
    # Resultados do benchmark
    speedup = sequential_time / parallel_time if parallel_time > 0 else 1
    efficiency = (speedup / engine.max_workers) * 100
    
    print(f"\n📊 Resultados do Benchmark:")
    print(f"   Tempo Sequencial: {sequential_time:.2f}s")
    print(f"   Tempo Paralelo:   {parallel_time:.2f}s")
    print(f"   Speedup:          {speedup:.2f}x")
    print(f"   Eficiência:       {efficiency:.1f}%")
    print(f"   Workers:          {engine.max_workers}")


def configuration_examples():
    """
    Exemplos de diferentes configurações de paralelização
    """
    print("\n🛠️  Exemplos de Configuração")
    print("-" * 40)
    
    # Reset engines para testar diferentes configurações
    reset_parallel_engines()
    
    # Configuração 1: Threads para I/O-bound
    print("\n1. Threads (I/O-bound tasks):")
    engine_threads = get_parallel_engine(max_workers=4, use_processes=False)
    print(f"   Workers: {engine_threads.max_workers}")
    print(f"   Tipo: {'Processos' if engine_threads.use_processes else 'Threads'}")
    
    # Reset para nova configuração
    reset_parallel_engines()
    
    # Configuração 2: Processos para CPU-bound
    print("\n2. Processos (CPU-bound tasks):")
    engine_processes = get_parallel_engine(max_workers=2, use_processes=True)
    print(f"   Workers: {engine_processes.max_workers}")
    print(f"   Tipo: {'Processos' if engine_processes.use_processes else 'Threads'}")
    
    # Configuração 3: Via variáveis de ambiente
    print("\n3. Via Environment Variables:")
    os.environ['MAX_WORKERS'] = '6'
    os.environ['USE_PROCESSES'] = '1'
    os.environ['FAST_CI'] = '1'
    
    reset_parallel_engines()
    engine_env = get_parallel_engine()
    print(f"   MAX_WORKERS={os.environ.get('MAX_WORKERS')}")
    print(f"   USE_PROCESSES={os.environ.get('USE_PROCESSES')}")
    print(f"   FAST_CI={os.environ.get('FAST_CI')}")
    print(f"   Workers Resultantes: {engine_env.max_workers}")
    print(f"   Tipo: {'Processos' if engine_env.use_processes else 'Threads'}")


def main():
    """
    Executa todos os exemplos de paralelização
    """
    print("🚀 Sistema de Paralelização - Exemplos e Testes")
    print("=" * 60)
    
    # Configuração inicial
    configure_parallel_environment()
    
    # Exemplos
    configuration_examples()
    example_parallel_predictions()
    example_parallel_training()
    benchmark_performance()
    
    print("\n✅ Todos os exemplos executados com sucesso!")
    print("\n📝 Para usar em produção:")
    print("   - Configure MAX_WORKERS baseado no seu hardware")
    print("   - Use USE_PROCESSES=1 para tarefas CPU-intensive")
    print("   - Use FAST_CI=1 em ambientes de CI/CD")
    print("   - Monitor o uso de recursos durante execução")


if __name__ == "__main__":
    import time
    main()