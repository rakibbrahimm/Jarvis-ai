import ast
import datetime
import math
import operator
import re
import urllib.parse
import urllib.request
import json


# ---------- SAFE CALCULATOR ----------

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calc(expression):
    expression = expression.replace("^", "**")
    expression = re.sub(r"(?i)\b(sqrt)\b", "sqrt", expression)

    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError()

        if isinstance(node, ast.BinOp):
            op = OPS.get(type(node.op))
            if not op:
                raise ValueError()
            return op(evaluate(node.left), evaluate(node.right))

        if isinstance(node, ast.UnaryOp):
            op = OPS.get(type(node.op))
            if not op:
                raise ValueError()
            return op(evaluate(node.operand))

        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "sqrt"
                and len(node.args) == 1
            ):
                return math.sqrt(evaluate(node.args[0]))

        raise ValueError()

    result = evaluate(tree.body)

    if isinstance(result, float) and result.is_integer():
        return str(int(result))

    return str(round(result, 10))


def calculator(command):
    c = command.lower().strip()

    prefixes = [
        "calculate ",
        "calc ",
        "what is ",
        "solve ",
    ]

    expression = c

    for prefix in prefixes:
        if expression.startswith(prefix):
            expression = expression[len(prefix):]
            break

    expression = expression.replace("?", "").strip()

    if not re.fullmatch(
        r"[0-9+\-*/().%^ \t]+|sqrt\s*\(\s*[0-9.]+\s*\)",
        expression,
        re.I,
    ):
        return None

    try:
        return "Result: " + safe_calc(expression)
    except Exception:
        return None


# ---------- TIME / DATE ----------

def time_tool(command):
    c = command.lower()

    keywords = [
        "what time",
        "current time",
        "time now",
        "time?",
    ]

    if any(x in c for x in keywords):
        now = datetime.datetime.now().astimezone()
        return "Current local time: " + now.strftime("%I:%M:%S %p")

    return None


def date_tool(command):
    c = command.lower()

    keywords = [
        "what date",
        "today's date",
        "todays date",
        "today date",
        "what day is it",
        "today",
    ]

    if any(x in c for x in keywords):
        now = datetime.datetime.now().astimezone()
        return "Today is " + now.strftime("%A, %d %B %Y")

    return None


# ---------- UNIT CONVERSION ----------

def conversion_tool(command):
    c = command.lower().strip()

    patterns = [
        (
            r"(-?\d+(?:\.\d+)?)\s*(km|kilometers?)\s*(?:to|in)\s*(m|meters?)",
            lambda x: x * 1000,
            "m",
        ),
        (
            r"(-?\d+(?:\.\d+)?)\s*(m|meters?)\s*(?:to|in)\s*(km|kilometers?)",
            lambda x: x / 1000,
            "km",
        ),
        (
            r"(-?\d+(?:\.\d+)?)\s*(kg|kilograms?)\s*(?:to|in)\s*(g|grams?)",
            lambda x: x * 1000,
            "g",
        ),
        (
            r"(-?\d+(?:\.\d+)?)\s*(g|grams?)\s*(?:to|in)\s*(kg|kilograms?)",
            lambda x: x / 1000,
            "kg",
        ),
        (
            r"(-?\d+(?:\.\d+)?)\s*(cm|centimeters?)\s*(?:to|in)\s*(m|meters?)",
            lambda x: x / 100,
            "m",
        ),
        (
            r"(-?\d+(?:\.\d+)?)\s*(m|meters?)\s*(?:to|in)\s*(cm|centimeters?)",
            lambda x: x * 100,
            "cm",
        ),
    ]

    for pattern, func, unit in patterns:
        match = re.fullmatch(pattern, c, re.I)

        if match:
            value = float(match.group(1))
            result = func(value)

            if result.is_integer():
                result = int(result)

            return f"{value:g} → {result} {unit}"

    # Celsius / Fahrenheit
    m = re.fullmatch(
        r"(-?\d+(?:\.\d+)?)\s*(c|°c|celsius)\s*(?:to|in)\s*(f|°f|fahrenheit)",
        c,
        re.I,
    )

    if m:
        value = float(m.group(1))
        result = value * 9 / 5 + 32
        return f"{value:g} °C → {result:g} °F"

    m = re.fullmatch(
        r"(-?\d+(?:\.\d+)?)\s*(f|°f|fahrenheit)\s*(?:to|in)\s*(c|°c|celsius)",
        c,
        re.I,
    )

    if m:
        value = float(m.group(1))
        result = (value - 32) * 5 / 9
        return f"{value:g} °F → {result:g} °C"

    return None


# ---------- WEB SEARCH, NO API KEY ----------

def web_search(command):
    c = command.strip()

    prefixes = [
        "search for ",
        "search ",
        "google ",
        "look up ",
        "find ",
    ]

    query = None

    for prefix in prefixes:
        if c.lower().startswith(prefix):
            query = c[len(prefix):].strip()
            break

    if not query or len(query) < 2:
        return None

    try:
        encoded = urllib.parse.quote_plus(query)

        url = (
            "https://html.duckduckgo.com/html/?q="
            + encoded
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 RAKIB/2.2"
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=8
        ) as response:
            html = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        titles = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            html,
            re.S,
        )

        titles = [
            re.sub("<.*?>", "", x).strip()
            for x in titles[:5]
        ]

        if not titles:
            return "I couldn't retrieve search results right now."

        return (
            "Search results for "
            + query
            + ":\n"
            + "\n".join(
                f"{i+1}. {title}"
                for i, title in enumerate(titles)
            )
        )

    except Exception as e:
        print("WEB SEARCH:", e)
        return (
            "Web search is temporarily unavailable. "
            "The no-key tools are still online."
        )


# ---------- SYSTEM ----------

def system_tool(command):
    c = command.lower().strip()

    if c in {
        "status",
        "system status",
        "rakib status",
    }:
        return (
            "RAKIB 2.2 is online. "
            "No-key tools: calculator, time, date, "
            "unit conversion and web search."
        )

    if c in {
        "help",
        "what can you do",
        "what can you do?",
    }:
        return (
            "I can calculate, convert units, tell the "
            "current time/date, attempt web searches, "
            "and use connected AI providers when available."
        )

    return None


def run_tools(command):
    tools = [
        calculator,
        time_tool,
        date_tool,
        conversion_tool,
        system_tool,
        web_search,
    ]

    for tool in tools:
        try:
            result = tool(command)

            if result:
                return result, tool.__name__

        except Exception as e:
            print(
                f"TOOL {tool.__name__}: {e}"
            )

    return None, None
