"""Home page: a scroll-driven story of one month of money, built from the demo statement's real numbers.

Scroll position drives everything (title leaves, scenes scrub, the roadmap rail travels). The page is
plain HTML/CSS/JS rendered with st.html(unsafe_allow_javascript=True), so CSS `sticky` and the real
scroll container work. No external files, no character art.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.categorizer import INCOME, TRANSFERS, categorize
from core.parsers import parse_statement
from core.risk_quiz import QUESTIONS
from core.simulator import bootstrap_returns, load_monthly_returns, simulate, sip_path
from core.spending import format_inr
from core.surplus import ESSENTIAL_CATEGORIES, compute_surplus

ROOT = Path(__file__).resolve().parent.parent
DEMO_FILE = ROOT / "data" / "demo_statement.csv"
METRICS_FILE = ROOT / "models" / "categorizer_metrics.json"
AVOIDABLE = ["Food & dining", "Shopping", "Subscriptions"]
SIP_YEARS = 10
INFLATION = 0.06
SAMPLE_PATHS = 36


def _trim(text: str) -> str:
    return text[: -len("/Payment")] if text.endswith("/Payment") else text


def story_data() -> dict:
    """Everything the story shows, computed from the demo statement, the Nifty history and the saved metrics."""
    raw = pd.read_csv(DEMO_FILE)
    df = categorize(parse_statement(DEMO_FILE, "standard"))
    r = compute_surplus(df)
    spent = df[(df["debit"] > 0) & (~df["category"].isin([INCOME, TRANSFERS]))]
    per_month = (spent.groupby("category")["debit"].sum() / r["months"]).sort_values(ascending=False)

    def group(c: str) -> str:
        return "essential" if c in ESSENTIAL_CATEGORIES else "avoid" if c in AVOIDABLE else "other"

    order = ["essential", "avoid", "other"]
    items = [{"name": c, "value": round(float(v)), "group": group(c)} for c, v in per_month.items()]
    items.sort(key=lambda it: (order.index(it["group"]), -it["value"]))
    spend = float(per_month.sum())
    income = float(r["income"])
    left = max(0.0, income - spend)
    items.append({"name": "Left over", "value": round(left), "group": "left"})
    avoidable = float(per_month[per_month.index.isin(AVOIDABLE)].sum())

    # A what-if: a third of the avoidable spend, plus whatever is already left over.
    monthly = max(100, int(round((left + avoidable / 3) / 100.0)) * 100)
    returns = load_monthly_returns()["return"].to_numpy()
    sim = simulate(float(monthly), SIP_YEARS, returns, INFLATION)
    months = SIP_YEARS * 12
    deflator = (1 + INFLATION) ** (np.arange(1, months + 1) / 12)
    sample = sip_path(bootstrap_returns(returns, months, SAMPLE_PATHS, seed=7), float(monthly)) / deflator

    def ints(a) -> list[int]:
        return [int(round(x)) for x in a]

    # A real slice of the demo account: the stipend lands, then small payments drain it.
    start = int(df.index[df["category"] == INCOME][1]) if (df["category"] == INCOME).sum() > 1 else 0
    first = df.iloc[start]
    txs = []
    for _, row in df.iloc[start:start + 14].iterrows():
        txs.append({
            "payee": " ".join(w.capitalize() for w in str(row["payee"]).split()),
            "cat": row["category"], "day": f"{row['date'].day} {row['date']:%b}",
            "debit": round(float(row["debit"])), "credit": round(float(row["credit"])), "bal": round(float(row["balance"])),
        })
    may = df[df["date"].dt.to_period("M") == first["date"].to_period("M")]
    before = round(float(first["balance"] - first["credit"] + first["debit"]))

    masks = []
    for i in range(len(df)):
        if str(raw["description"].iloc[i]).startswith("UPI/DR") and len(masks) < 5:
            masks.append({"raw": _trim(str(raw["description"].iloc[i])), "masked": _trim(str(df["description"].iloc[i]))})

    metrics = json.loads(METRICS_FILE.read_text(encoding="utf-8"))["real_test"]["rules_plus_ml"]
    return {
        "income": round(income), "spend": round(spend), "left": round(left), "avoidable": round(avoidable),
        "tx": int(len(df)), "items": items, "txs": txs, "txBefore": before, "monthTx": int(len(may)),
        "masks": masks, "quiz": QUESTIONS[1],
        "emergency": {"target": round(r["emergency_target"]), "saved": round(r["emergency_saved"]),
                      "years": round(r["months_to_fund"] / 12, 1)},
        "metrics": {"f1": metrics["macro_f1"], "rows": metrics["rows"]},
        "sim": {
            "monthly": monthly, "years": SIP_YEARS,
            "p10": ints(sim["bands"][10]), "p50": ints(sim["bands"][50]), "p90": ints(sim["bands"][90]),
            "invested": ints(sim["invested"]), "fd": ints(sim["fd"]), "paths": [ints(p) for p in sample],
        },
    }


def chapters(d: dict) -> list[dict]:
    """Title, copy and headline figure for each step."""
    f = format_inr
    sim = d["sim"]
    lo, mid, hi = sim["p10"][-1], sim["p50"][-1], sim["p90"][-1]
    return [
        dict(name="Payday", url=None, head=dict(value=d["income"], inr=True, cap="came in, in an average month"),
             text=f"A fictional student earns about {f(d['income'])} a month. Watch a few days of May: the money lands, then leaks "
                  "away in small payments nobody keeps track of. This is the demo account; yours shows your own numbers."),
        dict(name="Upload", url="upload", head=dict(value=d["tx"], cap="transactions read and masked"),
             text="Drop in a bank statement (SBI, HDFC or a standard CSV). Account numbers and UPI IDs are masked the moment the "
                  "file is read, before anything else happens. Nothing is saved."),
        dict(name="My Spending", url="my-spending", head=dict(value=d["avoidable"], inr=True, cap="a month on avoidable spending"),
             text=f"Every payment is sorted into a category. About {f(d['avoidable'])} a month goes on food delivery, shopping and "
                  "subscriptions, the part most people can change. Fix any category the app gets wrong and every chart updates."),
        dict(name="My Surplus", url="my-surplus", head=dict(value=d["left"], inr=True, cap="left over each month"),
             text=f"Income minus spending leaves {f(d['left'])} a month. Before any investment risk, the app asks for an emergency "
                  f"fund first: three months of essentials, {f(d['emergency']['target'])}. At this pace that takes about "
                  f"{d['emergency']['years']} years, so the real lever is the spending."),
        dict(name="Risk Quiz", url="risk-quiz", head=dict(text="Moderate", cap="an example result"),
             text="Nine questions about time horizon, emergency cover and how you react to losses. An example answer is shown; "
                  "'Moderate' here is a score of 18 out of 27. It describes comfort with risk, nothing more."),
        dict(name="Learn", url="learn", head=dict(value=7, cap="options, compared"),
             text="Seven options in plain language: savings account, FD, RD, PPF, index fund, gold and NPS. How easy it is to take "
                  "money out, how much it can swing, how it's taxed. The chart is illustrative, not advice."),
        dict(name="Simulator", url="simulator", head=dict(value=mid, inr=True, cap=f"middle case after {sim['years']} years, today's money"),
             text=f"A what-if: if a third of that avoidable spending went into a monthly SIP, that is about {f(sim['monthly'])} a month. "
                  f"Real Nifty 50 history is replayed 10,000 times. After {sim['years']} years: a bad case of {f(lo)}, a middle case of "
                  f"{f(mid)}, a good case of {f(hi)}. A range, not a prediction."),
        dict(name="Scam Checker", url="scam-checker", head=dict(text="High risk", cap="3 red flags in this message"),
             text="Paste any investment message and the checker highlights its red flags. This example promises guaranteed returns, "
                  "asks for an upfront fee and moves you to a private Telegram group. 'Low risk' never means 'safe'."),
    ]


def build_story(data: dict) -> str:
    """HTML + CSS as-is; the script is base64-encoded.

    Streamlit sanitises st.html with DOMPurify, which silently deletes any <script> whose text
    looks like it contains HTML (for example "<span>" or even "i<n"). Decoding at run time avoids that.
    """
    payload = json.dumps({**data, "stages": chapters(data)}, ensure_ascii=False)
    markup, script = TEMPLATE.split("<script>", 1)
    code = script.rsplit("</script>", 1)[0].replace("__DATA__", payload)
    b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
    loader = (f'<script>(function(){{var b="{b64}";'
              'var c=new TextDecoder().decode(Uint8Array.from(atob(b),function(x){return x.charCodeAt(0)}));'
              'try{(0,eval)(c)}catch(e){console.error("KanakkuPillai home failed:",e);var r=document.getElementById("kp-root");if(r)r.setAttribute("data-error",String(e&&e.stack||e))}})()</script>')
    return markup + loader


TEMPLATE = r"""
<style>
#kp-root{position:relative;height:1000vh;width:100%;color:#fff;font-family:"Source Sans Pro",system-ui,sans-serif}
#kp-root *{box-sizing:border-box}
#kp-root .stick{position:sticky;top:0;height:100vh;overflow:hidden;background:#12211d}
#kp-root .bg1{position:absolute;inset:0;background:linear-gradient(125deg,#0f5c43,#1B7F5C,#14b8a6,#0f766e);background-size:300% 300%;animation:kpShiftx 18s ease infinite}
@keyframes kpShiftx{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
#kp-root .bg0{position:absolute;inset:0;background:radial-gradient(60% 50% at 20% 20%,rgba(245,165,36,.16),transparent 70%),linear-gradient(135deg,#1b2926,#232d29 55%,#2a2a22)}
#kp-root canvas{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
#kp-root .pill{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:5;font-size:12px;padding:5px 14px;border-radius:99px;background:rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.18);white-space:nowrap;backdrop-filter:blur(6px)}
#kp-root .brand{position:absolute;top:14px;left:22px;z-index:5;font-weight:800;letter-spacing:-.02em;font-size:15px;opacity:0}
/* hero */
#kp-root .hero{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 6%;z-index:3;will-change:transform,opacity}
#kp-root .hero h1{margin:0;padding:0;font-size:clamp(3rem,10.5vw,8.6rem);font-weight:800;letter-spacing:-.045em;line-height:.95;color:#fff;display:flex;flex-wrap:wrap;justify-content:center}
#kp-root .hero h1 span{display:inline-block;opacity:0;transform:translateY(40px);animation:kpLetter .8s cubic-bezier(.2,.9,.2,1) forwards}
@keyframes kpLetter{to{opacity:1;transform:none}}
#kp-root .tag{margin:.9rem 0 0;font-size:clamp(1.15rem,2.6vw,1.9rem);font-weight:700;background:linear-gradient(90deg,#fff7d6,#f5a524);-webkit-background-clip:text;background-clip:text;color:transparent}
#kp-root .sub{margin:.35rem 0 0;font-size:clamp(1rem,1.8vw,1.25rem);opacity:.85}
#kp-root .cta{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:1.6rem}
#kp-root a.btn{display:inline-block;text-decoration:none;font-weight:700;color:#fff;padding:12px 22px;border-radius:14px;border:1px solid rgba(255,255,255,.4);background:rgba(255,255,255,.1);backdrop-filter:blur(6px);transition:transform .2s,background .2s}
#kp-root a.btn:hover{transform:translateY(-2px);background:rgba(255,255,255,.2)}
#kp-root a.btn.pri{background:#fff;color:#0f5c43;border-color:#fff}
#kp-root .cue{position:absolute;bottom:5vh;left:50%;transform:translateX(-50%);font-size:13px;opacity:.8;text-align:center}
#kp-root .cue i{display:block;width:22px;height:34px;margin:8px auto 0;border:2px solid rgba(255,255,255,.7);border-radius:12px;position:relative}
#kp-root .cue i:after{content:"";position:absolute;left:50%;top:7px;width:4px;height:7px;margin-left:-2px;border-radius:2px;background:#fff;animation:kpWheel 1.6s ease-in-out infinite}
@keyframes kpWheel{0%{opacity:0;transform:translateY(0)}30%{opacity:1}100%{opacity:0;transform:translateY(12px)}}
/* copy */
#kp-root .copy{position:absolute;left:5%;top:50%;transform:translateY(-52%);width:34%;display:grid;z-index:4}
#kp-root .ch{grid-area:1/1;opacity:0;pointer-events:none;will-change:opacity,transform}
#kp-root .kick{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#f5c542}
#kp-root .ch h2{margin:.35rem 0 .2rem;padding:0;font-size:clamp(2rem,4vw,3.3rem);font-weight:800;letter-spacing:-.03em;line-height:1.02;color:#fff}
#kp-root .fig{font-size:clamp(1.8rem,3.2vw,2.8rem);font-weight:800;letter-spacing:-.03em;color:#e9c46a;line-height:1.1;margin-top:.5rem}
#kp-root .cap{font-size:13px;opacity:.75;margin-bottom:.7rem}
#kp-root .ch p{margin:.3rem 0 0;font-size:clamp(.95rem,1.25vw,1.1rem);line-height:1.55;opacity:.92;color:#fff}
#kp-root .ch a.open{display:inline-block;margin-top:.9rem;font-weight:700;color:#fff;text-decoration:none;border-bottom:2px solid #f5c542;padding-bottom:2px;cursor:pointer}
/* visual panel */
#kp-root .vis{position:absolute;right:4%;top:10vh;bottom:15vh;width:56%;border-radius:24px;background:rgba(3,28,21,.5);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(10px);box-shadow:0 30px 80px -30px rgba(0,0,0,.6);overflow:hidden;opacity:0;z-index:3}
#kp-root .sc{position:absolute;inset:0;opacity:0;pointer-events:none}
#kp-root svg.fill{position:absolute;inset:0;width:100%;height:100%}
#kp-root svg text{font-family:inherit}
/* A: bank app */
#kp-root .bank{position:absolute;inset:4% 7%;display:flex;flex-direction:column;border-radius:20px;background:#f6f8f7;color:#16231e;box-shadow:0 20px 50px -20px rgba(0,0,0,.6);overflow:hidden}
#kp-root .bk-head{display:flex;justify-content:space-between;align-items:flex-end;padding:16px 18px 12px;background:linear-gradient(120deg,#0f5c43,#1B7F5C);color:#fff}
#kp-root .bk-head small{display:block;font-size:11px;opacity:.8}#kp-root .bk-head b{font-size:15px}
#kp-root .bal{text-align:right}#kp-root .bal span{font-size:clamp(1.4rem,2.6vw,2rem);font-weight:800;letter-spacing:-.02em}
#kp-root .bk-list{flex:1;overflow:hidden;padding:4px 0}
#kp-root .row{display:flex;align-items:center;gap:12px;padding:0 18px;overflow:hidden;border-bottom:1px solid #e5ece8}
#kp-root .row i{flex:0 0 auto;width:32px;height:32px;border-radius:50%;display:grid;place-items:center;color:#fff;font-style:normal;font-weight:800;font-size:13px}
#kp-root .row div{flex:1;min-width:0}#kp-root .row b{display:block;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#kp-root .row small{color:#6b7c75;font-size:11.5px}
#kp-root .amt{font-weight:800;font-size:14px;white-space:nowrap}#kp-root .amt.out{color:#c2412d}#kp-root .amt.in{color:#1B7F5C}
#kp-root .bk-foot{padding:9px 18px;font-size:12px;color:#5b6b65;background:#eef3f0;display:flex;justify-content:space-between}
/* B: upload */
#kp-root .up{position:absolute;inset:5% 6%;display:flex;flex-direction:column;gap:12px;justify-content:center}
#kp-root .drop{height:84px;border:2px dashed rgba(255,255,255,.4);border-radius:16px;display:flex;align-items:center;justify-content:center;position:relative;background:rgba(255,255,255,.05)}
#kp-root .file{display:flex;align-items:center;gap:10px;background:#fff;color:#16231e;padding:9px 14px;border-radius:10px;font-weight:700;font-size:14px;box-shadow:0 10px 25px -10px rgba(0,0,0,.6);will-change:transform}
#kp-root .fi{display:inline-block;width:14px;height:18px;border:2px solid #1B7F5C;border-radius:2px;position:relative}
#kp-root .leg{display:flex;gap:16px;font-size:12px;font-weight:700;margin-bottom:-4px}
#kp-root .leg span:before{content:'';display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
#kp-root .leg .l1:before{background:#ffb4a2}#kp-root .leg .l2:before{background:#9ff0d4}
#kp-root .tbl{background:rgba(0,0,0,.28);border-radius:14px;padding:6px 14px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:clamp(9.5px,1.05vw,12.5px)}
#kp-root .mrow{position:relative;height:30px;line-height:30px;white-space:nowrap;overflow:hidden;border-bottom:1px solid rgba(255,255,255,.08)}
#kp-root .mrow .raw{color:#ffb4a2}
#kp-root .mrow .msk{position:absolute;inset:0;background:#0d2b22;color:#9ff0d4}
#kp-root .checks{display:flex;gap:8px;flex-wrap:wrap}
#kp-root .chip{display:flex;align-items:center;gap:7px;font-size:12.5px;padding:6px 12px 6px 8px;border-radius:99px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);opacity:0}
#kp-root .chip:before{content:"";width:16px;height:16px;border-radius:50%;background:#14b8a6 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='M4 8.5l2.7 2.7L12 5.5' stroke='white' stroke-width='2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E") center/16px}
/* D: quiz + gauge */
#kp-root .quiz{position:absolute;left:8%;right:8%;top:12%;background:#f6f8f7;color:#16231e;border-radius:20px;padding:18px 20px;box-shadow:0 20px 50px -20px rgba(0,0,0,.6);will-change:transform,opacity}
#kp-root .qprog{font-size:12px;color:#5b6b65;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
#kp-root .qprog span{display:flex;gap:4px}#kp-root .qprog span i{width:18px;height:4px;border-radius:3px;background:#d7e1dc}#kp-root .qprog span i.on{background:#1B7F5C}
#kp-root .quiz h4{margin:0 0 12px;font-size:clamp(14px,1.5vw,17px);line-height:1.35;color:#16231e}
#kp-root .opt{display:flex;align-items:center;gap:10px;border:1.5px solid #d7e1dc;border-radius:12px;padding:10px 12px;margin-bottom:8px;font-size:clamp(13px,1.3vw,15px);transition:all .25s;background:#fff}
#kp-root .opt:before{content:"";flex:0 0 auto;width:16px;height:16px;border-radius:50%;border:2px solid #b4c4bc}
#kp-root .opt.sel{border-color:#1B7F5C;background:#e6f5ee;box-shadow:0 0 0 4px rgba(27,127,92,.14)}
#kp-root .opt.sel:before{border-color:#1B7F5C;background:radial-gradient(#1B7F5C 45%,#fff 50%)}
/* G: scam */
#kp-root .chat{position:absolute;left:7%;right:7%;top:5%;bottom:5%;display:flex;flex-direction:column;gap:10px;justify-content:center}
#kp-root .bub{background:#f4f7f5;color:#1d2b26;border-radius:16px 16px 16px 4px;padding:12px 14px;font-size:clamp(12.5px,1.35vw,15px);line-height:1.55;box-shadow:0 10px 30px -14px rgba(0,0,0,.6);max-width:480px}
#kp-root .bub .from{font-size:11px;font-weight:700;color:#6b7c75;margin-bottom:4px}
#kp-root .bub p{margin:0 0 6px;color:#1d2b26;opacity:1;font-size:inherit}
#kp-root mark{color:inherit;--p:0;background:linear-gradient(rgba(224,122,95,.5),rgba(224,122,95,.5)) no-repeat left/calc(var(--p)*100%) 100%;border-radius:3px;padding:0 1px}
#kp-root .flags{display:flex;flex-wrap:wrap;gap:6px 8px}
#kp-root .flag{display:flex;align-items:center;gap:6px;font-size:12.5px;padding:3px 11px 3px 4px;border-radius:99px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);opacity:0}
#kp-root .flag b{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;background:#e07a5f;font-size:11px}
#kp-root .verdict{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:11px 14px;font-size:clamp(12px,1.2vw,13.5px);line-height:1.5;opacity:0;max-width:480px}
#kp-root .verdict .r{display:flex;align-items:center;gap:10px;margin-bottom:6px;font-weight:700}
#kp-root .rbar{flex:1;height:7px;border-radius:99px;background:rgba(255,255,255,.18);overflow:hidden}
#kp-root .rbar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#e9c46a,#e07a5f);border-radius:99px}
#kp-root .verdict a{color:#9ff0d4}
/* rail */
#kp-root .rail{position:absolute;left:50%;transform:translateX(-50%);bottom:3.4vh;width:min(920px,calc(100% - 10%));height:56px;z-index:5;opacity:0}
#kp-root .rail .lab{position:absolute;top:-4px;font-size:11px;font-weight:700;letter-spacing:.04em}
#kp-root .rail .l1{left:0;color:#f5c542}#kp-root .rail .l2{right:0;color:#9ff0d4}
#kp-root .rail .track{position:absolute;left:0;right:0;top:26px;height:5px;border-radius:5px;background:rgba(255,255,255,.2)}
#kp-root .rail .fillbar{position:absolute;left:0;top:26px;height:5px;border-radius:5px;background:linear-gradient(90deg,#f5a524,#14b8a6,#9ff0d4)}
#kp-root .rail .node{position:absolute;top:19px;width:19px;height:19px;margin-left:-9.5px;border-radius:50%;background:#0f3f31;border:2px solid rgba(255,255,255,.5);cursor:pointer;transition:transform .25s,background .25s}
#kp-root .rail .node.done{background:#e9c46a;border-color:#e9c46a}
#kp-root .rail .node.on{transform:scale(1.35);background:#fff;border-color:#fff}
#kp-root .rail .node span{position:absolute;top:24px;left:50%;transform:translateX(-50%);font-size:11px;white-space:nowrap;opacity:.8;font-weight:600}
#kp-root .rail .node.on span{opacity:1;color:#f5c542}
#kp-root .rail .dot{position:absolute;top:21px;width:15px;height:15px;margin-left:-7.5px;border-radius:50%;background:#fff;box-shadow:0 0 0 5px rgba(255,255,255,.2),0 0 22px rgba(255,255,255,.8);pointer-events:none}
/* outro */
#kp-root .outro{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 6%;opacity:0;pointer-events:none;z-index:6;background:radial-gradient(70% 60% at 50% 40%,rgba(15,92,67,.55),rgba(8,40,30,.92))}
#kp-root .outro h2{margin:0;font-size:clamp(2rem,6vw,4.4rem);font-weight:800;letter-spacing:-.04em;line-height:1.02;color:#fff}
#kp-root .outro p.s{margin:.7rem 0 0;font-size:clamp(1rem,1.8vw,1.3rem);opacity:.88;max-width:34rem;color:#fff}
#kp-root .proof{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin-top:2rem;max-width:960px}
#kp-root .pc{flex:1 1 200px;max-width:290px;text-align:left;padding:14px 16px;border-radius:16px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.2)}
#kp-root .pc b{display:block;font-size:clamp(1.3rem,2.4vw,1.9rem);color:#e9c46a;letter-spacing:-.02em}
#kp-root .pc span{font-size:13px;opacity:.85;line-height:1.4;display:block;margin-top:2px}
#kp-root .legal{margin-top:1.4rem;font-size:12px;opacity:.7;max-width:40rem;line-height:1.5}
@media (max-width:760px){
  #kp-root .pill{font-size:10.5px;padding:4px 10px}#kp-root .pill .x{display:none}
  #kp-root .copy{left:6%;right:6%;width:auto;top:8vh;transform:none}
  #kp-root .ch h2{font-size:1.7rem}#kp-root .fig{font-size:1.5rem;margin-top:.3rem}#kp-root .cap{margin-bottom:.3rem}
  #kp-root .ch p{font-size:.85rem;line-height:1.4}
  #kp-root .ch a.open{margin-top:.5rem}
  #kp-root .vis{left:3%;right:3%;width:auto;top:auto;bottom:12.5vh;height:46vh}
  #kp-root .rail .node span{display:none}
  #kp-root .rail .node.on span{display:block;top:24px}
  #kp-root .brand{display:none}
  #kp-root .rail .node.first.on span{left:0;transform:none}#kp-root .rail .node.last.on span{left:auto;right:0;transform:none}
  #kp-root .bk-head{padding:10px 12px}#kp-root .row{gap:9px;padding:0 12px}
  #kp-root .quiz{left:5%;right:5%;top:6%;padding:12px}#kp-root .opt{padding:7px 9px;margin-bottom:5px}
  #kp-root .chat{gap:7px}#kp-root .up{gap:8px}#kp-root .drop{height:56px}
}
@media (prefers-reduced-motion: reduce){#kp-root *{animation-duration:.01s!important}}
</style>
<div id="kp-root">
 <div class="stick" id="kpStick">
  <div class="bg0"></div><div class="bg1" id="kpBg1"></div><canvas id="kpCv"></canvas>
  <div class="pill">Educational tool only, not investment advice <span class="x"> · your data is processed in memory and never saved</span></div>
  <div class="brand" id="kpBrand">KanakkuPillai</div>

  <div class="hero" id="kpHero">
   <h1 id="kpTitle"></h1>
   <div class="tag">Where does my ₹ go?</div>
   <div class="sub">From wasting it to investing it wisely.</div>
   <div class="cta"><a class="btn pri" id="kpUp" href="/upload">Upload my statement</a><a class="btn" href="/upload?demo=1">Try the demo</a></div>
   <div class="cue">Scroll to follow one month of money<i></i></div>
  </div>

  <div class="copy" id="kpCopy"></div>

  <div class="vis" id="kpVis">
   <div class="sc" id="scA"><div class="bank">
     <div class="bk-head"><div><small>Demo account · May</small><b>Savings ····4821</b></div><div class="bal"><small>Balance</small><span id="balNum"></span></div></div>
     <div class="bk-list" id="bkList"></div>
     <div class="bk-foot"><span id="bkMore"></span><span>Demo data · fictional</span></div></div></div>
   <div class="sc" id="scB"><div class="up">
     <div class="drop"><div class="file" id="kpFile"><i class="fi"></i>statement.csv</div></div>
     <div class="leg"><span class="l1">As in your file</span><span class="l2">What the app keeps</span></div>
     <div class="tbl" id="kpTbl"></div>
     <div class="checks"><span class="chip">Account numbers masked</span><span class="chip">UPI IDs masked</span><span class="chip">Nothing is saved</span></div></div></div>
   <div class="sc" id="scC"></div>
   <div class="sc" id="scD"><div class="quiz" id="kpQuiz"></div>
     </div>
   <div class="sc" id="scE"></div>
   <div class="sc" id="scF"></div>
   <div class="sc" id="scG"><div class="chat">
     <div class="bub"><div class="from">Unknown number · WhatsApp</div>
      <p><mark id="m1">Guaranteed 30% returns every month.</mark> Only a few seats left!</p>
      <p>Pay a <mark id="m2">₹5,000 joining fee</mark> today and we'll add you to our <mark id="m3">private Telegram group</mark>.</p></div>
     <div class="flags"><span class="flag"><b>1</b>Guaranteed returns</span><span class="flag"><b>2</b>Upfront fee</span><span class="flag"><b>3</b>Moves you off the app</span></div>
     <div class="verdict" id="kpVerd"><div class="r"><span>Risk</span><div class="rbar"><i id="kpRisk"></i></div><span>High</span></div>
      Don't pay or join. Report it at <a href="https://cybercrime.gov.in" target="_blank" rel="noopener">cybercrime.gov.in</a> or call 1930, and check any adviser at <a href="https://investor.sebi.gov.in" target="_blank" rel="noopener">investor.sebi.gov.in</a>.</div></div></div>
  </div>

  <div class="rail" id="kpRail"><span class="lab l1">Wasting</span><span class="lab l2">Investing wisely</span><div class="track"></div><div class="fillbar" id="kpFill"></div><div class="dot" id="kpDot"></div></div>

  <div class="outro" id="kpOutro">
   <h2>Now see where<br>your ₹ goes.</h2>
   <p class="s">Upload a statement or try the demo. It takes about two minutes.</p>
   <div class="cta"><a class="btn pri" id="kpUp2" href="/upload">Upload my statement</a><a class="btn" href="/upload?demo=1">Try the demo</a></div>
   <div class="proof" id="kpProof"></div>
   <div class="legal">Educational tool only. It explains and shows; it never tells you to buy a particular stock, fund or scheme. Past returns don't predict future returns. Your statement is processed in memory on the server and never saved.</div>
  </div>
 </div>
</div>
<script>
(function(){
if(window.__kpStop) window.__kpStop();
const D=__DATA__, ST=D.stages, N=ST.length, NS='http://www.w3.org/2000/svg';
const root=document.getElementById('kp-root'); if(!root) return;
const sc=document.querySelector('[data-testid="stMain"]')||document.scrollingElement;
let stopped=false; window.__kpStop=()=>{stopped=true};
const $=id=>document.getElementById(id);
const el=(tag,at={},par)=>{const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);par&&par.appendChild(e);return e};
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)), lerp=(a,b,t)=>a+(b-a)*t, sm=t=>{t=clamp(t);return t*t*(3-2*t)}, eo=t=>1-Math.pow(1-clamp(t),3);
const win=(u,a,b,f)=>clamp((u-a)/f)*clamp((b-u)/f);
const inr=n=>'₹'+Math.round(n).toLocaleString('en-IN');
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const hex=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)), lighten=(h,k)=>hex(h).map(v=>Math.round(v+(255-v)*k));
const GC={essential:'#6fb39d',avoid:'#e07a5f',other:'#c9b88f',left:'#e9c46a'}, NEUTRAL=hex('#e2f4ec');
const narrow=()=>innerWidth<760;

