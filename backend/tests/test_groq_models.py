import pytest

from app.services.ai.models import GROQ_ALLOWED_MODELS, resolve_model, text_model_fallback_chain


def test_text_model_fallback_chain_starts_with_primary():
    chain = text_model_fallback_chain("llama-3.3-70b-versatile")
    assert chain[0] == "llama-3.3-70b-versatile"
    assert "qwen/qwen3-32b" in chain
    assert len(chain) == len(GROQ_ALLOWED_MODELS)


def test_resolve_default_text_model():
    assert resolve_model(None) == "llama-3.3-70b-versatile"


def test_resolve_default_vision_model():
    assert resolve_model(None, vision=True) == "meta-llama/llama-4-scout-17b-16e-instruct"


def test_resolve_explicit_model():
    model = "qwen/qwen3-32b"
    assert resolve_model(model) == model


def test_resolve_vision_fallback_for_non_vision_model():
    assert resolve_model("qwen/qwen3-32b", vision=True) == "meta-llama/llama-4-scout-17b-16e-instruct"


def test_reject_unknown_model():
    with pytest.raises(ValueError):
        resolve_model("unknown/model")


def test_allowed_models_set():
    assert len(GROQ_ALLOWED_MODELS) == 4
