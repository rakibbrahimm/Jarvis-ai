import re


def _clean(text):
    text = re.sub(r"<.*?>", "", str(text))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def answer_from_results(question, raw):
    """
    Turns raw retrieval output into a readable answer.
    This is a deterministic fallback; a real LLM can provide
    deeper reasoning when an AI provider is available.
    """

    if not raw:
        return None

    text = _clean(raw)

    if not text:
        return None

    # Remove internal labels.
    text = re.sub(
        r"^(Wikipedia knowledge|Web research results):\s*",
        "",
        text,
        flags=re.I,
    )

    parts = re.split(
        r"\s+(?=[A-Z][^:]{1,100}: )",
        text,
    )

    useful = []

    for part in parts:
        part = part.strip(" -")

        if len(part) < 20:
            continue

        if part not in useful:
            useful.append(part)

    if not useful:
        return (
            "I found information related to your question:\n"
            + text
        )

    # Keep the response readable instead of dumping a large page.
    useful = useful[:4]

    lines = [
        "Based on the available information:"
    ]

    for item in useful:
        lines.append("• " + item)

    return "\n".join(lines)


def answer_memory(question, context):
    """
    Handles simple personal-context questions locally.
    """

    if not context:
        return None

    q = question.lower().strip()

    # Look for a recent explicit name statement.
    name = None

    for item in reversed(context):
        if item.get("role") != "user":
            continue

        text = str(item.get("content", "")).strip()

        match = re.search(
            r"\bmy name is\s+([A-Za-z][A-Za-z0-9 _-]{1,40})",
            text,
            flags=re.I,
        )

        if match:
            name = match.group(1).strip()
            break

        match = re.search(
            r"\bcall me\s+([A-Za-z][A-Za-z0-9 _-]{1,40})",
            text,
            flags=re.I,
        )

        if match:
            name = match.group(1).strip()
            break

    if name and re.search(
        r"\b(what(?:'s| is) my name|who am i)\b",
        q,
    ):
        return f"Your name is {name}."

    return None


def improve_answer(question, raw, context=None):
    memory = answer_memory(
        question,
        context or [],
    )

    if memory:
        return memory, "rakib-memory"

    answer = answer_from_results(
        question,
        raw,
    )

    if answer:
        return answer, "rakib-answer-engine"

    return None, None
