"""Configuration management for Hedorah."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Manages Hedorah configuration."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}

        # Load environment variables
        load_dotenv()

        # Load configuration
        self.load()

    def load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.example.yaml to config.yaml and configure it."
            )

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

        # Expand environment variables in config values
        self._expand_env_vars(self._config)

    def _expand_env_vars(self, obj: Any) -> None:
        """Recursively expand environment variables in config values.

        Args:
            obj: Configuration object (dict, list, or primitive)
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    obj[key] = os.getenv(env_var, value)
                else:
                    self._expand_env_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                self._expand_env_vars(item)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., 'vault.path')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def vault_path(self) -> Path:
        """Get vault path as Path object."""
        path = self.get('vault.path')
        if not path:
            raise ValueError("Vault path not configured")
        return Path(path)

    @property
    def vault_folders(self) -> Dict[str, str]:
        """Get vault folder structure."""
        return self.get('vault.folders', {})

    def get_vault_folder(self, folder_type: str) -> Path:
        """Get full path to a vault folder.

        Args:
            folder_type: Type of folder (papers, notes, experiments, attachments, inbox)

        Returns:
            Full path to the folder
        """
        folder_name = self.vault_folders.get(folder_type, folder_type)
        return self.vault_path / folder_name

    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key."""
        key = self.get('llm.reasoning.api_key')
        if not key or key.startswith('${'):
            raise ValueError("Anthropic API key not configured")
        return key

    @property
    def local_model(self) -> str:
        """Get local model name."""
        return self.get('llm.local.model', 'qwen2.5:latest')

    @property
    def reasoning_model(self) -> str:
        """Get reasoning model name."""
        return self.get('llm.reasoning.model', 'claude-sonnet-4-5-20250929')

    @property
    def ollama_url(self) -> str:
        """Get Ollama API URL."""
        return self.get('llm.local.api_url', 'http://localhost:11434')


# Global config instance
_config_instance: Config = None


def get_config(config_path: str = "config.yaml") -> Config:
    """Get or create global config instance.

    Args:
        config_path: Path to configuration file

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
