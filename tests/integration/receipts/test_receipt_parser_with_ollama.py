import os
import pytest

from app.receipts.llm_integrator import OllamaLLMClient
from app.receipts.receipt_parser import ReceiptParser
from app.receipts.schemas import ReceiptParseRequest


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_OLLAMA_TESTS"),
    reason="Set RUN_OLLAMA_TESTS=1 to run Ollama integration tests",
)
def test_receipt_parser_with_real_ollama():
    client = OllamaLLMClient()
    parser = ReceiptParser(llm_client=client)

    request = ReceiptParseRequest(
        message_text="Thank you for shopping at Test Store. Total: 10.00 USD.",
        message_subject="Your receipt from Test Store",
        message_from="no-reply@test-store.com",
    )

    result = parser.parse(request)

    assert result.raw_llm_response
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.errors, list)
