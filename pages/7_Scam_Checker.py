"""Scam Checker: paste a message, see its risk level and exactly which phrases raised it, and why."""
import json
from pathlib import Path

import streamlit as st

from core.scam_detector import assess, highlight_html, load_model
from core.ui import page_header, setup_page

setup_page("Scam Checker", "🚨")
page_header("Scam Checker", "🚨", "Paste a message and see which red flags it shows, and why.", step=7)

METRICS = Path(__file__).resolve().parents[1] / "models" / "scam_metrics.json"
LEVEL = {
    "Low": ("#1B7F5C", "No red flags found", "That doesn't mean it's safe. Never share an OTP or PIN, and check before you pay anyone."),
    "Medium": ("#d97706", "Be careful", "Some warning signs. Don't pay, click or share anything until you've checked it independently."),
    "High": ("#c2412d", "Very likely a scam", "This has several classic scam signs. Don't reply, pay, click or share any details."),
}
# Written for this page (not from the dataset), so nothing real is shown.
EXAMPLES = {
    "Stock tips group": "Join our VIP Telegram group for 5% guaranteed daily profit on Nifty options. Our SEBI registered analyst "
                        "shares sure-shot calls. Pay a refundable registration fee of Rs 999 today only, limited slots!",
    "KYC 'update'": "Dear customer, your account will be blocked today. Update your KYC immediately: install AnyDesk and share "
                    "the OTP you receive with our officer to complete verification.",
    "Bank debit SMS": "Dear UPI user, your A/c XX1234 is debited by Rs 250.00 on 21Nov26 to VPA shop@okaxis. "
                      "If not you, call your bank's official helpline to block UPI.",
}

st.markdown(
    """
<style>
  .sc-msg { border: 1px solid var(--kp-line); background: var(--kp-soft); border-radius: 14px; padding: 12px 14px;
            line-height: 1.6; font-size: .98rem; white-space: normal; word-break: break-word; }
  .sc-msg mark { background: rgba(224,122,95,.35); color: inherit; border-radius: 4px; padding: 0 2px; }
</style>
""",
    unsafe_allow_html=True,
)


def use_example(name: str) -> None:
    st.session_state["scam_text"] = EXAMPLES[name]


st.caption("🔒 The message is checked in memory and never saved. Remove names or numbers first if you like; the checker ignores them.")
ex = st.columns(len(EXAMPLES) + 1)
ex[0].markdown("**Try an example:**")
for col, name in zip(ex[1:], EXAMPLES):
    col.button(name, on_click=use_example, args=(name,), width="stretch")

text = st.text_area("Message", key="scam_text", height=150, max_chars=3000,
                    placeholder="Paste an SMS, WhatsApp or email message here")
checked = st.button("Check message", type="primary", disabled=not (text or "").strip())

if load_model() is None:
    st.caption("The language model couldn't be loaded, so only the red-flag rules are being used.")

if checked or st.session_state.get("scam_last") == text and (text or "").strip():
    st.session_state["scam_last"] = text
    r = assess(text)
    color, title, advice = LEVEL[r["level"]]
    st.divider()
    left, right = st.columns([1, 2], vertical_alignment="center")
    left.markdown(
        f"<div style='border-radius:16px;padding:14px 16px;background:{color};color:#fff'>"
        f"<div style='font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;opacity:.85'>Risk</div>"
        f"<div style='font-size:2rem;font-weight:800;line-height:1.1'>{r['level']}</div>"
        f"<div style='font-size:.9rem;opacity:.95'>{title}</div></div>",
        unsafe_allow_html=True,
    )
    right.markdown(
        f"<div style='font-size:.85rem;opacity:.8'>Risk score {r['score']:.2f} (Medium from 0.40, High from 0.70)</div>"
        f"<div style='height:10px;border-radius:99px;background:var(--kp-line);margin:.35rem 0 .2rem'>"
        f"<div style='height:100%;width:{min(r['score'], 1.0) * 100:.0f}%;border-radius:99px;background:{color}'></div></div>",
        unsafe_allow_html=True,
    )
    right.write(advice)

    st.markdown("**The message, with the phrases that raised flags**")
    # st.html: escaped and defanged, never Markdown, so nothing in the message can become a clickable link.
    st.html(f"<div class='sc-msg'>{highlight_html(text)}</div>")

    if r["flags"]:
        st.markdown(f"**{len(r['flags'])} red flag{'s' if len(r['flags']) != 1 else ''}**")
        for f in r["flags"]:
            with st.container(border=True, key=f"card_flag_{f.name}"):
                st.markdown(f"**{f.label}**  \n{f.reason}")
    elif r["level"] != "Low":
        st.info("No specific red flag, but the wording is similar to scam messages the model learned from.")
    if r["model_prob"] is not None:
        st.caption(f"Language model: {r['model_prob']:.0%} similar to scam messages it learned from. Rules carry more weight.")

    with st.container(border=True, key="card_scam_help"):
        st.markdown(
            "**If you think it's a scam**\n"
            "- Don't pay, click links, install apps or share an OTP, PIN or CVV.\n"
            "- Report it at [cybercrime.gov.in](https://cybercrime.gov.in) or call **1930** (National Cyber Crime Helpline).\n"
            "- Check any adviser or broker's registration at [investor.sebi.gov.in](https://investor.sebi.gov.in) "
            "and RBI-regulated entities at [sachet.rbi.org.in](https://sachet.rbi.org.in)."
        )

if METRICS.exists():
    m = json.loads(METRICS.read_text(encoding="utf-8"))["real_test"]["combined"]
    st.caption(f"How well it works: on {m['rows']} real messages it never trained on, it flagged {m['tp']} of "
               f"{m['tp'] + m['fn']} scams and wrongly flagged {m['fp']} of {m['fp'] + m['tn']} genuine ones. "
               "A small test, so treat it as a second opinion, not a verdict.")
if st.button("Next: How it works →", key="next_about"):
    st.switch_page("pages/8_About.py")
