import json
import logging
import requests
from typing import Optional, List, Dict, Any

from skls_generator.logger_config import get_logger

logger = get_logger(__name__)

class LlamaCppGenAI:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initializes the LlamaCpp client.

        Assumes you are running 'llama-server' (part of llama.cpp).
        Example: ./llama-server -m model.gguf -c 2048 --port 8080

        Args:
            base_url: URL to the llama.cpp server. Defaults to "http://localhost:8080/v1/chat/completions".
            api_key: Optional API key if the server is protected. Defaults to empty string.
        """
        # Default to the OpenAI-compatible endpoint provided by llama.cpp
        default_url = "http://localhost:8080/v1/chat/completions"

        self.base_url = base_url or default_url
        self.api_key = api_key or ""

        # Llama.cpp server usually serves one model at a time, so the name
        # is mostly for logging or satisfying the API schema.
        self.model_name = "local-llama-cpp-model"

        logger.info(f"LlamaCppGenAI initialized connecting to: {self.base_url}")

    def get_model(self) -> str:
        return self.model_name
    
    def complete(self,
                 user: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 payload: Any = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> str:
        """
        Generates a response from the local llama.cpp server.

        Args:
            user: The current user prompt.
            system_prompt: The system instruction.
            payload: A message history object (must have .messages attribute).
            temperature: The sampling temperature.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            The generated text response.
        """
        messages: List[Dict[str, str]] = []

        # 1. Handle System Prompt
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        # 2. Handle Payload (History)
        if payload and hasattr(payload, 'messages'):
            for message in payload.messages:
                role = message.role
                # Map internal roles to API standard
                if role in ["model", "agent"]:
                    role = "assistant"
                
                # Skip system messages in history if we have an explicit override
                if role == "system" and system_prompt:
                    continue
                
                messages.append({'role': role, 'content': message.content})

        # 3. Handle User Input
        if user:
            messages.append({'role': 'user', 'content': user})

        if not messages:
            raise ValueError("No messages provided. Supply 'user', 'payload', or 'system_prompt'.")

        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Note: llama.cpp's /v1/chat/completions endpoint accepts standard OpenAI params
        data = {
            "model": self.model_name, # Often ignored by the server but required by schema
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # Llama.cpp specific parameters can often be added here if needed,
            # e.g., "top_k": 40, "repeat_penalty": 1.1
        }

        logger.debug(f"Payload sending to LlamaCpp: {json.dumps(messages, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Standard OpenAI format response extraction
            content = result['choices'][0]['message']['content']
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"LlamaCpp API Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status Code: {e.response.status_code}")
                try:
                    logger.error(f"Response Body: {e.response.text}")
                except:
                    pass
            raise e
        except (KeyError, IndexError) as e:
            logger.error(f"Malformed response format from LlamaCpp: {e}")
            logger.debug(f"Raw Response: {result}") # type: ignore
            raise ValueError("Unexpected response format from LlamaCpp Server") from e

# Example Usage
if __name__ == "__main__":
    try:
        # Assumes server is running at localhost:8080
        ai = LlamaCppGenAI()

        logger.info("Sending request to local Llama...")
        response = ai.complete(
            system_prompt="You are a minimalist poet.",
            user="Write a poem about rust (the metal)."
        )
        logger.info(f"\nResponse:\n{response}")

    except Exception as err:
        logger.error(f"Failed to generate: {err}")
        logger.error("Ensure 'llama-server' is running. Example: ./llama-server -m model.gguf --port 8080")