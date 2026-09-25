import os
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from rakib_core.router import RAKIBRouter
from rakib_core.tools import run_tools
from rakib_core.answer_engine import improve_answer
from rakib_core.intent import detect_intent
from rakib_core.diagnostics import diagnostics


HOST = "127.0.0.1"

def ollama_provider(command):
    """Free local AI provider through Ollama."""
    try:
        import requests

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5:0.5b",
                "prompt": (
                    "You are RAKIB, a helpful school presentation AI assistant. "
                    "Answer clearly, accurately, and briefly. "
                    "If you are unsure, say so instead of inventing facts.\n\n"
                    f"User: {command}\nRAKIB:"
                ),
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 350
                }
            },
            timeout=60,
        )

        if response.status_code != 200:
            print("Ollama ERROR:", response.status_code, response.text[:300])
            return None

        data = response.json()
        text = data.get("response")

        if isinstance(text, str) and text.strip():
            return text.strip()

    except Exception as error:
        print("Ollama ERROR:", error)

    return None

PORT = 8082

router = RAKIBRouter()

# ============================================================
# CONVERSATION MEMORY
# ============================================================

CONTEXT = []
MAX_CONTEXT = 16


def remember(role, content):
    CONTEXT.append({
        "role": role,
        "content": str(content),
    })

    while len(CONTEXT) > MAX_CONTEXT:
        CONTEXT.pop(0)


def build_prompt(command):
    lines = [
        "You are RAKIB, a helpful general-purpose AI assistant.",
        "Understand the user's request before answering.",
        "Use conversation context when relevant.",
        "Do not invent facts.",
        "If information is uncertain, say so.",
        "Give a direct, useful answer.",
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

        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv(
                    "RAKIB_OPENAI_MODEL",
                    "gpt-5-mini",
                ),
                "input": build_prompt(command),
                "max_output_tokens": 900,
            },
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get("error", {}).get("message", "")
            except Exception:
                detail = response.text[:300]
            print(f"OpenAI ERROR {response.status_code}: {detail}")
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
            "gemini-2.5-flash",
        )

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/"
            + model
            + ":generateContent"
        )

        response = requests.post(
            url,
            params={"key": key},
            json={
                "contents": [{
                    "parts": [{
                        "text": build_prompt(command)
                    }]
                }]
            },
            timeout=30,
        )

        if response.status_code != 200:
            print("Gemini:", response.status_code)
            return None

        data = response.json()

        for candidate in data.get("candidates", []):
            for part in candidate.get(
                "content", {}
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

        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv(
                    "RAKIB_PERPLEXITY_MODEL",
                    "sonar",
                ),
                "messages": [{
                    "role": "user",
                    "content": build_prompt(command),
                }],
                "max_tokens": 900,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(
                "Perplexity:",
                response.status_code,
            )
            return None

        data = response.json()
        choices = data.get("choices", [])

        if choices:
            text = choices[0].get(
                "message", {}
            ).get("content")

            if isinstance(text, str) and text.strip():
                return text.strip()

    except Exception as error:
        print("Perplexity ERROR:", error)

    return None


# ============================================================
# LOCAL CORE + ANSWER ENGINE
# ============================================================

def local_core(command):
    c = command.lower().strip()

    if not c:
        return "Tell me what you need."

    if c in {
        "hi",
        "hello",
        "hey",
        "hlo",
        "salam",
        "assalamualaikum",
    }:
        return "Hello! I am RAKIB 3.0. How can I help you?"

    # Memory gets priority for direct memory questions.
    memory_answer, memory_provider = improve_answer(
        command,
        None,
        CONTEXT,
    )

    if memory_answer:
        return memory_answer

    # Deterministic tools + web research.
    tool_result, tool_provider = run_tools(command)

    if tool_result:
        # Turn raw web/Wikipedia output into an answer.
        if tool_provider == "rakib-web":
            answer, provider = improve_answer(
                command,
                tool_result,
                CONTEXT,
            )

            if answer:
                return answer

        return tool_result

    # Last local fallback.
    return (
        "I don't currently have a connected AI model "
        "that can reason through this question. "
        "Connect a working AI provider for full "
        "general-purpose reasoning."
    )


# ============================================================
# PROVIDERS
# ============================================================

router.register(
    "openai",
    openai_provider,
    priority=10,
)

router.register(
    "gemini",
    gemini_provider,
    priority=20,
)

router.register(
    "perplexity",
    perplexity_provider,
    priority=30,
)

router.register(
    "rakib-core",
    local_core,
    priority=1000,
)


# ============================================================
# HTTP
# ============================================================

class Handler(BaseHTTPRequestHandler):

    def _send_json(self, payload, status=200):
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*",
        )

        self.end_headers()

        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*",
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS, GET",
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )

        self.end_headers()

    def do_GET(self):
        if self.path == "/diagnostics":
            payload = diagnostics()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
            return


        if self.path == "/diagnostics":
            payload = diagnostics()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
            return


        if self.path == "/health":
            self._send_json({
                "status": "online",
                "assistant": "RAKIB",
                "brain": "RAKIB 3.0",
            "intent": detect_intent(command),
                "context_messages": len(CONTEXT),
            })
            return

        self._send_json({
            "status": "online",
            "assistant": "RAKIB",
            "brain": "RAKIB 3.0",
            "intent": detect_intent(command),
        })


    def do_POST(self):
        if self.path != "/ask":
            self._send_json({
                "status": "error",
                "reply": "Use POST /ask",
            }, 404)
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
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
                    "brain": "RAKIB 3.0",
            "intent": detect_intent(command),
                }, 400)
                return

            remember("user", command)

            reply, provider = router.ask(command)

            if not reply:
                reply = (
                    "I couldn't produce a reliable answer "
                    "with the currently available systems."
                )

            # Detect local web/memory answer providers.
            if provider == "rakib-core":
                lower = reply.lower()

                if (
                    lower.startswith(
                        "based on the available information:"
                    )
                ):
                    provider = "rakib-answer-engine"

                elif lower.startswith(
                    "your name is"
                ):
                    provider = "rakib-memory"

                elif lower.startswith(
                    "result:"
                ):
                    provider = "rakib-tools"

                elif (
                    "current local time:" in lower
                    or "today's date:" in lower
                ):
                    provider = "rakib-tools"

            remember("assistant", reply)

            self._send_json({
                "status": "success",
                "reply": reply,
                "provider": provider,
                "assistant": "RAKIB",
                "brain": "RAKIB 3.0",
            "intent": detect_intent(command),
                "context_messages": len(CONTEXT),
            })

        except Exception as error:
            print("SERVER ERROR:", error)

            self._send_json({
                "status": "error",
                "reply": "RAKIB encountered an internal error.",
                "provider": "rakib-core",
                "assistant": "RAKIB",
                "brain": "RAKIB 3.0",
            "intent": detect_intent(command),
            }, 500)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print("==============================================")
    print("       RAKIB 3.0 ONLINE")
    print("       ALL-QUESTION ANSWER ENGINE")
    print("==============================================")
    print("http://127.0.0.1:8082/ask")
    print("")
    print("AI:      OpenAI / Gemini / Perplexity")
    print("WEB:     Wikipedia + DuckDuckGo")
    print("TOOLS:   Math / Time / Date / Units")
    print("MEMORY:  Conversation context")
    print("ANSWER:  Retrieval + Answer Engine")
    print("==============================================")

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nRAKIB stopped.")

    finally:
        server.server_close()
