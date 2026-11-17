"""Generate data/demo_statement.csv: ~6 months of a realistic student's account.

Fictional person, fictional names, made-up reference numbers. The fixed seed
means re-running gives the identical file.

    python scripts/make_demo_statement.py
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "demo_statement.csv"
START, END = date(2026, 5, 1), date(2026, 10, 31)
OPENING_BALANCE = 6_500.00

rng = random.Random(42)


def ref() -> str:
    return str(rng.randint(10**11, 10**12 - 1))


def upi_dr(name: str, vpa: str, bank: str = "YESB") -> str:
    return f"UPI/DR/{ref()}/{name}/{bank}/{vpa}/Payment"


def upi_cr(name: str, vpa: str, bank: str = "SBIN") -> str:
    return f"UPI/CR/{ref()}/{name}/{bank}/{vpa}/Received"


# (name, vpa, bank, low, high, times per month)
FOOD = [("SWIGGY", "swiggy@ybl", "YESB", 140, 420, 6), ("ZOMATO", "zomato@hdfcbank", "HDFC", 150, 450, 5),
        ("CHAI POINT", "chaipoint@paytm", "PYTM", 40, 120, 3), ("DOMINOS PIZZA", "dominos@icici", "ICIC", 250, 600, 1)]
GROCERY = [("BLINKIT", "blinkit@axl", "UTIB", 120, 650, 3), ("ZEPTO", "zepto@ybl", "YESB", 100, 500, 2),
           ("DMART", "dmart.store@icici", "ICIC", 400, 1200, 1)]
TRAVEL = [("UBER", "uber@axisbank", "UTIB", 90, 380, 3), ("RAPIDO", "rapido@ybl", "YESB", 35, 120, 4),
          ("OLA", "olacabs@icici", "ICIC", 120, 350, 1)]
SHOPPING = [("AMAZON", "amazon@apl", "UTIB", 299, 1999, 1), ("FLIPKART", "flipkart@axisbank", "UTIB", 249, 1499, 1),
            ("MYNTRA", "myntra@ybl", "YESB", 399, 1799, 0.5)]
HEALTH = [("APOLLO PHARMACY", "apollopharmacy@icici", "ICIC", 80, 450, 0.7),
          ("PRACTO", "practo@hdfcbank", "HDFC", 300, 600, 0.2)]
FRIENDS = [("ARJUN S", "arjun.s07@okaxis"), ("PRIYA K", "priyak2005@oksbi"),
           ("KARTHIK R", "9876501234@ybl"), ("DIVYA M", "divya.m@okicici")]


def month_starts():
    d = START
    while d <= END:
        yield d
        d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)


def random_day(month_start: date) -> date:
    nxt = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return month_start + timedelta(days=rng.randrange((nxt - month_start).days))


def build() -> list[tuple[date, str, float, float]]:
    """Return (date, description, debit, credit) rows."""
    tx: list[tuple[date, str, float, float]] = []
    for m in month_starts():
        # Income: pocket money from parent + internship stipend
        tx.append((m, upi_cr("SURESH KUMAR", "suresh.kumar64@oksbi"), 0, 7000))
        tx.append((m.replace(day=5), f"NEFT/CR/N{ref()}/BRIGHTPATH LABS PVT LTD/STIPEND", 0, 10000))

        # Fixed bills and subscriptions
        tx.append((m.replace(day=2), "BY TRANSFER-HOSTEL MESS FEE-INB", 4500, 0))
        tx.append((m.replace(day=rng.randint(3, 8)), upi_dr("JIO PREPAID", "jiorecharge@ybl"), 299, 0))
        tx.append((m.replace(day=11), "ACH/NETFLIX.COM/" + ref(), 149, 0))
        tx.append((m.replace(day=17), upi_dr("SPOTIFY INDIA", "spotify@icici", "ICIC"), 119, 0))
        tx.append((m.replace(day=21), "ACH/YOUTUBE PREMIUM/GOOGLE/" + ref(), 129, 0))

        for group in (FOOD, GROCERY, TRAVEL, SHOPPING, HEALTH):
            for name, vpa, bank, low, high, per_month in group:
                count = int(per_month) + (rng.random() < per_month % 1)
                count += rng.choice([-1, 0, 0, 1]) if per_month >= 2 else 0
                for _ in range(max(count, 0)):
                    amount = round(rng.uniform(low, high), 0)
                    tx.append((random_day(m), upi_dr(name, vpa, bank), amount, 0))

        # Education: one course/book purchase some months
        if rng.random() < 0.5:
            name, vpa = rng.choice([("UDEMY", "udemy@icici"), ("COURSERA", "coursera@hdfcbank"),
                                    ("HIGGINBOTHAMS", "higginbothams@okaxis")])
            tx.append((random_day(m), upi_dr(name, vpa, "ICIC"), round(rng.uniform(399, 1299), 0), 0))

        # P2P: splitting bills with friends, both ways
        for _ in range(rng.randint(2, 4)):
            name, vpa = rng.choice(FRIENDS)
            tx.append((random_day(m), upi_dr(name, vpa, "SBIN"), round(rng.uniform(100, 800), -1), 0))
        for _ in range(rng.randint(1, 2)):
            name, vpa = rng.choice(FRIENDS)
            tx.append((random_day(m), upi_cr(name, vpa), 0, round(rng.uniform(100, 600), -1)))

        # Cash
        if rng.random() < 0.6:
            tx.append((random_day(m), f"ATM WDL/SBI ATM ANNA NAGAR/{ref()}", 500 * rng.randint(1, 3), 0))

    # Once-off: festival shopping in October, a birthday treat in July
    tx.append((date(2026, 10, 18), upi_dr("RELIANCE TRENDS", "reliancetrends@icici", "ICIC"), 2499, 0))
    tx.append((date(2026, 7, 12), upi_dr("BARBEQUE NATION", "bbqnation@hdfcbank", "HDFC"), 1850, 0))

    # Credits first on a given day so the balance never dips negative mid-day
    tx.sort(key=lambda t: (t[0], t[3] == 0))
    return tx


def main() -> None:
    rows = build()
    balance = OPENING_BALANCE
    lines = ["date,description,debit,credit,balance"]
    for d, desc, debit, credit in rows:
        balance = round(balance - debit + credit, 2)
        if balance < 0:
            raise SystemExit(f"Balance went negative on {d}; tweak amounts or the seed.")
        lines.append(f"{d.isoformat()},{desc},{debit:.2f},{credit:.2f},{balance:.2f}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} transactions to {OUT} (closing balance {balance:,.2f})")


if __name__ == "__main__":
    main()