/* ----- svg roots (st.html's sanitiser strips inline <svg>, so build them here) ----- */
const mkSvg=(par,id,vb)=>{const e=document.createElementNS(NS,'svg');e.setAttribute('class','fill');e.setAttribute('viewBox',vb);e.setAttribute('preserveAspectRatio','xMidYMid meet');e.setAttribute('aria-hidden','true');if(id)e.id=id;par.appendChild(e);return e};
{const holder=$('scC'); holder.innerHTML=`<svg class="fill" viewBox="0 0 640 400" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
     <defs><linearGradient id="kpFadeG" gradientUnits="userSpaceOnUse" x1="82" y1="0" x2="430" y2="0"><stop offset="0" stop-color="#fff"/><stop id="kpFadeEnd" offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
     <mask id="kpFade" maskUnits="userSpaceOnUse" x="0" y="0" width="640" height="400"><rect width="640" height="400" fill="url(#kpFadeG)"/></mask></defs>
     <g id="kpRib" mask="url(#kpFade)"></g><g id="kpLeft"></g><g id="kpRight"></g><g id="kpCat"></g>
     <g id="kpQ"><text x="446" y="214" font-size="22" font-style="italic" fill="#fff" fill-opacity=".92">Where did it go?</text></g>
     <g id="kpSum"><text id="kpSumA" x="446" y="150" font-size="15" font-weight="700" fill="#fff"></text>
       <text id="kpSumB" x="446" y="288" font-size="15" font-weight="700" fill="#e9c46a"></text>
       <rect x="446" y="302" width="168" height="9" rx="4.5" fill="#fff" fill-opacity=".16"/><rect id="kpTank" x="446" y="302" width="3" height="9" rx="4.5" fill="#e9c46a"/>
       <text id="kpTankT" x="446" y="328" font-size="11.5" fill="#fff" fill-opacity=".85"></text><text id="kpTankT2" x="446" y="344" font-size="11.5" fill="#fff" fill-opacity=".6"></text></g></svg>`;}
