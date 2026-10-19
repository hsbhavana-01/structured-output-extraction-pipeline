"""Generate a reproducible synthetic benchmark with ground-truth labels."""
import json
from pathlib import Path
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "benchmark.jsonl"
vendors = ["Acme Paper Co", "Bluebird Logistics", "Cedar Labs", "Delta Office Mart", "Evergreen Hosting", "Fable Foods", "Granite Works", "Harbor Analytics", "Indigo Print Shop"]
currencies = ["USD", "EUR", "GBP", "INR", "CAD"]
rows = []
for i in range(45):
    vendor = vendors[i % len(vendors)]
    currency = currencies[i % len(currencies)]
    amount = f"{(i + 1) * 17}.{(i * 13) % 100:02d}"
    invno = f"INV-{2026}-{i+1:04d}"
    d = date(2026, 1, 1) + timedelta(days=i)
    iso = d.isoformat()
    # Cycle through common invoice layouts supported by the baseline.
    if i % 3 == 0:
        doc = f"INVOICE\nVendor: {vendor}\nInvoice Number: {invno}\nInvoice Date: {iso}\nCurrency: {currency}\nGrand Total: {currency} {amount}\nPayment due in 30 days."
    elif i % 3 == 1:
        doc = f"Invoice\nFrom: {vendor}\nInvoice No: {invno}\nDate: {d.month:02d}/{d.day:02d}/{d.year}\nCurrency: {currency}\nTotal: {currency} {amount}\nThank you for your business."
    else:
        symbol = {"USD":"$", "EUR":"€", "GBP":"£", "INR":"₹", "CAD":"$"}[currency]
        doc = f"INVOICE\nVendor: {vendor}\nInvoice #: {invno}\nInvoice Date: {iso}\nCurrency: {currency}\nSubtotal: {amount}\nGrand Total: {symbol}{amount}"
    rows.append({"id": f"inv-{i+1:03d}", "text": doc, "ground_truth": {
        "document_type": "invoice", "invoice_number": invno, "vendor_name": vendor,
        "invoice_date": iso, "currency": currency, "total_amount": amount
    }})
non_invoice_docs = [
    "RESUME\nCandidate: Priya Sharma\nExperience: 5 years in data analytics.",
    "JOB POSTING\nRole: Backend Engineer\nLocation: Bengaluru\nRequirements: Python and SQL.",
    "PUBLIC FILING\nQuarterly operational update for shareholders.",
    "MEETING NOTES\nDiscuss roadmap, hiring, and launch risks.",
    "RECIPE\nFlour, water, yeast, and salt. Bake until golden.",
    "TRAVEL ITINERARY\nTrain departs at 09:15; arrive by 12:40.",
    "PRODUCT DESCRIPTION\nA compact desk lamp with adjustable brightness.",
    "CUSTOMER FEEDBACK\nThe delivery was quick and packaging was neat.",
    "PROJECT PLAN\nPhase 1: research. Phase 2: prototype. Phase 3: test.",
    "NEWSLETTER\nCommunity events and announcements for October.",
    "EMPLOYEE PROFILE\nTeam: Engineering. Start date: 2021-04-15.",
    "SUPPORT TICKET\nIssue: login page loops after password reset.",
    "LAB REPORT\nSample ID: A-118. Result: within expected range.",
    "EVENT AGENDA\nWelcome, keynote, panel discussion, closing remarks.",
    "SHIPPING LABEL\nDestination: Bengaluru, Karnataka. Weight: 2.4 kg.",
]
for i, doc in enumerate(non_invoice_docs, 1):
    rows.append({"id": f"non-{i:03d}", "text": doc, "ground_truth": {
        "document_type": "not_invoice", "invoice_number": None, "vendor_name": None,
        "invoice_date": None, "currency": None, "total_amount": None
    }})
with OUT.open("w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(f"Wrote {len(rows)} samples to {OUT}")
