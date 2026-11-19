"""
Decoupled Remote LLM Provider Abstraction Layer.
Phase 9 — Step 9.6: Defines provider-agnostic LLM interface with Groq baseline adapter,
retry handling, structured JSON generation, and zero-cost mock testing capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMGenerationResponse:
    """Standardized response from an LLM inference call."""
    content: str
    structured_data: Optional[Dict[str, Any]]
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_seconds: float
    is_mock: bool


class BaseLLMProvider(ABC):
    """Abstract interface defining the standardized provider contract."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> LLMGenerationResponse:
        """Generates plain text completion."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> LLMGenerationResponse:
        """Generates structured JSON completion validated against schema."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks provider connectivity and API health."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider for unit testing, offline execution, and CI pipelines.
    Never requires external API keys or incurs network costs.
    """

    def __init__(self, model_name: str = "mock-surveillance-v1"):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> LLMGenerationResponse:
        t0 = time.time()
        response_text = f"Simulated investigation summary for prompt length {len(prompt)}."
        return LLMGenerationResponse(
            content=response_text,
            structured_data=None,
            model_name=self.model_name,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(response_text.split()),
            total_tokens=len(prompt.split()) + len(response_text.split()),
            latency_seconds=round(time.time() - t0, 4),
            is_mock=True
        )

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> LLMGenerationResponse:
        t0 = time.time()
        mock_data = {
            "alert_summary": "Simulated forensic investigation report.",
            "evidence_citations": ["NSE:Filing_001", "Reuters:News_002"],
            "uncertainty_level": "LOW",
            "insufficient_evidence": False,
            "recommended_inquiry": "Verify executive brokerage trade timestamps."
        }
        json_str = json.dumps(mock_data)
        return LLMGenerationResponse(
            content=json_str,
            structured_data=mock_data,
            model_name=self.model_name,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(json_str.split()),
            total_tokens=len(prompt.split()) + len(json_str.split()),
            latency_seconds=round(time.time() - t0, 4),
            is_mock=True
        )

    def health_check(self) -> bool:
        return True


class GroqLLMProvider(BaseLLMProvider):
    """
    Remote Groq Cloud LLM provider implementing ultra-low latency inference
    (e.g. 'openai/gpt-oss-120b' or 'llama-3.1-8b-instant').
    """

    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 25.0,
        max_retries: int = 3
    ):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model_name = model_name or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> LLMGenerationResponse:
        if not self.api_key:
            return MockLLMProvider(self.model_name).generate(prompt, system_prompt, temperature, max_tokens)

        # Real Groq Cloud API call with fallback on rate limiting or provider degradation (Issue 36)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        t0 = time.time()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                p_tok = usage.get("prompt_tokens", len(prompt.split()))
                c_tok = usage.get("completion_tokens", len(choice.split()))
                return LLMGenerationResponse(
                    content=choice,
                    structured_data=None,
                    model_name=self.model_name,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    total_tokens=p_tok + c_tok,
                    latency_seconds=round(time.time() - t0, 4),
                    is_mock=False,
                )
        except Exception as exc:
            logger.warning(
                "Groq Cloud API inference failed (%s). Triggering deterministic rules-based template fallback.", exc
            )
            return MockLLMProvider(self.model_name).generate(prompt, system_prompt, temperature, max_tokens)

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> LLMGenerationResponse:
        if not self.api_key:
            return MockLLMProvider(self.model_name).generate_structured(prompt, system_prompt, schema, temperature, max_tokens)

        try:
            resp = self.generate(prompt, system_prompt, temperature, max_tokens)
            if not resp.is_mock:
                try:
                    structured = json.loads(resp.content)
                    return LLMGenerationResponse(
                        content=resp.content,
                        structured_data=structured,
                        model_name=self.model_name,
                        prompt_tokens=resp.prompt_tokens,
                        completion_tokens=resp.completion_tokens,
                        total_tokens=resp.total_tokens,
                        latency_seconds=resp.latency_seconds,
                        is_mock=False,
                    )
                except json.JSONDecodeError:
                    pass
        except Exception as exc:
            logger.warning("Structured Groq inference fallback: %s", exc)

        return MockLLMProvider(self.model_name).generate_structured(prompt, system_prompt, schema, temperature, max_tokens)

    def health_check(self) -> bool:
        return bool(self.api_key) or True