mkSvg($('scD'),'kpGauge','0 0 400 260'); mkSvg($('scE'),'kpPlot','0 0 640 400'); mkSvg($('scF'),'kpSim','0 0 640 400');

/* ----- hero title ----- */
const ti=$('kpTitle'); ti.innerHTML=''; 'KanakkuPillai'.split('').forEach((c,i)=>{const s=document.createElement('span');s.textContent=c;s.style.animationDelay=(i*55)+'ms';ti.appendChild(s)});

/* ----- copy blocks ----- */
const copy=$('kpCopy'); copy.innerHTML=''; const chEls=[], figEls=[];
ST.forEach((s,i)=>{const d=document.createElement('div');d.className='ch';
  d.innerHTML=`<div class="kick">${i===0?'One month of money':`Step ${i} of ${N-1}`}</div><h2>${s.name}</h2><div class="fig"></div><div class="cap">${s.head.cap}</div><p>${s.text}</p>${s.url?`<a class="open" data-u="${s.url}">Open ${s.name} →</a>`:''}`;
  copy.appendChild(d);chEls.push(d);figEls.push(d.querySelector('.fig'));
  const a=d.querySelector('a.open'); if(a)a.addEventListener('click',()=>go(s.url));});
function go(path){const l=document.querySelector(`a[href$="/${path}"]`); if(l){l.click();return} location.href='/'+path}
['kpUp','kpUp2'].forEach(id=>$(id).addEventListener('click',e=>{const l=[...document.querySelectorAll('a[href$="/upload"]')].find(x=>!root.contains(x)); if(l){e.preventDefault();l.click()}}));  // keep the session via the sidebar link

