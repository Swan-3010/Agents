RECEIPT_EXTRACTION_PROMPT_TEMPLATE = """
You extract structured receipt data from email content.

Return JSON with fields:
- store_name
- total_amount
- currency
- receipt_url
- confidence
- errors

Rules:
- If a field is missing, return null.
- confidence must be a number between 0 and 1.
- errors must be an array of strings.
- Return JSON only.

Email subject:
{subject}

Email from:
{sender}

Email body:
{text}
""".strip()
