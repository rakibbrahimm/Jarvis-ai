import ast
import datetime
import math
import operator
import re
import urllib.parse
import urllib.request
import json
import html


# ============================================================
# SAFE CALCULATOR
# ============================================================

_ALLOWED_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _calc_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("invalid number")

    if isinstance(node, ast.BinOp):
        op = type(node.op)

        if op not in _ALLOWED_BIN:
            raise ValueError("operator not allowed")

        left = _calc_node(node.left)
        right = _calc_node(node.right)

        if op is ast.Pow and abs(right) > 100:
            raise ValueError("power too large")

        return _ALLOWED_BIN[op](left, right)

    if isinstance(node, ast.UnaryOp):
        op = type(node.op)

        if op not in _ALLOWED_UNARY:
            raise ValueError("operator not allowed")

        return _ALLOWED_UNARY[op](_calc_node(node.operand))

    raise ValueError("unsupported expression")


def calculator(command):
    c = command.strip()

    if not re.search(r"\d", c):
        return None

    expr = c.lower()

    expr = expr.replace("×", "*")
    expr = expr.replace("÷", "/")
    expr = expr.replace("^", "**")

    expr = re.sub(r"\bcalculate\b", "", expr)
    expr = re.sub(r"\bwhat is\b", "", expr)
    expr = re.sub(r"\bcompute\b", "", expr)
    expr = expr.strip()

    if not re.fullmatch(r"[0-9+\-*/().%\s*]+", expr):
        return None

    try:
        tree = ast.parse(expr, mode="eval")
        value = _calc_node(tree.body)

        if isinstance(value, float):
            if value.is_integer():
                value = int(value)
            else:
                value = round(value, 10)

        return f"Result: {value}"

    except Exception:
        return None


# ============================================================
# TIME / DATE
# ============================================================

def time_tool(command):
    c = command.lower()

    words = [
        "time",
        "current time",
        "what time",
        "time now",
    ]

    if not any(x in c for x in words):
        return None

    now = datetime.datetime.now()

    return "Current local time: " + now.strftime("%I:%M:%S %p")


def date_tool(command):
    c = command.lower()

    words = [
        "today's date",
        "todays date",
        "what date",
        "current date",
        "today",
    ]

    if not any(x in c for x in words):
        return None

    now = datetime.datetime.now()

    return "Today's date: " + now.strftime("%A, %d %B %Y")


# ============================================================
# UNIT CONVERTER
# ============================================================

def conversion_tool(command):
    c = command.lower().strip()

    patterns = [
        (r"(-?\d+(?:\.\d+)?)\s*(km|kilometer|kilometers)\s*(?:to|in)\s*(m|meter|meters)",
         lambda x: f"{x:g} km → {x*1000:g} m"),

        (r"(-?\d+(?:\.\d+)?)\s*(m|meter|meters)\s*(?:to|in)\s*(km|kilometer|kilometers)",
         lambda x: f"{x:g} m → {x/1000:g} km"),

        (r"(-?\d+(?:\.\d+)?)\s*(kg|kilogram|kilograms)\s*(?:to|in)\s*(g|gram|grams)",
         lambda x: f"{x:g} kg → {x*1000:g} g"),

        (r"(-?\d+(?:\.\d+)?)\s*(g|gram|grams)\s*(?:to|in)\s*(kg|kilogram|kilograms)",
         lambda x: f"{x:g} g → {x/1000:g} kg"),

        (r"(-?\d+(?:\.\d+)?)\s*(cm|centimeter|centimeters)\s*(?:to|in)\s*(m|meter|meters)",
         lambda x: f"{x:g} cm → {x/100:g} m"),

        (r"(-?\d+(?:\.\d+)?)\s*(m|meter|meters)\s*(?:to|in)\s*(cm|centimeter|centimeters)",
         lambda x: f"{x:g} m → {x*100:g} cm"),
    ]

    for pattern, formatter in patterns:
        match = re.search(pattern, c)

        if match:
            value = float(match.group(1))
            return formatter(value)

    temp = re.search(
        r"(-?\d+(?:\.\d+)?)\s*(?:°\s*)?(c|celsius)\s*(?:to|in)\s*(f|fahrenheit)",
        c
    )

    if temp:
        value = float(temp.group(1))
        result = value * 9 / 5 + 32
        return f"{value:g} °C → {result:g} °F"

    temp = re.search(
        r"(-?\d+(?:\.\d+)?)\s*(?:°\s*)?(f|fahrenheit)\s*(?:to|in)\s*(c|celsius)",
        c
    )

    if temp:
        value = float(temp.group(1))
        result = (value - 32) * 5 / 9
        return f"{value:g} °F → {result:g} °C"

    return None


