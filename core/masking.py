"""Hide sensitive identifiers in transaction descriptions.

Runs right after parsing, so account numbers, card numbers, phone numbers
and UPI IDs never reach the rest of the app in readable form.
"""
import re

import pandas as pd

# name@handle, e.g. ravi.kumar99@okaxis or 9876543210@ybl
UPI_ID = re.compile(r"\b([A-Za-z0-9._]+)@([A-Za-z][A-Za-z0-9]+)\b")

# Long digit runs: account numbers, card numbers, phone numbers, UPI refs.
# Also catches partly-masked forms banks print, like 4123XXXXXXXX5678.
LONG_NUMBER = re.compile(r"\b[0-9Xx*]{5,}[0-9]{4}\b")


def mask_upi_id(match: re.Match) -> str:
    """ravi.kumar99@okaxis -> ra***@okaxis"""
    user, handle = match.group(1), match.group(2)
    return f"{user[:2]}***@{handle}"


def mask_number(match: re.Match) -> str:
    """123456789012 -> XXXXXXXX9012 (keep last 4, like banks do)."""
    text = match.group(0)
    return "X" * (len(text) - 4) + text[-4:]


def mask_text(text: str) -> str:
    """Mask UPI IDs first (they can contain digits), then long numbers."""
    if not isinstance(text, str):
        return text
    text = UPI_ID.sub(mask_upi_id, text)
    return LONG_NUMBER.sub(mask_number, text)


def mask_transactions(df: pd.DataFrame, column: str = "description") -> pd.DataFrame:
    """Return a copy of df with the given text column masked."""
    out = df.copy()
    out[column] = out[column].map(mask_text)
    return out
