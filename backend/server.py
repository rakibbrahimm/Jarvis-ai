import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from rakib_core.router import RAKIBRouter

PORT = 8082
router = RAKIBRouter()

def gpt(command):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None

    try:
        import requests

        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": os.getenv("RAKIB_OPENAI_MODEL", "gpt-5-mini"),
                "input": command,
                "max_output_tokens": 300
            },
            timeout=25
        )

        if r.status_code != 200:
            print("GPT:", r.status_code)
            return None

        data = r.json()

        if isinstance(data.get("output_text"), str):
            return data["output_text"].strip()

        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

    except Exception as e:
        print("GPT ERROR:", e)

    return None

router.register("gpt", gpt)

def local_core(command):
    c = command.lower().strip()

    greetings = {
        "hi", "hello", "hey", "hlo",
        "salam", "assalamualaikum"
    }

    if c in greetings:
        return "Hello! I am RAKIB 2.0. How can I help you?"

    if c in {"who are you", "what are you"}:
        return (
            "I am RAKIB 2.0, a personal AI assistant "
            "with a multi-provider architecture."
        )

    if c in {"status", "system status"}:
        return "RAKIB 2.0 Core is online."

    return (
        "RAKIB Core received your command. "
        "Connect an available AI provider for full AI answers."
    )

router.register("rakib-core", local_core)

class Handler(BaseHTTPRequestHandler):

    def send_json(self, data):
        raw = json.dumps(data).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
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
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            command = str(body.get("command", "")).strip()

            reply, provider = router.ask(command)

            self.send_json({
                "status": "success",
                "reply": reply,
                "provider": provider,
                "assistant": "RAKIB",
                "brain": "RAKIB 2.0"
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
print("       RAKIB 2.0 ONLINE")
print("================================")
print(f"http://127.0.0.1:{PORT}/ask")
print("Providers:", ", ".join(router.providers))
print("================================")

HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
