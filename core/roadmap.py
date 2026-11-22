"""Home-page story: Ananya walks the app's steps, from wasting money to investing wisely.

The reader moves the story (Next / Back, arrow keys, swipe, or tapping a stop).
Rendered with components.html; pure SVG + vanilla JS, no external files.
"""
from __future__ import annotations

import json

# title, story text, mood 0..1, url path of the page (None for the opening), thing she holds
STAGES = [
    ("Payday", "Ananya, 21, gets her first salary: ₹28,000. Ten days later the account is nearly empty, "
     "and she honestly can't say where it went.", 0.00, None, "phone"),
    ("Upload", "She downloads her bank statement and drops it in. Account numbers and UPI IDs are "
     "masked before anything else happens, and nothing is saved.", 0.12, "upload", "paper"),
    ("My Spending", "Every payment, sorted. Food delivery: ₹3,200 a month. Two subscriptions she forgot "
     "she even had. Seeing it is the turning point.", 0.26, "my-spending", "glass"),
    ("My Surplus", "Income minus essentials leaves about ₹6,000 a month. The first job for that money "
     "is an emergency fund, so the first coins go into the piggy bank.", 0.42, "my-surplus", "coin"),
    ("Risk Quiz", "Nine quick questions. She's 'Moderate': fine with some ups and downs, "
     "not fine with losing sleep over them.", 0.56, "risk-quiz", "compass"),
    ("Learn", "She flips through the Money Handbook: savings account, FD, RD, PPF, index funds, gold "
     "and NPS. What each one is, how locked-in, how it's taxed.", 0.70, "learn", "book"),
    ("Simulator", "₹3,000 a month for 10 years, replayed 10,000 times on real Nifty 50 history. "
     "Not a promise: a range of outcomes, with an FD line to compare.", 0.85, "simulator", "chart"),
    ("Scam Checker", "A WhatsApp message offers 'guaranteed 30% a month'. She pastes it in: high risk, "
     "three red flags. She deletes it and keeps her SIP going.", 1.00, "scam-checker", "shield"),
]


