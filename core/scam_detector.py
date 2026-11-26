"""Scam checker: red-flag rules (with reasons) + a small text model, combined into a low / medium / high risk.

Two views of a message:
- rule view: mask tokens (XXXX, XX5991, ra***@ybl) blanked out with spaces, so offsets still line up with the
  original text for highlighting and the rules can never react to masking.
- model view: lowercase, masks removed, links -> "link", every number -> "0". The data's mask tokens and
  numbers are a shortcut (most real legitimate SMS are masked, most scams are not), so the model never sees them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE = ROOT / "models" / "scam_model.joblib"

MASK_RE = re.compile(r"X{2,}[\dX]*|\b\w*\*{2,}\S*")
URL_RE = re.compile(r"\b(?:h(?:tt|xx)ps?://|www\.)\S+|\b[\w-]+(?:\[\.\]|\.)(?:com|net|org|in|me|ly|site|app|xyz|co|io|to)\b\S*", re.I)
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")

LOW_BELOW, HIGH_FROM = 0.40, 0.70      # risk score cut-offs, fixed before looking at the real held-out set


# ---------- text views ----------
def defang(text: str) -> str:
    """Make links unclickable: https://a.b.com/x -> hxxps://a[.]b[.]com/x."""
    def fix(m: re.Match) -> str:
        scheme, rest = m.group(0).split("://", 1)
        host, slash, path = rest.partition("/")
        return "hxxp" + scheme[4:] + "://" + host.replace(".", "[.]") + slash + path
    return re.sub(r"\bhttps?://\S+", fix, text, flags=re.I)


def rule_view(text: str) -> str:
    """Mask tokens blanked out (same length, so match positions still point into the original text)."""
    return MASK_RE.sub(lambda m: " " * len(m.group(0)), text)


def model_view(text: str) -> str:
    """What the model sees: no mask tokens, no digits, links reduced to a single word, numbers to 'num'."""
    t = MASK_RE.sub(" ", text)
    t = URL_RE.sub(" link ", t)
    t = NUM_RE.sub(" num ", t)
    return re.sub(r"\s+", " ", t.lower()).strip()


# ---------- red-flag rules ----------
NEGATION = re.compile(r"\b(never|not|don'?t|do not|does not|doesn'?t|cannot|won'?t|will not|no one|avoid|beware)\b[^.]{0,60}$", re.I)


@dataclass
class Rule:
    name: str
    label: str
    reason: str
    weight: float
    pattern: re.Pattern
    negatable: bool = False                 # skip a match that is part of "never share your OTP"
    unless: re.Pattern | None = None        # skip the rule if this appears anywhere (e.g. a real SEBI number)


@dataclass
class Flag:
    name: str
    label: str
    reason: str
    weight: float
    spans: list[tuple[int, int]] = field(default_factory=list)


def _r(p: str) -> re.Pattern:
    return re.compile(p, re.I)


