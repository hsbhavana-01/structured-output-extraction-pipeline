"""Extractor implementations: offline baseline and optional OpenAI structured output."""
import json
import os
import re
from decimal import Decimal, InvalidOperation
from typing import Protocol
from .schema import InvoiceRecord


class Extractor(Protocol):
    def extract(self, text: str) -> InvoiceRecord: ...


class RegexInvoiceExtractor:
    """Transparent offline baseline for benchmark/demo use; not a general-purpose parser."""
    DATE_PATTERNS = [
        r"(?:Invoice\s*Date|Date)\s*[:#-]?\s*(\d{4}-\d{2}-\d{2})",
        r"(?:Invoice\s*Date|Date)\s*[:#-]?\s*(\d{1,2})/(\d{1,2})/(\d{4})",
    ]
    def extract(self, text: str) -> InvoiceRecord:
        low = text.lower()
        if not re.search(r"\binvoice\b", low):
            return InvoiceRecord(document_type="not_invoice", evidence=[])

        def one(patterns):
            for pattern in patterns:
                match = re.search(pattern, text, re.I | re.M)
                if match:
                    return match
            return None

        inv = one([r"Invoice\s*(?:Number|No\.?|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9-]+)"])
        vendor = one([r"Vendor\s*[:#-]\s*(.+)", r"From\s*[:#-]\s*(.+)"])
        date_value = None
        m = re.search(self.DATE_PATTERNS[0], text, re.I)
        if m:
            date_value = m.group(1)
        else:
            m = re.search(self.DATE_PATTERNS[1], text, re.I)
            if m:
                a, b, year = map(int, m.groups())
                # Benchmark format is MM/DD/YYYY.
                date_value = f"{year:04d}-{a:02d}-{b:02d}"
        curr = one([r"Currency\s*[:#-]\s*([A-Z]{3})", r"Total\s*[:#-]?\s*(USD|EUR|GBP|INR|CAD|AUD)\s*"])
        currency = curr.group(1).upper() if curr else None
        amount_match = one([
            r"(?:Grand\s+)?Total\s*[:#-]?\s*(?:USD|EUR|GBP|INR|CAD|AUD)?\s*[$€£₹]?\s*([0-9][0-9,]*(?:\.[0-9]{2})?)\s*(?:USD|EUR|GBP|INR|CAD|AUD)?\b",
            r"Amount\s+Due\s*[:#-]?\s*[$€£₹]?\s*([0-9][0-9,]*(?:\.[0-9]{2})?)",
        ])
        amount = None
        if amount_match:
            try:
                amount = Decimal(amount_match.group(1).replace(",", ""))
            except InvalidOperation:
                amount = None
        if currency is None:
            if "$" in text: currency = "USD"
            elif "€" in text: currency = "EUR"
            elif "£" in text: currency = "GBP"
            elif "₹" in text: currency = "INR"
        evidence = []
        for line in text.splitlines():
            if re.search(r"invoice|vendor\s*:|from\s*:|invoice date|grand total|amount due|currency\s*:", line, re.I):
                evidence.append(line.strip()[:180])
            if len(evidence) >= 8: break
        return InvoiceRecord(
            document_type="invoice", invoice_number=inv.group(1) if inv else None,
            vendor_name=vendor.group(1).strip() if vendor else None,
            invoice_date=date_value, currency=currency, total_amount=amount, evidence=evidence,
        )


class OpenAIStructuredExtractor:
    """Uses OpenAI Structured Outputs. Install the 'openai' extra and set OPENAI_API_KEY."""
    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install with `pip install -e '.[openai]'` to use OpenAI extraction") from exc
        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def extract(self, text: str) -> InvoiceRecord:
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": (
                    "Extract invoice fields from the supplied document. Never infer missing values. "
                    "Use null for unavailable fields. If no invoice is present, document_type=not_invoice "
                    "and all invoice fields must be null. Dates must be valid YYYY-MM-DD. "
                    "Use ISO 4217 currency codes. Include short exact evidence snippets."
                )},
                {"role": "user", "content": text},
            ],
            text_format=InvoiceRecord,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("Model returned no parsed structured output")
        return parsed


def build_extractor(name: str = "regex") -> Extractor:
    if name == "regex": return RegexInvoiceExtractor()
    if name == "openai": return OpenAIStructuredExtractor()
    raise ValueError(f"Unknown extractor: {name}")
