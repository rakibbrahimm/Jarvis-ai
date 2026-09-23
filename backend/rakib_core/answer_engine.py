import re


def _clean_text(text):
    if not text:
        return ""

    text = str(text)

    # Remove common wrappers
    text = re.sub(
        r"^(Wikipedia knowledge|Web research results):\s*",
        "",
        text,
        flags=re.I,
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _split_results(raw):
    """
    Convert raw search output into individual result blocks.
    Supports the current RAKIB Wikipedia / web formats.
    """
    text = _clean_text(raw)

    if not text:
        return []

    # Existing result formatting often separates results by title:
    # Title: snippet
    parts = re.split(
        r"\s+(?=[A-Z][^:]{1,100}:\s)",
        text,
    )

    results = []

    for part in parts:
        part = part.strip(" -\n\t")

        if len(part) < 25:
            continue

        if part not in results:
            results.append(part)

    return results


def _title_and_body(item):
    """
    Split 'Title: body' while keeping useful text intact.
    """
    match = re.match(
        r"^([^:]{2,120}):\s*(.+)$",
        item,
        flags=re.S,
    )

    if not match:
        return "", item.strip()

    title = match.group(1).strip()
    body = match.group(2).strip()

    return title, body


def _sentences(text):
    """
    Extract complete-looking sentences and discard obvious
    truncated search fragments.
    """
    pieces = re.split(r"(?<=[.!?])\s+", text)

    good = []

    for sentence in pieces:
        sentence = sentence.strip()

        if len(sentence) < 35:
            continue

        # Search snippets frequently end mid-word or mid-thought.
        if sentence.endswith((
            "such as",
            "including",
            "across virtually",
            "primarily",
            "different",
            "and",
            "or",
            "the",
            "of",
            "to",
        )):
            continue

        if sentence not in good:
            good.append(sentence)

    return good


def _similar(a, b):
    """
    Lightweight duplicate detection without external packages.
    """
    wa = set(re.findall(r"[a-z0-9]+", a.lower()))
    wb = set(re.findall(r"[a-z0-9]+", b.lower()))

    if not wa or not wb:
        return False

    overlap = len(wa & wb) / max(1, min(len(wa), len(wb)))

    return overlap >= 0.72


def answer_from_results(question, raw):
    if not raw:
        return None

    results = _split_results(raw)

    if not results:
        return None

    selected = []
    seen_titles = set()

    for item in results[:10]:
        title, body = _title_and_body(item)

        sentences = _sentences(body)

        if not sentences:
            continue

        # Prefer the first useful complete sentence.
        sentence = sentences[0]

        duplicate = False

        for old in selected:
            if _similar(sentence, old["text"]):
                duplicate = True
                break

        if duplicate:
            continue

        key = title.lower()

        if key and key in seen_titles:
            continue

        if key:
            seen_titles.add(key)

        selected.append({
            "title": title,
            "text": sentence,
        })

        if len(selected) >= 4:
            break

    if not selected:
        return (
            "I found information related to your question, "
            "but the available search results were incomplete."
        )

    # --------------------------------------------------------
    # Lightweight fusion
    # --------------------------------------------------------
    question_lower = question.lower()

    # Build a concise answer from the strongest result.
    primary = selected[0]["text"]

    lines = [
        primary
    ]

    # Add complementary information only when it is genuinely
    # different from the primary result.
    for item in selected[1:]:
        if not _similar(primary, item["text"]):
            lines.append(item["text"])

        if len(lines) >= 3:
            break

    answer = " ".join(lines)

    # Clean accidental duplicate spaces.
    answer = re.sub(r"\s+", " ", answer).strip()

    # Source list
    sources = []
    for item in selected:
        if item["title"]:
            sources.append(item["title"])

    if sources:
        answer += "\n\nSources: " + " • ".join(sources[:4])

    return answer


def answer_memory(question, context):
    if not context:
        return None

    q = question.lower().strip()

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
            name = match.group(1).strip().rstrip(".,!?")
            break

        match = re.search(
            r"\bcall me\s+([A-Za-z][A-Za-z0-9 _-]{1,40})",
            text,
            flags=re.I,
        )

        if match:
            name = match.group(1).strip().rstrip(".,!?")
            break

    if name and re.search(
        r"\b(what(?:'s| is) my name|who am i)\b",
        q,
    ):
        return f"Your name is {name}."

    return None


def improve_answer(question, raw=None, context=None):
    """
    Main Answer Fusion entry point.
    """

    memory = answer_memory(question, context)

    if memory:
        return memory, "rakib-memory"

    fused = answer_from_results(question, raw)

    if fused:
        return fused, "rakib-answer-engine"

    return None, None
