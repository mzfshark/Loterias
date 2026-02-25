"""
Carregador de Configurações de Ambiente

Este módulo carrega configurações de arquivos .env e variáveis de ambiente
para o sistema de paralelização.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class EnvConfig:
    """Gerenciador de configurações de ambiente com suporte a .env"""
    
    def __init__(self, env_file: Optional[Union[str, Path]] = None):
        """
        Inicializa o carregador de configurações
        
        Args:
            env_file: Caminho para arquivo .env (None = auto-detect)
        """
        self.env_file = self._find_env_file(env_file)
        self.config = {}
        
        # Carrega configurações
        self._load_env_file()
        self._setup_logging()
        
        logger.info(f"📋 Configurações carregadas de: {self.env_file or 'variáveis de ambiente'}")
    
    def _find_env_file(self, env_file: Optional[Union[str, Path]]) -> Optional[Path]:
        """Encontra arquivo .env automaticamente"""
        if env_file:
            env_path = Path(env_file)
            if env_path.exists():
                return env_path
            else:
                logger.warning(f"⚠️ Arquivo .env não encontrado: {env_path}")
        
        # Busca automática do .env
        search_paths = [
            Path.cwd() / '.env',
            Path(__file__).parent.parent.parent / '.env',  # Raiz do projeto
            Path.cwd() / '.env.local',
            Path.cwd() / '.env.development'
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        logger.info("📋 Nenhum arquivo .env encontrado, usando apenas variáveis de ambiente")
        return None
    
    def _load_env_file(self):
        """Carrega configurações do arquivo .env"""
        if not self.env_file:
            return
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comentários e linhas vazias
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse linha KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove aspas se presentes
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Define variável de ambiente se não existir
                        if key not in os.environ:
                            os.environ[key] = value
                            logger.debug(f"🔧 Carregado do .env: {key}={value}")
                        else:
                            logger.debug(f"🔄 Mantendo env existente: {key}={os.environ[key]}")
                    else:
                        logger.warning(f"⚠️ Linha inválida em {self.env_file}:{line_num}: {line}")
                        
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {self.env_file}: {e}")
    
    def _setup_logging(self):
        """Configura nível de logging baseado na configuração"""
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        
        # Mapeia níveis de log
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if log_level in level_map:
            logging.basicConfig(
                level=level_map[log_level],
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Obtém valor inteiro da configuração"""
        value = os.environ.get(key, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Valor inválido para {key}='{value}', usando default={default}")
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Obtém valor booleano da configuração"""
        value = os.environ.get(key, '').lower().strip()
        
        # Valores verdadeiros
        true_values = {'1', 'true', 'yes', 'on', 'enabled'}
        # Valores falsos
        false_values = {'0', 'false', 'no', 'off', 'disabled', ''}
        
        if value in true_values:
            return True
        elif value in false_values:
            return False
        else:
            logger.warning(f"⚠️ Valor inválido para {key}='{value}', usando default={default}")
            return default
    
    def get_str(self, key: str, default: str = '') -> str:
        """Obtém valor string da configuração"""
        return os.environ.get(key, default)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Obtém valor float da configuração"""
        value = os.environ.get(key, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Valor inválido para {key}='{value}', usando default={default}")
            return default
    
    def print_config(self):
        """Exibe configurações carregadas"""
        print("🔧 Configurações Ativas:")
        print("-" * 30)
        
        # Configurações de paralelização
        parallel_configs = [
            'MAX_WORKERS', 'USE_PROCESSES', 'DISABLE_PARALLEL', 'FAST_CI',
            'LOG_LEVEL', 'PARALLEL_DEBUG'
        ]
        
        for key in parallel_configs:
            value = os.environ.get(key)
            if value:
                print(f"   {key}={value}")
        
        # Configurações personalizadas
        custom_configs = [k for k in os.environ.keys() 
                         if k.startswith(('MONTE_CARLO_', 'NEURAL_', 'PARALLEL_TIMEOUT_'))]
        
        if custom_configs:
            print("\n🎯 Configurações Específicas:")
            for key in sorted(custom_configs):
                print(f"   {key}={os.environ[key]}")
    
    def validate_config(self) -> bool:
        """Valida se as configurações são válidas"""
        errors = []
        
        # Validar MAX_WORKERS
        max_workers = self.get_int('MAX_WORKERS', 0)
        if max_workers < 0 or max_workers > 32:
            errors.append(f"MAX_WORKERS deve estar entre 0-32, recebido: {max_workers}")
        
        # Validar timeouts
        timeout_predict = self.get_int('PARALLEL_TIMEOUT_PREDICT', 300)
        timeout_train = self.get_int('PARALLEL_TIMEOUT_TRAIN', 600)
        
        if timeout_predict < 10:
            errors.append(f"PARALLEL_TIMEOUT_PREDICT muito baixo: {timeout_predict}s")
        if timeout_train < 30:
            errors.append(f"PARALLEL_TIMEOUT_TRAIN muito baixo: {timeout_train}s")
        
        # Reportar erros
        if errors:
            for error in errors:
                logger.error(f"❌ Configuração inválida: {error}")
            return False
        
        logger.info("✅ Todas as configurações são válidas")
        return True


# Instância global para uso em toda aplicação
_env_config = None

def get_env_config(env_file: Optional[Union[str, Path]] = None) -> EnvConfig:
    """
    Factory function para obter configuração de ambiente
    
    Args:
        env_file: Caminho para arquivo .env personalizado
    
    Returns:
        Instância do EnvConfig
    """
    global _env_config
    
    if _env_config is None:
        _env_config = EnvConfig(env_file)
    
    return _env_config

def reload_config(env_file: Optional[Union[str, Path]] = None):
    """Recarrega configurações (útil para testes)"""
    global _env_config
    _env_config = None
    return get_env_config(env_file)