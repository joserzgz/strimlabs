import re
import os
import aiohttp

BASE_PATTERNS = [
    r"\bn[i1!|]gg[e3]r",
    r"\bf[a@4]gg?[o0]t",
    r"\bk[i1!]ll?\s*(your|ur)\s*self",
    r"\bkys\b",
    r"\br[a@4]pe\b",
]

LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s", "!": "i", "|": "l",
})


def normalize_text(text: str) -> str:
    text = text.lower().translate(LEET_MAP)
    text = re.sub(r"[.\-_*]+", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def compile_blacklist(user_patterns: list[str] | None = None) -> re.Pattern | None:
    patterns = list(BASE_PATTERNS)
    if user_patterns:
        patterns.extend(user_patterns)
    if not patterns:
        return None
    combined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(combined, re.IGNORECASE)


def blacklist_match(text: str, compiled: re.Pattern | None) -> str | None:
    if compiled is None:
        return None
    normalized = normalize_text(text)
    m = compiled.search(normalized)
    if m:
        return m.group(0)
    m = compiled.search(text)
    if m:
        return m.group(0)
    return None


async def check_perspective_api(text: str, threshold: float = 0.8) -> tuple[bool, float]:
    api_key = os.getenv("PERSPECTIVE_API_KEY")
    if not api_key:
        return False, 0.0

    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={api_key}"
    body = {
        "comment": {"text": text},
        "languages": ["en", "es"],
        "requestedAttributes": {"TOXICITY": {}},
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                if resp.status != 200:
                    return False, 0.0
                data = await resp.json()
                score = data["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
                return score >= threshold, score
    except Exception:
        return False, 0.0
