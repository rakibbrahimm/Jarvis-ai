import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from rakib_core.router import RAKIBRouter

PORT = 8082
router = RAKIBRouter()

def gpt_provider(command):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "GPT provider is not configured yet."

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
            timeout=30
        )

        if r.status_code != 200:
            print("GPT ERROR:", r.status_code, r.text[:1000])
            return None

        data = r.json()

        text = data.get("output_text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        for item in data.get("output", []):
            for content in item.get("content", []):
                value = content.get("text")
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return None

    except Exception as e:
        print("GPT EXCEPTION:", e)
        return None

router.register("gpt", gpt_provider)

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data):
        raw = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_json({"status": "ok"})

    def do_POST(self):
        if self.path != "/ask":
            self.send_json({"status": "error", "reply": "Unknown endpoint"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            command = str(body.get("command", "")).strip()

            reply, provider = router.ask(command, preferred="gpt")

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

print(f"RAKIB 2.0 ONLINE — http://127.0.0.1:{PORT}/ask")
HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