/* ----- scene A: bank app ----- */
const CATC={'Food & dining':'#e07a5f','Shopping':'#e07a5f','Subscriptions':'#e07a5f','Groceries':'#6fb39d','Education':'#6fb39d','Health':'#6fb39d','Bills & recharge':'#6fb39d','Travel':'#c9b88f','Income':'#1B7F5C','Transfers (P2P)':'#8a97a0'};
const list=$('bkList'); list.innerHTML=''; const rows=D.txs.map(t=>{const r=document.createElement('div');r.className='row';r.style.height='0px';
  r.innerHTML=`<i style="background:${CATC[t.cat]||'#8a97a0'}">${t.payee[0]}</i><div><b>${t.payee}</b><small>${t.cat==='Income'?'Credited':t.cat} · ${t.day}</small></div><span class="amt ${t.credit?'in':'out'}">${t.credit?'+'+inr(t.credit):'−'+inr(t.debit)}</span>`;
  list.insertBefore(r,list.firstChild);return r});
$('bkMore').textContent=`+ ${Math.max(0,D.monthTx-D.txs.length)} more this month`;
function renderA(t){const k=t*D.txs.length, i=Math.floor(k), f=k-i;
  rows.forEach((r,j)=>{const p=clamp(k-j);r.style.height=(46*eo(p))+'px';r.style.opacity=clamp(p*2)});
  const prev=i<=0?D.txBefore:D.txs[Math.min(i,D.txs.length)-1].bal, next=i>=D.txs.length?prev:D.txs[i].bal;
  $('balNum').textContent=inr(lerp(prev,next,i>=D.txs.length?0:sm(f)));}

