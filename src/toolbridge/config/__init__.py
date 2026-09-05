"""Configuration package.

Provides a centralized, typed settings object built from environment variables.
Use ``get_settings()`` everywhere instead of calling ``os.getenv`` directly.
"""

from toolbridge.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
