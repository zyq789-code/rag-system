from integrations.llm.base import LLMProvider
from integrations.llm.deepseek import DeepSeekProvider
from integrations.llm.openai import OpenAIProvider
from core.config import Settings


def create_llm_provider(settings: Settings) -> LLMProvider:
    providers: dict[str, type[LLMProvider]] = {
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider,
    }
    provider_class = providers.get(settings.llm_provider)
    if provider_class is None:
        raise ValueError(
            f"Unknown LLM provider: {settings.llm_provider}. "
            f"Available: {list(providers.keys())}"
        )
    return provider_class(settings)