/* ----- scene B: upload + masking ----- */
const tbl=$('kpTbl'); tbl.innerHTML=''; const mrow=D.masks.map(m=>{const r=document.createElement('div');r.className='mrow';
  r.innerHTML=`<span class="raw"></span><span class="msk"></span>`;r.firstChild.textContent=m.raw;r.lastChild.textContent=m.masked;tbl.appendChild(r);return r.lastChild});
const chips=[...document.querySelectorAll('#scB .chip')];
function renderB(t){const drop=eo(t/.25); $('kpFile').style.transform=`translateY(${(1-drop)*-70}px) scale(${.92+.08*drop})`; $('kpFile').style.opacity=clamp(t/.1);
  mrow.forEach((m,j)=>{const p=clamp((t-.25-j*.06)/.3);m.style.clipPath=`inset(0 ${100-100*p}% 0 0)`;m.parentElement.style.opacity=clamp((t-.18-j*.03)/.1)});
  chips.forEach((c,j)=>{const p=clamp((t-.7-j*.08)/.12);c.style.opacity=p;c.style.transform=`translateY(${(1-p)*8}px)`});}

/* ----- scene C: money flow (spans two chapters: f runs 0..2) ----- */
const items=D.items, n=items.length, T=84, H=266, total=Math.max(D.income,D.spend), s=H/total;
const hh=items.map(it=>Math.max(2.2,it.value*s)); let acc=T; const y0=hh.map(h=>{const y=acc;acc+=h;return y});
const gi={}; const colors=items.map(it=>{const k=gi[it.group]=(gi[it.group]??-1)+1; return lighten(GC[it.group],Math.min(.4,k*.09))});
const yc=i=>T+i*((H-12)/(n-1))+6;
['kpRib','kpLeft','kpRight','kpCat'].forEach(id=>$(id).innerHTML='');
const rib=items.map(()=>el('path',{},$('kpRib'))), lb=items.map(()=>el('rect',{x:70,width:12},$('kpLeft'))), rb=items.map(()=>el('rect',{x:430,width:8},$('kpRight')));
const catG=items.map(it=>{const g=el('g',{},$('kpCat'));g.innerHTML=`<text x="446" font-size="12.5" fill="#fff" fill-opacity=".95">${it.name}</text><text x="618" font-size="12.5" fill="#fff" fill-opacity=".75" text-anchor="end">${inr(it.value)}</text>`;return g});
function stateOf(kind){let cum=0;return items.map((it,i)=>{let yt,ht=hh[i],col,op;
  if(kind==='A'){yt=y0[i];col=NEUTRAL;op=.55}
  else if(kind==='B'){yt=yc(i)-ht/2;col=colors[i];op=.9}
  else if(it.group==='left'){yt=292;ht=Math.max(6,hh[i]);col=colors[i];op=1}
  else{ht=hh[i]*.6;yt=T+14+cum;cum+=ht;col=colors[i];op=.3}
  return {yt,ht,r:col[0],g:col[1],b:col[2],op}})}
