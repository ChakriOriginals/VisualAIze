from __future__ import annotations
import itertools
import json
import logging
import time
import re
from typing import Type, TypeVar
from groq import Groq, RateLimitError
from pydantic import BaseModel, ValidationError
from backend.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
_client = None


GROQ_KEYS = [
    settings.groq_api_key,
]
_key_cycle = itertools.cycle([k for k in GROQ_KEYS if k])
_clients = {}

def _get_client():
    key = next(_key_cycle)
    if key not in _clients:
        _clients[key] = Groq(api_key=key)
    return _clients[key]


def llm_call(system_prompt, user_prompt, response_model, max_retries=2, max_tokens=None):
    client = _get_client()
    last_error = None
    tokens = max_tokens or settings.llm_max_tokens

    for attempt in range(max_retries + 1):
        try:
            logger.debug("Groq call attempt %d for %s", attempt + 1, response_model.__name__)
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nCRITICAL: Respond with valid JSON only. No markdown, no backticks, no explanation."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.llm_temperature,
                max_tokens=tokens,
                response_format={"type": "json_object"},  # forces JSON output
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            raw = raw.strip()
            data = json.loads(raw)
            return response_model.model_validate(data)

        except RateLimitError as exc:
            last_error = exc
            wait_time = (2 ** attempt) * 20
            logger.warning("Rate limit (attempt %d/%d), waiting %ds...", attempt + 1, max_retries + 1, wait_time)
            time.sleep(wait_time)

        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            logger.warning("Parse error (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)

        except Exception as exc:
            last_error = exc
            logger.error("Groq API error: %s", exc)
            raise

    raise RuntimeError(
        f"LLM failed to return valid {response_model.__name__} "
        f"after {max_retries + 1} attempts. Last error: {last_error}"
    )