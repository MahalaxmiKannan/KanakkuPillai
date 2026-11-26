import re
from pathlib import Path

import pandas as pd
import pytest

from core.scam_detector import (MASK_RE, assess, defang, find_flags, highlight_html, level_for, load_model, model_view,
                                rule_score, rule_view)

ROOT = Path(__file__).resolve().parents[1]
SCAM = ("Join our VIP Telegram group for 5% guaranteed daily profit. Our SEBI registered analyst shares sure-shot calls. "
        "Pay a refundable registration fee of Rs 999 today only!")


def names(text):
    return {f.name for f in find_flags(text)}


# ---------- the published dataset ----------
@pytest.fixture(scope="module")
def data():
    return pd.read_csv(ROOT / "data" / "scam_messages.csv")


def test_dataset_has_no_private_or_live_content(data):
    text = " ".join(data["text"])
    terms_file = ROOT / "data" / "raw" / "private_terms.txt"        # gitignored; only on the author's machine
    if terms_file.exists():
        terms = [ln.strip() for ln in terms_file.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
        assert terms, "private_terms.txt is empty"
        for private in terms:
            assert private not in text
    assert "Raya D1" not in text                                    # the non-financial row is gone
    assert not re.search(r"https?://\S*wixsite", text)           # the phishing link is defanged
    assert "hxxps://sbicardsupportweb[.]wixsite[.]com" in text
    assert not re.search(r"X{3,}\d", text)                       # no partial account numbers


def test_dataset_split_sizes(data):
    real = data[data["source"] == "real"]
    assert len(real) == 32 and int(real["label"].sum()) == 15


# ---------- the mask/number shortcut ----------
def test_model_never_sees_masks_or_digits(data):
    for t in data["text"]:
        v = model_view(t)
        assert not re.search(r"\d", v), v
        assert "xxxx" not in v and "*" not in v


def test_rule_view_blanks_masks_but_keeps_positions():
    t = "A/c XX5991 and ra***@ybl and XXXX done"
    v = rule_view(t)
    assert len(v) == len(t) and "X" not in v and "*" not in v and v.endswith("done")


def test_masks_alone_raise_nothing():
    assert names("Dear XXXX, A/c XXXX debited by XXXX on XXXX. Ref XXXX") == set()


def test_saved_model_vocabulary_has_no_masks_or_digits():
    model = load_model()
    assert model is not None
    for _, vec in model.named_steps["features"].transformer_list:
        vocab = vec.vocabulary_
        assert not any(re.search(r"\d|xxxx", term) for term in vocab)


# ---------- rules ----------
def test_classic_scam_raises_the_right_flags():
    found = names(SCAM)
    assert {"guaranteed", "off_platform", "upfront", "sebi_claim", "high_return", "urgency"} <= found
    assert assess(SCAM, model=None)["level"] == "High"


def test_warnings_are_not_flagged_as_promises():
    assert "credentials" not in names("SBI never asks for your OTP or PIN. Do not share it with anyone.")
    assert "guaranteed" not in names("Beware of unregistered entities promising guaranteed returns.")
    assert "sebi_claim" not in names("SEBI registered investment adviser, registration no. INH000012345.")


def test_otp_and_remote_access_requests():
    assert "credentials" in names("Please install AnyDesk and share the OTP to verify your account.")
    assert "credentials" in names("Open your UPI app, approve the collect request and enter your UPI PIN.")


def test_high_returns_rule():
    assert "high_return" in names("Earn 4% monthly return, credited to your bank.")
    assert "high_return" not in names("The Nifty 50 delivered about 12% annualized returns over 10 years.")


def test_rule_score_and_levels():
    assert rule_score([]) == 0.0
    assert level_for(0.1) == "Low" and level_for(0.5) == "Medium" and level_for(0.8) == "High"


def test_genuine_sms_is_low_without_flags():
    r = assess("Dear UPI user A/C XXXX debited by 2000.00 on 19Nov26. If not you, call your bank.", model=None)
    assert r["flags"] == [] and r["level"] == "Low"


# ---------- display: escaped, defanged, never a link ----------
def test_defang_and_highlight_are_safe():
    assert defang("go https://evil.example.com/x now") == "go hxxps://evil[.]example[.]com/x now"
    out = highlight_html("<b>Pay a joining fee</b> at https://a.wixsite.com/x")
    assert "<b>" not in out and "&lt;b&gt;" in out
    assert "<a " not in out and "href" not in out and "https://" not in out
    assert "hxxps://a[.]<mark>wixsite</mark>[.]com/x" in out     # defanged, and the free-host name is highlighted
    assert "<mark>" in out


# ---------- the page ----------
def test_scam_page_checks_a_message():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "pages" / "7_Scam_Checker.py"), default_timeout=90).run()
    assert not at.exception
    at.text_area[0].input(SCAM).run()
    next(b for b in at.button if b.label == "Check message").click().run()
    assert not at.exception
    assert any("High" in m.value for m in at.markdown)
    assert any("Guaranteed or risk-free returns" in m.value for m in at.markdown)
