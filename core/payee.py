"""Turn a noisy bank narration into a short payee name.

    UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment  ->  swiggy
    UPI-ZOMATO LTD-ZOMATO@HDFCBANK-HDFC0000001-...      ->  zomato ltd

The categorizer (Day 2) works on this payee string, not the raw text.
"""
import re

# Words that describe the payment channel, not who was paid.
NOISE_WORDS = {
    "upi", "dr", "cr", "neft", "imps", "rtgs", "ach", "nach", "ecs", "pos",
    "to", "by", "transfer", "trf", "payment", "paid", "txn", "ref",
    "inb", "mb", "ib", "bil", "onl", "ecom", "purchase", "debit", "credit",
    "sent", "received", "using", "via", "collect", "request", "na", "null",
    "mandate", "autopay", "achdr", "achcr",
}

# 4-letter bank codes that appear inside UPI narrations.
BANK_CODES = {
    "sbin", "hdfc", "icic", "utib", "yesb", "kkbk", "punb", "barb", "cnrb",
    "ubin", "idib", "ioba", "indb", "fdrl", "kvbl", "tmbl", "cbin", "pytm",
    "airp", "aubl", "idfb", "rbls", "sibl", "jaka", "bkid", "mahb", "ucba",
}

IFSC = re.compile(r"^[a-z]{4}0[a-z0-9]{6}$")
SPLIT = re.compile(r"[/|\\:]+|\s-\s|-(?=\S)|--+")


def _is_noise(token: str) -> bool:
    if not token or token in NOISE_WORDS or token in BANK_CODES:
        return True
    if "@" in token:                       # UPI ID; the name part is elsewhere
        return True
    if IFSC.match(token) or re.fullmatch(r"[0-9x*]+", token):
        return True                        # IFSC codes, refs, masked 4123XXXX5678
    # Reference codes are mostly digits (N911856239313); initials like "k" are kept.
    letters = sum(c.isalpha() for c in token)
    return any(c.isdigit() for c in token) and letters < 2


def clean_payee(description: str) -> str:
    """Return the first meaningful chunk of a narration, lowercased."""
    if not isinstance(description, str) or not description.strip():
        return "unknown"
    text = description.lower().strip()
    for chunk in SPLIT.split(text):
        chunk = re.sub(r"[^a-z0-9&.\s]", " ", chunk)
        words = [w for w in chunk.split() if not _is_noise(w.strip("."))]
        if words:
            name = " ".join(w.strip(".") for w in words)
            # drop trailing domain junk: netflix.com -> netflix
            name = re.sub(r"\.(com|in|co|net|org)\b", "", name).strip()
            if name:
                return name
    return "unknown"
