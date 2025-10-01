"""
Sistema de Paralelização para Modelos de Loteria

Este módulo fornece capacidade de execução paralela para treinamento e predição
dos modelos de loteria, otimizando o uso de recursos computacionais.
"""

import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, Tuple
import numpy as np
import time
import logging
from contextlib import contextmanager
import os

# Configuração de ambiente com suporte a .env
try:
    from .env_config import get_env_config
    env_config = get_env_config()
except ImportError:
    # Fallback se env_config não estiver disponível
    class MockEnvConfig:
        def get_int(self, key: str, default: int = 0) -> int:
            try:
                return int(os.environ.get(key, str(default)))
            except (ValueError, TypeError):
                return default
        
        def get_bool(self, key: str, default: bool = False) -> bool:
            value = os.environ.get(key, '').lower().strip()
            return value in {'1', 'true', 'yes', 'on', 'enabled'}
    
    env_config = MockEnvConfig()

# Configuração de logging
logger = logging.getLogger(__name__)

class ParallelEngine:
    """
    Sistema central de paralelização para modelos de loteria
    
    Oferece execução paralela tanto para predições quanto para treinamentos,
    com suporte a threads e processos baseado na natureza da tarefa.
    """
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        Inicializa o engine de paralelização
        
        Args:
            max_workers: Número máximo de workers (None = auto-detect)
            use_processes: Se True usa ProcessPoolExecutor, senão ThreadPoolExecutor
        """
        # Carrega configurações do .env
        config_max_workers = env_config.get_int('MAX_WORKERS', 0)
        config_use_processes = env_config.get_bool('USE_PROCESSES', False)
        
        self.max_workers = max_workers or config_max_workers or self._get_optimal_workers()
        self.use_processes = use_processes or config_use_processes
        self._executor = None
        
        # Controle para CI/CD - reduz workers em ambiente de integração
        self.fast_ci = env_config.get_bool('FAST_CI', False)
        if self.fast_ci:
            self.max_workers = min(2, self.max_workers)
            logger.info(f"🔧 FAST_CI ativo: limitando a {self.max_workers} workers")
            
        # Verifica se paralelização está desabilitada
        self.parallel_enabled = not env_config.get_bool('DISABLE_PARALLEL', False)
        
        # Timeouts configuráveis
        self.timeout_predict = env_config.get_int('PARALLEL_TIMEOUT_PREDICT', 300)
        self.timeout_train = env_config.get_int('PARALLEL_TIMEOUT_TRAIN', 600)
        
        if self.parallel_enabled:
            logger.info(f"🚀 ParallelEngine configurado: {self.max_workers} workers, "
                       f"{'processos' if use_processes else 'threads'}")
        else:
            logger.info("🔧 Paralelização desabilitada por configuração")
    
    def _get_optimal_workers(self) -> int:
        """
        Calcula número ótimo de workers baseado no hardware disponível
        
        Returns:
            Número recomendado de workers
        """
        cpu_count = multiprocessing.cpu_count()
        
        # Para threads: pode usar mais que CPU cores (I/O bound tasks)
        # Para processos: limitado por CPU cores (CPU bound tasks)
        if self.use_processes:
            return max(1, cpu_count - 1)  # Deixa 1 core livre para sistema
        else:
            return max(2, min(cpu_count * 2, 8))  # Máximo de 8 threads
    
    @contextmanager
    def get_executor(self):
        """Context manager para executor thread/process-safe"""
        if not self.parallel_enabled:
            yield None
            return
            
        if self.use_processes:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        try:
            yield self._executor
        finally:
            # Use non-blocking shutdown to avoid deadlocks when the
            # application receives KeyboardInterrupt while threads are
            # busy. Pending futures should be cancelled by the caller
            # when handling interrupts.
            if self._executor:
                try:
                    self._executor.shutdown(wait=False)
                except Exception:
                    # Best-effort shutdown; log and continue
                    logger.exception("Erro durante shutdown do executor")
                finally:
                    self._executor = None
    
    def parallel_predict(self, models: Dict[str, Callable], data: Any, 
                        progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Executa predições em paralelo para múltiplos modelos
        
        Args:
            models: Dict com nome_modelo -> função_predict
            data: Dados de entrada para os modelos
            progress_callback: Função chamada a cada modelo concluído
        
        Returns:
            Dict com resultados de cada modelo
        """
        if not self.parallel_enabled:
            return self._sequential_predict(models, data, progress_callback)
            
        results = {}
        completed_count = 0
        total_models = len(models)
        
        logger.info(f"🚀 Iniciando predições paralelas: {total_models} modelos, "
                   f"{self.max_workers} workers")
        
        start_time = time.time()
        
        with self.get_executor() as executor:
            if executor is None:
                return self._sequential_predict(models, data, progress_callback)
                
            # Submete todos os trabalhos
            future_to_model = {
                executor.submit(self._safe_predict, model_name, predict_func, data): model_name
                for model_name, predict_func in models.items()
            }
            
            # Coleta resultados conforme completam
            try:
                for future in as_completed(future_to_model):
                    model_name = future_to_model[future]
                    completed_count += 1

                    try:
                        result = future.result(timeout=self.timeout_predict)
                        results[model_name] = result

                        elapsed = time.time() - start_time
                        logger.info(f"✅ {model_name}: concluído ({completed_count}/{total_models}) "
                                   f"- {elapsed:.1f}s")

                        if progress_callback:
                            progress_callback(model_name, result, completed_count, total_models)

                    except Exception as e:
                        logger.error(f"❌ {model_name}: erro - {e}")
                        results[model_name] = None

            except KeyboardInterrupt:
                # Usuário interrompeu (Ctrl-C). Cancela futures pendentes e
                # retorna resultados parciais. Usamos cancel() em cada future
                # que ainda não terminou.
                logger.warning("⏹️ Execução interrompida pelo usuário. Cancelando tarefas pendentes...")
                for future, mname in future_to_model.items():
                    try:
                        if not future.done():
                            future.cancel()
                            results[mname] = None
                    except Exception:
                        logger.exception(f"Falha ao cancelar future para {mname}")
                # Não re-raise; retornamos os resultados parciais coletados até aqui.
        
        total_time = time.time() - start_time
        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"🎯 Predições paralelas concluídas em {total_time:.2f}s "
                   f"({success_count}/{total_models} sucessos)")
        
        return results
    
    def _sequential_predict(self, models: Dict[str, Callable], data: Any,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Execução sequencial como fallback"""
        results = {}
        total_models = len(models)
        
        logger.info(f"🔄 Executando predições sequencialmente: {total_models} modelos")
        
        for i, (model_name, predict_func) in enumerate(models.items(), 1):
            try:
                result = self._safe_predict(model_name, predict_func, data)
                results[model_name] = result
                
                logger.info(f"✅ {model_name}: concluído ({i}/{total_models})")
                
                if progress_callback:
                    progress_callback(model_name, result, i, total_models)
                    
            except Exception as e:
                logger.error(f"❌ {model_name}: erro - {e}")
                results[model_name] = None
        
        return results
    
    @staticmethod
    def _safe_predict(model_name: str, predict_func: Callable, data: Any) -> Any:
        """Wrapper seguro para execução de predições"""
        try:
            start = time.time()
            result = predict_func(data)
            elapsed = time.time() - start
            
            logger.debug(f"🔄 {model_name}: {elapsed:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"💥 {model_name}: falha na predição - {e}")
            raise
    
    def parallel_train(self, training_jobs: List[Dict], 
                      progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        Executa treinamentos em paralelo
        
        Args:
            training_jobs: Lista de dicts com {'name', 'train_func', 'data', 'params'}
            progress_callback: Função de callback para progresso
        
        Returns:
            Lista com resultados dos treinamentos na ordem original
        """
        if not self.parallel_enabled:
            return self._sequential_train(training_jobs, progress_callback)
            
        results = []
        total_jobs = len(training_jobs)
        
        logger.info(f"🧠 Iniciando treinamentos paralelos: {total_jobs} jobs")
        
        with self.get_executor() as executor:
            if executor is None:
                return self._sequential_train(training_jobs, progress_callback)
                
            future_to_job = {
                executor.submit(
                    self._safe_train, 
                    job['name'], 
                    job['train_func'], 
                    job.get('data'), 
                    job.get('params', {})
                ): i for i, job in enumerate(training_jobs)
            }
            
            # Ordena resultados pela ordem original
            indexed_results = {}

            try:
                for future in as_completed(future_to_job):
                    job_index = future_to_job[future]
                    job_name = training_jobs[job_index]['name']

                    try:
                        result = future.result(timeout=self.timeout_train)
                        indexed_results[job_index] = result

                        logger.info(f"✅ Treinamento {job_name}: concluído")

                        if progress_callback:
                            progress_callback(job_name, result, len(indexed_results), total_jobs)

                    except Exception as e:
                        logger.error(f"❌ Treinamento {job_name}: erro - {e}")
                        indexed_results[job_index] = None

            except KeyboardInterrupt:
                logger.warning("⏹️ Treinamentos interrompidos pelo usuário. Cancelando jobs pendentes...")
                for future, idx in future_to_job.items():
                    try:
                        if not future.done():
                            future.cancel()
                            indexed_results[idx] = None
                    except Exception:
                        logger.exception(f"Falha ao cancelar job index {idx}")
            
            # Reconstrói lista na ordem original
            results = [indexed_results.get(i) for i in range(total_jobs)]
        
        return results
    
    def _sequential_train(self, training_jobs: List[Dict],
                         progress_callback: Optional[Callable] = None) -> List[Any]:
        """Execução sequencial de treinamentos como fallback"""
        results = []
        total_jobs = len(training_jobs)
        
        logger.info(f"🔄 Executando treinamentos sequencialmente: {total_jobs} jobs")
        
        for i, job in enumerate(training_jobs):
            try:
                result = self._safe_train(
                    job['name'], 
                    job['train_func'], 
                    job.get('data'), 
                    job.get('params', {})
                )
                results.append(result)
                
                logger.info(f"✅ Treinamento {job['name']}: concluído ({i+1}/{total_jobs})")
                
                if progress_callback:
                    progress_callback(job['name'], result, i+1, total_jobs)
                    
            except Exception as e:
                logger.error(f"❌ Treinamento {job['name']}: erro - {e}")
                results.append(None)
        
        return results
    
    @staticmethod 
    def _safe_train(name: str, train_func: Callable, data: Any, params: Dict) -> Any:
        """Wrapper seguro para treinamentos"""
        try:
            start = time.time()
            result = train_func(data, **params)
            elapsed = time.time() - start
            
            logger.info(f"🔄 Treinamento {name}: {elapsed:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"💥 Treinamento {name}: falha - {e}")
            raise


class ParallelConfig:
    """Configurações centralizadas de paralelização com suporte a .env"""
    
    @staticmethod
    def get_max_workers() -> Optional[int]:
        """Obtém número máximo de workers das configurações"""
        return env_config.get_int('MAX_WORKERS', 0) or None  # 0 = auto-detect
    
    @staticmethod  
    def is_parallel_enabled() -> bool:
        """Verifica se paralelização está habilitada"""
        return not env_config.get_bool('DISABLE_PARALLEL', False)
    
    @staticmethod
    def use_processes() -> bool:
        """Verifica se deve usar processos ao invés de threads"""
        return env_config.get_bool('USE_PROCESSES', False)
    
    @staticmethod
    def is_fast_mode() -> bool:
        """Verifica se está no modo rápido (CI/CD)"""
        return env_config.get_bool('FAST_CI', False)
    
    @staticmethod
    def get_timeouts() -> Dict[str, int]:
        """Obtém timeouts configurados"""
        return {
            'predict': env_config.get_int('PARALLEL_TIMEOUT_PREDICT', 300),
            'train': env_config.get_int('PARALLEL_TIMEOUT_TRAIN', 600)
        }
    
    @staticmethod
    def print_config():
        """Exibe configurações ativas"""
        if hasattr(env_config, 'print_config'):
            env_config.print_config()
        else:
            print("🔧 Configurações básicas carregadas via environment variables")


# Instância global singleton
_parallel_engine = None
_process_engine = None

def get_parallel_engine(max_workers: Optional[int] = None, 
                       use_processes: bool = False) -> ParallelEngine:
    """
    Factory function para obter instância do ParallelEngine
    
    Args:
        max_workers: Número máximo de workers (sobrescreve .env)
        use_processes: Se True, usa ProcessPoolExecutor (sobrescreve .env)
    
    Returns:
        Instância do ParallelEngine
    """
    global _parallel_engine, _process_engine
    
    # Aplica configurações do .env se não especificado
    config_workers = max_workers or ParallelConfig.get_max_workers()
    config_processes = use_processes or ParallelConfig.use_processes()
    
    if config_processes:
        if _process_engine is None:
            _process_engine = ParallelEngine(config_workers, use_processes=True)
        return _process_engine
    else:
        if _parallel_engine is None:
            _parallel_engine = ParallelEngine(config_workers, use_processes=False)
        return _parallel_engine


def reset_parallel_engines():
    """Reseta instâncias globais (útil para testes)"""
    global _parallel_engine, _process_engine
    _parallel_engine = None
    _process_engine = None