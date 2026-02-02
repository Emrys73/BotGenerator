"""Provider-agnostic LLM service supporting multiple AI providers."""

import os
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to LLM."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider using new google-genai package."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
        except ImportError:
            raise ImportError(
                "google-genai not installed. "
                "Run: pip install google-genai"
            )
        
        # Configure client
        self.client = self.genai.Client(api_key=api_key)
        self.model_name = model
        logger.info(f"Initialized Gemini provider with model: {model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Gemini."""
        try:
            # Convert messages to Gemini format
            contents = []
            
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                if msg["role"] == "system":
                    # System messages become user messages in Gemini
                    role = "user"
                
                contents.append(
                    self.types.Content(
                        role=role,
                        parts=[self.types.Part(text=msg["content"])]
                    )
                )
            
            # Ensure model name has 'models/' prefix
            model_id = self.model_name if self.model_name.startswith("models/") else f"models/{self.model_name}"
            
            # Generate response
            response = self.client.models.generate_content(
                model=model_id,
                contents=contents
            )
            
            return {
                "content": response.text,
                "model": self.model_name,
                "provider": "gemini",
                "tool_calls": None  # Gemini function calling would go here
            }
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError(
                "openai not installed. "
                "Run: pip install openai"
            )
        
        self.model = model
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to OpenAI."""
        try:
            params = {
                "model": self.model,
                "messages": messages
            }
            
            if tools:
                params["tools"] = tools
            
            response = await self.client.chat.completions.create(**params)
            
            message = response.choices[0].message
            
            # Extract tool calls if any
            tool_calls = None
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = [
                    {
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                    for tc in message.tool_calls
                ]
            
            return {
                "content": message.content or "",
                "model": self.model,
                "provider": "openai",
                "tool_calls": tool_calls
            }
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError(
                "anthropic not installed. "
                "Run: pip install anthropic"
            )
        
        self.model = model
        logger.info(f"Initialized Claude provider with model: {model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Claude."""
        try:
            # Extract system message if present
            system = None
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            params = {
                "model": self.model,
                "messages": claude_messages,
                "max_tokens": 4096
            }
            
            if system:
                params["system"] = system
            
            if tools:
                params["tools"] = tools
            
            response = await self.client.messages.create(**params)
            
            # Extract content
            content = ""
            tool_calls = None
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    if tool_calls is None:
                        tool_calls = []
                    tool_calls.append({
                        "name": block.name,
                        "arguments": block.input
                    })
            
            return {
                "content": content,
                "model": self.model,
                "provider": "claude",
                "tool_calls": tool_calls
            }
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, model: str = "llama3.2:latest", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.
        
        Args:
            model: Ollama model name (e.g., llama3.2:latest, codellama, mistral)
            base_url: Ollama API endpoint
        """
        self.model = model
        self.base_url = base_url
        logger.info(f"Initialized Ollama provider with model: {model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Ollama."""
        try:
            import aiohttp
            
            # Convert messages to Ollama format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "stream": False
            }
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {error_text}")
                    
                    result = await response.json()
                    
                    # Extract content
                    content = result.get("message", {}).get("content", "")
                    
                    return {
                        "content": content,
                        "model": self.model,
                        "provider": "ollama"
                    }
        
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise


class LLMService:
    """Provider-agnostic LLM service."""
    
    def __init__(
        self,
        provider: str = None,
        api_key: str = None,
        model: str = None
    ):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider (gemini, openai, claude, ollama).
                     Falls back to LLM_PROVIDER env var if not provided.
            api_key: API key for the provider.
                    Falls back to LLM_API_KEY env var if not provided.
            model: Model name/ID.
                  Falls back to LLM_MODEL env var if not provided.
        """
        self.provider_name = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL")
        
        # API key not required for Ollama (local)
        if not self.api_key and self.provider_name != "ollama":
            raise ValueError("LLM_API_KEY not set in environment or parameters")
        
        # Initialize provider
        self.provider = self._create_provider()
        
        logger.info(
            f"LLM Service initialized: "
            f"provider={self.provider_name}, model={self.model_name}"
        )
    
    def _create_provider(self) -> LLMProvider:
        """Create appropriate provider instance."""
        if self.provider_name == "gemini":
            model = self.model_name or "gemini-2.5-flash"
            return GeminiProvider(self.api_key, model)
        
        elif self.provider_name == "openai":
            model = self.model_name or "gpt-4-turbo-preview"
            return OpenAIProvider(self.api_key, model)
        
        elif self.provider_name == "claude":
            model = self.model_name or "claude-3-opus-20240229"
            return ClaudeProvider(self.api_key, model)
        
        elif self.provider_name == "ollama":
            model = self.model_name or "llama3.2:latest"
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaProvider(model, base_url)
        
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider_name}. "
                f"Supported: gemini, openai, claude, ollama"
            )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request to configured LLM provider.
        
        Args:
            messages: List of conversation messages
            tools: Optional tool definitions for function calling
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Dictionary with response content and metadata
        """
        return await self.provider.chat(messages, tools, **kwargs)
