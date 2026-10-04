"""Validation of what the client types. Each function returns the cleaned value or None."""
import re

_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f<>]")
_SPAM = re.compile(r"(.)\1{5,}")              # aaaaaa, ......, 111111
_URL = re.compile(r"(https?://|www\.|t\.me/)", re.I)


def clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", _CTRL.sub("", s or "")).strip()


def free_text(s, min_len=2, max_len=1500):
    """A free description: at least a couple of characters with a letter or digit, no control chars, no spam runs."""
    t = _CTRL.sub("", s or "")
    t = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()
    if not (min_len <= len(t) <= max_len) or not any(ch.isalnum() for ch in t) or _SPAM.search(t):
        return None
    return t


def first_name(s):
    """A first name (or name and surname): letters only (Latin, Cyrillic, Armenian), 2-60 chars."""
    t = clean(s)
    if not (2 <= len(t) <= 60) or _SPAM.search(t) or _URL.search(t) or "@" in t:
        return None
    words = t.split(" ")
    if len(words) > 4 or not all(re.fullmatch(r"[^\W\d_]+(?:['’.\-][^\W\d_]+)*\.?", w) for w in words):
        return None
    return t


def quantity(s):
    """A positive whole number up to 100000; accepts '50', '50 шт', '50 pcs', '1 000'."""
    t = clean(s).lower().replace(" ", "")
    m = re.fullmatch(r"(\d{1,6})(?:шт\.?|штук|pcs|հատ|copies|копий|копии)?", t)
    if not m:
        return None
    n = int(m.group(1))
    return n if 1 <= n <= 100000 else None


def size_text(s):
    """A size such as '50x70', '50 x 70 cm', 'A3', 'А4', '10х15'. Returns the cleaned text or None."""
    t = clean(s)
    if not (2 <= len(t) <= 40) or _SPAM.search(t):
        return None
    if re.search(r"\d", t) or re.fullmatch(r"[aAаА][0-6]\+?", t):
        return t
    return None


def phone_norm(s):
    """Armenian numbers in any way of writing -> '+374 XX XXXXXX'; other countries only with '+': '+<digits>'.
    '+37499123456', '37499123456', '099123456', '99123456', '+374 (99) 12-34-56', '0037499123456' all give '+374 99 123456'."""
    raw = clean(s)
    if not re.fullmatch(r"\+?[\d\s()\-.]{8,22}", raw):
        return None
    d = re.sub(r"\D", "", raw)
    intl = raw.startswith("+")
    if d.startswith("00"):
        d, intl = d[2:], True
    if len(set(d)) < 3:
        return None
    nat = None
    if d.startswith("374") and (intl or len(d) in (11, 12)):
        nat = d[3:]
    elif not intl and d.startswith("0") and len(d) == 9:
        nat = d[1:]
    elif not intl and len(d) == 8:
        nat = d
    if nat is not None:
        if len(nat) == 9 and nat.startswith("0"):
            nat = nat[1:]
        return f"+374 {nat[:2]} {nat[2:]}" if len(nat) == 8 and nat[0] != "0" else None
    return "+" + d if intl and 8 <= len(d) <= 15 else None


def address_text(s):
    t = clean(s)
    if not (6 <= len(t) <= 200) or not any(ch.isalpha() for ch in t) or _SPAM.search(t) or _URL.search(t):
        return None
    return t
