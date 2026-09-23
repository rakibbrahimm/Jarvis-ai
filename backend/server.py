import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from rakib_core.router import RAKIBRouter

PORT = 8082
router = RAKIBRouter()


def openai_provider(command):
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        return None

    try:
        import requests

        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("RAKIB_OPENAI_MODEL", "gpt-5-mini"),
                "input": command,
                "max_output_tokens": 500,
            },
            timeout=30,
        )

        if r.status_code != 200:
            print("OpenAI:", r.status_code)
            return None

        data = r.json()

        text = data.get("output_text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

    except Exception as e:
        print("OpenAI ERROR:", e)

    return None


def gemini_provider(command):
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not key:
        return None

    try:
        import requests

        model = os.getenv(
            "RAKIB_GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + model
            + ":generateContent"
        )

        r = requests.post(
            url,
            params={"key": key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": command}
                        ]
                    }
                ]
            },
            timeout=30,
        )

        if r.status_code != 200:
            print("Gemini:", r.status_code)
            return None

        data = r.json()

        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

    except Exception as e:
        print("Gemini ERROR:", e)

    return None


def perplexity_provider(command):
    key = os.getenv("PERPLEXITY_API_KEY")

    if not key:
        return None

    try:
        import requests

        r = requests.post(
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
                        "content": command
                    }
                ],
                "max_tokens": 500,
            },
            timeout=30,
        )

        if r.status_code != 200:
            print("Perplexity:", r.status_code)
            return None

        data = r.json()

        choices = data.get("choices", [])

        if choices:
            message = choices[0].get("message", {})
            text = message.get("content")

            if isinstance(text, str) and text.strip():
                return text.strip()

    except Exception as e:
        print("Perplexity ERROR:", e)

    return None


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
        return "Hello! I am RAKIB 2.1. How can I help you?"

    if c in {"who are you", "what are you"}:
        return (
            "I am RAKIB 2.1, a multi-provider AI assistant."
        )

    if c in {"status", "system status"}:
        return (
            "RAKIB 2.1 Core is online. "
            f"Providers detected: {len(router.providers)}"
        )

    return (
        "RAKIB received your command. "
        "No external AI provider answered it."
    )


router.register("openai", openai_provider, 10)
router.register("gemini", gemini_provider, 20)
router.register("perplexity", perplexity_provider, 30)
router.register("rakib-core", local_core, 1000)


class Handler(BaseHTTPRequestHandler):

    def send_json(self, data):
        raw = json.dumps(data).encode()

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.send_header(
            "Content-Length",
            str(len(raw))
        )
        self.end_headers()

        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_json({"status": "ok"})

    def do_POST(self):

        if self.path != "/ask":
            self.send_json({
                "status": "error",
                "reply": "Unknown endpoint."
            })
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = json.loads(
                self.rfile.read(length) or b"{}"
            )

            command = str(
                body.get("command", "")
            ).strip()

            reply, provider = router.ask(command)

            self.send_json({
                "status": "success",
                "reply": reply,
                "provider": provider,
                "assistant": "RAKIB",
                "brain": "RAKIB 2.1",
            })

        except Exception as e:

            print("SERVER ERROR:", e)

            self.send_json({
                "status": "error",
                "reply": "RAKIB server error."
            })

    def log_message(self, *args):
        pass


print("================================")
print("        RAKIB 2.1 ONLINE")
print("================================")
print(f"http://127.0.0.1:{PORT}/ask")
print(
    "Providers:",
    ", ".join(
        name for _, name, _ in router.providers
    )
)
print("================================")

HTTPServer(
    ("127.0.0.1", PORT),
    Handler
).serve_forever()