def build_roadmap(dark: bool = False) -> str:
    stages = json.dumps([{"name": n, "text": t, "mood": m, "url": u, "item": i} for n, t, m, u, i in STAGES],
                        ensure_ascii=False)
    return TEMPLATE.replace("__STAGES__", stages).replace("__THEME__", "dark" if dark else "light")


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{--card:#ffffff;--ink:#12261f;--muted:#5b6b65;--line:rgba(15,92,67,.18)}
.dark{--card:#10211b;--ink:#e7f2ed;--muted:#9fb5ab;--line:rgba(255,255,255,.14)}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:transparent;font-family:"Source Sans Pro",system-ui,sans-serif;overflow:hidden}
.frame{position:absolute;inset:0;border-radius:26px;overflow:hidden;display:flex;gap:14px;padding:14px;
  background:linear-gradient(125deg,#0f5c43,#1B7F5C,#14b8a6,#0f766e);background-size:300% 300%;animation:shift 14s ease infinite}
@keyframes shift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.blob{position:absolute;border-radius:50%;filter:blur(40px);pointer-events:none}
.b1{width:260px;height:260px;background:#f5a524;opacity:.35;right:-70px;bottom:-110px}
.b2{width:220px;height:220px;background:#7c5cff;opacity:.22;left:30%;top:-120px}
.stage{position:relative;flex:1.65;min-width:0;border-radius:18px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);overflow:hidden}
.stage svg{width:100%;height:100%;display:block}
.card{position:relative;flex:1;min-width:0;display:flex;flex-direction:column;border-radius:18px;padding:18px 20px 14px;
  background:var(--card);color:var(--ink);box-shadow:0 18px 40px -22px rgba(0,0,0,.5)}
.kicker{font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#1B7F5C}
.dark .kicker{color:#5eead4}
h2{margin:.25rem 0 .55rem;font-size:1.55rem;line-height:1.15;letter-spacing:-.02em}
.text{font-size:1.02rem;line-height:1.55;color:var(--ink);opacity:.9;flex:1}
.fade{animation:fade .45s ease both}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.meter{display:flex;align-items:center;gap:8px;font-size:.74rem;font-weight:700;margin:.4rem 0 .7rem}
.meter .bar{position:relative;flex:1;height:8px;border-radius:99px;background:var(--line)}
.meter .fill{position:absolute;inset:0 auto 0 0;border-radius:99px;background:linear-gradient(90deg,#f59e0b,#14b8a6,#1B7F5C);transition:width .9s cubic-bezier(.3,.8,.3,1)}
.open{display:inline-block;margin-bottom:.6rem;font-weight:700;color:#1B7F5C;text-decoration:none;cursor:pointer;font-size:.95rem}
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
.node{cursor:pointer}
#girl,#fx,#pigWrap,#cloud,#sun{pointer-events:none}
@keyframes rain{from{transform:translateY(-6px)}to{transform:translateY(14px);opacity:0}}
.drop{animation:rain .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#rays{animation:spin 30s linear infinite}
@keyframes wiggle{0%,100%{transform:rotate(0)}25%{transform:rotate(-6deg)}75%{transform:rotate(6deg)}}
#pig{transform-box:fill-box;transform-origin:50% 100%}
.wiggle{animation:wiggle .35s ease 2}
@keyframes twinkle{0%,100%{opacity:0;transform:scale(.4)}50%{opacity:1;transform:scale(1)}}
.spark{animation:twinkle 1.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@media (max-width:640px){
  .frame{flex-direction:column;padding:10px;gap:10px}
  .stage{flex:0 0 42%}
  .card{padding:12px 14px 10px}
  h2{font-size:1.2rem;margin:.1rem 0 .3rem}
  .text{font-size:.9rem;line-height:1.4}
  .meter{margin:.2rem 0 .4rem}
  .hint{display:none}
}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}
</style></head><body class="__THEME__">
<div class="frame">
 <span class="blob b1"></span><span class="blob b2"></span>
 <div class="stage" id="stage">
 <svg id="s" viewBox="0 0 600 380" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
  <defs>
   <linearGradient id="pigG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc4d6"/><stop offset="1" stop-color="#f48fb1"/></linearGradient>
   <radialGradient id="coinG" cx=".35" cy=".35"><stop offset="0" stop-color="#fff3b0"/><stop offset=".6" stop-color="#f5c542"/><stop offset="1" stop-color="#c8901a"/></radialGradient>
   <linearGradient id="goldFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe27a"/><stop offset="1" stop-color="#e0a82e"/></linearGradient>
   <clipPath id="belly"><ellipse cx="0" cy="0" rx="46" ry="35"/></clipPath>
   <linearGradient id="hill1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".18"/><stop offset="1" stop-color="#ffffff" stop-opacity=".04"/></linearGradient>
  </defs>
  <rect id="glow" x="-300" y="-300" width="1200" height="980" fill="#fff6d5" opacity="0"/>
  <g id="cloud" transform="translate(70,58)">
   <g fill="#e2e8f0" opacity=".9"><circle cx="0" cy="0" r="16"/><circle cx="18" cy="-8" r="20"/><circle cx="38" cy="0" r="15"/><rect x="0" y="0" width="38" height="15" rx="7"/></g>
   <g stroke="#bfdbfe" stroke-width="2.4" stroke-linecap="round">
    <line class="drop" x1="6" y1="22" x2="3" y2="30"/><line class="drop" x1="20" y1="22" x2="17" y2="30" style="animation-delay:-.3s"/><line class="drop" x1="34" y1="22" x2="31" y2="30" style="animation-delay:-.55s"/>
   </g>
  </g>
  <g id="sun" transform="translate(84,62)" opacity="0">
   <g id="rays" stroke="#fde68a" stroke-width="3" stroke-linecap="round">
    <line x1="0" y1="-30" x2="0" y2="-38"/><line x1="0" y1="30" x2="0" y2="38"/><line x1="-30" y1="0" x2="-38" y2="0"/><line x1="30" y1="0" x2="38" y2="0"/>
    <line x1="21" y1="21" x2="27" y2="27"/><line x1="-21" y1="-21" x2="-27" y2="-27"/><line x1="21" y1="-21" x2="27" y2="-27"/><line x1="-21" y1="21" x2="-27" y2="27"/>
   </g>
   <circle r="22" fill="#fcd34d"/><circle r="22" fill="#fff7d6" opacity=".35"/>
  </g>
  <path d="M0,300 C90,250 170,270 260,240 S430,220 600,250 L900,250 L900,700 L-300,700 L-300,300Z" fill="url(#hill1)"/>
  <path d="M0,335 C120,300 250,330 360,305 S520,290 600,300 L900,300 L900,700 L-300,700 L-300,335Z" fill="#ffffff" opacity=".07"/>
  <path id="road" d="M36,338 C120,340 130,262 205,268 S300,330 352,292 S392,198 450,206 S520,250 548,170"
    fill="none" stroke="rgba(255,255,255,.28)" stroke-width="26" stroke-linecap="round"/>
  <path id="roadDone" d="M36,338 C120,340 130,262 205,268 S300,330 352,292 S392,198 450,206 S520,250 548,170"
    fill="none" stroke="#fcd34d" stroke-opacity=".55" stroke-width="26" stroke-linecap="round"/>
  <path d="M36,338 C120,340 130,262 205,268 S300,330 352,292 S392,198 450,206 S520,250 548,170"
    fill="none" stroke="rgba(255,255,255,.75)" stroke-width="2" stroke-dasharray="8 10"/>
  <g id="nodes"></g>
  <g id="pigWrap" transform="translate(420,92)">
   <g id="pig">
    <ellipse cx="2" cy="44" rx="44" ry="6" fill="#000" opacity=".15"/>
    <rect x="-30" y="22" width="11" height="20" rx="5" fill="#f48fb1"/><rect x="18" y="22" width="11" height="20" rx="5" fill="#f48fb1"/>
    <path d="M44,-4 c12,-6 14,8 4,6 c-8,-2 -2,-12 6,-10" fill="none" stroke="#f48fb1" stroke-width="3" stroke-linecap="round"/>
    <ellipse cx="0" cy="0" rx="46" ry="35" fill="url(#pigG)"/>
    <g clip-path="url(#belly)"><rect id="pigLevel" x="-50" y="35" width="100" height="80" fill="url(#goldFill)" opacity=".75"/>
     <g id="pigCoins" opacity="0"><circle cx="-20" cy="24" r="7" fill="url(#coinG)"/><circle cx="-4" cy="28" r="7" fill="url(#coinG)"/><circle cx="12" cy="23" r="7" fill="url(#coinG)"/><circle cx="26" cy="29" r="7" fill="url(#coinG)"/></g>
    </g>
    <ellipse cx="0" cy="0" rx="46" ry="35" fill="none" stroke="#e57399" stroke-width="2"/>
    <ellipse cx="-16" cy="-14" rx="16" ry="8" fill="#fff" opacity=".35"/>
    <rect x="-14" y="-37" width="28" height="6" rx="3" fill="#7a2948"/>
    <path d="M-30,-26 L-38,-46 L-18,-33Z" fill="#f48fb1" stroke="#e57399" stroke-width="1.5"/>
    <ellipse cx="-47" cy="4" rx="10" ry="12" fill="#ffb3c9" stroke="#e57399" stroke-width="2"/>
    <circle cx="-49" cy="0" r="2" fill="#a23b62"/><circle cx="-49" cy="8" r="2" fill="#a23b62"/>
    <circle cx="-28" cy="-10" r="3.6" fill="#3b1d2a"/><circle cx="-27" cy="-11.3" r="1.2" fill="#fff"/>
    <path d="M-36,10 q3,4 7,1" stroke="#a23b62" stroke-width="1.6" fill="none" stroke-linecap="round"/>
   </g>
   <g id="sparks" opacity="0" fill="#fff7d6">
    <path class="spark" d="M-58,-40 l3,-8 l3,8 l8,3 l-8,3 l-3,8 l-3,-8 l-8,-3z"/>
    <path class="spark" style="animation-delay:-.6s" d="M52,-46 l2,-6 l2,6 l6,2 l-6,2 l-2,6 l-2,-6 l-6,-2z"/>
    <path class="spark" style="animation-delay:-1.1s" d="M60,30 l2,-5 l2,5 l5,2 l-5,2 l-2,5 l-2,-5 l-5,-2z"/>
   </g>
  </g>
  <g id="fx"></g>
  <g id="girl">
   <ellipse cx="0" cy="1" rx="17" ry="4" fill="#000" opacity=".22"/>
   <g id="fig">
    <g id="legB" transform="translate(0,-46)"><line x1="0" y1="0" x2="0" y2="22" stroke="#24323f" stroke-width="7" stroke-linecap="round"/>
     <g id="shinB" transform="translate(0,22)"><line x1="0" y1="0" x2="0" y2="22" stroke="#24323f" stroke-width="6" stroke-linecap="round"/><path d="M-3,20 h11 a3,3 0 0 1 0,5 h-11z" fill="#111827"/></g></g>
    <g id="armB" transform="translate(0,-84)"><line x1="0" y1="0" x2="0" y2="17" stroke="#c98c5a" stroke-width="5" stroke-linecap="round"/>
     <g id="foreB" transform="translate(0,17)"><line x1="0" y1="0" x2="0" y2="16" stroke="#c98c5a" stroke-width="4.5" stroke-linecap="round"/></g></g>
    <path id="top" d="M-11,-88 Q0,-92 11,-88 L13,-56 Q15,-46 12,-40 L-12,-40 Q-15,-46 -13,-56Z" fill="#94a3b8"/>
    <path d="M-10,-87 Q4,-70 12,-58" stroke="#f5a524" stroke-width="4" fill="none" stroke-linecap="round" opacity=".9"/>
    <g id="legF" transform="translate(0,-46)"><line x1="0" y1="0" x2="0" y2="22" stroke="#334155" stroke-width="7" stroke-linecap="round"/>
     <g id="shinF" transform="translate(0,22)"><line x1="0" y1="0" x2="0" y2="22" stroke="#334155" stroke-width="6" stroke-linecap="round"/><path d="M-3,20 h11 a3,3 0 0 1 0,5 h-11z" fill="#1f2937"/></g></g>
    <g id="head" transform="translate(0,-92)">
     <rect x="-3" y="-6" width="6" height="8" fill="#d9a066"/>
     <path id="pony" d="M-10,-22 Q-22,-14 -18,2 Q-15,-8 -9,-14Z" fill="#1c120d"/>
     <ellipse cx="0" cy="-17" rx="11" ry="12.5" fill="#e0ac69"/>
     <path d="M-11.5,-17 Q-12,-31 0,-31 Q12,-31 11.5,-17 Q8,-26 0,-26 Q-6,-26 -11.5,-17Z" fill="#1c120d"/>
     <circle cx="-11" cy="-15" r="2.4" fill="#d9a066"/>
     <ellipse cx="3" cy="-17" rx="1.5" ry="1.9" fill="#1c120d"/><ellipse cx="8.5" cy="-17" rx="1.4" ry="1.8" fill="#1c120d"/>
     <path id="brow" d="M1,-21 L5,-21.5 M7,-21.5 L10.5,-21" stroke="#1c120d" stroke-width="1.2" stroke-linecap="round"/>
     <circle cx="10" cy="-12" r="2.2" fill="#f08a8a" opacity=".35"/>
     <path id="mouth" d="M3,-10 Q6,-9 9,-10" stroke="#8b2c1d" stroke-width="1.6" fill="none" stroke-linecap="round"/>
    </g>
    <g id="armF" transform="translate(0,-84)"><line x1="0" y1="0" x2="0" y2="17" stroke="#e0ac69" stroke-width="5" stroke-linecap="round"/>
     <g id="foreF" transform="translate(0,17)"><line x1="0" y1="0" x2="0" y2="16" stroke="#e0ac69" stroke-width="4.5" stroke-linecap="round"/>
      <g id="hand" transform="translate(0,17)"></g></g></g>
   </g>
  </g>
 </svg>
 </div>
 <div class="card" id="card" aria-live="polite">
  <div class="kicker" id="kicker"></div>
  <h2 id="title"></h2>
  <div class="meter"><span style="color:#d97706">Wasting</span><span class="bar"><span class="fill" id="fill"></span></span><span style="color:#1B7F5C">Investing wisely</span></div>
  <div class="text" id="text"></div>
  <a class="open" id="open" href="#"></a>
  <div class="nav"><button class="btn back" id="back">← Back</button><div class="dots" id="dots"></div><button class="btn next" id="next">Start →</button></div>
  <div class="hint">Use ← → keys, swipe, or tap a stop on the road</div>
 </div>
</div>
<script>
const ST=__STAGES__, N=ST.length, NS='http://www.w3.org/2000/svg';
const $=id=>document.getElementById(id);
const road=$('road'), L=road.getTotalLength(), reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const frac=i=>0.03+0.94*i/(N-1), pt=f=>road.getPointAtLength(L*f);
const mix=(a,b,t)=>{const p=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)),A=p(a),B=p(b);
  return '#'+A.map((v,i)=>Math.round(v+(B[i]-v)*t).toString(16).padStart(2,'0')).join('')};
$('roadDone').style.strokeDasharray=L; $('roadDone').style.strokeDashoffset=L;

// things she holds, drawn small in her front hand
const ITEMS={
 phone:'<rect x="-4" y="-2" width="9" height="15" rx="2" fill="#111827"/><rect x="-2.5" y="0" width="6" height="10" rx="1" fill="#60a5fa"/>',
 paper:'<rect x="-4" y="-4" width="14" height="18" rx="1.5" fill="#fff" stroke="#cbd5e1"/><line x1="-1" y1="1" x2="7" y2="1" stroke="#94a3b8"/><line x1="-1" y1="5" x2="7" y2="5" stroke="#94a3b8"/><line x1="-1" y1="9" x2="5" y2="9" stroke="#94a3b8"/>',
 glass:'<circle cx="4" cy="2" r="6" fill="#bae6fd" fill-opacity=".5" stroke="#334155" stroke-width="2"/><line x1="0" y1="7" x2="-4" y2="13" stroke="#334155" stroke-width="2.5" stroke-linecap="round"/>',
 coin:'<circle cx="3" cy="3" r="7" fill="url(#coinG)" stroke="#b7791f"/><text x="3" y="6.5" font-size="9" font-weight="800" text-anchor="middle" fill="#7c4a03">₹</text>',
 compass:'<circle cx="3" cy="3" r="7" fill="#fff" stroke="#334155" stroke-width="1.5"/><path d="M3,-2 L5,3 L3,8 L1,3Z" fill="#e11d48"/>',
 book:'<rect x="-5" y="-3" width="16" height="12" rx="1.5" fill="#1B7F5C"/><line x1="3" y1="-3" x2="3" y2="9" stroke="#fff" stroke-width="1"/>',
 chart:'<rect x="-5" y="-4" width="16" height="14" rx="2" fill="#fff" stroke="#cbd5e1"/><polyline points="-3,7 1,4 4,5 9,-1" fill="none" stroke="#1B7F5C" stroke-width="1.8"/>',
 shield:'<path d="M3,-5 L11,-2 Q11,8 3,12 Q-5,8 -5,-2Z" fill="#14b8a6" stroke="#0f766e"/><path d="M0,3 l2.5,2.5 l5,-5" stroke="#fff" stroke-width="1.6" fill="none"/>'};

ST.forEach((s,i)=>{const p=pt(frac(i)),g=document.createElementNS(NS,'g');g.setAttribute('class','node');g.dataset.i=i;
  g.innerHTML=`<circle cx="${p.x}" cy="${p.y}" r="11" fill="rgba(255,255,255,.85)" stroke="#fff" stroke-width="2"/><text x="${p.x}" y="${p.y+4}" font-size="11" font-weight="800" text-anchor="middle" fill="#0f5c43">${i}</text>`;
  g.addEventListener('click',()=>go(i)); $('nodes').appendChild(g);});
const nodes=[...$('nodes').children];
ST.forEach((s,i)=>{const b=document.createElement('button');b.className='dot';b.setAttribute('aria-label',`${i}. ${s.name}`);b.onclick=()=>go(i);$('dots').appendChild(b)});
const dots=[...$('dots').children];

// how she looks at a given mood (0 wasting .. 1 wise)
function look(m){
  $('cloud').setAttribute('opacity',Math.max(0,1-2*m)); $('sun').setAttribute('opacity',Math.min(1,Math.max(0,(m-.3)*1.8)));
  $('glow').setAttribute('opacity',(m*.16).toFixed(3));
  $('top').setAttribute('fill',mix('#94a3b8','#0f9d6e',m));
  $('mouth').setAttribute('d',`M3,-10 Q6,${-10+5*(m-.3)} 9,-10`);
  $('brow').setAttribute('d',m<.25?'M1,-20.5 L5,-22 M7,-22 L10.5,-20.5':'M1,-21.5 L5,-22 M7,-22 L10.5,-21.5');
  $('head').setAttribute('transform',`translate(0,-92) rotate(${(1-m)*9})`);
  $('fig').setAttribute('transform',`rotate(${(1-m)*3})`);
}
function pigFill(v){ $('pigLevel').setAttribute('y',35-70*v); $('pigCoins').setAttribute('opacity',v>0?1:0); $('sparks').setAttribute('opacity',v>=.99?1:0);}
const save=i=>Math.max(0,(ST[i].mood-.35)/.65);

// a natural walk: hips, knees, shoulders and elbows swing out of phase
function pose(phase,walking){
  const a=walking?Math.sin(phase):-0.22, k=walking?Math.max(0,Math.sin(phase+1.3)):0, k2=walking?Math.max(0,Math.sin(phase+1.3+Math.PI)):0;
  $('legF').setAttribute('transform',`translate(0,-46) rotate(${-24*a})`); $('shinF').setAttribute('transform',`translate(0,22) rotate(${32*k})`);
  $('legB').setAttribute('transform',`translate(0,-46) rotate(${24*a})`);  $('shinB').setAttribute('transform',`translate(0,22) rotate(${32*k2})`);
  $('armF').setAttribute('transform',`translate(0,-84) rotate(${walking?20*a:-8})`); $('foreF').setAttribute('transform',`translate(0,17) rotate(${walking?-25:-70})`);
  $('armB').setAttribute('transform',`translate(0,-84) rotate(${-20*a})`); $('foreB').setAttribute('transform','translate(0,17) rotate(-20)');
  $('pony').setAttribute('transform',`rotate(${walking?6*Math.sin(phase*2):0} -10 -20)`);
  return walking?Math.abs(Math.cos(phase))*2.2:0;
}
function place(f,phase,walking){const p=pt(f),q=pt(Math.min(1,f+.003)),r=pt(Math.max(0,f-.003));
  const dir=(q.x-r.x)>=0?1:-1, bob=pose(phase,walking);
  $('girl').setAttribute('transform',`translate(${p.x},${p.y-2-bob}) scale(${dir*.95},.95)`);
  $('roadDone').style.strokeDashoffset=L*(1-f);}

// effects: notes flying away while wasting, coins dropping into the pig when saving
function here(){const m=$('girl').transform.baseVal.consolidate().matrix;return {x:m.e,y:m.f}}
function burstNotes(){const p=here();
  for(let n=0;n<5;n++)setTimeout(()=>fly(p.x+8,p.y-70,p.x+40+Math.random()*120,p.y-140-Math.random()*90,'note',900),n*140);}
function dropCoins(count){const p=here();
  for(let n=0;n<count;n++)setTimeout(()=>fly(p.x+6,p.y-60,420,52,'coin',950,()=>{const g=$('pig');g.classList.remove('wiggle');void g.getBBox();g.classList.add('wiggle')}),n*220);}
function fly(x0,y0,x1,y1,kind,d,done){const g=document.createElementNS(NS,'g');
  g.innerHTML=kind==='coin'?'<circle r="7" fill="url(#coinG)" stroke="#b7791f"/><text y="3.5" font-size="9" font-weight="800" text-anchor="middle" fill="#7c4a03">₹</text>'
   :'<rect x="-9" y="-5" width="18" height="10" rx="1.5" fill="#86efac" stroke="#15803d"/><circle r="2.5" fill="#15803d"/>';
  $('fx').appendChild(g); const t0=performance.now(), spin=(Math.random()-.5)*540;
  (function step(now){const t=Math.min(1,(now-t0)/d), e=t*(2-t);
    const x=x0+(x1-x0)*e, y=y0+(y1-y0)*t-(kind==='coin'?90:30)*Math.sin(Math.PI*t);
    g.setAttribute('transform',`translate(${x},${y}) rotate(${kind==='coin'?0:spin*t}) scale(${kind==='coin'?1-.3*t:1})`);
    g.setAttribute('opacity',kind==='coin'?1:1-t);
    if(t<1)requestAnimationFrame(step); else {g.remove(); done&&done();}})(t0);}

function card(i){const s=ST[i];
  ['kicker','title','text'].forEach(id=>{const e=$(id);e.classList.remove('fade');void e.offsetWidth;e.classList.add('fade')});
  $('kicker').textContent=i===0?'The story · start':`Step ${i} of ${N-1}`;
  $('title').textContent=s.name; $('text').textContent=s.text; $('fill').style.width=(s.mood*100)+'%';
  const o=$('open'); if(s.url){o.style.visibility='visible';o.textContent=`Open ${s.name} →`;o.href=base+s.url}else{o.style.visibility='hidden'}
  $('back').disabled=i===0; $('next').textContent=i===0?'Start →':i===N-1?'Start over ↺':'Next →';
  dots.forEach((d,k)=>d.classList.toggle('on',k===i));
  nodes.forEach((n,k)=>{const c=n.querySelector('circle');c.setAttribute('fill',k<=i?'#fcd34d':'rgba(255,255,255,.85)');c.setAttribute('r',k===i?14:11)});
  $('hand').innerHTML=ITEMS[s.item];}
// Streamlit's iframe can't navigate the page itself, but it is same-origin, so click the
// matching sidebar link: an in-app page switch that keeps the user's session.
let base='/'; try{base=window.parent.location.origin+'/'}catch(e){}
$('open').addEventListener('click',e=>{
  try{const url=ST[at].url, link=window.parent.document.querySelector(`a[href$="/${url}"]`);
    if(link){e.preventDefault(); link.click(); return;}}catch(err){}
  e.preventDefault(); window.open($('open').href,'_blank');   // fallback: new tab
});

// moving between stops: she walks the road; mood, sky and piggy change with her
let at=0, busy=false, anim=null, phase=0;
function go(i){ if(i===at&&!busy) return; cancelAnimationFrame(anim);
  const from=frac(at), to=frac(i), m0=ST[at].mood, m1=ST[i].mood, p0=save(at), p1=save(i), forward=i>at;
  card(i); at=i;
  if(reduce){place(to,0,false);look(m1);pigFill(p1);return;}
  const d=Math.min(2600,700+Math.abs(to-from)*5200), t0=performance.now(); busy=true;
  (function step(now){const t=Math.min(1,(now-t0)/d), e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
    phase+=0.21; place(from+(to-from)*e,phase,t<1); look(m0+(m1-m0)*e);
    if(!forward) pigFill(p0+(p1-p0)*e);
    if(t<1) anim=requestAnimationFrame(step);
    else{busy=false; place(to,0,false);
      if(forward){ if(m1<.35) burstNotes(); else { dropCoins(i===N-1?6:3); setTimeout(()=>pigFill(p1),900);} } }})(t0);}

$('next').onclick=()=>go(at===N-1?0:at+1);
$('back').onclick=()=>at>0&&go(at-1);
addEventListener('keydown',e=>{if(e.key==='ArrowRight')$('next').click(); if(e.key==='ArrowLeft')$('back').click();});
let sx=null; addEventListener('touchstart',e=>sx=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(sx===null)return;const dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>40)(dx<0?$('next'):$('back')).click();sx=null});

card(0); look(0); pigFill(0); place(frac(0),0,false);
if(!reduce) setTimeout(burstNotes,600);
</script></body></html>"""
