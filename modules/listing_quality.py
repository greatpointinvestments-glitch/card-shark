"""Listing quality + variation matching for Flip Finder.

The whole point: don't show users a "flip" that's actually a reprint, a wrong
parallel, a damaged card, or a raw-vs-graded mismatch. Every flip must be
apples-to-apples with the sold comps it's being compared to.
"""

import re
from typing import Optional


# ----------------------------------------------------------------------------
# Suspect title patterns — hide these entirely
# ----------------------------------------------------------------------------

_SUSPECT_PATTERNS = re.compile(
    r"\b(reprint|re-print|re print|rp|proxy|custom|novelty|art card|"
    r"reproduction|repro|fake|counterfeit|replica|facsimile|digital|nft)\b|"
    r"\b(damaged|creased|crease|bent|trimmed|altered|"
    r"poor condition|off[- ]?center|off centered|miscut|torn|ripped|water|stained)\b|"
    r"\b(lot of \d+|card lot|bulk|mystery|grab bag|"
    r"repack|set break|you pick|you choose|u pick|pick your|pick \d+)\b",
    re.IGNORECASE,
)

# "Auction" listings hide real prices behind opening bids + shill risk
# (handled in flip_finder by requiring BIN, but we expose a helper anyway)

# ----------------------------------------------------------------------------
# Grading detection
# ----------------------------------------------------------------------------

_GRADED_PATTERN = re.compile(
    r"\b(psa|bgs|sgc|cgc|hga|gma|beckett|gem mt|gem mint)\s*"
    r"(10|9\.5|9|8\.5|8|7|6|5|4|3|2|1)\b",
    re.IGNORECASE,
)


def is_graded(title: str) -> bool:
    """True if the title describes a graded card."""
    return bool(_GRADED_PATTERN.search(title or ""))


def extract_grade(title: str) -> Optional[str]:
    """Return a normalized grade string like 'PSA 10' or None."""
    if not title:
        return None
    m = _GRADED_PATTERN.search(title)
    if not m:
        return None
    company = m.group(1).upper().replace("BECKETT", "BGS").replace("GEM MT", "BGS").replace("GEM MINT", "BGS")
    grade = m.group(2)
    return f"{company} {grade}"


# ----------------------------------------------------------------------------
# Parallel / variation parsing
# ----------------------------------------------------------------------------

# Order matters — first match wins, so put rarer/more-specific tags first
_PARALLEL_TAGS = [
    ("superfractor", r"\bsuperfractor\b"),
    ("one_of_one", r"\b1[/\- ]?of[/\- ]?1\b|\b1/1\b"),
    ("black_prizm", r"\bblack\s+(prizm|refractor|shimmer)\b"),
    ("gold_prizm", r"\bgold\s+(prizm|refractor|shimmer|vinyl)\b"),
    ("red_refractor", r"\bred\s+refractor\b"),
    ("orange_refractor", r"\borange\s+refractor\b"),
    ("blue_refractor", r"\bblue\s+refractor\b"),
    ("green_refractor", r"\bgreen\s+refractor\b"),
    ("purple_refractor", r"\bpurple\s+refractor\b"),
    ("pink_refractor", r"\bpink\s+refractor\b"),
    ("silver_prizm", r"\bsilver\s+prizm\b|\bsilver\s+wave\b"),
    ("red_wave", r"\bred\s+wave\b"),
    ("blue_wave", r"\bblue\s+wave\b"),
    ("mojo_refractor", r"\bmojo\b"),
    ("x_fractor", r"\bxfractor\b|\bx-fractor\b"),
    ("shimmer", r"\bshimmer\b"),
    ("auto_patch", r"\b(auto|autograph).*\b(patch|relic|jersey)\b|\b(patch|relic)\s+auto\b"),
    ("auto", r"\b(autograph|auto)\b"),
    ("patch", r"\b(patch|relic|jersey)\b"),
    ("refractor", r"\brefractor\b"),
    ("prizm", r"\bprizm\b"),
    ("holo", r"\bholo\b|\bholofoil\b"),
    ("chrome", r"\bchrome\b"),
    ("base", r""),  # fallback
]

