from unittest.mock import Mock, patch

import pytest
import requests

from app.receipts.llm_integrator import OllamaLLMClient


def test_generate_calls_ollama_api():
    mock_response = Mock()
    mock_response.json.return_value = {"response": "{\"store_name\": \"Amazon\"}"}
    mock_response.raise_for_status.return_value = None

    client = OllamaLLMClient(
        model="llama3.2",
        base_url="http://localhost:11434",
        timeout=30.0,
    )

    with patch("app.receipts.llm_integrator.requests.post", return_value=mock_response) as mock_post:
        result = client.generate("Extract receipt data")

    assert result == "{\"store_name\": \"Amazon\"}"

    mock_post.assert_called_once_with(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": "Extract receipt data",
            "stream": False,
        },
        timeout=30.0,
    )


def test_generate_strips_trailing_slash_from_base_url():
    mock_response = Mock()
    mock_response.json.return_value = {"response": "ok"}
    mock_response.raise_for_status.return_value = None

    client = OllamaLLMClient(
        model="llama3.2",
        base_url="http://localhost:11434/",
    )

    with patch("app.receipts.llm_integrator.requests.post", return_value=mock_response) as mock_post:
        client.generate("prompt")

    mock_post.assert_called_once()
    called_url = mock_post.call_args.args[0]
    assert called_url == "http://localhost:11434/api/generate"


def test_generate_raises_for_http_errors():
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("boom")

    client = OllamaLLMClient(model="llama3.2")

    with patch("app.receipts.llm_integrator.requests.post", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            client.generate("prompt")
