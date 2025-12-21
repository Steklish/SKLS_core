import os
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from google.api_core import retry
import google.generativeai as genai
from google.generativeai import types
from google.api_core import exceptions as google_exceptions

from skls_generator.logger_config import get_logger

logger = get_logger(__name__)

load_dotenv(override=True)

class GoogleGenAI:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initializes the Google Gemini client.
        
        Args:
            api_key: Gemini API Key. Defaults to env var GEMINI_API_KEY.
            model_name: Model identifier (e.g., 'gemini-1.5-flash'). Defaults to env var GEMINI_MODEL.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL")

        if not self.api_key:
            raise ValueError("API Key is missing. Set GEMINI_API_KEY env var or pass it to the constructor.")
        
        if not self.model_name:
            logger.warning("No model name provided. Ensure GEMINI_MODEL is set. Defaulting to 'gemini-1.5-flash'.")
            self.model_name = "gemini-1.5-flash"

        # Configure the global genai client
        genai.configure(api_key=self.api_key) # pyright: ignore[reportPrivateImportUsage]

    
    def get_model(self) -> str:
        return self.model_name if self.model_name else "model_name is not accessible"
    
    
    def complete(self,
                 user: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 payload: Any = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> str:
        """
        Generates a response from the Gemini model.

        Args:
            user: The current user prompt.
            system_prompt: The system instruction.
            payload: A message history object (must have .messages attribute).
            temperature: The sampling temperature.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            The generated text response.
        """
        
        # --- 1. Prepare Message History (Contents) ---
        contents = []
        
        # If payload (history) exists, convert it to Gemini format
        if payload and hasattr(payload, 'messages'):
            for message in payload.messages:
                # Map roles: standard "assistant" -> Gemini "model"
                role = "model" if message.role in ["assistant", "model", "agent"] else "user"
                
                # Gemini treats 'system' prompt separately in the model constructor,
                # so we skip system messages inside the chat history to avoid errors.
                if message.role == "system":
                    continue
                
                contents.append({'role': role, 'parts': [{'text': message.content}]})

        # --- 2. Add Current User Input ---
        if user:
            contents.append({'role': 'user', 'parts': [{'text': user}]})

        if not contents:
            raise ValueError("No messages provided. Supply 'user' or 'payload'.")

        # --- 3. Instantiate Model with System Prompt ---
        # Google's SDK sets the system_instruction at instantiation, not per call.
        model_instance = genai.GenerativeModel( # pyright: ignore[reportPrivateImportUsage]
            model_name=self.model_name, # type: ignore
            system_instruction=system_prompt if system_prompt else None
        )

        generation_config = types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=0.9, # Standard default for Gemini
            top_k=40,
        )
        
        logger.debug(f"Sending to Gemini ({self.model_name}): {len(contents)} messages")
        retry_policy = retry.Retry(
            predicate=retry.if_exception_type(google_exceptions.DeadlineExceeded),
            initial=1.0, multiplier=2.0, maximum=60.0, deadline=600
        )
        try:
            # We use generate_content. If there is history (contents > 1), strictly speaking
            # we are passing a list of contents.
            response = model_instance.generate_content(
                contents=contents,
                generation_config=generation_config,
                stream=False, # Stream=False is easier for non-async usage
                request_options={"timeout": 600, "retry": retry_policy}
            )
            
            # Check if response was blocked (safety filters)
            if not response.parts:
                if response.prompt_feedback:
                    logger.warning(f"Gemini Safety Block: {response.prompt_feedback}")
                raise ValueError("Gemini returned an empty response (likely safety block).")

            return response.text

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Google API Error: {e}")
            raise e
        except ValueError as e:
            logger.error(f"Value Error (often content safety): {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in Gemini client: {e}")
            raise e

# Example Usage
if __name__ == "__main__":
    try:
        # Assumes GEMINI_API_KEY and GEMINI_MODEL are set in .env
        ai = GoogleGenAI() 
        
        logger.info("Sending request to Gemini...")
        response = ai.complete(
            system_prompt="You are a JSON robot.",
            user="Generate a JSON object for a car."
        )
        logger.info(f"\nResponse:\n{response}")
        
    except Exception as err:
        logger.error(f"Failed to generate: {err}")