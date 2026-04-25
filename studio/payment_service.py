import json
import os
from datetime import datetime, timezone
from PIL import Image
from google import genai


def _extract_json_block(text):
    text = (text or "").strip()
    if not text:
        return {}

    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    return json.loads(text[start:end + 1])


def analyze_ln_receipt(image_path, expected_sats, expected_payee, expected_invoice=None, max_age_days=2):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("NANO_BANANA_API_KEY")
    if not api_key:
        raise ValueError("Server Gemini key missing for payment verification.")

    model = os.environ.get("GEMINI_PAYMENT_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    invoice_hint = expected_invoice or ""
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    prompt = f"""
You are validating a Lightning Network payment receipt screenshot.

Validation requirements:
1) Payment must look COMPLETED/SENT/SUCCESSFUL (not pending).
2) Amount in sats must be >= {expected_sats}.
3) Recipient/payee should match this merchant identity when visible: {expected_payee}.
4) If invoice string is visible, it should be consistent with this hint: {invoice_hint}
5) Receipt date/time must be visible and recent (within {int(max_age_days)} day(s) of {now_utc}).

Return ONLY JSON in this shape:
{{
  "is_valid_payment": true/false,
  "payment_completed": true/false,
  "is_lightning_receipt": true/false,
  "detected_amount_sats": 0,
  "amount_meets_requirement": true/false,
  "payee_match": true/false,
  "detected_payee": "",
  "detected_invoice_or_hash": "",
  "date_visible": true/false,
  "receipt_datetime_iso": "",
  "is_recent_receipt": true/false,
  "reason": "short reason"
}}
"""

    image = Image.open(image_path)
    response = client.models.generate_content(
        model=model,
        contents=[prompt, image],
    )

    parsed = _extract_json_block(getattr(response, "text", ""))
    if not isinstance(parsed, dict):
        parsed = {}

    parsed.setdefault("is_valid_payment", False)
    parsed.setdefault("payment_completed", False)
    parsed.setdefault("is_lightning_receipt", False)
    parsed.setdefault("detected_amount_sats", 0)
    parsed.setdefault("amount_meets_requirement", False)
    parsed.setdefault("payee_match", False)
    parsed.setdefault("detected_payee", "")
    parsed.setdefault("detected_invoice_or_hash", "")
    parsed.setdefault("date_visible", False)
    parsed.setdefault("receipt_datetime_iso", "")
    parsed.setdefault("is_recent_receipt", False)
    parsed.setdefault("reason", "Unable to verify payment from provided image.")

    return parsed
