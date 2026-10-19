from extraction_pipeline.pipeline import ExtractionPipeline
from extraction_pipeline.schema import InvoiceRecord

class SequenceExtractor:
    def __init__(self, outputs): self.outputs, self.i = outputs, 0
    def extract(self, text):
        out = self.outputs[min(self.i, len(self.outputs)-1)]; self.i += 1
        if isinstance(out, Exception): raise out
        return out

def test_valid_output_accepted():
    p = ExtractionPipeline(SequenceExtractor([{"document_type":"invoice", "invoice_number":"INV-1", "total_amount":"10.00"}]))
    r = p.run("invoice")
    assert r.status == "accepted" and r.data["invoice_number"] == "INV-1"

def test_invalid_then_valid_retried():
    p = ExtractionPipeline(SequenceExtractor([{"document_type":"invoice", "currency":"US"}, {"document_type":"invoice", "currency":"USD"}]), 2)
    r = p.run("invoice")
    assert r.status == "accepted" and r.attempts == 2 and len(r.errors) == 1

def test_failed_outputs_routed_to_review():
    p = ExtractionPipeline(SequenceExtractor([{"document_type":"not_invoice", "invoice_number":"oops"}]), 2)
    r = p.run("nothing")
    assert r.status == "needs_review" and r.data is None and r.attempts == 2

def test_non_invoice_allows_empty_target_fields():
    r = ExtractionPipeline(SequenceExtractor([InvoiceRecord(document_type="not_invoice")])).run("a résumé")
    assert r.status == "accepted" and r.data["document_type"] == "not_invoice"
