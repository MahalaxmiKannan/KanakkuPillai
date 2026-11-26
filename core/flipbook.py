"""Turns the Learn cards into a small page-turning book (plain HTML/CSS/JS, no extra packages)."""
from __future__ import annotations

import html
import re
from pathlib import Path

ICONS = ["💳", "🏦", "🔁", "🏛️", "📈", "🥇", "👵"]

DIVERSIFICATION = (
    "Different options behave differently. Some stay steady and some swing a lot, and they don't all fall "
    "at the same time. Putting everything in one place means one bad outcome hits all of it. Spreading money "
    "across a few kinds of options, and across many companies inside a fund, is how people reduce that risk. "
    "It lowers the chance of a big loss; it doesn't remove it or guarantee a gain."
)


def _inline(text: str) -> str:
    """Escape, then apply **bold**, *italic* and [links](url)."""
    out = html.escape(text, quote=False)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", out)
    return out


def md_to_html(md: str) -> str:
    """Just enough Markdown for our cards: paragraphs, tables, bold, italic, links."""
    blocks, table = [], []

    def flush_table():
        if not table:
            return
        rows = [r for r in table if not re.fullmatch(r"\|?[\s|:-]+\|?", r)]
        cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        body = "".join(
            f"<tr><th>{_inline(c[0])}</th><td>{_inline(c[1]) if len(c) > 1 else ''}</td></tr>"
            for c in cells if any(c)
        )
        blocks.append(f"<table>{body}</table>")
        table.clear()

    for line in md.splitlines():
        if line.strip().startswith("|"):
            table.append(line)
            continue
        flush_table()
        if line.strip():
            css = ' class="foot"' if line.strip().startswith("*") and not line.strip().startswith("**") else ""
            blocks.append(f"<p{css}>{_inline(line.strip())}</p>")
    flush_table()
    return "\n".join(blocks)


def load_chapters(content_dir: Path) -> list[dict]:
    chapters = []
    for i, path in enumerate(sorted(content_dir.glob("[0-9]_*.md"))):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        title_line, _, body = text.partition("\n")
        what = re.search(r"\*\*What it is:\*\*\s*(.+)", body)
        chapters.append({
            "title": title_line.lstrip("# ").strip(),
            "icon": ICONS[i % len(ICONS)],
            "teaser": what.group(1).strip() if what else "",
            "html": md_to_html(body.strip()),
        })
    return chapters


def _opener(ch: dict, number: int) -> str:
    return (
        f'<div class="opener"><div class="chap">Chapter {number}</div><div class="big">{ch["icon"]}</div>'
        f'<h2>{html.escape(ch["title"])}</h2><p>{_inline(ch["teaser"])}</p><div class="hint">Turn the page →</div></div>'
    )


def build_book(chapters: list[dict], dark: bool = False) -> str:
    """Leaves sit on the right; each leaf's front is a chapter, its back opens the next one."""
    n = len(chapters)
    contents = "".join(
        f'<li><a href="#" data-go="{i + 1}"><span>{c["icon"]}</span>{html.escape(c["title"])}</a></li>'
        for i, c in enumerate(chapters)
    )
    leaves = []
    # leaf 0: front = cover, back = contents
    leaves.append((
        '<div class="cover"><div class="emblem">📖</div><h1>The Money Handbook</h1>'
        '<p>Seven ways to save and invest, explained simply.</p><div class="hint">Tap to open →</div></div>',
        f'<div class="toc"><h3>Contents</h3><ol>{contents}</ol><p class="foot">Tap a chapter, use ← → keys, or swipe.</p></div>',
    ))
    for i, ch in enumerate(chapters):
        front = f'<div class="page-body"><div class="runner">{ch["icon"]} {html.escape(ch["title"])}</div>{ch["html"]}<div class="num">{i + 1}</div></div>'
        if i + 1 < n:
            back = _opener(chapters[i + 1], i + 2)
        else:
            back = (
                '<div class="page-body"><div class="runner">🧺 Before you close the book</div>'
                '<h2>Spreading your money</h2>'
                f"<p>{html.escape(DIVERSIFICATION)}</p>"
                '<p class="foot">General information about how investing works. Not a recommendation to buy anything.</p></div>'
            )
        leaves.append((front, back))
    # the first chapter's opener needs a left page before leaf 1 is turned: it is shown on the contents' facing side
    first_opener = _opener(chapters[0], 1) if chapters else ""

    leaf_html = "".join(
        f'<div class="leaf" data-i="{k}" style="z-index:{len(leaves) - k}">'
        f'<div class="face front">{f}</div><div class="face back">{b}</div></div>'
        for k, (f, b) in enumerate(leaves)
    )
    theme = "dark" if dark else "light"
    total = len(leaves)
    return TEMPLATE.replace("{{THEME}}", theme).replace("{{LEAVES}}", leaf_html).replace(
        "{{TOTAL}}", str(total)).replace("{{FIRST}}", first_opener)


