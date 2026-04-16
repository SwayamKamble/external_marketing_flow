"""YAML configuration loader for ContentForge.

Loads and validates configuration from config/ directory.
Supports environment variable substitution in YAML values.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Load .env file on import
load_dotenv()


class ConfigLoader:
    """Loads YAML config files with environment variable substitution.

    Usage:
        config = ConfigLoader(config_dir="./config")
        llm_config = config.get("llm_config")
        platform_rules = config.get("platform_rules")
    """

    def __init__(self, config_dir: str | Path = "./config"):
        self.config_dir = Path(config_dir)
        self._cache: dict[str, dict[str, Any]] = {}

        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")

    def get(self, config_name: str) -> dict[str, Any]:
        """Load a config file by name (without .yaml extension).

        Args:
            config_name: Name of the config file (e.g., "llm_config").

        Returns:
            Parsed YAML as a dictionary with env vars substituted.
        """
        if config_name in self._cache:
            return self._cache[config_name]

        config_path = self.config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        # Substitute environment variables: ${VAR_NAME}
        substituted = self._substitute_env_vars(raw_content)

        parsed = yaml.safe_load(substituted) or {}
        self._cache[config_name] = parsed
        return parsed

    def get_llm_config(self) -> dict[str, Any]:
        """Shortcut to load LLM configuration."""
        return self.get("llm_config")

    def get_platform_rules(self) -> dict[str, Any]:
        """Shortcut to load platform rules."""
        return self.get("platform_rules")

    def get_content_mix(self) -> dict[str, Any]:
        """Shortcut to load content mix framework."""
        return self.get("content_mix")

    def get_pipeline_config(self) -> dict[str, Any]:
        """Shortcut to load pipeline configuration."""
        return self.get("pipeline_config")

    def get_model_for_node(self, node_name: str) -> str:
        """Get the model name assigned to a specific node.

        Args:
            node_name: The pipeline node name (e.g., "caption_writer").

        Returns:
            Model name string (e.g., "gpt-5-chat").
        """
        llm_config = self.get_llm_config()
        mapping = llm_config.get("node_model_mapping", {})
        default = llm_config.get("default_model", "gpt-5-chat")
        return mapping.get(node_name, default)

    def get_provider_config(self) -> dict[str, Any]:
        """Get the default provider's connection config."""
        llm_config = self.get_llm_config()
        default_provider = llm_config.get("default_provider", "azure_openai")
        providers = llm_config.get("providers", {})
        return providers.get(default_provider, {})

    def reload(self, config_name: str | None = None) -> None:
        """Clear cache and reload config(s).

        Args:
            config_name: Specific config to reload, or None for all.
        """
        if config_name:
            self._cache.pop(config_name, None)
        else:
            self._cache.clear()

    @staticmethod
    def _substitute_env_vars(content: str) -> str:
        """Replace ${VAR_NAME} patterns with environment variable values.

        Args:
            content: Raw YAML string with potential env var references.

        Returns:
            String with env vars substituted.
        """
        pattern = re.compile(r"\$\{(\w+)\}")

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            value = os.getenv(var_name, "")
            if not value:
                # Return the original placeholder if env var is not set
                return match.group(0)
            return value

        return pattern.sub(replacer, content)
