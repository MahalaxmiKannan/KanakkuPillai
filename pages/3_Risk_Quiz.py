"""Risk quiz: one landscape card, one question at a time, then the score, the profile and a way on to Learn.
No product recommendations."""
import streamlit as st

from core.risk_quiz import QUESTIONS, result
from core.ui import page_header, setup_page

setup_page("Risk Quiz", "🧭")
page_header("Risk Quiz", "🧭", "Nine questions about how you feel about risk. There are no right answers.", step=3)

N = len(QUESTIONS)
PROFILE_COLOR = {"Conservative": "#5b9e86", "Moderate": "#14b8a6", "Aggressive": "#e9a23b"}

st.markdown(
    """
<style>
  .qz-step { font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--kp-green); }
  .qz-q { font-size: clamp(1.25rem, 2.2vw, 1.7rem); font-weight: 750; line-height: 1.25; letter-spacing: -.01em; margin: .35rem 0 .6rem; }
  .qz-dots { display: flex; gap: 6px; margin-top: .4rem; }
  .qz-dots i { width: 22px; height: 6px; border-radius: 99px; background: var(--kp-line); }
  .qz-dots i.done { background: var(--kp-green); }
  .qz-dots i.now { background: var(--kp-teal); width: 34px; }
  .qz-big { font-size: 3.2rem; font-weight: 800; letter-spacing: -.03em; line-height: 1; }
  .qz-scale { position: relative; height: 12px; border-radius: 99px; margin: 1.1rem 0 .4rem;
              background: linear-gradient(90deg, #5b9e86 0 36%, #14b8a6 36% 69%, #e9a23b 69% 100%); }
  .qz-scale b { position: absolute; top: -7px; width: 26px; height: 26px; margin-left: -13px; border-radius: 50%;
                background: #fff; border: 4px solid #0f5c43; box-shadow: 0 4px 12px rgba(0,0,0,.2); }
  .qz-scale-l { display: flex; justify-content: space-between; font-size: .8rem; opacity: .75; }
</style>
""",
    unsafe_allow_html=True,
)


def answers() -> dict:
    """Answers live here, not in the radio widgets: Streamlit forgets a widget's value once it stops being shown."""
    return st.session_state.setdefault("quiz_answers", {})


def save(i: int) -> None:
    answers()[i] = st.session_state.get(f"quiz_w_{i}")


def go(step: int) -> None:
    st.session_state["quiz_step"] = max(0, min(N - 1, step))


def finish() -> None:
    picks = [answers().get(i) for i in range(1, N + 1)]
    if all(p is not None for p in picks):
        chosen = [QUESTIONS[i]["options"].index(p) for i, p in enumerate(picks)]
        st.session_state["risk_result"] = result(chosen)


def retake() -> None:
    for i in range(1, N + 1):
        st.session_state.pop(f"quiz_w_{i}", None)
    st.session_state["quiz_answers"] = {}
    st.session_state.pop("risk_result", None)
    st.session_state["quiz_step"] = 0


res = st.session_state.get("risk_result")

# ---------- the quiz: one card, one question ----------
if not res:
    step = st.session_state.setdefault("quiz_step", 0)
    i = step + 1
    item = QUESTIONS[step]
    with st.container(border=True, key="card_quiz"):
        left, right = st.columns([2, 3], gap="large", vertical_alignment="center")
        dots = "".join(f'<i class="{"done" if k < step else "now" if k == step else ""}"></i>' for k in range(N))
        left.markdown(f'<div class="qz-step">Question {i} of {N}</div><div class="qz-q">{item["q"]}</div>'
                      f'<div class="qz-dots">{dots}</div>', unsafe_allow_html=True)
        with right:
            saved = answers().get(i)
            if saved is not None and st.session_state.get(f"quiz_w_{i}") is None:
                st.session_state[f"quiz_w_{i}"] = saved                 # restore when coming back to this question
            st.radio(item["q"], item["options"], index=None, key=f"quiz_w_{i}", label_visibility="collapsed",
                     on_change=save, args=(i,))
            answer = answers().get(i)
        st.write("")
        back, _, nxt = st.columns([1, 3, 1.3])
        back.button("← Back", on_click=go, args=(step - 1,), disabled=step == 0, width="stretch")
        if i < N:
            nxt.button("Next →", type="primary", on_click=go, args=(step + 1,), disabled=answer is None, width="stretch")
        else:
            nxt.button("Finish quiz ✓", type="primary", on_click=finish, disabled=answer is None, width="stretch")
    st.caption("Pick the answer closest to how you'd really feel. You can go back and change any answer before you finish.")

# ---------- the result ----------
else:
    color = PROFILE_COLOR[res["profile"]]
    position = (res["total"] - N) / (res["max"] - N) * 100          # 9..27 -> 0..100
    with st.container(border=True, key="card_quiz_result"):
        left, right = st.columns([2, 3], gap="large", vertical_alignment="center")
        left.markdown(
            f'<div class="qz-step">Your score</div>'
            f'<div class="qz-big">{res["total"]}<span style="font-size:1.3rem;opacity:.6"> / {res["max"]}</span></div>'
            f'<div style="font-size:1.6rem;font-weight:800;color:{color};margin-top:.3rem">{res["profile"]}</div>'
            f'<div class="qz-scale"><b style="left:{position:.0f}%"></b></div>'
            f'<div class="qz-scale-l"><span>Conservative</span><span>Moderate</span><span>Aggressive</span></div>',
            unsafe_allow_html=True,
        )
        with right:
            st.markdown(f"**{res['summary']}**")
            st.write(res["meaning"])
            for note in res["notes"]:
                st.warning(note)
            st.caption("A quiz can't know your whole situation. This describes comfort with risk; it doesn't tell you what to buy.")
    go_learn, redo, _ = st.columns([1.4, 1, 2])
    if go_learn.button("Start learning →", type="primary", width="stretch"):
        st.switch_page("pages/4_Learn.py")
    redo.button("Retake the quiz", on_click=retake, width="stretch")