RULES = [
    Rule("guaranteed", "Guaranteed or risk-free returns", "Real investments can lose money. Anyone promising they can't is lying.", 0.45,
         _r(r"\b(guaranteed?|assured|sure[- ]shot|risk[- ]free|zero[- ](loss|risk)|no[- ]loss|100\s*%\s*(accura\w+|safe|confirmed|principal|protect\w*|guarantee\w*)|principal (is )?(fully |100% )?protected|confirmed (hni |ipo )?allotment)\b"),
         negatable=True),
    Rule("credentials", "Asks for OTP, PIN or remote access", "No bank, broker or app ever needs your OTP, UPI PIN, CVV or screen access.", 0.5,
         _r(r"\b(share|send|enter|tell|give|provide|approve)\b[^.]{0,40}\b(otp|upi pin|pin|cvv|password|collect request)\b|\b(anydesk|teamviewer|quick ?support|screen ?shar\w*|remote access)\b"),
         negatable=True),
    Rule("upfront", "Pay or deposit money first", "Being asked to pay a fee or move money into someone else's account to 'unlock' gains is how these schemes take money.", 0.45,
         _r(r"\b(registration|joining|processing|activation|membership|unlock\w*|refundable)\s+(fee|charge|amount)\b|\bpay (a |the )?(small )?(refundable )?(fee|charge)\b|\b(deposit|transfer)\b[^.]{0,50}\b(pool|managed|company|our)\b[^.]{0,30}\b(account|website|app)\b|\bpool account\b")),
    Rule("off_platform", "Moves you to a private chat group", "Scams pull people into WhatsApp, Telegram or Instagram groups where no regulator is watching.", 0.4,
         _r(r"\b(join|add|message|dm|contact|click|reply)\b[^.]{0,50}\b(telegram|whatsapp|instagram|signal)\b|\b(telegram|whatsapp|instagram)\b[^.]{0,20}\b(group|channel|admin|community)\b|\bdm us\b")),
    Rule("sebi_claim", "Claims SEBI registration with no number", "A genuine adviser shows a SEBI registration number (INH/INA...). Check it at investor.sebi.gov.in.", 0.35,
         _r(r"\b(sebi[- ]registered|registered with sebi|sebi (approved|certified))\b"),
         unless=_r(r"\bIN[AHZ]\d{6,}\b")),
    Rule("insider", "'Institutional' or insider access", "Talk of HNI quotas, institutional pools, upper circuits or block deals is how fake 'insider' tips are sold.", 0.4,
         _r(r"\b(institutional (pool|quota|account|app|block|research|stock)|hni (quota|allotment)|anchor pool|upper[- ]circuit|block[- ]deal|insider|stock recommendations?|core stocks|bull stocks|daily limit)\b")),
    Rule("crypto", "Crypto, forex or 'doubling' scheme", "Promises to double money quickly, often with crypto or forex bots, are a classic scam.", 0.4,
         _r(r"\b(double|triple|2x|3x)\b[^.]{0,20}\b(money|capital|investment|amount)\b|\b(arbitrage bot|trading bot|forex signals?|usdt|bitcoin|ethereum)\b")),
    Rule("task", "Pays you for simple online tasks", "'Like, rate or review to earn' tasks start with small payouts, then ask you to pay in.", 0.4,
         _r(r"\b(task|like|review|rate|rating|view)\b[^.]{0,60}\b(earn|payment|income|commission|paid)\b|\bpart[- ]time (job|work|income)\b|\bwork from home\b|\b(prepaid|merchant) task\b|\border deposit\b")),
    Rule("prize", "A prize or giveaway you didn't enter", "Surprise winnings that need your details or a payment are bait.", 0.35,
         _r(r"\b(you have won|you've won|randomly selected|giveaway|lottery|lucky draw|cashback voucher|shortlisted)\b")),
    Rule("link_action", "A link that pushes you to act", "Links on free website builders or ones that ask you to click to block, claim or verify are common phishing.", 0.35,
         _r(r"\b(wixsite|weebly|blogspot|ngrok|bit\.ly|tinyurl)\b|\b(click|tap)\b[^.]{0,30}\b(deactivate|verify|claim|block|unlock|activate|updates?)\b")),
    Rule("urgency", "Pressure to act fast", "Deadlines like 'within minutes' or 'today only' are meant to stop you from checking.", 0.15,
         _r(r"\b(urgent\w*|immediately|right now|today only|limited (slots|seats|time|period)|only a few (seats|slots)|within (a few minutes|\d+ ?(minutes?|hours?))|24-hour|hurry|last chance|act fast|slots? remaining|before registration closes)\b"),
         negatable=True),
]

PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*%")
PERIOD_RE = re.compile(r"\b(daily|a day|per day|every day|weekly|a week|per week|monthly|a month|per month|every month)\b", re.I)
GAIN_RE = re.compile(r"\b(return|profit|gain|growth|payout|earn|commission)", re.I)


