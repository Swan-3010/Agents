import json

from app.receipts.receipt_parser import ReceiptParser
from app.receipts.schemas import ReceiptParseRequest


class FakeLLMClient:
    def __init__(self, response: str):
        self.response = response

    def generate(self, prompt: str) -> str:
        return self.response


def test_parse_receipt_success():
    response = json.dumps({
        "store_name": "Amazon",
        "total_amount": "19.99",
        "currency": "USD",
        "receipt_url": "https://example.com/receipt/123",
        "confidence": 0.98,
        "errors": [],
    })
    parser = ReceiptParser(llm_client=FakeLLMClient(response))

    result = parser.parse(
        ReceiptParseRequest(
            message_text="Your Amazon order receipt. Total: $19.99",
            message_subject="Amazon receipt",
            message_from="auto-confirm@amazon.com",
        )
    )

    assert result.store_name == "Amazon"
    assert result.total_amount == "19.99"
    assert result.currency == "USD"
    assert result.receipt_url == "https://example.com/receipt/123"
    assert result.confidence == 0.98
    assert result.errors == []


def test_parse_receipt_without_url():
    response = json.dumps({
        "store_name": "Uber",
        "total_amount": "12.50",
        "currency": "EUR",
        "receipt_url": None,
        "confidence": 0.91,
        "errors": [],
    })
    parser = ReceiptParser(llm_client=FakeLLMClient(response))

    result = parser.parse(
        ReceiptParseRequest(message_text="Thanks for riding with Uber. Total 12.50 EUR")
    )

    assert result.store_name == "Uber"
    assert result.receipt_url is None
    assert result.total_amount == "12.50"
    assert result.currency == "EUR"


def test_parse_receipt_invalid_json_response():
    parser = ReceiptParser(llm_client=FakeLLMClient("not a json"))

    result = parser.parse(
        ReceiptParseRequest(message_text="Receipt text")
    )

    assert result.confidence == 0.0
    assert "invalid_json_response" in result.errors
    assert result.raw_llm_response == "not a json"


def test_parse_receipt_partial_data():
    response = json.dumps({
        "store_name": "Local Shop",
        "total_amount": None,
        "currency": None,
        "receipt_url": None,
        "confidence": 0.42,
        "errors": ["amount_not_found"],
    })
    parser = ReceiptParser(llm_client=FakeLLMClient(response))

    result = parser.parse(
        ReceiptParseRequest(message_text="Thank you for your purchase at Local Shop")
    )

    assert result.store_name == "Local Shop"
    assert result.total_amount is None
    assert result.currency is None
    assert "amount_not_found" in result.errors

def test_parse_receipt_json_wrapped_in_markdown_fence():
    response = """```json
{
  "store_name": "Test Store",
  "total_amount": 10.00,
  "currency": "USD",
  "receipt_url": null,
  "confidence": 0.95,
  "errors": []
}
```"""
    parser = ReceiptParser(llm_client=FakeLLMClient(response))

    result = parser.parse(
        ReceiptParseRequest(
            message_text="Thank you for shopping at Test Store. Total: 10.00 USD."
        )
    )

    assert result.store_name == "Test Store"
    assert result.total_amount == "10.0"
    assert result.currency == "USD"
    assert result.receipt_url is None
    assert result.confidence == 0.95
    assert result.errors == []
