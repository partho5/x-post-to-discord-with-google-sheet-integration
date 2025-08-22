"""
OpenAI API handler for generating responses.
"""

import sys
import io
import re
import logging
from openai import OpenAI
from .config import Config

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)


class OpenAIHandler:
    """OpenAI API handler for generating text responses."""
    
    def __init__(self):
        """Initialize OpenAI client with configuration."""
        self.config = Config()
        self.client = OpenAI(api_key=self.config.openai_api_key)
    
    def get_chat_completion(self, messages, model, temperature=0.7, max_tokens=1000):
        """
        Get chat completion from OpenAI API.
        
        Args:
            messages: List of message objects
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (response_text, usage_info)
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip(), response.usage
        except Exception as e:
            # Handle specific OpenAI exceptions
            error_type = type(e).__name__
            if "AuthenticationError" in error_type:
                raise RuntimeError("Invalid API key")
            elif "RateLimitError" in error_type:
                raise RuntimeError("Rate limit exceeded")
            elif "APIError" in error_type:
                raise RuntimeError(f"OpenAI API Error: {e}")
            else:
                raise RuntimeError(f"Unexpected error: {e}")
    
    def clean_response(self, text):
        """
        Clean response text by removing code blocks, markdown, and excess whitespace.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned text
        """
        # Remove code blocks, markdown, and excess whitespace
        text = re.sub(r"```(?:\w+)?\n(.*?)```", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        return text.strip()
    
    def openai_response(self, prompt, system_message="You are a X(Twitter) expert and helpful assistant."):
        """
        Generate OpenAI response for given prompt.
        
        Args:
            prompt: User prompt text
            system_message: System message for context
            
        Returns:
            Plain text response ready for use
        """
        if not prompt or not prompt.strip():
            logger.error("Prompt is empty or invalid")
            return "[Error] Empty prompt provided"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        try:
            raw_response, usage = self.get_chat_completion(
                messages=messages,
                model=self.config.openai_model,
                temperature=0.7,
                max_tokens=1000
            )
            return self.clean_response(raw_response)
        except RuntimeError as e:
            logger.error(f"OpenAI API error: {e}")
            return f"[Error] {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in openai_response: {e}")
            return f"[Error] Unexpected error occurred"
