"""Risk-profile quiz. Scores answers 1-3 and maps the total to a profile.

It describes how someone might feel about risk; it never recommends a product.
"""
from __future__ import annotations

QUESTIONS = [
    {
        "q": "How long before you will need this money?",
        "options": ["Less than 3 years", "3 to 7 years", "More than 7 years"],
    },
    {
        "q": "If your savings fell 20% in a few months, what would you most likely do?",
        "options": ["Sell to stop the loss", "Wait and do nothing", "See it as a chance to put in more"],
    },
    {
        "q": "How steady is your income?",
        "options": ["Irregular or none right now", "Fairly steady", "Steady, and likely to grow"],
    },
    {
        "q": "If you lost your income tomorrow, how long could you cover essentials from savings?",
        "options": ["Under 3 months", "3 to 6 months", "More than 6 months"],
    },
    {
        "q": "How much do you know about investing?",
        "options": ["Very little", "The basics", "Quite a lot"],
    },
    {
        "q": "Which outcome sounds most acceptable over a year?",
        "options": [
            "A small gain, but no chance of loss",
            "A moderate gain, with a small chance of loss",
            "A big gain, with a real chance of a big loss",
        ],
    },
    {
        "q": "How would a loss of this money affect your life?",
        "options": ["Seriously", "It would hurt but I'd manage", "Barely"],
    },
    {
        "q": "Do people depend on your income?",
        "options": ["Yes, several", "One or two", "No"],
    },
    {
        "q": "How often would you check the value of your investments?",
        "options": ["Every day, and worry", "Now and then", "Rarely; I think long term"],
    },
]

PROFILES = {
    "Conservative": {
        "summary": "You prefer certainty and would be uncomfortable seeing your money fall.",
        "meaning": (
            "People with this profile tend to value safety and easy access to money over higher growth. "
            "Options with fixed, predictable returns usually match this comfort level. "
            "The trade-off is that returns may not beat inflation over long periods."
        ),
    },
    "Moderate": {
        "summary": "You accept some ups and downs in exchange for the chance of better growth.",
        "meaning": (
            "People with this profile tend to be comfortable mixing steady and growth-oriented options. "
            "They can usually ride out a bad year, but would not want large swings. "
            "Spreading money across different kinds of options is a common way to balance this."
        ),
    },
    "Aggressive": {
        "summary": "You are comfortable with big swings and have a long time to wait.",
        "meaning": (
            "People with this profile tend to focus on long-term growth and accept that value can fall sharply "
            "for a while. This only works if the money truly isn't needed soon and an emergency fund exists."
        ),
    },
}


def score(answers: list[int]) -> int:
    """answers are option positions 0-2; each scores 1-3."""
    if len(answers) != len(QUESTIONS):
        raise ValueError(f"Expected {len(QUESTIONS)} answers, got {len(answers)}.")
    if any(a not in (0, 1, 2) for a in answers):
        raise ValueError("Each answer must be 0, 1 or 2.")
    return sum(a + 1 for a in answers)


def profile_for(total: int) -> str:
    """9-15 Conservative, 16-21 Moderate, 22-27 Aggressive."""
    if total <= 15:
        return "Conservative"
    if total <= 21:
        return "Moderate"
    return "Aggressive"


def result(answers: list[int]) -> dict:
    total = score(answers)
    name = profile_for(total)
    notes = []
    if answers[0] == 0 or answers[3] == 0:
        notes.append(
            "Your answers about time or emergency cover suggest that building an emergency fund "
            "matters more than any growth option right now, whatever your score."
        )
    if answers[1] == 0 and total >= 22:
        notes.append("You said you would sell after a 20% fall, which doesn't fit a high score. It's worth rethinking that answer.")
    return {"total": total, "max": 3 * len(QUESTIONS), "profile": name, **PROFILES[name], "notes": notes}
