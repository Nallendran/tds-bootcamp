from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dateutil import parser
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvoiceRequest(BaseModel):
    invoice_text: str

@app.post("/extract")
def extract(req: InvoiceRequest):

    text = req.invoice_text

    result = {
        "invoice_no": None,
        "date": None,
        "vendor": None,
        "amount": None,
        "tax": None,
        "currency": None
    }

    # Invoice number patterns
    patterns = [
        r"Invoice\s*No[:\s]+([A-Za-z0-9\-\/]+)",
        r"Ref[:\s]+([A-Za-z0-9\-\/]+)"
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            result["invoice_no"] = m.group(1)
            break

    # Date
    m = re.search(r"(?:Date|Issued)[:\s]+([^\n]+)", text, re.I)
    if m:
        try:
            result["date"] = parser.parse(m.group(1)).date().isoformat()
        except:
            pass

    # Vendor
    m = re.search(r"Vendor[:\s]+([^\n]+)", text, re.I)
    if m:
        result["vendor"] = m.group(1).strip()
    else:
        first_line = text.split("\n")[0].strip()
        if "invoice" not in first_line.lower():
            result["vendor"] = first_line.replace("— Tax Invoice", "").strip()

    # Currency
    m = re.search(r"Currency[:\s]+([A-Z]{3})", text)
    if m:
        result["currency"] = m.group(1)

    # Subtotal / Amount
    m = re.search(
        r"Subtotal[:.\s]*Rs\.?\s*([\d,]+\.\d+)",
        text,
        re.I
    )
    if m:
        result["amount"] = float(m.group(1).replace(",", ""))

    # Tax
    m = re.search(
        r"(?:GST|IGST|CGST|SGST|Tax)[^\n]*Rs\.?\s*([\d,]+\.\d+)",
        text,
        re.I
    )
    if m:
        result["tax"] = float(m.group(1).replace(",", ""))

    return result