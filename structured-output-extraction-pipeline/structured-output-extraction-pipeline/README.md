# Structured Output Extraction Pipeline

Turn messy document text into validated, typed invoice data. The pipeline validates every extraction, retries invalid/error outputs, and routes exhausted failures to `needs_review` rather than accepting them silently. It includes an offline regex baseline, an optional OpenAI Structured Outputs adapter, tests, a 60-sample synthetic benchmark, and a reproducible evaluation script.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  | macOS/Linux: source .venv/bin/activate
pip install -e '.[test]'
pytest
python scripts/evaluate.py
python -m extraction_pipeline.cli data/sample_invoice.txt
```

For model-backed extraction:

```bash
pip install -e '.[openai,test]'
# Set OPENAI_API_KEY in your environment; optionally set OPENAI_MODEL.
python -m extraction_pipeline.cli data/sample_invoice.txt --extractor openai
```

Never commit API keys. The OpenAI adapter uses Pydantic-backed Structured Outputs; the pipeline validates the parsed object again at the application boundary.

## Contract and failure semantics

- `InvoiceRecord` is the typed schema (`src/extraction_pipeline/schema.py`). Unknown keys are forbidden; currency, ISO date, amount, and non-invoice consistency are validated.
- Missing target fields are represented as `null`, not guessed.
- `accepted` means schema validation passed.
- `needs_review` means every attempt failed; `data` is null and diagnostics are preserved.
- The regex extractor is a transparent baseline for this synthetic dataset, not a claim of production-grade document understanding. Use the OpenAI adapter or another provider for varied real-world documents.

## Evaluation

`python scripts/evaluate.py` scores 60 deterministic synthetic examples with ground truth: 45 invoice-like documents and 15 documents without invoice fields. It reports field-level accuracy over all target fields, exact-record accuracy, non-invoice classification accuracy, and the count routed to review. The committed `docs/accuracy_report.md` records the baseline run. This is a synthetic smoke benchmark, not evidence of real-world performance; replace/add a labeled, representative dataset before deployment.

## Suggested next steps for production

1. Add a human-review queue and persist `needs_review` records with access controls.
2. Evaluate on 50+ independently sourced, labeled documents and report per-field precision/recall, exact-match accuracy, and confidence intervals.
3. Add OCR and document-type routing for PDFs/images; preserve provenance and source spans.
4. Add provider timeouts, rate-limit handling, observability, PII redaction, and versioned prompts/schemas.
