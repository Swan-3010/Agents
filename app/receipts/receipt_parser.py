import json

from app.receipts.interfaces import LLMClient
from app.receipts.prompts import RECEIPT_EXTRACTION_PROMPT_TEMPLATE
from app.receipts.schemas import ReceiptParseRequest, ReceiptParseResult


class ReceiptParser:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _normalize_raw_response(self, raw_response: str) -> str:
        text = raw_response.strip()

        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return text

    def parse(self, request: ReceiptParseRequest) -> ReceiptParseResult:
        prompt = RECEIPT_EXTRACTION_PROMPT_TEMPLATE.format(
            subject=request.message_subject or "",
            sender=request.message_from or "",
            text=request.message_text,
        )

        raw_response = self.llm_client.generate(prompt)
        normalized_response = self._normalize_raw_response(raw_response)

        try:
            payload = json.loads(normalized_response)
        except json.JSONDecodeError:
            return ReceiptParseResult(
                confidence=0.0,
                raw_llm_response=raw_response,
                errors=["invalid_json_response"],
            )

        return ReceiptParseResult(
            store_name=payload.get("store_name"),
            total_amount=str(payload["total_amount"]) if payload.get("total_amount") is not None else None,
            currency=payload.get("currency"),
            receipt_url=payload.get("receipt_url"),
            confidence=float(payload.get("confidence", 0.0)),
            raw_llm_response=raw_response,
            errors=payload.get("errors", []),
        )
