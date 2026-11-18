"""Rules layer: well-known Indian merchants and shop-type keywords by category.

Matching happens in core/categorizer.py. The longest key wins, so
"swiggy instamart" (Groceries) beats "swiggy" (Food & dining).
"""

MERCHANTS: dict[str, list[str]] = {
    "Food & dining": [
        "swiggy", "zomato", "eatsure", "dominos", "domino's", "pizza hut", "kfc", "mcdonald",
        "burger king", "subway", "starbucks", "cafe coffee day", "ccd", "chai point", "chaayos",
        "third wave coffee", "blue tokai", "haldiram", "adyar ananda bhavan", "a2b",
        "saravana bhavan", "barbeque nation", "behrouz", "faasos", "wow momo", "baskin robbins",
        "naturals ice cream", "taco bell", "biryani", "restaurant", "bakery", "sweets",
        "canteen", "tiffin", "cafe",
    ],
    "Groceries": [
        "blinkit", "zepto", "swiggy instamart", "instamart", "bigbasket", "dmart", "more retail",
        "reliance fresh", "reliance smart", "jiomart", "spencers", "natures basket", "ratnadeep",
        "nilgiris", "milkbasket", "country delight", "licious", "freshtohome", "amazon fresh",
        "flipkart grocery", "supermarket", "kirana", "provision store",
    ],
    "Travel": [
        "uber", "ola", "olacabs", "rapido", "namma yatri", "blusmart", "yulu", "irctc", "redbus",
        "abhibus", "makemytrip", "goibibo", "ixigo", "cleartrip", "easemytrip", "indigo",
        "air india", "spicejet", "akasa air", "fastag", "chennai metro", "cmrl", "delhi metro",
        "dmrc", "namma metro", "bmrcl", "metro rail", "tnstc", "setc", "bmtc", "indian oil",
        "hpcl", "bpcl", "bharat petroleum", "petrol", "fuel",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa", "tata cliq", "snapdeal",
        "croma", "reliance digital", "reliance trends", "vijay sales", "decathlon", "ikea",
        "hnm", "zara", "uniqlo", "max fashion", "pantaloons", "westside", "lifestyle",
        "shoppers stop", "lenskart", "boat", "bata", "puma", "nike", "adidas", "titan",
        "tanishq", "miniso", "firstcry",
    ],
    "Bills & recharge": [
        "jio", "airtel", "bsnl", "vodafone", "tata play", "dish tv", "sun direct", "act fibernet",
        "hathway", "tneb", "tangedco", "bescom", "msedcl", "bses", "tata power",
        "adani electricity", "indane", "bharat gas", "hp gas", "electricity", "broadband",
        "recharge", "water board",
    ],
    "Subscriptions": [
        "netflix", "spotify", "prime video", "amazon prime", "hotstar", "jiohotstar", "youtube",
        "google one", "google play", "apple services", "icloud", "sony liv", "sonyliv", "zee5",
        "aha", "sun nxt", "gaana", "jiosaavn", "wynk", "audible", "kindle unlimited", "chatgpt",
        "openai", "canva", "linkedin premium", "notion", "microsoft 365", "adobe", "tinder",
        "bumble",
    ],
    "Education": [
        "udemy", "coursera", "byjus", "unacademy", "physicswallah", "vedantu", "upgrad",
        "simplilearn", "great learning", "scaler", "leetcode", "geeksforgeeks", "nptel",
        "higginbothams", "crossword", "sapna book", "college", "university", "school", "tuition",
        "hostel", "exam fee",
    ],
    "Health": [
        "apollo", "medplus", "netmeds", "pharmeasy", "tata 1mg", "1mg", "practo", "thyrocare",
        "dr lal", "metropolis", "fortis", "manipal hospital", "narayana health", "aster hospital",
        "max healthcare", "pharmacy", "medical", "hospital", "clinic", "diagnostic", "dental",
    ],
}
