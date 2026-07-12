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


def extract_amount(value):
    try:
        return float(value.replace(",", "").strip())
    except:
        return None


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

    # -------------------------
    # Invoice Number
    # -------------------------
    invoice_patterns = [
        r"Invoice\s*(?:No|Number)?\s*[:#]?\s*([A-Z0-9\-\/]+)",
        r"Inv\s*(?:No|Number)?\s*[:#]?\s*([A-Z0-9\-\/]+)",
        r"Ref(?:erence)?\s*[:#]?\s*([A-Z0-9\-\/]+)",
        r"Order\s*Code\s*[:#]?\s*([A-Z0-9\-\/]+)",
        r"Document\s*No\s*[:#]?\s*([A-Z0-9\-\/]+)",
        r"Bill\s*No\s*[:#]?\s*([A-Z0-9\-\/]+)"
    ]

    for pattern in invoice_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            result["invoice_no"] = m.group(1).strip()
            break

    # -------------------------
    # Date
    # -------------------------
    date_patterns = [
        r"(?:Date|Issued|Invoice Date)\s*[:#]?\s*([^\n]+)",
    ]

    for pattern in date_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                result["date"] = parser.parse(
                    m.group(1).strip(),
                    fuzzy=True
                ).date().isoformat()
                break
            except:
                pass

    # -------------------------
    # Vendor
    # -------------------------
    vendor_patterns = [
        r"Vendor\s*[:#]?\s*([^\n]+)",
        r"Supplier\s*[:#]?\s*([^\n]+)",
        r"From\s*[:#]?\s*([^\n]+)"
    ]

    for pattern in vendor_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            result["vendor"] = m.group(1).strip()
            break

    if result["vendor"] is None:
        first_line = text.splitlines()[0].strip()
        if len(first_line) > 3:
            result["vendor"] = re.sub(
                r"tax invoice|invoice",
                "",
                first_line,
                flags=re.I
            ).strip(" -—:")

    # -------------------------
    # Currency
    # -------------------------
    m = re.search(r"Currency\s*[:#]?\s*([A-Z]{3})", text, re.I)

    if m:
        result["currency"] = m.group(1).upper()
    elif "Rs" in text or "₹" in text:
        result["currency"] = "INR"
    elif "$" in text:
        result["currency"] = "USD"

    # -------------------------
    # Amount (subtotal before tax)
    # -------------------------
    amount_patterns = [
        r"Subtotal\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Sub[- ]?Total\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Amount\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Net Amount\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Base Amount\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Taxable Value\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Before Tax\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)"
    ]

    for pattern in amount_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            result["amount"] = extract_amount(m.group(1))
            break

    # -------------------------
    # Tax
    # -------------------------
    tax_patterns = [
        r"IGST.*?(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"CGST.*?(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"SGST.*?(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"GST.*?(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        r"Tax.*?(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)"
    ]

    taxes = []

    for pattern in tax_patterns:
        for match in re.finditer(pattern, text, re.I):
            value = extract_amount(match.group(1))
            if value is not None:
                taxes.append(value)

    if taxes:
        result["tax"] = round(sum(taxes), 2)

    # -------------------------
    # Amount fallback
    # -------------------------
    if result["amount"] is None:

        amount_patterns = [
            r"Amount\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
            r"Net Amount\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
            r"Base Amount\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
            r"Taxable Value\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
            r"Before Tax\s*[:.]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)"
        ]

        for pattern in amount_patterns:
            m = re.search(pattern, text, re.I)
            if m:
                result["amount"] = extract_amount(m.group(1))
                break

    # -------------------------
    # Last fallback for amount
    # -------------------------
    if result["amount"] is None:

        numbers = re.findall(
            r"(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)",
            text,
            re.I
        )

        values = []

        for n in numbers:
            try:
                values.append(float(n.replace(",", "")))
            except:
                pass

        if values:

            if result["tax"] is not None:
                candidates = [v for v in values if v > result["tax"]]

                if candidates:
                    result["amount"] = sorted(candidates)[-1]

            if result["amount"] is None:
                result["amount"] = sorted(values)[-1]

    return result