import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Iterable, List

REMOTE_PATTERNS = [
    r"\bremote\b",
    r"\bwork from home\b",
    r"\bWFH\b",
    r"\banywhere\b",
]

CURRENCY_MAP = {
    "lpa": "INR",
    "inr": "INR",
    "₹": "INR",
    "rs": "INR",
    "$": "USD",
    "usd": "USD",
}

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
]

def choose_user_agent(seed: int | None = None) -> str:
    import random
    rnd = random.Random(seed)
    return rnd.choice(UA_LIST)

def to_tags(iterable: Iterable[str]) -> List[str]:
    dedup = set()
    for t in iterable:
        t = (t or "").strip().lower()
        if t:
            dedup.add(t)
    return sorted(dedup)

def derive_is_remote(title: str, location: str | None, tags: List[str]) -> bool:
    hay = " ".join([title or "", location or "", " ".join(tags or [])]).lower()
    return any(re.search(p, hay) for p in REMOTE_PATTERNS)

def parse_salary(s: str | None):
    if not s:
        return None, None, None
    s_clean = s.strip().lower().replace(",", "").replace("lakhs", "lpa")
    # capture currency
    currency = None
    for k, v in CURRENCY_MAP.items():
        if k in s_clean:
            currency = v
            break
    # numeric range like "3-7 lpa" or "₹10,00,000 - ₹14,00,000 per year"
    nums = re.findall(r"(\d+(?:\.\d+)?)", s_clean)
    if not nums:
        return None, None, currency
    # Heuristic: if "lpa" present, treat nums as Lakhs per annum
    if "lpa" in s_clean or "lakh" in s_clean:
        vals = [float(n) * 100000 for n in nums[:2]]
    elif "k" in s_clean:  # "50k-70k"
        vals = [float(n) * 1000 for n in nums[:2]]
    else:
        vals = [float(n) for n in nums[:2]]
    if len(vals) == 1:
        vals.append(vals[0])
    return int(vals[0]), int(vals[1]), currency

def parse_posted_date(text: str, tz: str = "Asia/Kolkata") -> datetime:
    text = (text or "").strip().lower()
    now = datetime.now(ZoneInfo(tz))
    if text in {"just now", "today"}:
        return now
    m = re.match(r"(\d+)\s*(minute|hour|day|week|month)s?\s*ago", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {
            "minute": timedelta(minutes=n),
            "hour": timedelta(hours=n),
            "day": timedelta(days=n),
            "week": timedelta(weeks=n),
            "month": timedelta(days=30*n),
        }[unit]
        return now - delta
    # fallback: try ISO parse
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return now
