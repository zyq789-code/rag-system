import pytest
from integrations.llm.base import LLMProvider
from integrations.llm.deepseek import DeepSeekProvider
from integrations.llm.openai import OpenAIProvider
from integrations.llm.factory import create_llm_provider
from core.config import Settings


def test_llm_provider_is_abstract():
    with pytest.raises(TypeError):
        LLMProvider()


def test_deepseek_provider_creation():
    settings = Settings(
        deepseek_api_key="test-key",
        deepseek_base_url="https://api.deepseek.com/v1",
        deepseek_model="deepseek-chat",
    )
    provider = DeepSeekProvider(settings)
    assert isinstance(provider, LLMProvider)


def test_openai_provider_creation():
    settings = Settings(
        openai_api_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        openai_model="gpt-4o",
    )
    provider = OpenAIProvider(settings)
    assert isinstance(provider, LLMProvider)


def test_factory_deepseek():
    settings = Settings(llm_provider="deepseek", deepseek_api_key="test")
    provider = create_llm_provider(settings)
    assert isinstance(provider, DeepSeekProvider)


def test_factory_openai():
    settings = Settings(llm_provider="openai", openai_api_key="test")
    provider = create_llm_provider(settings)
    assert isinstance(provider, OpenAIProvider)


def test_factory_unknown_raises():
    settings = Settings(llm_provider="unknown")
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_provider(settings)
