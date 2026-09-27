"invoice_extractor. Extract the price per pound and shipping date from invoice PDF files."
import re

import pandas as pd
import pdfplumber

SPANISH_MONTHS = {
        1: "ENERO",
        2: "FEBRERO",
        3: "MARZO",
        4: "ABRIL",
        5: "MAYO",
        6: "JUNIO",
        7: "JULIO",
        8: "AGOSTO",
        9: "SEPTIEMBRE",
        10: "OCTUBRE",
        11: "NOVIEMBRE",
        12: "DICIEMBRE"
    }

def format_invoice_date(raw_date):
    """Convert a date value to the invoice date format"""
    try:
        dt = pd.to_datetime(raw_date)
        return f"{dt.day:02d}-{SPANISH_MONTHS[dt.month]}-{dt.year}"
    except (ValueError, TypeError):
        return raw_date

def extract_invoice_data(invoice_path):
    """Extract the price per pound and shipping date from invoice PDF."""
    price_per_pound = None
    invoice_date = None

    with pdfplumber.open(invoice_path) as pdf:
        for page in pdf.pages:
            invoice_tables = page.extract_tables()

            for table in invoice_tables:
                if not table or len(table) < 2:
                    continue

                invoice_df = pd.DataFrame(table)

                for row_idx in range(len(invoice_df)):
                    for col_idx in range(len(invoice_df.columns)):
                        cell = str(
                        invoice_df.iloc[row_idx, col_idx]).lower()

                        # FIND AND FORMAT SHIPPING DATE
                        if 'date' in cell and (
                            'shipped' in cell or 'envoi' in cell):
                            if row_idx + 1 < len(invoice_df):
                                value_below = str(
                                    invoice_df.iloc[
                                        row_idx + 1,
                                        col_idx
                                    ]
                                ).strip()

                                if (
                                    re.search(r'\d', value_below)
                                    and invoice_date is None
                                ):
                                    raw_date = value_below.upper()
                                    invoice_date = format_invoice_date(raw_date)

                        # FIND UNIT PRICE
                        if 'unit price' in cell or 'unitaire' in cell:
                            for i in range(
                                row_idx + 1,
                                len(invoice_df)
                            ):
                                value_below = str(
                                    invoice_df.iloc[i, col_idx]
                                ).strip()

                                match = re.search(
                                    r'([0-9]+\.[0-9]{2,5})',
                                    value_below
                                )

                                if match and price_per_pound is None:
                                    price_per_pound = float(
                                        match.group(1)
                                    )
                                    break

    return price_per_pound, invoice_date