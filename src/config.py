"""
Configuration management for the Research Agent.
Loads environment variables and provides centralized config access.
"""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    # API Keys
    openai_api_key: str = Field(default="", description="OpenAI API key")
    google_api_key: str = Field(default="", description="Google Gemini API key")
    anthropic_api_key: str = Field(default="", description="Anthropic Claude API key")
    tavily_api_key: str = Field(default="", description="Tavily search API key")
    
    # Model Configuration
    primary_model: Literal["openai", "google", "anthropic"] = Field(
        default="openai",
        description="Primary model provider for planning and synthesis"
    )
    secondary_model: Literal["openai", "google", "anthropic"] = Field(
        default="anthropic",
        description="Secondary model for validation and analysis"
    )
    primary_model_name: str = Field(
        default="gpt-4-turbo-preview",
        description="Specific model name for primary provider"
    )
    secondary_model_name: str = Field(
        default="claude-opus-4",
        description="Specific model name for secondary provider"
    )
    
    # Agent Configuration
    max_research_depth: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum consecutive search iterations"
    )
    max_queries_per_iteration: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum search queries per iteration"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Stop research if confidence reaches this level"
    )
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=20,
        description="Max API requests per minute"
    )
    request_timeout_seconds: int = Field(
        default=30,
        description="HTTP request timeout"
    )
    
    # Output Configuration
    output_dir: Path = Field(
        default=Path("reports"),
        description="Directory for generated reports"
    )
    audit_logs_enabled: bool = Field(
        default=True,
        description="Enable detailed audit logging"
    )
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for a specific provider."""
        key_map = {
            "openai": self.openai_api_key,
            "google": self.google_api_key,
            "anthropic": self.anthropic_api_key,
            "tavily": self.tavily_api_key
        }
        key = key_map.get(provider, "")
        if not key:
            raise ValueError(f"API key for {provider} not found in environment")
        return key
    
    def validate_models(self):
        """Validate that required model API keys are present."""
        errors = []
        
        # Check primary model
        if not self.get_api_key(self.primary_model):
            errors.append(f"Primary model ({self.primary_model}) API key missing")
        
        # Check secondary model
        if not self.get_api_key(self.secondary_model):
            errors.append(f"Secondary model ({self.secondary_model}) API key missing")
        
        # Check search API
        if not self.tavily_api_key:
            errors.append("Tavily API key missing")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.ensure_output_dir()
    return _config


def load_config(validate: bool = True) -> Config:
    """
    Load configuration from environment.
    
    Args:
        validate: If True, validate required API keys are present
        
    Returns:
        Config instance
    """
    config = get_config()
    if validate:
        config.validate_models()
    return config


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config(validate=False)
        print("Configuration loaded successfully:")
        print(f"  Primary model: {config.primary_model} ({config.primary_model_name})")
        print(f"  Secondary model: {config.secondary_model} ({config.secondary_model_name})")
        print(f"  Max research depth: {config.max_research_depth}")
        print(f"  Output directory: {config.output_dir}")
    except Exception as e:
        print(f"Configuration error: {e}")

# Use it like this in other modules:
# from src.config import load_config
# config = load_config()
# client = OpenAI(api_key=config.openai_api_key)
# model_name = config.primary_model_name


# Test this config by running this file directly with 
# python -m src.config
