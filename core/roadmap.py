"""Home-page story: one month of money, from "where did it go?" to a plan, told with the demo statement's real numbers.

The reader moves the story (Next / Back, arrow keys, swipe, dots, or a stop's link).
Rendered with components.html; pure SVG + vanilla JS, no external files, no character art.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.categorizer import INCOME, TRANSFERS, categorize
from core.parsers import parse_statement
from core.simulator import load_monthly_returns, simulate
from core.spending import format_inr
from core.surplus import ESSENTIAL_CATEGORIES, compute_surplus

AVOIDABLE = ["Food & dining", "Shopping", "Subscriptions"]
SIP_YEARS = 10
INFLATION = 0.06
DEMO_FILE = Path(__file__).resolve().parent.parent / "data" / "demo_statement.csv"


def story_data() -> dict:
    """Numbers for the story, all computed from the demo statement and the Nifty history."""
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
    sim = simulate(float(monthly), SIP_YEARS, load_monthly_returns()["return"].to_numpy(), INFLATION)

    def series(a) -> list[int]:
        return [int(round(x)) for x in a]

    return {
        "income": round(income), "spend": round(spend), "left": round(left), "avoidable": round(avoidable),
        "tx": int(len(df)), "items": items,
        "emergency": {"target": round(r["emergency_target"]), "saved": round(r["emergency_saved"])},
        "sim": {
            "monthly": monthly, "years": SIP_YEARS,
            "p10": series(sim["bands"][10]), "p50": series(sim["bands"][50]), "p90": series(sim["bands"][90]),
            "invested": series(sim["invested"]), "fd": series(sim["fd"]),
        },
    }


def chapters(d: dict) -> list[dict]:
    """Title, card text, headline figure, mood (0 to 1) and page for each step."""
    f = format_inr
    sim = d["sim"]
    lo, mid, hi = sim["p10"][-1], sim["p50"][-1], sim["p90"][-1]
    return [
        dict(name="Payday", url=None, mood=0.0, head=dict(value=d["income"], inr=True, cap="came in, in an average month"),
             text=f"A fictional student earns {f(d['income'])} a month. By the end of it almost all of it has gone, "
                  "and it's hard to say where. This is the demo account; yours would show your own numbers."),
        dict(name="Upload", url="upload", mood=0.12, head=dict(value=d["tx"], cap="transactions read and masked"),
             text=f"Upload a bank statement (SBI, HDFC or a standard CSV). Here, {d['tx']} transactions are read, and "
                  "account numbers and UPI IDs are masked before anything else happens. Nothing is saved."),
        dict(name="My Spending", url="my-spending", mood=0.26, head=dict(value=d["avoidable"], inr=True, cap="a month on avoidable spending"),
             text=f"Every payment is sorted into a category. About {f(d['avoidable'])} a month goes on food delivery, "
                  "shopping and subscriptions, the part most people can change. Fix any category the app gets wrong and every chart updates."),
        dict(name="My Surplus", url="my-surplus", mood=0.42, head=dict(value=d["left"], inr=True, cap="left over each month"),
             text=f"Income minus spending leaves {f(d['left'])} a month. Before taking any investment risk, the app asks for an "
                  f"emergency fund first: three months of essentials, {f(d['emergency']['target'])} here."),
        dict(name="Risk Quiz", url="risk-quiz", mood=0.56, head=dict(text="Moderate", cap="example risk profile"),
             text="Nine questions about time horizon, emergency cover and how you react to losses. An example result: "
                  "'Moderate', a score of 18 out of 27, comfortable with some ups and downs. It describes comfort with risk, nothing more."),
        dict(name="Learn", url="learn", mood=0.70, head=dict(value=7, cap="options, compared"),
             text="Seven options in plain language: savings account, FD, RD, PPF, index fund, gold and NPS. How easy it is to take "
                  "money out, how much it can swing and how it's taxed. The chart is illustrative, not advice."),
        dict(name="Simulator", url="simulator", mood=0.85, head=dict(value=mid, inr=True, cap=f"middle case after {sim['years']} years, in today's money"),
             text=f"A what-if: if a third of that avoidable spending went into a monthly SIP, that's about {f(sim['monthly'])} a month. "
                  f"Real Nifty 50 history is replayed 10,000 times. After {sim['years']} years, in today's money: a bad case of {f(lo)}, "
                  f"a middle case of {f(mid)}, a good case of {f(hi)}. A range, not a prediction."),
        dict(name="Scam Checker", url="scam-checker", mood=1.0, head=dict(text="High risk", cap="3 red flags in this message"),
             text="Paste any investment message and the checker highlights its red flags. This example promises guaranteed returns, "
                  "asks for an upfront fee and moves you to a private Telegram group. Deleting it costs nothing."),
    ]


def build_roadmap(data: dict, dark: bool = False) -> str:
    payload = json.dumps({**data, "stages": chapters(data)}, ensure_ascii=False)
    return TEMPLATE.replace("__DATA__", payload).replace("__THEME__", "dark" if dark else "light")


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{--card:#ffffff;--ink:#12261f;--muted:#5b6b65;--line:rgba(15,92,67,.18)}
.dark{--card:#10211b;--ink:#e7f2ed;--muted:#9fb5ab;--line:rgba(255,255,255,.14)}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:transparent;font-family:"Source Sans Pro",system-ui,sans-serif;overflow:hidden}
.frame{position:absolute;inset:0;border-radius:26px;overflow:hidden;display:flex;gap:14px;padding:14px;
  background:linear-gradient(125deg,#0f5c43,#1B7F5C,#14b8a6,#0f766e);background-size:300% 300%;animation:shift 14s ease infinite}
@keyframes shift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.blob{position:absolute;border-radius:50%;filter:blur(40px);pointer-events:none}
.b1{width:260px;height:260px;background:#f5a524;opacity:.28;right:-70px;bottom:-110px}
.b2{width:220px;height:220px;background:#7c5cff;opacity:.18;left:30%;top:-120px}
.stage{position:relative;flex:1.7;min-width:0;border-radius:18px;background:rgba(3,28,21,.55);border:1px solid rgba(255,255,255,.14);overflow:hidden;color:#fff}
.stage svg{position:absolute;inset:0;width:100%;height:100%;display:block}
.stage svg text{font-family:inherit}
.scene{transition:opacity .55s ease}
.card{position:relative;flex:1;min-width:0;display:flex;flex-direction:column;border-radius:18px;padding:18px 20px 14px;
  background:var(--card);color:var(--ink);box-shadow:0 18px 40px -22px rgba(0,0,0,.5)}
.kicker{font-size:.76rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#1B7F5C}
.dark .kicker{color:#5eead4}
h2{margin:.25rem 0 .55rem;font-size:1.5rem;line-height:1.15;letter-spacing:-.02em}
.text{font-size:1rem;line-height:1.55;color:var(--ink);opacity:.9;flex:1;overflow:auto}
.fade{animation:fade .45s ease both}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.meter{display:flex;align-items:center;gap:8px;font-size:.72rem;font-weight:700;margin:.35rem 0 .65rem}
.meter .bar{position:relative;flex:1;height:6px;border-radius:99px;background:var(--line)}
.meter .fill{position:absolute;inset:0 auto 0 0;border-radius:99px;background:linear-gradient(90deg,#e9a23b,#14b8a6,#1B7F5C);transition:width .9s cubic-bezier(.3,.8,.3,1)}
.open{display:inline-block;margin:.5rem 0;font-weight:700;color:#1B7F5C;text-decoration:none;cursor:pointer;font-size:.95rem}
.dark .open{color:#5eead4}
.open:hover{text-decoration:underline}
.nav{display:flex;align-items:center;gap:10px;border-top:1px solid var(--line);padding-top:12px}
.btn{border:0;border-radius:12px;padding:8px 13px;white-space:nowrap;font-weight:700;font-size:.95rem;cursor:pointer;font-family:inherit}
.btn.next{background:linear-gradient(120deg,#1B7F5C,#14b8a6);color:#fff}
.btn.back{background:transparent;color:var(--ink);border:1px solid var(--line)}
.btn:disabled{opacity:.35;cursor:default}
.btn:focus-visible,.dot:focus-visible,.open:focus-visible{outline:3px solid #f5a524;outline-offset:2px}
.dots{display:flex;gap:5px;flex:1;justify-content:center;min-width:0}
.dot{flex:0 0 auto;width:8px;height:8px;border-radius:50%;border:0;padding:0;background:var(--line);cursor:pointer;transition:width .3s}
.dot.on{background:#1B7F5C;width:18px;border-radius:99px}
.hint{font-size:.72rem;color:var(--muted);margin-top:6px;text-align:right}
.pop{opacity:0;transform-box:fill-box;transform-origin:center}
.go .pop{animation:pop .5s cubic-bezier(.3,1.4,.5,1) forwards}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:none}}
.scam{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;gap:10px;padding:19% 8% 6%;opacity:0;pointer-events:none;transition:opacity .55s ease}
.scam.show{opacity:1}
.msg{background:#f4f7f5;color:#1d2b26;border-radius:14px 14px 14px 4px;padding:12px 14px;font-size:13.5px;line-height:1.5;box-shadow:0 10px 30px -14px rgba(0,0,0,.6);max-width:430px}
.msg .from{font-size:11px;font-weight:700;color:#6b7c75;margin-bottom:4px}
.msg p{margin:0 0 6px}
mark{color:inherit;background:linear-gradient(rgba(224,122,95,.45),rgba(224,122,95,.45)) no-repeat left/0% 100%;transition:background-size .7s ease;border-radius:3px;padding:0 1px}
.scam.show mark{background-size:100% 100%}
.scam.show mark[data-n="1"]{transition-delay:.7s}.scam.show mark[data-n="2"]{transition-delay:1.3s}.scam.show mark[data-n="3"]{transition-delay:1.9s}
.flags{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px 8px;font-size:12.5px}
.flags li{opacity:0;transform:translateY(6px);transition:all .45s ease;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:99px;padding:3px 10px 3px 4px;display:flex;align-items:center;gap:6px}
.flags b{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;background:#e07a5f;color:#fff;font-size:11px}
.scam.show .flags li{opacity:1;transform:none}
.scam.show .flags li:nth-child(1){transition-delay:.9s}.scam.show .flags li:nth-child(2){transition-delay:1.5s}.scam.show .flags li:nth-child(3){transition-delay:2.1s}
.risk{display:flex;align-items:center;gap:10px;font-size:12.5px;max-width:430px}
.rbar{flex:1;height:7px;border-radius:99px;background:rgba(255,255,255,.18);overflow:hidden}
.rbar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#e9c46a,#e07a5f);transition:width 1s ease 2.4s;border-radius:99px}
.scam.show .rbar i{width:92%}
.narrow .catlab{display:none}
@media (max-width:640px){
  .frame{flex-direction:column;padding:10px;gap:10px}
  .stage{flex:0 0 42%}
  .card{padding:12px 14px 10px}
  h2{font-size:1.2rem;margin:.1rem 0 .3rem}
  .text{font-size:.9rem;line-height:1.4}
  .meter{margin:.2rem 0 .4rem}
  .hint{display:none}
  .msg{font-size:12px;padding:9px 11px}.flags{font-size:11px}
  .scam{padding:20% 5% 4%;gap:7px}
}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}.pop{opacity:1}}
</style></head><body class="__THEME__">
<div class="frame">
 <span class="blob b1"></span><span class="blob b2"></span>
 <div class="stage" id="stage">
 <svg id="s" viewBox="0 0 640 400" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
  <defs>
   <linearGradient id="fadeG" gradientUnits="userSpaceOnUse" x1="82" y1="0" x2="430" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="1"/><stop id="fadeEnd" offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
   <mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="640" height="400"><rect width="640" height="400" fill="url(#fadeG)"/></mask>
   <clipPath id="simClip"><rect id="simClipRect" x="70" y="40" width="0" height="330"/></clipPath>
   <linearGradient id="bandG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4" stop-opacity=".5"/><stop offset="1" stop-color="#5eead4" stop-opacity=".16"/></linearGradient>
  </defs>
  <text id="headNum" x="34" y="46" font-size="34" font-weight="700" fill="#fff" letter-spacing="-.5"></text>
  <text id="headCap" x="36" y="64" font-size="12.5" fill="#fff" fill-opacity=".72"></text>

  <g id="g_flow" class="scene">
   <g id="ribbons" mask="url(#fade)"></g>
   <g id="leftBar"></g><g id="rightBar"></g>
   <g id="catLabels" class="catlab"></g>
   <g id="sumLabels" opacity="0">
    <text id="sumSpent" x="448" y="150" font-size="14" font-weight="600" fill="#fff"></text>
    <text id="sumLeft" x="448" y="290" font-size="14" font-weight="600" fill="#e9c46a"></text>
    <rect x="448" y="304" width="164" height="8" rx="4" fill="#fff" fill-opacity=".16"/>
    <rect id="tankFill" x="448" y="304" width="0" height="8" rx="4" fill="#e9c46a"/>
    <text id="tankTxt" x="448" y="330" font-size="11" fill="#fff" fill-opacity=".75"></text>
    <text x="448" y="344" font-size="11" fill="#fff" fill-opacity=".55">3 months of essentials, built first</text>
   </g>
   <g id="q" opacity="0"><text x="448" y="222" font-size="20" font-style="italic" fill="#fff" fill-opacity=".9">Where did it go?</text></g>
   <g id="chips" opacity="0">
    <g transform="translate(448,150)"><rect width="164" height="26" rx="13" fill="#fff" fill-opacity=".12" stroke="#fff" stroke-opacity=".25"/><path d="M12,13 l4,4 l7,-8" stroke="#5eead4" stroke-width="2" fill="none" stroke-linecap="round"/><text id="chipTx" x="30" y="17.5" font-size="11.5" fill="#fff"></text></g>
    <g transform="translate(448,186)"><rect width="164" height="26" rx="13" fill="#fff" fill-opacity=".12" stroke="#fff" stroke-opacity=".25"/><path d="M12,13 l4,4 l7,-8" stroke="#5eead4" stroke-width="2" fill="none" stroke-linecap="round"/><text x="30" y="17.5" font-size="11.5" fill="#fff">Account numbers masked</text></g>
    <g transform="translate(448,222)"><rect width="164" height="26" rx="13" fill="#fff" fill-opacity=".12" stroke="#fff" stroke-opacity=".25"/><path d="M12,13 l4,4 l7,-8" stroke="#5eead4" stroke-width="2" fill="none" stroke-linecap="round"/><text x="30" y="17.5" font-size="11.5" fill="#fff">Nothing is saved</text></g>
   </g>
  </g>

  <g id="g_risk" class="scene" opacity="0">
    <rect x="90" y="190" width="460" height="10" rx="5" fill="#fff" fill-opacity=".14"/>
    <rect x="90" y="190" width="153" height="10" rx="5" fill="#8fc7b1" fill-opacity=".8"/>
    <rect x="233" y="190" width="174" height="10" fill="#14b8a6" fill-opacity=".9"/>
    <rect x="397" y="190" width="153" height="10" rx="5" fill="#e9a23b" fill-opacity=".85"/>
    <g font-size="14" font-weight="600" fill="#fff" text-anchor="middle">
     <text x="166" y="238">Conservative</text><text x="320" y="238">Moderate</text><text x="474" y="238">Aggressive</text></g>
    <g font-size="11" fill="#fff" fill-opacity=".65" text-anchor="middle">
     <text x="166" y="256">prefers stability</text><text x="320" y="256">accepts some ups and downs</text><text x="474" y="256">comfortable with big swings</text>
     <text x="166" y="150">score 9 to 15</text><text x="320" y="150">16 to 21</text><text x="474" y="150">22 to 27</text></g>
    <g id="riskMark"><path d="M0,178 l-8,-14 h16z" fill="#fff"/><circle cx="0" cy="195" r="11" fill="#fff" stroke="#0f5c43" stroke-width="3"/></g>
    <text x="320" y="300" font-size="11.5" fill="#fff" fill-opacity=".6" text-anchor="middle">Nine questions · an example result, not a recommendation</text>
  </g>

  <g id="g_learn" class="scene" opacity="0">
   <g stroke="#fff" stroke-opacity=".25"><line x1="110" y1="330" x2="580" y2="330"/><line x1="110" y1="330" x2="110" y2="96"/></g>
   <text x="345" y="358" font-size="11.5" fill="#fff" fill-opacity=".7" text-anchor="middle">How long your money is locked in  →</text>
   <text transform="translate(78,213) rotate(-90)" font-size="11.5" fill="#fff" fill-opacity=".7" text-anchor="middle">How much it can grow or swing  →</text>
   <g id="learnDots"></g>
   <text x="345" y="378" font-size="10.5" fill="#fff" fill-opacity=".5" text-anchor="middle">Illustrative positions to show the trade-off, not advice</text>
  </g>

  <g id="g_sim" class="scene" opacity="0">
   <g id="simAxes"></g>
   <g clip-path="url(#simClip)">
    <path id="simBand" fill="url(#bandG)"/>
    <polyline id="simInv" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="1.6" stroke-dasharray="2 4"/>
    <polyline id="simFd" fill="none" stroke="#e9c46a" stroke-width="1.8" stroke-dasharray="7 5"/>
    <polyline id="simMid" fill="none" stroke="#5eead4" stroke-width="3" stroke-linejoin="round"/>
   </g>
   <g id="simEnds" opacity="0"></g>
   <text id="simLegend" x="90" y="392" font-size="10" fill="#fff" fill-opacity=".65"></text>
  </g>
 </svg>
 <div class="scam" id="scam">
  <div class="msg"><div class="from">Unknown number · WhatsApp</div>
   <p><mark data-n="1">Guaranteed 30% returns every month.</mark> Only a few seats left!</p>
   <p>Pay a <mark data-n="2">₹5,000 joining fee</mark> today and we'll add you to our <mark data-n="3">private Telegram group</mark>.</p></div>
  <ul class="flags"><li><b>1</b>Guaranteed returns</li><li><b>2</b>Upfront fee</li><li><b>3</b>Moves you off the app</li></ul>
  <div class="risk"><span>Risk</span><div class="rbar"><i></i></div><b>High</b></div>
 </div>
 </div>
 <div class="card" id="card" aria-live="polite">
  <div class="kicker" id="kicker"></div>
  <h2 id="title"></h2>
  <div class="meter"><span style="color:#c27a10">Wasting</span><span class="bar"><span class="fill" id="fill"></span></span><span style="color:#1B7F5C">Investing wisely</span></div>
  <div class="text" id="text"></div>
  <a class="open" id="open" href="#"></a>
  <div class="nav"><button class="btn back" id="back">← Back</button><div class="dots" id="dots"></div><button class="btn next" id="next">Start →</button></div>
  <div class="hint">Use ← → keys, swipe, or tap the dots</div>
 </div>
</div>
<script>
const D=__DATA__, ST=D.stages, N=ST.length, NS='http://www.w3.org/2000/svg';
const $=id=>document.getElementById(id), svg=(tag,at={},par)=>{const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);par&&par.appendChild(e);return e};
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(innerWidth<640) document.body.classList.add('narrow');
const inr=n=>'₹'+Math.round(n).toLocaleString('en-IN');
const ease=t=>1-Math.pow(1-t,3), lerp=(a,b,t)=>a+(b-a)*t;
function tween(d,fn,done){ if(reduce)d=0; const t0=performance.now(); let id;
  (function f(now){const t=d?Math.min(1,(now-t0)/d):1; fn(ease(t)); if(t<1)id=requestAnimationFrame(f); else done&&done();})(t0);
  return()=>cancelAnimationFrame(id);}
const hex=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
const lighten=(h,k)=>hex(h).map(v=>Math.round(v+(255-v)*k));

/* ---------- money flow ---------- */
const items=D.items, n=items.length, T=84, H=266, total=Math.max(D.income,D.spend), s=H/total;
const GC={essential:'#6fb39d',avoid:'#e07a5f',other:'#c9b88f',left:'#e9c46a'}, NEUTRAL=hex('#e2f4ec');
const hh=items.map(it=>Math.max(2.2,it.value*s)); let acc=T; const y0=hh.map(h=>{const y=acc;acc+=h;return y});
const gi={}; const colors=items.map(it=>{const k=gi[it.group]=(gi[it.group]??-1)+1; return lighten(GC[it.group],Math.min(.4,k*.09))});
const yc=i=>T+i*((H-12)/(n-1))+6;
const rib=items.map(()=>svg('path',{},$('ribbons'))), lb=items.map(()=>svg('rect',{x:70,width:12},$('leftBar'))), rb=items.map(()=>svg('rect',{x:430,width:8},$('rightBar')));
items.forEach((it,i)=>{const g=svg('g',{},$('catLabels'));
  g.innerHTML=`<text x="448" font-size="12" fill="#fff" fill-opacity=".92">${it.name}</text><text x="612" font-size="12" fill="#fff" fill-opacity=".7" text-anchor="end">${inr(it.value)}</text>`});
const catG=[...$('catLabels').children];
function target(step){
  const S={end:[0,.45,1,1][step]??1,lc:step===2?1:0,ls:step===3?1:0,chip:step===1?1:0,q:step===0?1:0,it:[]};
  let cum=0;
  items.forEach((it,i)=>{
    let yt,ht=hh[i],col,op;
    if(step<=1){yt=y0[i];col=NEUTRAL;op=step?.6:.55}
    else if(step===2){yt=yc(i)-ht/2;col=colors[i];op=.88}
    else if(it.group==='left'){yt=292;ht=Math.max(6,hh[i]);col=colors[i];op=1}
    else{ht=hh[i]*.6;yt=T+14+cum;cum+=ht;col=colors[i];op=.3}
    S.it.push({yt,ht,r:col[0],g:col[1],b:col[2],op});
  });
  return S;
}
const mixS=(a,b,t)=>({end:lerp(a.end,b.end,t),lc:lerp(a.lc,b.lc,t),ls:lerp(a.ls,b.ls,t),chip:lerp(a.chip,b.chip,t),q:lerp(a.q,b.q,t),
  it:a.it.map((x,i)=>{const y=b.it[i],o={};for(const k in x)o[k]=lerp(x[k],y[k],t);return o})});
function render(S){
  $('fadeEnd').setAttribute('stop-opacity',S.end.toFixed(3));
  S.it.forEach((p,i)=>{const col=`rgb(${p.r|0},${p.g|0},${p.b|0})`, x0=82, x1=430, c=(x1-x0)*.5, ya=y0[i], ha=hh[i];
    rib[i].setAttribute('d',`M${x0},${ya} C${x0+c},${ya} ${x1-c},${p.yt} ${x1},${p.yt} L${x1},${p.yt+p.ht} C${x1-c},${p.yt+p.ht} ${x0+c},${ya+ha} ${x0},${ya+ha}Z`);
    rib[i].setAttribute('fill',col); rib[i].setAttribute('fill-opacity',p.op.toFixed(3));
    lb[i].setAttribute('y',ya); lb[i].setAttribute('height',ha); lb[i].setAttribute('fill',col);
    rb[i].setAttribute('y',p.yt); rb[i].setAttribute('height',p.ht); rb[i].setAttribute('fill',col); rb[i].setAttribute('fill-opacity',(p.op*S.end).toFixed(3));
    catG[i].setAttribute('transform',`translate(0,${p.yt+p.ht/2+4})`);
  });
  $('catLabels').setAttribute('opacity',S.lc.toFixed(3)); $('sumLabels').setAttribute('opacity',S.ls.toFixed(3));
  $('chips').setAttribute('opacity',S.chip.toFixed(3)); $('q').setAttribute('opacity',S.q.toFixed(3));
}
$('sumSpent').textContent=`Spent ${inr(D.spend)} a month`; $('sumLeft').textContent=`Left over ${inr(D.left)} a month`;
$('tankTxt').textContent=`Emergency fund: ${inr(D.emergency.saved)} of ${inr(D.emergency.target)}`;
$('tankFill').setAttribute('width',Math.max(2,164*D.emergency.saved/D.emergency.target)); $('chipTx').textContent=`${D.tx} transactions read`;
let S=target(0), flowCancel=()=>{}; render(S);

/* ---------- risk profile ---------- */
let riskCancel=()=>{};
function enterRisk(){riskCancel(); $('riskMark').setAttribute('transform','translate(90,0)');
  riskCancel=tween(1100,t=>$('riskMark').setAttribute('transform',`translate(${lerp(90,320,t)},0)`));}

/* ---------- options compared ---------- */
const OPT=[['Savings account',.04,.10],['FD',.38,.27],['RD',.52,.19],['Gold',.17,.55],['PPF',.88,.40],['NPS',.97,.68],['Index fund',.22,.90]];
OPT.forEach(([name,x,y],i)=>{const px=110+x*470*.92, py=330-y*215, left=x>.8, g=svg('g',{class:'pop',style:`animation-delay:${i*160}ms`},$('learnDots'));
  svg('circle',{cx:px,cy:py,r:7,fill:i===6?'#5eead4':'#fff','fill-opacity':.9,stroke:'#0f5c43','stroke-width':2},g);
  const t=svg('text',{x:left?px-13:px+13,y:py+4.5,'font-size':13,fill:'#fff','text-anchor':left?'end':'start','font-weight':600},g); t.textContent=name;});
function enterLearn(){const g=$('learnDots');g.classList.remove('go');void g.getBoundingClientRect();g.classList.add('go');}

/* ---------- simulator range ---------- */
const sim=D.sim, M=sim.p50.length, X0=90, X1=468, Y0=330, Y1=96, vmax=Math.max(...sim.p90)*1.06;
const sx=m=>X0+(m+1)/M*(X1-X0), sy=v=>Y0-v/vmax*(Y0-Y1), pt=(v,m)=>`${sx(m).toFixed(1)},${sy(v).toFixed(1)}`, pts=a=>a.map((v,m)=>pt(v,m)).join(' ');
let band='M'+sim.p90.map((v,m)=>pt(v,m)).join(' L'); for(let m=M-1;m>=0;m--)band+=' L'+pt(sim.p10[m],m); $('simBand').setAttribute('d',band+'Z');
$('simMid').setAttribute('points',pts(sim.p50)); $('simInv').setAttribute('points',pts(sim.invested)); $('simFd').setAttribute('points',pts(sim.fd));
(function axes(){const g=$('simAxes'), lk=v=>v>=1e5?`₹${+(v/1e5).toFixed(1)}L`:`₹${Math.round(v/1e3)}k`;
  const stepv=[1e5,2e5,5e5,1e6,2e6].find(v=>vmax/v<=5)||2e6;
  for(let v=0;v<=vmax;v+=stepv){svg('line',{x1:X0,x2:X1,y1:sy(v),y2:sy(v),stroke:'#fff','stroke-opacity':v?.1:.3},g); if(v){const t=svg('text',{x:X0-8,y:sy(v)+4,'font-size':11,fill:'#fff','fill-opacity':.65,'text-anchor':'end'},g);t.textContent=lk(v);}}
  [[X0,'Today','start'],[(X0+X1)/2,`${sim.years/2} years`,'middle'],[X1,`${sim.years} years`,'end']].forEach(([x,l,a])=>{const t=svg('text',{x,y:Y0+18,'font-size':11,fill:'#fff','fill-opacity':.65,'text-anchor':a},g);t.textContent=l});})();
(function ends(){const g=$('simEnds'), e=[[sim.p90.at(-1),'Good case','#5eead4'],[sim.p50.at(-1),'Middle','#5eead4'],[sim.fd.at(-1),'FD','#e9c46a'],[sim.p10.at(-1),'Bad case','#fff'],[sim.invested.at(-1),'Put in','#fff']];
  const ys=e.map(([v])=>sy(v)), o=ys.map((y,i)=>i).sort((a,b)=>ys[a]-ys[b]); let prev=-99; const fy={};
  o.forEach(i=>{const y=Math.max(ys[i],prev+13);fy[i]=y;prev=y});
  e.forEach(([v,l,c],i)=>{const t=svg('text',{x:X1+6,y:fy[i]+4,'font-size':11,fill:c,'font-weight':600},g);t.textContent=`${l} ${inr(v)}`});})();
$('simLegend').textContent=`Shaded: 1 in 10 worse to 1 in 10 better · Dashed: FD at 7% · Dotted: money put in · ${inr(sim.monthly)} a month, in today's money`;
let simCancel=()=>{};
function enterSim(){simCancel(); $('simEnds').style.transition='none'; $('simEnds').setAttribute('opacity',0); const r=$('simClipRect'); r.setAttribute('x',X0-6); r.setAttribute('width',0);
  simCancel=tween(1700,t=>r.setAttribute('width',(X1-X0+12)*t),()=>{$('simEnds').style.transition='opacity .6s';$('simEnds').setAttribute('opacity',1)});}

/* ---------- scam message ---------- */
function setScam(on){const el=$('scam');el.classList.remove('show');if(on){void el.offsetWidth;el.classList.add('show')}}

/* ---------- headline, card, navigation ---------- */
let headCancel=()=>{};
function setHead(h){headCancel(); $('headCap').textContent=h.cap;
  if(h.text){$('headNum').textContent=h.text;return}
  const f=h.inr?inr:v=>Math.round(v).toLocaleString('en-IN'); headCancel=tween(900,t=>$('headNum').textContent=f(h.value*t));}
const dots=[]; ST.forEach((st,i)=>{const b=document.createElement('button');b.className='dot';b.setAttribute('aria-label',`${i}. ${st.name}`);b.onclick=()=>go(i);$('dots').appendChild(b);dots.push(b)});
let base='/'; try{base=window.parent.location.origin+'/'}catch(e){}
let at=0;
$('open').addEventListener('click',e=>{e.preventDefault(); const url=ST[at].url; if(!url)return;
  try{const link=window.parent.document.querySelector(`a[href$="/${url}"]`); if(link){link.click();return}}catch(err){}
  window.open(base+url,'_blank');});
function card(i){const st=ST[i];
  ['kicker','title','text'].forEach(id=>{const e=$(id);e.classList.remove('fade');void e.offsetWidth;e.classList.add('fade')});
  $('kicker').textContent=i===0?'One month of money':`Step ${i} of ${N-1}`;
  $('title').textContent=st.name; $('text').textContent=st.text; $('fill').style.width=(st.mood*100)+'%';
  const o=$('open'); if(st.url){o.style.display='inline-block';o.textContent=`Open ${st.name} →`;o.href=base+st.url}else{o.style.display='none'}
  $('back').disabled=i===0; $('next').textContent=i===0?'Start →':i===N-1?'Start over ↺':'Next →';
  dots.forEach((d,k)=>d.classList.toggle('on',k===i));}
const SCENE=['flow','flow','flow','flow','risk','learn','sim','scam'];
function go(i){ at=i; card(i); setHead(ST[i].head);
  const sc=SCENE[i]; ['flow','risk','learn','sim'].forEach(k=>$('g_'+k).setAttribute('opacity',k===sc?1:0));
  setScam(sc==='scam');
  if(sc==='flow'){flowCancel(); const a=S,b=target(i); flowCancel=tween(1100,t=>{S=mixS(a,b,t);render(S)});}
  if(sc==='risk')enterRisk(); if(sc==='learn')enterLearn(); if(sc==='sim')enterSim();}
$('next').onclick=()=>go(at===N-1?0:at+1);
$('back').onclick=()=>at>0&&go(at-1);
addEventListener('keydown',e=>{if(e.key==='ArrowRight')$('next').click(); if(e.key==='ArrowLeft')$('back').click();});
let sx0=null; addEventListener('touchstart',e=>sx0=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(sx0===null)return;const dx=e.changedTouches[0].clientX-sx0;if(Math.abs(dx)>40)(dx<0?$('next'):$('back')).click();sx0=null});
go(0);
</script></body></html>"""
