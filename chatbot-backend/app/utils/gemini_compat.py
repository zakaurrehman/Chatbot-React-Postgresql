"""
Gemini API client wrapper for the chatbot.
"""

import os
import logging
import json
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default API key as fallback if environment variable is not set
DEFAULT_API_KEY = "AIzaSyCsjcvmRf_LVIWADTYf7eHYUzcqraHxzi0"

logger = logging.getLogger(__name__)

class GeminiClient:
    """Wrapper for Google's Gemini API."""
    
    def __init__(self, api_key=None):
        """Initialize the Gemini API client.
        
        Args:
            api_key: API key for Google Gemini API
        """
        # Use provided key, or environment variable, or default fallback
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", DEFAULT_API_KEY)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        logger.info("Using Google Gemini API client")
    
    def create_chat_completion(self, model: str, messages: List[Dict[str, str]], 
                               temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> Dict[str, Any]:
        """Create a chat completion using the Gemini API.
        
        Args:
            model: The model to use (will be mapped to Gemini model)
            messages: List of message objects with role and content
            temperature: Temperature parameter for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Response in OpenAI-compatible format
        """
        # Map OpenAI model to Gemini model
        gemini_model = self._map_model(model)
        
        # Format messages for Gemini API
        contents = self._format_messages(messages)
        
        # Set up the API request
        url = f"{self.base_url}/{gemini_model}:generateContent?key={self.api_key}"
        
        # Prepare request data
        request_data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": kwargs.get("top_p", 0.95),
                "topK": kwargs.get("top_k", 40)
            }
        }
        
        try:
            # Make the API request
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=request_data
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            gemini_response = response.json()
            
            # Format the response to be compatible with OpenAI format
            return self._format_response(gemini_response)
            
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            
            # Return a graceful error response in OpenAI format
            return {
                "choices": [{
                    "message": {
                        "content": f"I apologize, but I encountered an error when processing your request: {str(e)}"
                    }
                }]
            }
    
    def _map_model(self, openai_model: str) -> str:
        """Map OpenAI model name to Gemini model name.
        
        Args:
            openai_model: OpenAI model name
            
        Returns:
            Gemini model name
        """
        model_mapping = {
            "gpt-3.5-turbo": "gemini-2.0-flash",
            "gpt-4": "gemini-2.0-pro",
            "gpt-4-turbo": "gemini-2.0-pro",
            "text-davinci-003": "gemini-1.5-flash"
        }
        
        # Default to gemini-2.0-flash if model not found in mapping
        return model_mapping.get(openai_model, "gemini-2.0-flash")
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, List[Dict[str, str]]]]:
        """Format messages from OpenAI format to Gemini format.
        
        Args:
            messages: List of message objects with role and content
            
        Returns:
            Formatted messages for Gemini API
        """
        contents = []
        system_prompt = ""
        
        # Extract system prompt if present
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
                break
        
        # Format user and assistant messages
        current_content = None
        
        for message in messages:
            if message["role"] == "system":
                # Already handled
                continue
                
            if message["role"] == "user":
                # Start a new content object for each user message
                if current_content:
                    contents.append(current_content)
                
                user_text = message["content"]
                if system_prompt and len(contents) == 0:
                    # Prepend system prompt to first user message
                    user_text = f"{system_prompt}\n\n{user_text}"
                
                current_content = {
                    "role": "user",
                    "parts": [{"text": user_text}]
                }
            
            elif message["role"] == "assistant":
                if current_content:
                    # Add assistant response to current content
                    assistant_content = {
                        "role": "model",
                        "parts": [{"text": message["content"]}]
                    }
                    contents.append(current_content)
                    contents.append(assistant_content)
                    current_content = None
        
        # Add final content if present
        if current_content:
            contents.append(current_content)
        
        return contents
    
    def _format_response(self, gemini_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format Gemini API response to be compatible with OpenAI format.
        
        Args:
            gemini_response: Response from Gemini API
            
        Returns:
            Response formatted like OpenAI API response
        """
        try:
            # Extract the generated text
            generated_content = gemini_response.get("candidates", [{}])[0].get("content", {})
            text = ""
            
            # Extract text from parts
            for part in generated_content.get("parts", []):
                if "text" in part:
                    text += part["text"]
            
            # Format in OpenAI style
            return {
                "choices": [{
                    "message": {
                        "content": text
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error formatting Gemini response: {e}")
            logger.error(f"Original response: {gemini_response}")
            
            # Fallback error response
            return {
                "choices": [{
                    "message": {
                        "content": "I apologize, but I encountered an error processing the response."
                    }
                }]
            }