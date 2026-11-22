"""Home-page roadmap: one girl walks the app's steps and turns from wasting money to investing wisely.

Rendered with components.html. Pure SVG + vanilla JS, no external files.
"""
from __future__ import annotations

import json

# (feature, her thought, mood 0..1, thing in her hand)
STAGES = [
    ("Payday", "Salary came in... where did it all go?", 0.00, "💸"),
    ("Upload", "Okay. Let me actually look at my statement.", 0.12, "📄"),
    ("My Spending", "₹3,200 on food delivery?! No way.", 0.25, "🔍"),
    ("My Surplus", "Emergency fund first, then I can set some aside.", 0.42, "🐷"),
    ("Risk Quiz", "Now I know how much ups and downs I can handle.", 0.57, "🧭"),
    ("Learn", "FD, PPF, index funds... I get the difference now.", 0.71, "📚"),
    ("Simulator", "Small monthly SIPs, a range of outcomes, no promises.", 0.85, "📈"),
    ("Scam Checker", "'Guaranteed 30% a month'? That's a red flag.", 1.00, "🛡️"),
]


def build_roadmap(dark: bool = False) -> str:
    stages = json.dumps([{"name": n, "say": s, "mood": m, "item": i} for n, s, m, i in STAGES], ensure_ascii=False)
    theme = "dark" if dark else "light"
    return TEMPLATE.replace("__STAGES__", stages).replace("__THEME__", theme)


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{--ink:#1f2937;--muted:#6b7280;--road:#d6d3d1;--roadline:#fff;--card:#ffffffee;--node:#fff;--ring:#cbd5e1;
--bad:#e11d48;--good:#1B7F5C;--sky-bad:#fde2e4;--sky-good:#d8f3e6;}
.dark{--ink:#e5e7eb;--muted:#9ca3af;--road:#44403c;--roadline:#78716c;--card:#1f2937ee;--node:#111827;--ring:#4b5563;
--sky-bad:#3b1d24;--sky-good:#123528;}
html,body{margin:0;height:100%;background:transparent;font-family:"Source Sans Pro",system-ui,sans-serif;color:var(--ink);overflow:hidden}
svg{width:100%;height:100%;display:block}
.label{font-size:15px;font-weight:700;fill:var(--ink)}
.num{font-size:13px;font-weight:800;fill:var(--muted)}
.node circle.dot{fill:var(--node);stroke:var(--ring);stroke-width:3;transition:all .4s}
.node.done circle.dot{fill:var(--good);stroke:var(--good)}
.node.done .num{fill:#fff}
.node.now circle.dot{stroke:var(--good);stroke-width:5}
.node{cursor:pointer}
.node:hover circle.dot{stroke:var(--good)}
.bubble rect{fill:var(--card);stroke:var(--ring);stroke-width:1.5}
.bubble text{font-size:15px;fill:var(--ink)}
.meter text{font-size:12.5px;font-weight:700}
.coin{font-size:18px}
#girl,#bubble,#coins,#jar,#cloud,#sun,.meter{pointer-events:none}
#ctrl{cursor:pointer}
#ctrl rect{fill:var(--card);stroke:var(--ring)}
#ctrl text{font-size:13px;fill:var(--ink);font-weight:700}
.walk{animation:bob .45s ease-in-out infinite}
@keyframes bob{50%{transform:translateY(-3px)}}
.legL{animation:legs .45s ease-in-out infinite alternate;transform-origin:0 -26px}
.legR{animation:legs .45s ease-in-out infinite alternate-reverse;transform-origin:0 -26px}
@keyframes legs{from{transform:rotate(14deg)}to{transform:rotate(-14deg)}}
.idle,.idle *{animation:none!important}
@media (prefers-reduced-motion: reduce){.walk,.legL,.legR{animation:none}}
</style></head><body class="__THEME__">
<svg id="s" viewBox="0 0 1000 400" preserveAspectRatio="xMidYMid meet" role="img"
 aria-label="Roadmap: Payday, Upload, My Spending, My Surplus, Risk Quiz, Learn, Simulator, Scam Checker. She goes from wasting money to investing wisely.">
<defs>
 <linearGradient id="sky" x1="0" x2="1"><stop id="sk1" offset="0"/><stop id="sk2" offset="1"/></linearGradient>
 <linearGradient id="mood" x1="0" x2="1"><stop offset="0" stop-color="#e11d48"/><stop offset=".5" stop-color="#f5a524"/><stop offset="1" stop-color="#1B7F5C"/></linearGradient>
</defs>
<rect id="skyRect" x="0" y="0" width="1000" height="400" rx="26" fill="url(#sky)"/>
<g id="cloud" opacity=".9"><text x="70" y="70" font-size="40">🌧️</text></g>
<g id="sun" opacity="0"><text x="66" y="72" font-size="42">☀️</text></g>

<g id="meter" class="meter" transform="translate(330,26)">
 <text x="0" y="12" fill="var(--bad)">Wasting</text>
 <rect x="62" y="2" width="216" height="12" rx="6" fill="url(#mood)" opacity=".85"/>
 <circle id="moodDot" cx="62" cy="8" r="9" fill="var(--node)" stroke="var(--ink)" stroke-width="2.5"/>
 <text x="288" y="12" fill="var(--good)">Investing wisely</text>
</g>

<path id="road" d="M40,330 C180,330 170,200 300,215 S440,330 560,300 S650,165 760,170 S900,240 965,150"
 fill="none" stroke="var(--road)" stroke-width="30" stroke-linecap="round"/>
<path id="roadDone" d="M40,330 C180,330 170,200 300,215 S440,330 560,300 S650,165 760,170 S900,240 965,150"
 fill="none" stroke="var(--good)" stroke-opacity=".35" stroke-width="30" stroke-linecap="round"/>
<path id="roadLine" d="M40,330 C180,330 170,200 300,215 S440,330 560,300 S650,165 760,170 S900,240 965,150"
 fill="none" stroke="var(--roadline)" stroke-width="2.5" stroke-dasharray="10 12"/>

<g id="jar" transform="translate(955,262)" opacity="0">
 <text id="plant" x="-2" y="-34" font-size="30" text-anchor="middle" opacity="0">🌱</text>
 <text x="0" y="0" font-size="34" text-anchor="middle">🫙</text>
</g>
<g id="nodes"></g>
<g id="coins"></g>
<g id="girl">
 <g id="body">
  <line class="legL" x1="-5" y1="-26" x2="-6" y2="0" stroke="#6b4f3a" stroke-width="4.5" stroke-linecap="round"/>
  <line class="legR" x1="5" y1="-26" x2="6" y2="0" stroke="#6b4f3a" stroke-width="4.5" stroke-linecap="round"/>
  <path id="dress" d="M-16,-24 L-9,-52 L9,-52 L16,-24 Z" fill="#9ca3af"/>
  <line x1="-9" y1="-49" x2="-17" y2="-32" stroke="#e0ac69" stroke-width="4" stroke-linecap="round"/>
  <line x1="9" y1="-49" x2="18" y2="-34" stroke="#e0ac69" stroke-width="4" stroke-linecap="round"/>
  <text id="item" x="22" y="-26" font-size="20" text-anchor="middle">💸</text>
  <path d="M-13,-66 Q-15,-84 0,-85 Q15,-84 13,-66 Q16,-56 12,-50 L-12,-50 Q-16,-56 -13,-66Z" fill="#2b1d16"/>
  <circle cx="0" cy="-66" r="11.5" fill="#e0ac69"/>
  <path d="M-11.5,-69 Q0,-80 11.5,-69 Q8,-77 0,-78 Q-8,-77 -11.5,-69Z" fill="#2b1d16"/>
  <circle cx="-4" cy="-66" r="1.6" fill="#2b1d16"/><circle cx="4" cy="-66" r="1.6" fill="#2b1d16"/>
  <path id="brow" d="M-7,-71 L-2,-70 M2,-70 L7,-71" stroke="#2b1d16" stroke-width="1.3" stroke-linecap="round"/>
  <path id="mouth" d="M-4,-59 Q0,-62 4,-59" stroke="#7c2d12" stroke-width="1.8" fill="none" stroke-linecap="round"/>
 </g>
</g>
<g id="bubble" class="bubble"><rect id="brect" rx="12"/><text id="btext"></text></g>
<g id="ctrl" transform="translate(906,356)"><rect width="72" height="28" rx="14"/><text id="ctext" x="36" y="19" text-anchor="middle">Pause</text></g>
</svg>
<script>
const ST=__STAGES__, N=ST.length;
const narrow=innerWidth<640;
if(narrow){ // phone: tall zig-zag road instead of a wide one
  const D='M70,120 C70,175 330,150 330,205 S70,250 70,300 S330,345 330,395 S70,440 70,480';
  ['road','roadDone','roadLine'].forEach(id=>document.getElementById(id).setAttribute('d',D));
  document.getElementById('s').setAttribute('viewBox','0 0 400 '+Math.round(400*innerHeight/innerWidth));
  const sr=document.getElementById('skyRect'); sr.setAttribute('width',400); sr.setAttribute('height',Math.round(400*innerHeight/innerWidth));
  document.getElementById('meter').setAttribute('transform','translate(10,16) scale(.9)');
  document.getElementById('jar').setAttribute('transform','translate(150,505)');
  document.getElementById('ctrl').setAttribute('transform','translate(318,'+(Math.round(400*innerHeight/innerWidth)-36)+')');
  document.querySelectorAll('#cloud text,#sun text').forEach(t=>{t.setAttribute('x',330);t.setAttribute('y',95);t.setAttribute('font-size',30)});
}
const S=document.getElementById('s'), road=document.getElementById('road'), done=document.getElementById('roadDone');
const L=road.getTotalLength(), girl=document.getElementById('girl'), body=document.getElementById('body');
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const frac=i=>0.02+0.96*i/(N-1);
const pt=f=>road.getPointAtLength(L*f);
const mix=(a,b,t)=>{const p=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));const A=p(a),B=p(b);
  return '#'+A.map((v,i)=>Math.round(v+(B[i]-v)*t).toString(16).padStart(2,'0')).join('')};
const css=getComputedStyle(document.body), skyBad=css.getPropertyValue('--sky-bad').trim(), skyGood=css.getPropertyValue('--sky-good').trim();
done.style.strokeDasharray=L; done.style.strokeDashoffset=L;

// nodes, labels alternate above/below the road
const G=document.getElementById('nodes');
ST.forEach((s,i)=>{const p=pt(frac(i)), up=[1,0,1,0,1,0,1,0][i];
  const g=document.createElementNS('http://www.w3.org/2000/svg','g'); g.setAttribute('class','node'); g.dataset.i=i;
  const ly=narrow? p.y+5 : p.y+44, lx=narrow? (p.x<200? p.x+28 : p.x-28) : Math.min(Math.max(p.x,60),925), anc=narrow? (p.x<200?'start':'end') : 'middle';
  g.innerHTML=`<circle class="dot" cx="${p.x}" cy="${p.y}" r="15"/><text class="num" x="${p.x}" y="${p.y+4.5}" text-anchor="middle">${i}</text>
   <text class="label" x="${lx}" y="${ly}" text-anchor="${anc}">${s.name}</text>`;
  g.addEventListener('click',()=>{playing=false;setCtrl();go(i,true)}); G.appendChild(g);});
const nodes=[...G.children];

let mood=0;
function look(m){ // m: 0 wasting .. 1 wise
  mood=m;
  document.getElementById('moodDot').setAttribute('cx',62+216*m);
  document.getElementById('sk1').setAttribute('stop-color',mix(skyBad,skyGood,Math.min(1,m*0.6)));
  document.getElementById('sk2').setAttribute('stop-color',mix(skyBad,skyGood,Math.min(1,m*1.4)));
  document.getElementById('cloud').setAttribute('opacity',Math.max(0,.9-1.6*m));
  document.getElementById('sun').setAttribute('opacity',Math.max(0,(m-.45)*1.9));
  document.getElementById('dress').setAttribute('fill',mix('#9ca3af','#1B7F5C',m));
  document.getElementById('mouth').setAttribute('d',`M-4.5,-59.5 Q0,${-59.5+7*(m-0.35)} 4.5,-59.5`);  // frown -> smile
  document.getElementById('brow').setAttribute('d', m<.3? 'M-7,-70 L-2,-72 M2,-72 L7,-70' : 'M-7,-72 L-2,-72.5 M2,-72.5 L7,-72');
  document.getElementById('jar').setAttribute('opacity',Math.max(0,(m-.35)*1.6));
  const pl=document.getElementById('plant'); pl.textContent=m>.95?'🪴':'🌱'; pl.setAttribute('opacity',Math.max(0,(m-.6)*2.5));
}
function place(f){const p=pt(f), q=pt(Math.min(1,f+0.004));
  const flip=q.x<p.x?-1:1; girl.setAttribute('transform',`translate(${p.x},${p.y-8})`); body.setAttribute('transform',`scale(${1.35*flip},1.35)`);
  done.style.strokeDashoffset=L*(1-f);}
function say(i){const s=ST[i], p=pt(frac(i)), t=document.getElementById('btext'), r=document.getElementById('brect');
  t.textContent=s.say; document.getElementById('item').textContent=s.item;
  const w=t.getComputedTextLength()+28, W=narrow?400:1000, x=Math.min(Math.max(p.x-w/2,10),W-10-w), y=narrow? Math.max(p.y-135,62) : Math.max(p.y-175,48);
  t.setAttribute('x',x+14); t.setAttribute('y',y+24); r.setAttribute('x',x); r.setAttribute('y',y); r.setAttribute('width',w); r.setAttribute('height',36);
  nodes.forEach((n,k)=>n.setAttribute('class','node'+(k<i?' done':k===i?' now':'')));}

// coins: red ones fly away while wasting, green ones fly into the jar once saving
const C=document.getElementById('coins');
function coin(){const p=girl.transform.baseVal.consolidate()?.matrix; if(!p) return;
  const saving=mood>=.4, el=document.createElementNS('http://www.w3.org/2000/svg','text');
  el.setAttribute('class','coin'); el.textContent=saving?'🪙':'💸'; C.appendChild(el);
  const x0=p.e, y0=p.f-55;
  const jt=document.getElementById('jar').transform.baseVal.consolidate().matrix;
  const x1=saving? jt.e : x0-60-Math.random()*80, y1=saving? jt.f-20 : y0-90-Math.random()*60, t0=performance.now(), d=saving?1400:1100;
  (function step(now){const t=Math.min(1,(now-t0)/d), e=t*(2-t);
    el.setAttribute('x',x0+(x1-x0)*e); el.setAttribute('y',y0+(y1-y0)*e-(saving?60*Math.sin(Math.PI*t):0));
    el.setAttribute('opacity',saving?1-t*.3:1-t); if(t<1) requestAnimationFrame(step); else el.remove();})(t0);}

let at=0, playing=!reduce, anim=null;
function go(i,jump){cancelAnimationFrame(anim); const from=frac(at), to=frac(i), m0=ST[at].mood, m1=ST[i].mood;
  if(jump||reduce){place(to);look(m1);at=i;say(i);girl.classList.add('idle');document.getElementById('bubble').setAttribute('opacity',1);return;}
  const t0=performance.now(), d=1500; girl.classList.remove('idle'); document.getElementById('bubble').setAttribute('opacity',0);
  (function step(now){const t=Math.min(1,(now-t0)/d), e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
    place(from+(to-from)*e); look(m0+(m1-m0)*e);
    if(t<1) anim=requestAnimationFrame(step); else {at=i; say(i); girl.classList.add('idle'); document.getElementById('bubble').setAttribute('opacity',1);}})(t0);}
function setCtrl(){document.getElementById('ctext').textContent=playing?'Pause':'Play';}
document.getElementById('ctrl').addEventListener('click',()=>{playing=!playing;setCtrl(); if(playing&&at===N-1){go(0,true)}});

place(frac(0)); look(0); say(0); setCtrl();
if(reduce){go(N-1,true)}
setInterval(()=>{ if(!playing) return; if(at<N-1) go(at+1); else go(0,true); }, 3200);
setInterval(()=>{ if(!document.hidden && !reduce) coin(); }, 700);
</script></body></html>"""