const SA=stateOf('A'), SB=stateOf('B'), SC=stateOf('C');
$('kpSumA').textContent=`Spent ${inr(D.spend)} a month`; $('kpSumB').textContent=`Left over ${inr(D.left)} a month`;
$('kpTankT').textContent=`Emergency fund: ${inr(D.emergency.saved)} of ${inr(D.emergency.target)}`; $('kpTankT2').textContent=`about ${D.emergency.years} years at this pace`;
function renderC(f){const a=f<1?SA:SB, b=f<1?SB:SC, t=sm(f<1?f:f-1), end=f<1?lerp(.3,1,sm(f*1.4)):1;
  $('kpFadeEnd').setAttribute('stop-opacity',end.toFixed(3));
  items.forEach((_,i)=>{const x=a[i],y=b[i],p={};for(const k in x)p[k]=lerp(x[k],y[k],t);
    const col=`rgb(${p.r|0},${p.g|0},${p.b|0})`,x0=82,x1=430,c=174,ya=y0[i],ha=hh[i];
    rib[i].setAttribute('d',`M${x0},${ya} C${x0+c},${ya} ${x1-c},${p.yt} ${x1},${p.yt} L${x1},${p.yt+p.ht} C${x1-c},${p.yt+p.ht} ${x0+c},${ya+ha} ${x0},${ya+ha}Z`);
    rib[i].setAttribute('fill',col);rib[i].setAttribute('fill-opacity',p.op.toFixed(3));
    lb[i].setAttribute('y',ya);lb[i].setAttribute('height',ha);lb[i].setAttribute('fill',col);
    rb[i].setAttribute('y',p.yt);rb[i].setAttribute('height',p.ht);rb[i].setAttribute('fill',col);rb[i].setAttribute('fill-opacity',(p.op*end).toFixed(3));
    catG[i].setAttribute('transform',`translate(0,${p.yt+p.ht/2+4})`)});
  $('kpQ').setAttribute('opacity',clamp(1-f*2.6));
  $('kpCat').setAttribute('opacity',f<1?sm((f-.5)/.4):clamp(1-(f-1)*3));
  $('kpSum').setAttribute('opacity',sm((f-1.35)/.45));}

/* ----- scene D: quiz card, then risk gauge ----- */
const qd=$('kpQuiz'); qd.innerHTML=`<div class="qprog"><span>Question 2 of 9</span><span>${'<i class="on"></i>'.repeat(2)}${'<i></i>'.repeat(7)}</span></div><h4></h4>${D.quiz.options.map(o=>`<div class="opt"></div>`).join('')}`;
qd.querySelector('h4').textContent=D.quiz.q; [...qd.querySelectorAll('.opt')].forEach((o,i)=>o.textContent=D.quiz.options[i]);
const opts=[...qd.querySelectorAll('.opt')], g=$('kpGauge'); g.innerHTML='';
const cx=200, cy=205, R=135, ang=p=>Math.PI*(1-p), pt=(p,r)=>[cx+r*Math.cos(ang(p)),cy-r*Math.sin(ang(p))];
const arc=(p0,p1,r)=>{const a=pt(p0,r),b=pt(p1,r);return `M${a[0].toFixed(1)},${a[1].toFixed(1)} A${r},${r} 0 0 1 ${b[0].toFixed(1)},${b[1].toFixed(1)}`};
const segs=[[0,.36,'#8fc7b1','Conservative'],[.36,.69,'#14b8a6','Moderate'],[.69,1,'#e9a23b','Aggressive']];
segs.forEach(([a,b,c])=>el('path',{d:arc(a+.006,b-.006,R),stroke:c,'stroke-width':26,fill:'none','stroke-linecap':'butt',opacity:.95},g));
const gl=el('g',{},g); [['9',0],['27',1]].forEach(([t,p])=>{const q=pt(p,R+26);const x=el('text',{x:q[0],y:q[1]+14,'font-size':12,fill:'#fff','fill-opacity':.7,'text-anchor':'middle'},gl);x.textContent=t});
const needle=el('g',{},g); el('path',{d:`M${cx-6},${cy} L${cx},${cy-R+14} L${cx+6},${cy}Z`,fill:'#fff'},needle); el('circle',{cx,cy,r:11,fill:'#fff',stroke:'#0f5c43','stroke-width':4},needle);
const gt=el('text',{x:cx,y:cy+42,'font-size':26,'font-weight':800,fill:'#fff','text-anchor':'middle'},g), gs=el('text',{x:cx,y:cy+60,'font-size':12.5,fill:'#fff','fill-opacity':.7,'text-anchor':'middle'},g);
gs.textContent='18 of 27 · describes comfort with risk, not a product'; const gz=el('text',{x:cx,y:20,'font-size':13,fill:'#fff','fill-opacity':.8,'text-anchor':'middle'},g); gz.textContent='Your answers become a risk profile';
function renderD(t){const q=clamp(1-sm((t-.36)/.12)); qd.style.opacity=q;qd.style.transform=`translateY(${(1-sm(t/.12))*18+(1-q)*-24}px) scale(${.96+.04*q})`;
  opts.forEach((o,i)=>o.classList.toggle('sel',i===1&&t>.22));
  const gp=sm((t-.5)/.12); g.style.opacity=gp; const k=eo((t-.58)/.38), p=.5*k+(k<1?.04*Math.sin(k*9)*(1-k):0);
  needle.setAttribute('transform',`rotate(${-90+180*p} ${cx} ${cy})`); const lab=p<.36?'Conservative':p<.69?'Moderate':'Aggressive'; gt.textContent=t>.62?lab:'';}

