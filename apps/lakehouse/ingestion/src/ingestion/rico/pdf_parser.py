import re
from base64 import b64decode
from io import BytesIO
from decimal import Decimal

import pendulum
import pdfplumber
from pdfplumber.page import Page

_HEADER_RE = re.compile(
    r"Nr\.\s*nota\s+Folha\s+Data\s+preg[ãa]o\s*\n\s*(?P<note_number>\d+)\s+\d+\s+"
    r"(?P<negotiation_date>\d{2}/\d{2}/\d{4})"
)
_GROSS_RE = re.compile(
    r"Valor l[íi]quido das opera[çc][õo]es\s+(?P<value>[\d.]+,\d{2})(?:\s+(?P<dc>[DC]))?"
)
_NET_RE = re.compile(
    r"L[íi]quido para\s+\d{2}/\d{2}/\d{4}\s+(?P<value>[\d.]+,\d{2})(?:\s+(?P<dc>[DC]))?"
)
_OPERATIONS = {"C": "buy", "V": "sell"}
_MARKET_TYPES = {"VISTA": "standard", "FRACIONARIO": "fractional"}


def parse_note(record: dict, password: str) -> dict:
    pdf_bytes = b64decode(record["contentBytes"])

    with pdfplumber.open(BytesIO(pdf_bytes), password=password) as pdf:
        header = _HEADER_RE.search(pdf.pages[0].extract_text() or "")

        if header is None:
            raise ValueError(f"Header not found in attachment {record['id']}")

        trades = [trade for page in pdf.pages for trade in _parse_trades(page)]

        gross, net = _parse_financial_summary(pdf.pages[-1])

    return {
        "id": int(header["note_number"]),
        "negotiation_date": pendulum.from_format(
            header["negotiation_date"], "DD/MM/YYYY"
        ).date(),
        "trades": trades,
        "taxes": abs(gross - net),
        "net_amount": net,
        "gross_amount": gross,
    }


def _parse_trades(page: Page) -> list[dict]:
    top_hits = page.search(r"Negócios realizados")

    if not top_hits:
        return []

    bottom_hits = page.search(r"Resumo dos Negócios")
    bottom = bottom_hits[0]["top"] if bottom_hits else page.height

    region = page.crop((0, top_hits[0]["bottom"], page.width, bottom))

    rects = sorted(region.rects, key=lambda r: (r["top"], r["x0"]))

    if not rects:
        return []

    first_row = [r for r in rects if abs(r["top"] - rects[0]["top"]) < 1]

    columns = [r["x0"] for r in first_row] + [first_row[-1]["x1"]]

    table = region.extract_table(
        {
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": columns,
            "horizontal_strategy": "text",
        }
    )

    return [
        {
            "operation": _OPERATIONS[operation],
            "market_type": _MARKET_TYPES[market_type],
            "asset": asset,
            "quantity": int(quantity),
            "price": Decimal(price.replace(".", "").replace(",", ".")),
        }
        for _, _, operation, market_type, _, asset, _, quantity, price, _, dc in (
            table or []
        )
        if dc in ("C", "D")
    ]


def _parse_financial_summary(page: Page) -> tuple[Decimal, Decimal]:
    anchor = page.search(r"Resumo Financeiro")[0]

    region = page.crop(
        (anchor["x0"] - 2, anchor["bottom"] + 1, page.width, page.height)
    )

    text = region.extract_text()

    gross = _GROSS_RE.search(text)
    net = _NET_RE.search(text)

    if gross is None or net is None:
        raise ValueError("Financial summary not found")

    return (
        Decimal(gross["value"].replace(".", "").replace(",", ".")),
        Decimal(net["value"].replace(".", "").replace(",", ".")),
    )
