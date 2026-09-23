import os
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from rakib_core.router import RAKIBRouter
from rakib_core.tools import run_tools


HOST = "127.0.0.1"
PORT = 8082

router = RAKIBRouter()

# ============================================================
# CONVERSATION MEMORY
# ============================================================

CONTEXT = []
MAX_CONTEXT = 12


def remember(role, content):
    CONTEXT.append({
        "role": role,
        "content": str(content),
    })

    while len(CONTEXT) > MAX_CONTEXT:
        CONTEXT.pop(0)


def build_prompt(command):
    if not CONTEXT:
        return command

    lines = [
        "You are RAKIB, a helpful general-purpose AI assistant.",
        "Use the conversation context when it is relevant.",
        "Answer clearly and directly.",
        "",
        "Conversation context:",
    ]

    for item in CONTEXT:
        lines.append(
            f"{item['role']}: {item['content']}"
        )

    lines.extend([
        "",
        "New user request:",
        command,
    ])

    return "\n".join(lines)


# ============================================================
# OPENAI
# ============================================================

def openai_provider(command):
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        return None

    try:
        import requests

        prompt = build_prompt(command)

        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv(
                    "RAKIB_OPENAI_MODEL",
                    "gpt-5-mini"
                ),
                "input": prompt,
                "max_output_tokens": 700,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(
                "OpenAI:",
                response.status_code
            )
            return None

        data = response.json()

        text = data.get("output_text")

        if isinstance(text, str) and text.strip():
            return text.strip()

        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")

                if isinstance(text, str) and text.strip():
                    return text.strip()

    except Exception as error:
        print("OpenAI ERROR:", error)

    return None


# ============================================================
# GEMINI
# ============================================================

def gemini_provider(command):
    key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )

    if not key:
        return None

    try:
        import requests

        model = os.getenv(
            "RAKIB_GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/"
            + model
            + ":generateContent"
        )

        prompt = build_prompt(command)

        response = requests.post(
            url,
            params={"key": key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(
                "Gemini:",
                response.status_code
            )
            return None

        data = response.json()

        for candidate in data.get(
            "candidates",
            []
        ):
            for part in candidate.get(
                "content",
                {}
            ).get("parts", []):
                text = part.get("text")

                if isinstance(text, str) and text.strip():
                    return text.strip()

    except Exception as error:
        print("Gemini ERROR:", error)

    return None


# ============================================================
# PERPLEXITY
# ============================================================

def perplexity_provider(command):
    key = os.getenv("PERPLEXITY_API_KEY")

    if not key:
        return None

    try:
        import requests

        prompt = build_prompt(command)

        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv(
                    "RAKIB_PERPLEXITY_MODEL",
                    "sonar"
                ),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "max_tokens": 700,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(
                "Perplexity:",
                response.status_code
            )
            return None

        data = response.json()

        choices = data.get("choices", [])

        if choices:
            message = choices[0].get(
                "message",
                {}
            )

            text = message.get("content")

            if isinstance(text, str) and text.strip():
                return text.strip()

    except Exception as error:
        print(
            "Perplexity ERROR:",
            error
        )

    return None


# ============================================================
# LOCAL INTELLIGENCE
# ============================================================

def local_core(command):
    c = command.lower().strip()

    if not c:
        return "Tell me what you need."

    greetings = {
        "hi",
        "hello",
        "hey",
        "hlo",
        "salam",
        "assalamualaikum",
    }

    if c in greetings:
        return (
            "Hello! I am RAKIB 2.3. "
            "How can I help you?"
        )

    tool_result, tool_name = run_tools(command)

    if tool_result:
        return tool_result

    return None


# ============================================================
# PROVIDER REGISTRATION
# ============================================================

router.register(
    "openai",
    openai_provider,
    priority=10
)

router.register(
    "gemini",
    gemini_provider,
    priority=20
)

router.register(
    "perplexity",
    perplexity_provider,
    priority=30
)

router.register(
    "rakib-core",
    local_core,
    priority=1000
)


# ============================================================
# HTTP SERVER
# ============================================================

class Handler(BaseHTTPRequestHandler):

    def _send_json(self, payload, status=200):
        body = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS, GET"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json({
                "status": "online",
                "assistant": "RAKIB",
                "brain": "RAKIB 2.3",
                "context_messages": len(CONTEXT),
            })
            return

        self._send_json({
            "status": "online",
            "assistant": "RAKIB",
            "brain": "RAKIB 2.3",
        })

    def do_POST(self):
        if self.path != "/ask":
            self._send_json({
                "status": "error",
                "message": "Use POST /ask",
            }, 404)
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            raw = self.rfile.read(length)

            data = json.loads(
                raw.decode("utf-8")
            )

            command = str(
                data.get("command", "")
            ).strip()

            if not command:
                self._send_json({
                    "status": "error",
                    "reply": "Tell me what you need.",
                    "provider": "rakib-core",
                    "assistant": "RAKIB",
                    "brain": "RAKIB 2.3",
                }, 400)
                return

            remember(
                "user",
                command
            )

            reply, provider = router.ask(
                command
            )

            if not reply:
                reply = (
                    "I couldn't find a reliable answer "
                    "with the currently available systems."
                )

            remember(
                "assistant",
                reply
            )

            self._send_json({
                "status": "success",
                "reply": reply,
                "provider": provider,
                "assistant": "RAKIB",
                "brain": "RAKIB 2.3",
                "context_messages": len(CONTEXT),
            })

        except Exception as error:
            print("SERVER ERROR:", error)

            self._send_json({
                "status": "error",
                "reply": "RAKIB encountered an internal error.",
                "provider": "rakib-core",
                "assistant": "RAKIB",
                "brain": "RAKIB 2.3",
            }, 500)

    def log_message(self, format, *args):
        return


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    print("==============================================")
    print("       RAKIB 2.3 ONLINE")
    print("       GENERAL INTELLIGENCE CORE")
    print("==============================================")
    print("http://127.0.0.1:8082/ask")
    print("")
    print("AI:      OpenAI / Gemini / Perplexity")
    print("WEB:     DuckDuckGo + Wikipedia")
    print("TOOLS:   Calculator / Time / Date / Units")
    print("MEMORY:  Conversation context")
    print("==============================================")

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nRAKIB stopped.")
    finally:
        server.server_close()
