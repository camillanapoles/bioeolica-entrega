"""
Alias/proxy para retrocompatibilidade.
Importações antigas utilizavam `modules.config_manager`, mas o módulo canônico
foi movido para `kdi_m3.config_manager` durante a reestruturação para o `src/`.
"""
from kdi_m3.config_manager import ConfigManager, create_default_config

__all__ = ["ConfigManager", "create_default_config"]
