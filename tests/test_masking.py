import pytest

from core.masking import mask_text
from core.payee import clean_payee


@pytest.mark.parametrize("raw, hidden, kept", [
    ("UPI/DR/412345678901/RAVI/SBIN/ravi.kumar99@okaxis/Pay", "ravi.kumar99", "ra***@okaxis"),
    ("UPI-KARTHIK-9876501234@YBL-YESB0YBLUPI", "9876501234", "@YBL"),
    ("Account Number 00000012345678901", "0000001234567", "8901"),
    ("UPI-SWIGGY-swiggy@icici-412345678901", "swiggy@", "UPI-SWIGGY-"),
    ("POS 4123XXXXXXXX5678 AMAZON", "4123XXXX", "5678 AMAZON"),
    # SBI truncates UPI IDs, sometimes leaving no @handle at all
    ("WDL TFR UPI/DR/412345678901/RAVI K/SBIN/ravikumar.9/ UPI 1234", "ravikumar", "/SBIN/ra***"),
    ("WDL TFR UPI/DR/412345678901/RAVI K/SBIN/ravikumar@/ UPI 1234", "ravikumar", "/SBIN/ra***"),
    ("WDL TFR UPI/DR/412345678901/RAVI K/SBIN/9876501234/ UPI 1234", "9876501234", "/SBIN/98***"),
    # Digits glued to letters
    ("DEP TFR PFN CMP12345678901234567 ACME", "12345678901234567", "CMPXXXXXXXXXXXXX4567"),
    ("DEBIT NACH123456789012", "123456789012", "NACHXXXXXXXX9012"),
])
def test_mask_text_hides_ids(raw, hidden, kept):
    masked = mask_text(raw)
    assert hidden not in masked
    assert kept in masked


def test_mask_keeps_short_numbers_and_amounts():
    assert mask_text("JIO 299 PLAN 2026") == "JIO 299 PLAN 2026"


def test_mask_handles_non_text():
    assert mask_text(None) is None


@pytest.mark.parametrize("narration, payee", [
    ("UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment", "swiggy"),
    ("TO TRANSFER-UPI/DR/345864938384/JIO PREPAID/YESB/jiorecharge@ybl/Payment--", "jio prepaid"),
    ("UPI-ZOMATO LTD-ZOMATO@HDFCBANK-HDFC0000499-628104123456-PAYMENT", "zomato ltd"),
    ("POS 4123XXXXXXXX5678 AMAZON PAY INDIA", "amazon pay india"),
    ("ACH/NETFLIX.COM/123456789012", "netflix"),
    ("NEFT/CR/N911856239313/BRIGHTPATH LABS PVT LTD/STIPEND", "brightpath labs pvt ltd"),
    ("DEBIT-ACHDr NETFLIX.COM 9876543210123", "netflix"),
    ("ATM WDL/SBI ATM ANNA NAGAR/123456789012", "atm wdl"),
    # SBI layout: optional branch first, branch details after the UPI fields
    ("WDL TFR UPI/DR/412345678901/SWIGGY/YESB/swiggy/ UPI 1234567890123 AT 01234 STATION ROAD BRANCH", "swiggy"),
    ("CITYNAME DEP TFR UPI/CR/412345678901/RAVI K/SBIN/ravi/ UPI 1234567890123 AT 01234 MAIN ROAD", "ravi k"),
    ("UPI DEP TFR 1234567890123 AT 01234 MAIN ROAD BRANCH UPI/CR/412345678901/PRIYA S/SBIN/priya", "priya s"),
    ("WDL TFR UPI/DR/412345678901/12345678/YESB/9876501234/", "unknown"),
    ("CITYNAME DEP TFR PFN CMP12345678901234567 ACME TRADERS", "acme traders"),
    ("", "unknown"),
    (None, "unknown"),
])
def test_clean_payee(narration, payee):
    assert clean_payee(narration) == payee
