import re


def detect_intent(command):
    q = command.lower().strip()

    if re.fullmatch(r"[0-9+\-*/().% \t]+", q):
        return "math"

    if re.search(r"\b(what time|current time|time now)\b", q):
        return "time"

    if re.search(r"\b(today'?s date|what date|current date|date today)\b", q):
        return "date"

    if re.search(
        r"\b(latest|today|recent|currently|current|news|breaking|"
        r"this week|this month|right now)\b",
        q,
    ):
        return "web"

    if re.search(
        r"\b(convert|conversion|how many)\b", q
    ):
        return "conversion"

    if re.search(
        r"^(who|what|where|when|why|how|explain|define|tell me)\b",
        q,
    ):
        return "knowledge"

    return "general"