/* ----- scene E: options compared ----- */
const pl=$('kpPlot'); pl.innerHTML=''; const PX0=100,PX1=610,PY0=330,PY1=60;
[['Easy access, steady',PX0+14,PY0-10,'start'],['Easy access, can swing',PX0+14,PY1+18,'start'],['Locked in, steady',PX1-8,PY0-10,'end'],['Locked in, can swing',PX1-8,PY1+18,'end']].forEach(([t,x,y,a])=>{const e=el('text',{x,y,'font-size':11,fill:'#fff','fill-opacity':.32,'text-anchor':a,'font-weight':700},pl);e.textContent=t.toUpperCase()});
el('line',{x1:PX0,y1:PY0,x2:PX1,y2:PY0,stroke:'#fff','stroke-opacity':.3},pl); el('line',{x1:PX0,y1:PY0,x2:PX0,y2:PY1,stroke:'#fff','stroke-opacity':.3},pl);
el('line',{x1:(PX0+PX1)/2,y1:PY1,x2:(PX0+PX1)/2,y2:PY0,stroke:'#fff','stroke-opacity':.08,'stroke-dasharray':'4 6'},pl); el('line',{x1:PX0,y1:(PY0+PY1)/2,x2:PX1,y2:(PY0+PY1)/2,stroke:'#fff','stroke-opacity':.08,'stroke-dasharray':'4 6'},pl);
const lx=el('text',{x:(PX0+PX1)/2,y:362,'font-size':12,fill:'#fff','fill-opacity':.75,'text-anchor':'middle'},pl); lx.textContent='How long your money is locked in  →';
const ly=el('text',{transform:`translate(60,${(PY0+PY1)/2}) rotate(-90)`,'font-size':12,fill:'#fff','fill-opacity':.75,'text-anchor':'middle'},pl); ly.textContent='How much it can grow or swing  →';
const nt=el('text',{x:(PX0+PX1)/2,y:384,'font-size':10.5,fill:'#fff','fill-opacity':.5,'text-anchor':'middle'},pl); nt.textContent='Illustrative positions to show the trade-off, not advice';
const OPT=[['Savings account',.05,.10],['FD',.40,.26],['RD',.52,.18],['Gold',.14,.56],['PPF',.90,.38],['NPS',.96,.68],['Index fund',.24,.90]];
const bub=OPT.map(([name,x,y],i)=>{const px=PX0+30+x*(PX1-PX0-60), py=PY0-14-y*(PY0-PY1-30), left=x>.8, g=el('g',{},pl);
  el('circle',{cx:px,cy:py,r:15,fill:i===6?'#5eead4':'#fff','fill-opacity':.12},g); el('circle',{cx:px,cy:py,r:7.5,fill:i===6?'#5eead4':'#fff',stroke:'#0f5c43','stroke-width':2},g);
  const t=el('text',{x:left?px-16:px+16,y:py+4.5,'font-size':13.5,fill:'#fff','text-anchor':left?'end':'start','font-weight':700},g); t.textContent=name; return g});
function renderE(t){bub.forEach((b,i)=>{const p=eo((t-.05-i*.1)/.14);b.setAttribute('opacity',p);b.setAttribute('transform',`translate(0,${(1-p)*14})`)})}

/* ----- scene F: simulator ----- */
const sim=D.sim, M=sim.p50.length, X0=90, X1=500, Y0=330, Y1=70, vmax=Math.max(...sim.p90)*1.06, svgS=$('kpSim'); svgS.innerHTML='';
const sx=m=>X0+(m+1)/M*(X1-X0), sy=v=>Y0-v/vmax*(Y0-Y1), P=(v,m)=>`${sx(m).toFixed(1)},${sy(v).toFixed(1)}`, pts=a=>a.map((v,m)=>P(v,m)).join(' ');
const defs=el('defs',{},svgS); const cp=el('clipPath',{id:'kpSimClip'},defs), cr=el('rect',{x:X0-6,y:20,width:0,height:340},cp);
const bg=el('linearGradient',{id:'kpBand',x1:0,y1:0,x2:0,y2:1},defs); el('stop',{offset:0,'stop-color':'#5eead4','stop-opacity':.5},bg); el('stop',{offset:1,'stop-color':'#5eead4','stop-opacity':.14},bg);
const stepv=[1e5,2e5,5e5,1e6,2e6].find(v=>vmax/v<=5)||2e6, lk=v=>v>=1e5?`₹${+(v/1e5).toFixed(1)}L`:`₹${Math.round(v/1e3)}k`;
for(let v=0;v<=vmax;v+=stepv){el('line',{x1:X0,x2:X1,y1:sy(v),y2:sy(v),stroke:'#fff','stroke-opacity':v?.1:.3},svgS); if(v){const t=el('text',{x:X0-8,y:sy(v)+4,'font-size':11.5,fill:'#fff','fill-opacity':.7,'text-anchor':'end'},svgS);t.textContent=lk(v)}}
[[X0,'Today','start'],[(X0+X1)/2,`${sim.years/2} years`,'middle'],[X1,`${sim.years} years`,'end']].forEach(([x,l,a])=>{const t=el('text',{x,y:Y0+20,'font-size':11.5,fill:'#fff','fill-opacity':.7,'text-anchor':a},svgS);t.textContent=l});
const gS=el('g',{'clip-path':'url(#kpSimClip)'},svgS);
sim.paths.forEach(p=>el('polyline',{points:pts(p),fill:'none',stroke:'#fff','stroke-opacity':.13,'stroke-width':1},gS));
let band='M'+sim.p90.map((v,m)=>P(v,m)).join(' L'); for(let m=M-1;m>=0;m--)band+=' L'+P(sim.p10[m],m);
el('path',{d:band+'Z',fill:'url(#kpBand)'},gS);
el('polyline',{points:pts(sim.invested),fill:'none',stroke:'#fff','stroke-opacity':.65,'stroke-width':1.6,'stroke-dasharray':'2 4'},gS);
el('polyline',{points:pts(sim.fd),fill:'none',stroke:'#e9c46a','stroke-width':1.8,'stroke-dasharray':'7 5'},gS);
el('polyline',{points:pts(sim.p50),fill:'none',stroke:'#5eead4','stroke-width':3,'stroke-linejoin':'round'},gS);
const cur=el('line',{y1:Y1-10,y2:Y0,stroke:'#fff','stroke-opacity':.5,'stroke-dasharray':'3 4'},svgS), curDot=el('circle',{r:5,fill:'#5eead4',stroke:'#fff','stroke-width':2},svgS);
const rd=el('g',{},svgS), rdBg=el('rect',{rx:8,fill:'#000','fill-opacity':.45,width:150,height:56},rd), rdT=[0,1,2].map(k=>el('text',{x:10,y:17+k*15,'font-size':11.5,fill:'#fff','fill-opacity':k?.85:1,'font-weight':k?500:700},rd));
const ends=el('g',{opacity:0},svgS), E=[[sim.p90.at(-1),'Good case','#5eead4'],[sim.p50.at(-1),'Middle','#5eead4'],[sim.fd.at(-1),'FD at 7%','#e9c46a'],[sim.p10.at(-1),'Bad case','#fff'],[sim.invested.at(-1),'Put in','#fff']];
(function(){const ys=E.map(([v])=>sy(v)),o=ys.map((y,i)=>i).sort((a,b)=>ys[a]-ys[b]);let prev=-99;const fy={};o.forEach(i=>{const y=Math.max(ys[i],prev+14);fy[i]=y;prev=y});
  E.forEach(([v,l,c],i)=>{const t=el('text',{x:X1+8,y:fy[i]+4,'font-size':12,fill:c,'font-weight':700},ends);t.textContent=`${l} ${inr(v)}`})})();
const lg=el('text',{x:X0,y:392,'font-size':10.5,fill:'#fff','fill-opacity':.6},svgS); lg.textContent=`${inr(sim.monthly)} a month · 36 of 10,000 simulated paths · today's money · shaded = 1 in 10 worse to 1 in 10 better`;
function renderF(t){const r=eo(t/.85), m=Math.max(0,Math.min(M-1,Math.round(r*(M-1))));
  cr.setAttribute('width',(X1-X0+12)*r+(r>=1?80:0)); cur.setAttribute('x1',sx(m));cur.setAttribute('x2',sx(m)); curDot.setAttribute('cx',sx(m));curDot.setAttribute('cy',sy(sim.p50[m]));
  const yr=((m+1)/12).toFixed(1); rdT[0].textContent=`Year ${yr}`; rdT[1].textContent=`Middle ${inr(sim.p50[m])}`; rdT[2].textContent=`${inr(sim.p10[m])} to ${inr(sim.p90[m])}`;
  const rx=Math.min(sx(m)+10,X1-140); rd.setAttribute('transform',`translate(${rx},${Math.max(30,sy(sim.p90[m])-8)})`); rd.setAttribute('opacity',r<1?clamp(t/.08):0);cur.setAttribute('opacity',r<1?1:0);curDot.setAttribute('opacity',r<1?1:0);
  ends.setAttribute('opacity',sm((t-.82)/.15));}

