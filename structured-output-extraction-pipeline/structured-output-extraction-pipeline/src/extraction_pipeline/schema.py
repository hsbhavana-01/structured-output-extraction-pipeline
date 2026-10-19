from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InvoiceRecord(BaseModel):
    """Normalized invoice fields. Missing fields are explicitly represented as None."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    document_type: Literal["invoice", "not_invoice", "uncertain"] = "uncertain"
    invoice_number: str | None = Field(default=None, max_length=100)
    vendor_name: str | None = Field(default=None, max_length=200)
    invoice_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    total_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    evidence: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("invoice_date")
    @classmethod
    def validate_iso_date(cls, value):
        if value is None:
            return value
        from datetime import date
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("invoice_date must be a valid ISO date YYYY-MM-DD") from exc
        if parsed.isoformat() != value:
            raise ValueError("invoice_date must use YYYY-MM-DD format")
        return value

    @model_validator(mode="after")
    def check_document_consistency(self):
        if self.document_type == "not_invoice" and any((self.invoice_number, self.vendor_name, self.invoice_date, self.currency, self.total_amount is not None)):
            raise ValueError("not_invoice records must not contain invoice fields")
        return self
