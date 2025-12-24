import json
import time
import re
from typing import Type, TypeVar, Optional, Any, List, Dict
from pydantic import BaseModel, ValidationError

from skls_generator.utils import measure_time

try:
    from json_repair import repair_json
except ImportError:
    raise ImportError("Please run: pip install json_repair")

# Import logger with fallback
try:
    # Try relative import first (when used as part of the package)
    from ..skls_core.logging import get_skls_logger
except (ImportError, ValueError):
    try:
        # Fallback to absolute import (when used as standalone package)
        from skls_core.logging import get_skls_logger
    except ImportError:
        # Final fallback when used as part of larger project
        import logging
        get_skls_logger = logging.getLogger

RETRIES_COUNT = 8
logger = get_skls_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class Generator:
    """
    A class to generate instances of Pydantic models by instructing an LLM.
    """

    def __init__(self, client, logger_instance=None):
        self.client = client
        self.logger = logger_instance if logger_instance is not None else get_skls_logger(__name__)
        self.logger.info(f"Generator initialized with model: {self.client.get_model()}")

    def _parse_and_repair_json(self, text_response: str) -> Dict[str, Any]:
        """
        Robustly extracts and parses JSON, fixing syntax errors automatically.
        Handles:
        - Markdown code blocks
        - Unclosed parentheses/braces
        - Trailing commas
        - Single quotes instead of double
        """
        # 1. First pass: Remove Markdown code blocks purely to clean up noise
        # (json_repair usually handles this, but regex is faster for large text blocks)
        text_response = re.sub(r'```json\s*', '', text_response)
        text_response = re.sub(r'```\s*', '', text_response)

        # 2. Attempt to repair and load
        try:
            # return_objects=True makes it return the Dict immediately, 
            # rather than a repaired JSON string.
            parsed_json = repair_json(text_response, return_objects=True)
            
            # 3. Validation: repair_json might return a list if the LLM output a list.
            # If we expect a dict (single object), ensure we got one.
            if isinstance(parsed_json, list) and parsed_json:
                # Heuristic: If we wanted an object but got a list,
                # maybe the LLM wrapped it in [ ... ]
                self.logger.warning("Received a list but expected a Dict. Using first item.")
                return parsed_json[0]
            
            if not isinstance(parsed_json, (dict, list)):
                raise ValueError("Parsed result is not a valid JSON structure (Dict or List).")

            return parsed_json # type: ignore

        except Exception as e:
            # If repair failed, it's garbage text
            raise ValueError(f"Fatal JSON parsing error: {e}")

    @measure_time(logger)
    def generate_one_shot(
        self,
        pydantic_model: Type[T],
        prompt: Optional[str] = None,
        language: Optional[str] = None,
        retries: int = RETRIES_COUNT,
        system_prompt_override: str = "",
        temperature: float = 0.7
    ) -> T:
        """
        Generates a Pydantic instance. Includes Self-Correction logic.
        """
        schema_json = json.dumps(pydantic_model.model_json_schema(), indent=2)
        
        system_prompt = (
            "You are a strict JSON generation API. \n"
            "Output ONLY valid JSON. \n"
            "Do not output markdown blocks, comments, or conversational text."
        )
        if system_prompt_override:
            system_prompt = system_prompt_override

        description = prompt if prompt else "Generate a creative, random example."
        lang_instruction = f"All string values must be in {language}." if language else ""
        
        initial_user_prompt = f"""
Target JSON Schema:
{schema_json}

Instructions:
1. {description}
2. {lang_instruction}
3. Strict Adherence to the Schema is required.
"""
        
        class MessagePayload:
            def __init__(self):
                self.messages = []
            def add(self, role, content):
                self.messages.append(type('obj', (object,), {'role': role, 'content': content}))

        history = MessagePayload()
        history.add("user", initial_user_prompt)

        for i in range(retries):
            self.logger.info(f"Attempt {i + 1}/{retries} for {pydantic_model.__name__}")

            try:
                # Call the API
                response_text = self.client.complete(
                    system_prompt=system_prompt,
                    payload=history,
                    temperature=temperature,
                    max_tokens=2048
                )

                # ---------------------------------------------------
                # CHANGED: Use the robust repair method
                # ---------------------------------------------------
                parsed_data = self._parse_and_repair_json(response_text)

                # Validation against Pydantic
                instance = pydantic_model(**parsed_data)
                return instance

            except ValidationError as e:
                error_msg = f"Schema Validation Failed: {e.errors()}"
                self.logger.warning(error_msg)

                # Reflexion: Tell LLM what went wrong
                history.add("assistant", response_text) # type: ignore
                history.add("user", f"JSON valid, but schema invalid: {e}. Fix structure.")

            except ValueError as e:
                # This catches the JSON parsing errors from _parse_and_repair_json
                error_msg = f"JSON Parsing Failed (even after repair): {str(e)}"
                self.logger.warning(error_msg)

                history.add("assistant", response_text) # type: ignore
                history.add("user", "Output was unreadable JSON. Output ONLY valid JSON.")

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(1)

        raise Exception(f"Failed to generate valid {pydantic_model.__name__} after {retries} attempts.")