def _high_returns(view: str) -> list[tuple[int, int]]:
    """Percent returns that are far above anything normal: any daily/weekly %, more than 3% a month, or 20%+ gains."""
    spans = []
    for m in PCT_RE.finditer(view):
        pct = float(m.group(2) or m.group(1))
        window = view[max(0, m.start() - 60): m.end() + 40]
        period = PERIOD_RE.search(window)
        gainy = GAIN_RE.search(window)
        if period and period.group(1).lower() in ("daily", "a day", "per day", "every day", "weekly", "a week", "per week"):
            spans.append(m.span())
        elif period and pct > 3 and gainy:
            spans.append(m.span())
        elif gainy and pct >= 20:
            spans.append(m.span())
    return spans


HIGH_RETURN = ("high_return", "Unrealistic returns", "Steady daily or weekly returns, or 3%+ a month, don't exist in real markets. The Nifty 50 averaged about 8% a year.", 0.45)


def find_flags(text: str) -> list[Flag]:
    """Every red flag in the message, with the character spans that triggered it."""
    view = rule_view(text)
    flags = []
    for rule in RULES:
        if rule.unless is not None and rule.unless.search(view):
            continue
        spans = []
        for m in rule.pattern.finditer(view):
            if rule.negatable and NEGATION.search(view[max(0, m.start() - 60): m.start()]):
                continue
            spans.append(m.span())
        if spans:
            flags.append(Flag(rule.name, rule.label, rule.reason, rule.weight, spans))
    hr = _high_returns(view)
    if hr:
        flags.append(Flag(*HIGH_RETURN, hr))
    return flags


def rule_score(flags: list[Flag]) -> float:
    """Combine flag weights like independent pieces of evidence: 1 - product(1 - weight)."""
    keep = 1.0
    for f in flags:
        keep *= 1 - f.weight
    return 1 - keep


# ---------- model ----------
def build_model():
    """Word and character n-grams + logistic regression (sentence embeddings were too heavy for free hosting)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline
    return Pipeline([
        ("features", FeatureUnion([
            ("words", TfidfVectorizer(preprocessor=model_view, ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("chars", TfidfVectorizer(preprocessor=model_view, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ])),
        ("clf", LogisticRegression(max_iter=3000, C=2.0, class_weight="balanced")),
    ])


_MODEL = None


def load_model(path: Path = MODEL_FILE):
    global _MODEL
    if _MODEL is None and path.exists():
        import joblib
        _MODEL = joblib.load(path)
    return _MODEL


def level_for(score: float) -> str:
    return "High" if score >= HIGH_FROM else "Medium" if score >= LOW_BELOW else "Low"


def assess(text: str, model=None) -> dict:
    """Risk for one message: rules + model. Model is optional (rules still work without it)."""
    flags = find_flags(text)
    rs = rule_score(flags)
    model = model if model is not None else load_model()
    prob = float(model.predict_proba([text])[0][1]) if model is not None and text.strip() else None
    # Rules are explicit evidence; the model adds a softer, capped push (it alone can reach Medium, not High).
    score = rs if prob is None else 1 - (1 - rs) * (1 - 0.75 * prob)
    return {"score": score, "level": level_for(score), "rule_score": rs, "model_prob": prob, "flags": flags}


def highlight_html(text: str) -> str:
    """The message as safe HTML with flagged phrases marked. Links are defanged first and stay plain text."""
    import html
    shown = defang(text)
    marks = sorted({sp for f in find_flags(shown) for sp in f.spans})
    out, pos = [], 0
    for start, end in marks:
        if start < pos:
            continue
        out.append(html.escape(shown[pos:start]))
        out.append(f"<mark>{html.escape(shown[start:end])}</mark>")
        pos = end
    out.append(html.escape(shown[pos:]))
    return "".join(out).replace("\n", "<br>")
