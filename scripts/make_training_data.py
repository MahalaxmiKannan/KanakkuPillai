"""Generate data/labeled_transactions_synthetic.csv: a STARTER training set.

These rows are written by script, not hand-labelled from real statements.
They let the app work today. Scores measured on them are NOT your project's
real evaluation numbers: use data/raw/labeled_real.csv for those.

    python scripts/make_training_data.py
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.merchants import MERCHANTS  # noqa: E402

OUT = ROOT / "data" / "labeled_transactions_synthetic.csv"
rng = random.Random(42)

# Made-up neighbourhood businesses that the merchant dictionary doesn't know.
LOCAL = {
    "Food & dining": [
        "sri krishna tiffins", "annapoorna mess", "murugan idli shop", "hotel saravana",
        "ganesh fast food", "royal shawarma", "paradise family restaurant", "anand bhavan",
        "kovai kitchen", "juice junction", "madras coffee house", "tea time corner",
        "karaikudi chettinad", "star kebabs", "the burger shack", "pasta street", "momo magic",
        "dosa plaza", "lassi corner", "nellai foods", "ambur star dum", "kerala kitchen",
        "punjabi dhaba", "thalappakatti hotel", "cool bites", "snack point", "food court",
        "hot chips", "ice cream world", "rolls mania",
    ],
    "Groceries": [
        "kumar provisions", "sri lakshmi departmental", "balaji general stores", "vegetable market",
        "fresh farm vegetables", "aavin milk booth", "selvam rice mandi", "mani fruits stall",
        "pothys super store", "kannan departmental", "gupta kirana", "murugan vegetables",
        "daily needs mart", "green grocers", "farm fresh eggs", "meena oil store",
        "royal fruit shop", "family grocery", "anbu milk agency", "shree grains",
        "krishna general store", "organic bazaar", "village fresh", "ram dairy", "the veggie cart",
        "new annai stores", "sakthi rice traders", "fruit basket", "bharat dal mill", "nadar stores",
    ],
    "Travel": [
        "kpn travels", "srm transports", "parveen travels", "orange tours", "auto stand",
        "call taxi", "fast track cabs", "city bus pass", "railway booking", "bus ticket counter",
        "toll plaza", "national highway toll", "ravi bike rentals", "royal brothers rental",
        "vel petrol bunk", "sri murugan fuels", "nayara energy", "parking charges",
        "airport shuttle", "yatra holidays", "state transport", "greenline travels",
        "sharma transports", "zingbus", "vrl travels", "kallada travels", "ooty tours",
        "go cabs", "local train pass", "ferry services",
    ],
    "Shopping": [
        "chennai silks", "pothys textiles", "saravana stores", "jeyachandran textiles",
        "lalitha jewellery", "ramraj cotton", "poorvika mobiles", "sangeetha mobiles",
        "gift corner", "fancy palace", "footwear world", "the shirt shop", "denim hub",
        "mobile accessories", "sri kumaran silks", "vasanth and co", "home decor mart",
        "watch world", "bag house", "kids toy centre", "style bazaar", "fashion junction",
        "new look tailors", "sports zone", "electronics corner", "laptop world", "photo studio",
        "perfume palace", "beauty parlour", "naturals salon",
    ],
    "Bills & recharge": [
        "tnpdcl bill", "eb bill payment", "corporation water tax", "property tax online",
        "piped gas bill", "gas cylinder agency", "local cable tv", "wifi monthly plan",
        "fiber net services", "mobile prepaid topup", "dth topup", "postpaid bill",
        "maintenance charges", "apartment association", "laundry services", "iron shop monthly", "metro water", "sewage charges",
        "you broadband", "spectra internet", "excitel", "tikona networks", "landline bill",
        "insurance premium", "lic premium", "bike insurance", "loan emi",
    ],
    "Subscriptions": [
        "crunchyroll", "mubi", "discovery plus", "lionsgate play", "voot select", "alt balaji",
        "hoichoi", "apple music", "apple tv", "amazon music", "steam games", "xbox game pass",
        "playstation plus", "nintendo online", "dropbox plus", "evernote", "grammarly",
        "github copilot", "perplexity pro", "claude pro", "midjourney", "strava", "headspace",
        "calm app", "times prime", "the hindu digital", "medium membership", "patreon",
        "substack", "scribd",
    ],
    "Rent": [
        "house rent", "room rent", "pg rent", "flat rent", "monthly rent", "rent payment",
        "hostel rent", "mess and rent", "landlord", "house owner", "rent for room",
        "sri lakshmi pg", "green view pg", "comfort stay pg", "royal residency rent",
        "balaji nilayam", "student hostel", "boys pg", "girls hostel", "shared flat rent",
    ],
    "Movies": [
        "sathyam cinemas", "escape cinemas", "ags cinemas", "kasi theatre", "devi cineplex",
        "luxe cinemas", "fame cinemas", "gold cinemas", "city multiplex", "fun cinemas",
        "rohini silver screens", "vetri theatres", "pvr cinemas chennai", "inox forum",
        "movie tickets", "film club", "imax screen", "drive in theatre", "sri murugan theatre",
        "friday night shows",
    ],
    "Education": [
        "fiitjee", "aakash institute", "allen career", "narayana coaching", "ielts exam",
        "gate registration", "tnpsc fees", "semester fee", "lab record fee", "xerox shop",
        "stationery corner", "book house", "notes centre", "typing institute", "spoken english",
        "coding academy", "nasscom course", "pluralsight", "datacamp", "codecademy",
        "brilliant org", "khan tutorials", "maths classes", "physics coaching", "library fee",
        "bus fee college", "project centre", "print and bind", "training institute", "skill lab",
    ],
    "Health": [
        "sri ram medicals", "lotus medical", "kauvery hospitals", "meenakshi mission", "sims healthcare",
        "gleneagles", "vision eye care", "agarwal eye", "smile dental", "city scans",
        "blood test lab", "physio care", "ayush siddha", "homeo care", "cult fit gym",
        "gold gym", "yoga studio", "health plus", "wellness forever", "nursing home",
        "skin care doctor", "dr ramesh consult", "dr priya ent", "ortho care", "neuberg labs",
        "vijaya labs", "hitech lab", "care ambulance", "life care drugs", "sanjeevani drugs",
    ],
}

FIRST = """arjun priya karthik divya rahul sneha vignesh anitha suresh deepa harish kavya naveen
meena pranav lakshmi rohit nithya ajay swathi gokul janani manoj preethi sanjay ramya tarun aishwarya
vikram pooja dinesh shruti ashwin keerthana bala mohan revathi senthil yamini""".split()
LAST = """kumar sharma reddy nair iyer patel singh raj krishnan menon pillai rao das verma gupta""".split()

SUFFIXES = {"Food & dining": ["cafe", "hotel"], "Groceries": ["store", "mart"], "Shopping": ["store", "fashions"],
            "Travel": ["travels"], "Health": ["care"], "Education": ["academy"], "Bills & recharge": ["payment"],
            "Subscriptions": ["subscription"], "Rent": ["payment"], "Movies": ["tickets"]}


def variants(name: str, category: str) -> list[str]:
    """Spellings banks really print: cut off, joined up, or with a suffix."""
    options = {name}
    if len(name) > 11:
        options.add(name[:rng.randint(9, 11)].strip())
    options.add(name.replace(" ", ""))
    options.add(f"{name} {rng.choice(SUFFIXES[category])}")
    extra = sorted(options - {name})
    return [name] + rng.sample(extra, k=min(1, len(extra)))


def main() -> None:
    rows = []
    for category, names in LOCAL.items():
        for name in names:
            rows += [(v, category, name, "synthetic-local") for v in variants(name, category)]
    for category, keys in MERCHANTS.items():
        rows += [(key, category, key, "dictionary") for key in keys]

    people = sorted({f"{f} {rng.choice(LAST + [c for c in 'ksmrvpn'])}" for f in FIRST for _ in range(3)})
    people += FIRST
    for person in people:
        rows.append((person, "Transfers (P2P)", person.split()[0], "synthetic-person"))

    rng.shuffle(rows)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["payee", "category", "merchant_group", "source"])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic rows to {OUT}")


if __name__ == "__main__":
    main()
