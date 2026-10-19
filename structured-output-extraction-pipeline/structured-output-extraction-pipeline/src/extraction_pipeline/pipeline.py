from dataclasses import dataclass, asdict
from typing import Any
from pydantic import ValidationError
from .schema import InvoiceRecord


@dataclass
class ExtractionResult:
    status: str
    data: dict[str, Any] | None
    attempts: int
    errors: list[str]
    review_reason: str | None = None


class ExtractionPipeline:
    """Validates every result; failed attempts are retried and then routed to review."""
    def __init__(self, extractor, max_attempts: int = 3):
        if max_attempts < 1: raise ValueError("max_attempts must be >= 1")
        self.extractor = extractor
        self.max_attempts = max_attempts

    def run(self, text: str) -> ExtractionResult:
        errors = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                raw = self.extractor.extract(text)
                if isinstance(raw, InvoiceRecord):
                    validated = InvoiceRecord.model_validate(raw.model_dump())
                else:
                    validated = InvoiceRecord.model_validate(raw)
                return ExtractionResult("accepted", validated.model_dump(mode="json"), attempt, errors)
            except (ValidationError, ValueError, TypeError, RuntimeError) as exc:
                errors.append(f"attempt {attempt}: {type(exc).__name__}: {str(exc)[:500]}")
            except Exception as exc:
                # Provider/network errors are not silently accepted either.
                errors.append(f"attempt {attempt}: {type(exc).__name__}: {str(exc)[:500]}")
        return ExtractionResult("needs_review", None, self.max_attempts, errors,
                               "No valid schema-conforming output after configured attempts")