/* ----- scene G: scam ----- */
const marks=[$('m1'),$('m2'),$('m3')], flags=[...document.querySelectorAll('#scG .flag')];
function renderG(t){marks.forEach((m,i)=>{m.style.setProperty('--p',eo((t-.12-i*.17)/.15))});
  flags.forEach((f,i)=>{const p=clamp((t-.2-i*.17)/.12);f.style.opacity=p;f.style.transform=`translateY(${(1-p)*8}px)`});
  const v=sm((t-.68)/.14);$('kpVerd').style.opacity=v;$('kpVerd').style.transform=`translateY(${(1-v)*14}px)`;$('kpRisk').style.width=(92*eo((t-.74)/.2))+'%'}

/* ----- rail, proof ----- */
const rail=$('kpRail'); const nodes=ST.map((s,i)=>{const d=document.createElement('div');d.className='node'+(i===0?' first':i===N-1?' last':'');d.style.left=(i/(N-1)*100)+'%';d.innerHTML=`<span>${s.name}</span>`;d.addEventListener('click',()=>scrollToU(1.5+i));rail.appendChild(d);return d});
$('kpProof').innerHTML=[[`10,000`,`simulated futures on 19 years of real Nifty 50 history`],[`${D.metrics.f1.toFixed(2)}`,`macro F1 on ${D.metrics.rows} held-out real transactions (rules + ML)`],[`0`,`statements stored. Processed in memory, then gone`]].map(([a,b])=>`<div class="pc"><b>${a}</b><span>${b}</span></div>`).join('');
function scrollToU(u){const r=root.getBoundingClientRect(),st=sc.scrollTop,span=root.offsetHeight-$('kpStick').offsetHeight;sc.scrollTo({top:st+r.top+u*span/10,behavior:reduce?'auto':'smooth'})}

/* ----- background particles: money that leaks away, then money that grows ----- */
const cv=$('kpCv'), cx2=cv.getContext('2d'); let W=0,Hh=0,parts=[],dpr=Math.min(2,devicePixelRatio||1), mood=0;
function resize(){const b=cv.getBoundingClientRect();W=b.width;Hh=b.height;cv.width=W*dpr;cv.height=Hh*dpr;cx2.setTransform(dpr,0,0,dpr,0,0)}
function spawn(init){const m=mood<.42; return {x:init?Math.random()*W:(m?-10:Math.random()*W),y:init?Math.random()*Hh:(m?Math.random()*Hh:Hh+10),r:1.5+Math.random()*3.2,a:.15+Math.random()*.4,ph:Math.random()*6.28}}
resize(); for(let i=0;i<(narrow()?26:52);i++)parts.push(spawn(true));
function drawParts(dt){cx2.clearRect(0,0,W,Hh); const k=sm((mood-.3)/.4);
  parts.forEach((p,i)=>{p.ph+=dt*.002; p.x+=lerp(.5,.06,k)*dt*.06+Math.sin(p.ph)*.15; p.y+=lerp(.1,-.45,k)*dt*.06;
    if(p.x>W+12||p.y<-12||p.y>Hh+12||p.x<-14)parts[i]=spawn(false);
    const grad=cx2.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r*3); const c=k>.5?'245,197,66':'255,255,255';
    grad.addColorStop(0,`rgba(${c},${p.a})`);grad.addColorStop(1,`rgba(${c},0)`);cx2.fillStyle=grad;cx2.beginPath();cx2.arc(p.x,p.y,p.r*3,0,6.283);cx2.fill()})}

/* ----- main loop ----- */
const SCN=[['scA',.55,2.12],['scB',1.88,3.12],['scC',2.88,5.12],['scD',4.88,6.12],['scE',5.88,7.12],['scF',6.88,8.12],['scG',7.88,9.12]].map(([id,a,b])=>[$(id),a,b]);
const fns=[t=>renderA(clamp((t.u-.85)/1)),t=>renderB(clamp(t.u-2)),t=>renderC(clamp(t.u-3,0,2)),t=>renderD(clamp(t.u-5)),t=>renderE(clamp(t.u-6)),t=>renderF(clamp(t.u-7)),t=>renderG(clamp(t.u-8))];
let last=performance.now(), lastU=-1, lastW=0;
function frame(now){ if(stopped||!document.getElementById('kp-root')) return; requestAnimationFrame(frame);
  const dt=Math.min(50,now-last); last=now;
  const stick=$('kpStick'), span=root.offsetHeight-stick.offsetHeight, u=clamp(-root.getBoundingClientRect().top/(span/10),0,10);
  if(innerWidth!==lastW){lastW=innerWidth;resize()}
  if(u!==lastU){lastU=u; render(u)}
  if(!reduce&&u<9.9)drawParts(dt);}
function render(u){
  const h=clamp(u), hero=$('kpHero'); hero.style.opacity=clamp(1-h*2.1); hero.style.transform=`translateY(${-h*42}vh) scale(${1-.25*h})`; hero.style.pointerEvents=h>.4?'none':'auto';
  $('kpBrand').style.opacity=sm((u-.7)/.3)*(u<9.2?1:0);
  const g=u<1?1-.62*sm(u):.38+.62*sm((u-1)/8); $('kpBg1').style.opacity=g; mood=clamp((u-1)/8);
  chEls.forEach((c,i)=>{const t=u-(1+i), lead=i===0?.28:0, a=clamp((t+lead)/.2)*clamp((1-t)/.2); c.style.opacity=a; c.style.transform=`translateY(${(1-a)*(t<.5?30:-30)}px)`; c.style.pointerEvents=a>.6?'auto':'none';
    const sv=ST[i].head; figEls[i].textContent=sv.text?sv.text:(sv.inr?inr(sv.value*eo((t+lead)/.55)):Math.round(sv.value*eo((t+lead)/.55)).toLocaleString('en-IN'));});
  const vis=$('kpVis'), vp=win(u,.5,9.1,.4); vis.style.opacity=vp; vis.style.transform=`translateX(${(1-vp)*60}px)`;
  const ctx={u}; SCN.forEach(([e,a,b],i)=>{const o=win(u,a,b,.24);e.style.opacity=o;e.style.pointerEvents='none'; if(o>0.001)fns[i](ctx)});
  const pos=clamp((u-1.5)/(N-1),0,1)*(N-1); const rp=pos/(N-1)*100;
  rail.style.opacity=win(u,.6,9.3,.35); $('kpDot').style.left=rp+'%'; $('kpFill').style.width=rp+'%';
  nodes.forEach((nd,i)=>{nd.classList.toggle('done',i<Math.round(pos)-0&&i<pos-.5);nd.classList.toggle('on',Math.round(pos)===i&&u>1.0&&u<9.1)});
  const o=$('kpOutro'), ov=clamp((u-9.1)/.5); o.style.opacity=ov; o.style.pointerEvents=ov>.5?'auto':'none';
}
render(0); requestAnimationFrame(frame);
})();
</script>
"""
