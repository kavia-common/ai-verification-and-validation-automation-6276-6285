import os
from typing import Optional


class BaseLLM:
    """Abstract base LLM provider."""

    # PUBLIC_INTERFACE
    def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate text from a prompt using an LLM backend."""
        raise NotImplementedError


class MockLLM(BaseLLM):
    """Deterministic mock LLM for local/dev environments."""

    def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        # Return a synthetic predictable JSON-like content for test cases
        return (
            '{ "test_cases": ['
            '{ "id": "REQ-1", "title": "Sample login", "steps": ["Go to /login", "Enter user", "Enter pass", "Click Login"], "expected": "Dashboard" },'
            '{ "id": "REQ-2", "title": "Sample logout", "steps": ["Click profile", "Click Logout"], "expected": "Login page" }'
            "] }"
        )


class OpenAILLM(BaseLLM):
    """OpenAI provider implementation, used only if OPENAI_API_KEY is present."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import openai  # type: ignore

            self._openai = openai
            self._openai.api_key = api_key
        except Exception:
            self._openai = None

    def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        if not self._openai:
            # Fallback safe behavior
            return MockLLM().generate_text(prompt, model)
        model_name = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
        try:
            # Simplified completion for portability; adapt to latest SDKs if needed
            resp = self._openai.ChatCompletion.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message["content"]
        except Exception:
            # Fallback on any error
            return MockLLM().generate_text(prompt, model)


# PUBLIC_INTERFACE
def get_llm() -> BaseLLM:
    """Select a concrete LLM provider based on environment, defaulting to Mock."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return OpenAILLM(api_key)
    return MockLLM()
