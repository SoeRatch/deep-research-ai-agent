"""
Multi-model LLM integration with specialized roles.

Supports OpenAI, Google Gemini, and Anthropic Claude with fallback logic.
"""

from typing import Literal, Optional, Any, Dict
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import logging

from src.config import Config

logger = logging.getLogger(__name__)


class ModelRole:
    """Enum for model roles in the research pipeline."""
    PLANNER = "planner"  # Initial strategy and query generation
    RESEARCHER = "researcher"  # Information extraction
    ANALYZER = "analyzer"  # Risk analysis and pattern recognition
    VALIDATOR = "validator"  # Fact cross-checking
    SYNTHESIZER = "synthesizer"  # Final report generation


class MultiModelOrchestrator:
    """Orchestrates multiple LLM providers with role-based routing."""
    
    def __init__(self, config: Config):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.primary_model = self._init_model(
            config.primary_model,
            config.primary_model_name
        )
        self.secondary_model = self._init_model(
            config.secondary_model,
            config.secondary_model_name
        )
        
        # Role assignments
        self.role_assignments = {
            ModelRole.PLANNER: self.primary_model,
            ModelRole.RESEARCHER: self.primary_model,
            ModelRole.ANALYZER: self.secondary_model,  # Use different model for validation
            ModelRole.VALIDATOR: self.secondary_model,
            ModelRole.SYNTHESIZER: self.primary_model,
        }
        
        logger.info(f"Initialized primary model: {config.primary_model} ({config.primary_model_name})")
        logger.info(f"Initialized secondary model: {config.secondary_model} ({config.secondary_model_name})")
    
    def _init_model(self, provider: str, model_name: str) -> BaseChatModel:
        """
        Initialize a model from provider.
        
        Args:
            provider: Model provider (openai, google, anthropic)
            model_name: Specific model name
            
        Returns:
            Initialized chat model
        """
        api_key = self.config.get_api_key(provider)
        
        if provider == "openai":
            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                temperature=0.7,
                request_timeout=self.config.request_timeout_seconds
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.7,
                request_timeout=self.config.request_timeout_seconds
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=api_key,
                temperature=0.7,
                timeout=self.config.request_timeout_seconds
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def get_model_for_role(self, role: str) -> BaseChatModel:
        """
        Get the appropriate model for a specific role.
        
        Args:
            role: ModelRole constant
            
        Returns:
            Chat model instance
        """
        return self.role_assignments.get(role, self.primary_model)
    
    async def invoke_with_fallback(
        self,
        role: str,
        messages: list,
        fallback_to_secondary: bool = True
    ) -> str:
        """
        Invoke model with automatic fallback if primary fails.
        
        Args:
            role: ModelRole constant
            messages: List of messages to send
            fallback_to_secondary: If True, fall back to secondary model on error
            
        Returns:
            Model response as string
        """
        primary = self.get_model_for_role(role)
        
        try:
            response = await primary.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Primary model failed for role {role}: {e}")
            
            if fallback_to_secondary and primary != self.secondary_model:
                logger.info(f"Falling back to secondary model for role {role}")
                try:
                    response = await self.secondary_model.ainvoke(messages)
                    return response.content
                except Exception as e2:
                    logger.error(f"Secondary model also failed: {e2}")
                    raise
            else:
                raise
    
    def invoke_sync(self, role: str, messages: list) -> str:
        """
        Synchronous version of invoke_with_fallback.
        
        Args:
            role: ModelRole constant
            messages: List of messages to send
            
        Returns:
            Model response as string
        """
        primary = self.get_model_for_role(role)
        
        try:
            response = primary.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Primary model failed for role {role}: {e}")
            
            if primary != self.secondary_model:
                logger.info(f"Falling back to secondary model for role {role}")
                try:
                    response = self.secondary_model.invoke(messages)
                    return response.content
                except Exception as e2:
                    logger.error(f"Secondary model also failed: {e2}")
                    raise
            else:
                raise


# Convenience function for direct access
_orchestrator: Optional[MultiModelOrchestrator] = None


def get_orchestrator(config: Optional[Config] = None) -> MultiModelOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        from src.config import get_config
        cfg = config or get_config()
        _orchestrator = MultiModelOrchestrator(cfg)
    return _orchestrator