# ============================================================
# INTENT DETECTION
# ============================================================

def needs_web(command):
    c = command.lower().strip()

    explicit = (
        "search for ",
        "search ",
        "google ",
        "look up ",
        "find information about ",
        "find info about ",
        "web search ",
    )

    current = (
        "latest ",
        "current ",
        "today ",
        "right now",
        "this week",
        "this month",
        "recent ",
        "news ",
        "who is the current",
        "what happened",
        "what's happening",
        "whats happening",
    )

    knowledge = (
        "who is ",
        "what is ",
        "what are ",
        "where is ",
        "when was ",
        "when did ",
        "why is ",
        "why did ",
        "how does ",
        "tell me about ",
        "explain ",
    )

    return (
        c.startswith(explicit)
        or any(x in c for x in current)
        or any(c.startswith(x) for x in knowledge)
    )


def clean_search_query(command):
    q = command.strip()

    prefixes = [
        "search for ",
        "search ",
        "google ",
        "look up ",
        "web search ",
        "find information about ",
        "find info about ",
    ]

    lower = q.lower()

    for prefix in prefixes:
        if lower.startswith(prefix):
            return q[len(prefix):].strip()

    return q


# ============================================================
# WIKIPEDIA
# ============================================================

def wikipedia_search(query):
    try:
        encoded = urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 3,
        })

        url = "https://en.wikipedia.org/w/api.php?" + encoded

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "RAKIB/2.3"}
        )

        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("query", {}).get("search", [])

        if not results:
            return None

        output = []

        for item in results[:3]:
            title = html.unescape(item.get("title", ""))

            snippet = item.get("snippet", "")
            snippet = re.sub("<.*?>", "", snippet)
            snippet = html.unescape(snippet)

            if title and snippet:
                output.append(f"{title}: {snippet}")

        if output:
            return "Wikipedia knowledge:\n" + "\n".join(output)

    except Exception:
        pass

    return None


# ============================================================
# DUCKDUCKGO WEB SEARCH
# ============================================================

def duckduckgo_search(query):
    try:
        encoded = urllib.parse.urlencode({"q": query})

        url = (
            "https://html.duckduckgo.com/html/?"
            + encoded
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                "Mozilla/5.0 (Android; RAKIB 2.3)"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        blocks = re.findall(
            r'class="result__a".*?>(.*?)</a>.*?'
            r'class="result__snippet".*?>(.*?)</',
            page,
            flags=re.S
        )

        results = []

        for title, snippet in blocks[:5]:
            title = re.sub("<.*?>", "", title)
            snippet = re.sub("<.*?>", "", snippet)

            title = html.unescape(title).strip()
            snippet = html.unescape(snippet).strip()

            if title and snippet:
                results.append(
                    f"{title}: {snippet}"
                )

        if results:
            return (
                "Web research results:\n"
                + "\n".join(results)
            )

    except Exception:
        pass

    return None


def web_tool(command):
    if not needs_web(command):
        return None

    query = clean_search_query(command)

    if not query:
        return None

    # Encyclopedia-style questions first.
    wiki = wikipedia_search(query)

    if wiki:
        return wiki

    # Broader web fallback.
    return duckduckgo_search(query)


# ============================================================
# SYSTEM INFO
# ============================================================

def system_tool(command):
    c = command.lower().strip()

    if c in {
        "help",
        "what can you do",
        "what can you do?",
        "capabilities",
    }:
        return (
            "RAKIB 2.3 capabilities:\n"
            "• General AI provider routing\n"
            "• Web research\n"
            "• Wikipedia knowledge\n"
            "• Calculator\n"
            "• Time and date\n"
            "• Unit conversion\n"
            "• Conversation context\n"
            "• Multi-provider fallback"
        )

    if c in {"who are you", "what are you"}:
        return (
            "I am RAKIB 2.3, a general-purpose AI assistant "
            "with AI providers, web research, tools and context."
        )

    return None


# ============================================================
# TOOL ROUTER
# ============================================================

def run_tools(command):
    # Deterministic tools first.
    for tool in (
        calculator,
        time_tool,
        date_tool,
        conversion_tool,
        system_tool,
    ):
        result = tool(command)

        if result:
            return result, "rakib-tools"

    # Knowledge/current-information layer.
    result = web_tool(command)

    if result:
        return result, "rakib-web"

    return None, None