# Serial number pattern, e.g. "/99", "#/25", "numbered to 10"
_SERIAL_PATTERN = re.compile(r"(?:#\s*/\s*|/\s*|numbered\s+to\s+)(\d{1,4})\b", re.IGNORECASE)


def extract_parallel(title: str) -> str:
    """Return a normalized parallel/variation key for the title.

    Examples:
        'Luka Doncic 2018 Prizm Silver' -> 'silver_prizm'
        'Jordan 1986 Fleer Rookie' -> 'base'
        'Mahomes Select Blue Wave /99' -> 'blue_wave'
    """
    if not title:
        return "base"
    t = title.lower()
    for key, pat in _PARALLEL_TAGS:
        if not pat:  # fallback
            return key
        if re.search(pat, t):
            return key
    return "base"


def extract_serial(title: str) -> Optional[int]:
    """Return the print run number from '/99' style notation, or None."""
    if not title:
        return None
    m = _SERIAL_PATTERN.search(title)
    if not m:
        return None
    try:
        n = int(m.group(1))
        # Filter out year-like numbers (1900-2099) — they're card years, not serial #s
        if 1900 <= n <= 2099:
            return None
        return n if 1 <= n <= 9999 else None
    except ValueError:
        return None


# ----------------------------------------------------------------------------
# Rookie / variation sanity
# ----------------------------------------------------------------------------

_ROOKIE_TOKENS = re.compile(r"\b(rookie|rc|1st year|first year|debut)\b", re.IGNORECASE)


def is_rookie(title: str) -> bool:
    return bool(_ROOKIE_TOKENS.search(title or ""))


# ----------------------------------------------------------------------------
# Main filter + confidence scoring
# ----------------------------------------------------------------------------

def is_suspect(title: str) -> bool:
    """Return True if the listing title matches any hide-this pattern."""
    if not title:
        return True
    return bool(_SUSPECT_PATTERNS.search(title))


def listings_match(listing_title: str, comp_title: str, require_rookie_match: bool = True) -> bool:
    """True if two listings represent the *same* card for comp purposes."""
    if extract_parallel(listing_title) != extract_parallel(comp_title):
        return False
    if is_graded(listing_title) != is_graded(comp_title):
        return False
    if require_rookie_match and is_rookie(listing_title) != is_rookie(comp_title):
        return False
    # Optional: serial-numbered cards compared only to same-serial comps
    s1, s2 = extract_serial(listing_title), extract_serial(comp_title)
    if (s1 is not None) != (s2 is not None):
        return False
    return True


def confidence_score(
    listing: dict,
    matched_comp_count: int,
    seller_feedback_pct: Optional[float] = None,
    seller_feedback_count: Optional[int] = None,
) -> int:
    """Return a 0-100 confidence score for a flip opportunity.

    Deducts points for:
    - Low matched comp volume (need 5+ same-variation sales)
    - Poor seller reputation
    - Missing data
    - Auction format (already filtered out upstream usually)
    """
    score = 100

    # Comp volume — need real data to trust a median
    if matched_comp_count < 3:
        score -= 50
    elif matched_comp_count < 5:
        score -= 25
    elif matched_comp_count < 10:
        score -= 10

    # Seller quality
    if seller_feedback_pct is not None:
        if seller_feedback_pct < 95:
            score -= 40
        elif seller_feedback_pct < 98:
            score -= 20
        elif seller_feedback_pct < 99:
            score -= 5
    else:
        score -= 10  # unknown seller = penalty

    if seller_feedback_count is not None:
        if seller_feedback_count < 10:
            score -= 30
        elif seller_feedback_count < 50:
            score -= 15
        elif seller_feedback_count < 200:
            score -= 5

    if listing.get("buying_format") == "Auction":
        score -= 30

    return max(0, min(100, score))


def confidence_label(score: int) -> str:
    """Human-friendly tier from a confidence score."""
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "Low"
    return "Very Low"