TEMPLATE = """<!doctype html><html data-theme="{{THEME}}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root { --paper:#fffaf0; --paper2:#f6eedb; --ink:#2b2a26; --muted:#6b675d; --accent:#1B7F5C; --line:#e4d9bf;
        --cover1:#0f5c43; --cover2:#14b8a6; --shadow:rgba(60,40,10,.25); --bg:transparent; }
html[data-theme="dark"] { --paper:#23221f; --paper2:#1b1a18; --ink:#efece4; --muted:#b5b0a3; --line:#3b3934; --shadow:rgba(0,0,0,.6); }
* { box-sizing:border-box; }
body { margin:0; font-family: "Source Sans Pro", "Segoe UI", system-ui, sans-serif; color:var(--ink); background:var(--bg);
       display:flex; flex-direction:column; align-items:center; padding:18px 8px 8px; overflow:hidden; }
.stage { perspective: 2200px; width:100%; display:flex; justify-content:center; }
.book { position:relative; width:min(980px, 100%); aspect-ratio: 980/600; max-height:600px; transition: transform .6s cubic-bezier(.3,.8,.3,1); }
.book.closed { transform: translateX(-25%); }
.book.ended { transform: none; }
.left-page { position:absolute; left:0; top:0; width:50%; height:100%; background:linear-gradient(90deg,var(--paper2),var(--paper));
             border-radius:14px 0 0 14px; box-shadow: 0 20px 40px -18px var(--shadow); overflow:hidden; opacity:0; transition:opacity .4s; }
.book:not(.closed) .left-page { opacity:1; }
.leaf { position:absolute; left:50%; top:0; width:50%; height:100%; transform-origin:left center; transform-style:preserve-3d;
        transition: transform 1s cubic-bezier(.645,.045,.355,1); cursor:pointer; }
.leaf.flipped { transform: rotateY(-180deg); }
.face { position:absolute; inset:0; backface-visibility:hidden; -webkit-backface-visibility:hidden; overflow:hidden;
        background:var(--paper); box-shadow: 0 20px 40px -18px var(--shadow); }
.front { border-radius:0 14px 14px 0; background:linear-gradient(90deg, var(--paper2) 0%, var(--paper) 6%); }
.back  { border-radius:14px 0 0 14px; transform: rotateY(180deg); background:linear-gradient(270deg, var(--paper2) 0%, var(--paper) 6%); }
.leaf.turning .face::after { content:""; position:absolute; inset:0; background:linear-gradient(90deg, rgba(0,0,0,.18), transparent 60%); pointer-events:none; }
.page-body, .opener, .toc, .cover { position:absolute; inset:0; padding:30px 34px 44px; overflow:auto; }
.page-body::-webkit-scrollbar { width:6px } .page-body::-webkit-scrollbar-thumb { background:var(--line); border-radius:3px }
.runner { font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:var(--accent); font-weight:700; margin-bottom:12px; }
.num { position:sticky; float:right; bottom:0; margin-top:8px; font-size:.8rem; color:var(--muted); }
p { line-height:1.5; margin:.55em 0; font-size:.95rem; }
p.foot { font-size:.8rem; color:var(--muted); font-style:italic; border-top:1px dashed var(--line); padding-top:8px; margin-top:12px; }
a { color:var(--accent); }
table { width:100%; border-collapse:separate; border-spacing:0 6px; margin:8px 0; font-size:.88rem; }
th { text-align:left; width:30%; vertical-align:top; color:var(--accent); padding:7px 10px; background:rgba(27,127,92,.08); border-radius:8px 0 0 8px; }
td { padding:7px 10px; background:rgba(128,128,128,.07); border-radius:0 8px 8px 0; line-height:1.4; }
h2 { margin:.2em 0 .4em; font-size:1.6rem; letter-spacing:-.02em; }
.cover { color:#fff; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;
         background: radial-gradient(circle at 80% 85%, rgba(245,165,36,.55), transparent 45%), linear-gradient(140deg,var(--cover1),var(--cover2));
         border-left:10px solid rgba(0,0,0,.18); }
.cover h1 { font-size:2.3rem; margin:.2em 0; letter-spacing:-.02em; }
.cover p { opacity:.9; font-size:1rem; }
.emblem { font-size:4.2rem; animation: bob 3s ease-in-out infinite; }
@keyframes bob { 50% { transform: translateY(-10px) rotate(-6deg); } }
.hint { margin-top:18px; font-size:.82rem; opacity:.75; animation: nudge 1.6s ease-in-out infinite; }
@keyframes nudge { 50% { transform: translateX(6px); } }
.opener { display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; }
.opener .chap { font-size:.8rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
.opener .big { font-size:4.4rem; margin:10px 0; width:120px; height:120px; display:flex; align-items:center; justify-content:center;
               border-radius:32px; background:linear-gradient(140deg, rgba(27,127,92,.18), rgba(20,184,166,.10)); }
.opener p { max-width:24em; color:var(--muted); }
.opener .hint { color:var(--accent); opacity:1; }
.toc h3 { margin:.2em 0 .6em; font-size:1.3rem; }
.toc ol { list-style:none; padding:0; margin:0; counter-reset:c; }
.toc li { counter-increment:c; }
.toc a { display:flex; gap:12px; align-items:center; padding:9px 12px; margin:4px 0; border-radius:10px; text-decoration:none; color:var(--ink);
         border:1px solid var(--line); transition: background .2s, transform .2s; }
.toc a::before { content: counter(c); font-weight:700; color:var(--accent); width:1.2em; }
.toc a:hover { background:rgba(27,127,92,.10); transform:translateX(4px); }
.controls { display:flex; gap:12px; align-items:center; margin-top:18px; }
button { font:inherit; font-weight:650; border:1px solid var(--line); background:var(--paper); color:var(--ink); padding:8px 18px; border-radius:12px; white-space:nowrap;
         cursor:pointer; transition: transform .15s, background .2s; }
button:hover:not(:disabled) { background:rgba(27,127,92,.12); } button:active:not(:disabled) { transform:scale(.94); }
button:disabled { opacity:.35; cursor:default; }
.endcard { position:absolute; left:50%; top:0; width:50%; height:100%; z-index:100; display:flex; flex-direction:column;
           justify-content:center; align-items:center; text-align:center; gap:10px; padding:30px 34px; color:#fff;
           border-radius:0 14px 14px 0; box-shadow: 0 20px 40px -18px var(--shadow);
           background: radial-gradient(circle at 80% 85%, rgba(245,165,36,.5), transparent 45%), linear-gradient(140deg,var(--cover1),var(--cover2));
           opacity:0; transform:translateX(-14px); pointer-events:none; transition: opacity .5s .6s, transform .5s .6s; }
.book.ended .endcard { opacity:1; transform:none; pointer-events:auto; }
.endcard .emblem { font-size:3.4rem; }
.endcard h2 { margin:0; font-size:1.7rem; }
.endcard p { margin:0 0 8px; opacity:.92; max-width:22em; }
.endcard button { width:min(300px, 100%); }
.endcard .primary { background:#fff; color:#0f5c43; border-color:#fff; font-weight:750; }
.endcard .ghost { background:transparent; color:#fff; border-color:rgba(255,255,255,.65); }
.endcard .ghost:hover, .endcard .primary:hover { background:rgba(255,255,255,.85) !important; color:#0f5c43; }
.dots { display:flex; gap:6px; } .dot { width:8px; height:8px; border-radius:50%; background:var(--line); transition: all .3s; cursor:pointer; }
.dot.on { background:var(--accent); width:22px; border-radius:4px; }
/* phones: a single page that turns away */
@media (max-width: 640px) {
  .book, .book.closed, .book.ended { width:100%; aspect-ratio:auto; height:560px; max-height:none; transform:none; }
  .left-page { display:none; }
  .leaf { left:0; width:100%; }
  .leaf.flipped { transform: rotateY(-180deg); opacity:0; transition: transform .9s ease, opacity .2s .7s; }
  .front { border-radius:14px; }
  .endcard { left:0; width:100%; border-radius:14px; }
  .page-body, .opener, .toc, .cover { padding:24px 22px 30px; }
  button { padding:8px 12px; } .dots { gap:4px; }
}
@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
</style></head><body>
<div class="stage"><div class="book closed" id="book">
  <div class="left-page">{{FIRST}}</div>
  {{LEAVES}}
  <div class="endcard" id="endcard" aria-live="polite">
    <div class="emblem">🎓</div>
    <h2>You've finished the Handbook</h2>
    <p>Seven options, from a savings account to NPS. Next, put it to work: see what's left each month and how fast it could become an emergency fund.</p>
    <button class="primary" id="toSurplus">Next: Set your surplus →</button>
    <button class="ghost" id="restart">↺ Start from the beginning</button>
  </div>
</div></div>
<div class="controls"><button id="prev" aria-label="Previous page">← Back</button><div class="dots" id="dots"></div><button id="next" aria-label="Next page">Next →</button></div>
<script>
const total = {{TOTAL}};
const leaves = [...document.querySelectorAll('.leaf')];
const book = document.getElementById('book'), dots = document.getElementById('dots');
let at = 0;   // number of flipped leaves
for (let i = 0; i <= total; i++) { const d = document.createElement('span'); d.className = 'dot'; d.onclick = () => go(i); dots.appendChild(d); }
function render() {
  leaves.forEach((l, i) => {
    const flipped = i < at;
    if (l.classList.contains('flipped') !== flipped) { l.classList.add('turning'); setTimeout(() => l.classList.remove('turning'), 1000); }
    l.classList.toggle('flipped', flipped);
    // flipped leaves stack on the left in reverse order
    l.style.zIndex = flipped ? (i + 1) : (total - i);
  });
  book.classList.toggle('closed', at === 0);
  book.classList.toggle('ended', at === total);
  document.getElementById('prev').disabled = at === 0;
  const nx = document.getElementById('next');
  nx.disabled = false;
  nx.textContent = at === total ? '↺ Start again' : 'Next →';
  nx.setAttribute('aria-label', at === total ? 'Start the book again' : 'Next page');
  [...dots.children].forEach((d, i) => d.classList.toggle('on', i === at));
}
function go(n) { at = Math.max(0, Math.min(total, n)); render(); }
leaves.forEach((l, i) => l.addEventListener('click', e => {
  if (e.target.closest('a')) return;
  go(l.classList.contains('flipped') ? i : i + 1);
}));
document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); go(+a.dataset.go); }));
document.getElementById('prev').onclick = () => go(at - 1);
document.getElementById('next').onclick = () => go(at === total ? 0 : at + 1);
document.getElementById('restart').onclick = () => go(0);
// Streamlit's component iframe is same-origin but may not navigate the page itself, so click the app's own
// sidebar link (keeps the session); open a new tab only if that isn't possible.
document.getElementById('toSurplus').onclick = () => {
  try {
    const link = window.parent.document.querySelector('a[href$="/my-surplus"]');
    if (link) { link.click(); return; }
    window.open(window.parent.location.origin + '/my-surplus', '_blank');
  } catch (err) { window.open('/my-surplus', '_blank'); }
};
document.addEventListener('keydown', e => { if (e.key === 'ArrowRight') go(at + 1); if (e.key === 'ArrowLeft') go(at - 1); });
let sx = null;
document.addEventListener('touchstart', e => sx = e.touches[0].clientX, { passive: true });
document.addEventListener('touchend', e => { if (sx === null) return; const dx = e.changedTouches[0].clientX - sx;
  if (Math.abs(dx) > 40) go(at + (dx < 0 ? 1 : -1)); sx = null; });
render();
</script></body></html>"""
