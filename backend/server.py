from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import subprocess
from datetime import datetime
import requests


# =========================================================
# JARVIS V7 HYBRID AI CORE
# =========================================================

HOST = "127.0.0.1"
PORT = 8082

MEMORY_FILE = "jarvis_memory.json"

LLAMA_CLI = os.path.expanduser(
    "~/Jarvis/local-ai/llama.cpp/build/bin/llama-cli"
)

MODEL_FILE = os.path.expanduser(
    "~/Jarvis/local-ai/models/tinyllama.gguf"
)

OPENAI_API_URL = "https://api.openai.com/v1/responses"

# Cost-sensitive OpenAI model
OPENAI_MODEL = "gpt-5.6-luna"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

MAX_CONTEXT = 6
conversation = []


# =========================================================
# MEMORY
# =========================================================

def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, dict):
                    return data

    except Exception as e:
        print("MEMORY ERROR:", e)

    return {}


memory = load_memory()


def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(
                memory,
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception as e:
        print("SAVE MEMORY ERROR:", e)


# =========================================================
# CONVERSATION MEMORY
# =========================================================

def remember_conversation(user, reply):

    conversation.append({
        "user": user,
        "assistant": reply
    })

    if len(conversation) > MAX_CONTEXT:
        del conversation[:-MAX_CONTEXT]


def get_name():
    return memory.get("name")


# =========================================================
# REMEMBER USER NAME
# =========================================================

def remember_name(command):

    lower = command.lower()

    if "my name is" not in lower:
        return None

    name = command[
        lower.find("my name is") +
        len("my name is"):
    ].strip()

    if not name:
        return None

    name = name[:50]

    memory["name"] = name.title()

    save_memory()

    return f"Nice to meet you, {memory['name']}."


# =========================================================
# SPECIAL JARVIS COMMANDS
# =========================================================

def special_command(command):

    lower = command.lower().strip()

    # -----------------------------------------------------
    # HELLO
    # -----------------------------------------------------

    if lower in [
        "hello",
        "hi",
        "hey",
        "hello jarvis",
        "hi jarvis",
        "hey jarvis",
        "hello rakib",
        "hi rakib",
        "hey rakib"
    ]:

        if get_name():
            return f"Hello {get_name()}."

        return "Hello. I am RAKIB. How can I help?"

    # -----------------------------------------------------
    # USER NAME
    # -----------------------------------------------------

    if "what is my name" in lower:

        if get_name():
            return f"Your name is {get_name()}."

        return "I do not know your name yet."

    # -----------------------------------------------------
    # JARVIS IDENTITY
    # -----------------------------------------------------

    if (
        "what is your name" in lower
        or "what's your name" in lower
        or "who are you" in lower
        or "what are you" in lower
    ):

        return (
            "My name is RAKIB. "
            "I am your AI personal assistant."
        )

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    if (
        "what time" in lower
        or lower == "time"
    ):

        now = datetime.now().strftime("%I:%M %p")

        return f"The current time is {now}."

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    if (
        "what is the date" in lower
        or lower == "date"
        or "today's date" in lower
    ):

        today = datetime.now().strftime(
            "%A, %d %B %Y"
        )

        return f"Today's date is {today}."

    # -----------------------------------------------------
    # DIAGNOSTICS
    # -----------------------------------------------------

    if (
        "run diagnostics" in lower
        or lower == "diagnostics"
    ):

        online = bool(OPENAI_API_KEY)

        return (
            "JARVIS diagnostics complete. "
            "Backend online. "
            "Memory online. "
            "TinyLlama local AI ready. "
            + (
                "Online AI configured."
                if online
                else
                "Online AI key not configured."
            )
        )

    return None


# =========================================================
# BUILD AI CONTEXT
# =========================================================

def build_context():

    messages = []

    for item in conversation[-MAX_CONTEXT:]:

        messages.append({
            "role": "user",
            "content": item["user"]
        })

        messages.append({
            "role": "assistant",
            "content": item["assistant"]
        })

    return messages


# =========================================================
# ONLINE AI
# =========================================================

def ask_online_ai(command, attachment=None):

    if not OPENAI_API_KEY:
        return None

    name = get_name() or "the user"

    system_prompt = (
        "You are JARVIS, a helpful AI personal assistant. "
        f"The user's name is {name}. "
        "Answer naturally, accurately and clearly. "
        "Be concise unless the user asks for detail. "
        "Use the conversation context when useful. "
        "Do not claim to have performed actions that you "
        "cannot actually perform."
    )

    input_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    input_messages.extend(build_context())

    if attachment:
        attachment_name = str(
            attachment.get("name", "attachment")
        )
        attachment_type = str(
            attachment.get("type", "")
        )
        attachment_data = attachment.get("data", "")

        if not attachment_data:
            return "I received the attachment, but its data was empty."

        # Keep uploads reasonably small for the Android/Termux setup.
        if len(attachment_data) > 16 * 1024 * 1024:
            return "That attachment is too large. Please choose a smaller file."

        if attachment_type.startswith("image/"):
            user_content = [
                {
                    "type": "input_text",
                    "text": command or "Analyze this image and answer my question."
                },
                {
                    "type": "input_image",
                    "image_url": attachment_data
                }
            ]

        else:
            user_content = [
                {
                    "type": "input_text",
                    "text": command or "Read this file and answer my question."
                },
                {
                    "type": "input_file",
                    "filename": attachment_name,
                    "file_data": attachment_data
                }
            ]

        input_messages.append({
            "role": "user",
            "content": user_content
        })

    else:
        input_messages.append({
            "role": "user",
            "content": command
        })

    payload = {
        "model": OPENAI_MODEL,
        "input": input_messages,
        "max_output_tokens": 250
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            OPENAI_API_URL,
            headers=headers,
            json=payload,
            timeout=45
        )

        print(
            "ONLINE AI STATUS:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "ONLINE AI ERROR:",
                response.text[:1000]
            )

            return None

        data = response.json()

        # Responses API convenience field
        text = data.get("output_text")

        if text:
            return text.strip()[:3000]

        # Fallback parser
        output = data.get("output", [])

        parts = []

        for item in output:

            if item.get("type") != "message":
                continue

            for content in item.get("content", []):

                if content.get("type") == "output_text":

                    text_part = content.get(
                        "text",
                        ""
                    )

                    if text_part:
                        parts.append(text_part)

        reply = "\n".join(parts).strip()

        if reply:
            return reply[:3000]

        print("ONLINE AI ERROR: Empty response")

        return None

    except requests.Timeout:

        print("ONLINE AI ERROR: Request timed out")

        return None

    except Exception as e:

        print(
            "ONLINE AI EXCEPTION:",
            e
        )

        return None


# =========================================================
# LOCAL TINYLLAMA FALLBACK
# =========================================================

def ask_local_ai(command):

    name = get_name() or "the user"

    context_text = ""

    for item in conversation[-4:]:
        context_text += (
            "\nUser: " +
            item["user"] +
            "\nRAKIB: " +
            item["assistant"]
        )

    prompt = (
        "<|system|>\n"
        "You are RAKIB, a helpful personal AI assistant. "
        f"The user's name is {name}. "
        "Answer clearly and briefly."
        "\nPrevious conversation:"
        + context_text +
        "\n<|user|>\n"
        + command +
        "\n<|assistant|>\n"
    )

    try:

        result = subprocess.run(
            [
                LLAMA_CLI,
                "-m",
                MODEL_FILE,
                "--chat-template",
                "chatml",
                "--single-turn",
                "--no-display-prompt",
                "--simple-io",
                "--log-disable",
                "-c",
                "1024",
                "-n",
                "120",
                "-t",
                "2",
                "-p",
                prompt
            ],
            capture_output=True,
            text=True,
            timeout=180
        )

        # llama-cli normally puts generated text in stdout.
        # stderr contains loading/performance diagnostics.
        output = (result.stdout or "").strip()

        if not output:
            output = (result.stderr or "").strip()

        # Remove prompt/template markers if present.
        if "<|assistant|>" in output:
            output = output.rsplit("<|assistant|>", 1)[-1]

        # Remove llama-cli performance/debug output.
        for marker in (
            "[ Prompt:",
            "[ Generation:",
            "llama_perf_",
            "llama_print_timings:"
        ):
            if marker in output:
                output = output.split(marker, 1)[0]

        lines = []

        for line in output.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith("llama_"):
                continue

            if line.startswith("Loading model"):
                continue

            if line.startswith("build"):
                continue

            if line.startswith("model"):
                continue

            if line.startswith("ftype"):
                continue

            if line.startswith("modalities"):
                continue

            if line.startswith("available commands"):
                continue

            if line.startswith("/exit"):
                continue

            if line.startswith("/regen"):
                continue

            if line.startswith("/clear"):
                continue

            if line.startswith("/read"):
                continue

            if line.startswith("/glob"):
                continue

            if line == ">":
                continue

            lines.append(line)

        reply = " ".join(lines).strip()

        if not reply:
            return "My local AI brain generated an empty response."

        return reply[:1500]

    except subprocess.TimeoutExpired:

        return (
            "My local AI brain took too long "
            "to respond."
        )

    except Exception as e:

        print("LOCAL AI ERROR:", e)

        return (
            "I encountered a problem while "
            "accessing my local AI brain."
        )


# =========================================================
# MASTER JARVIS CORE
# =========================================================

def jarvis_core(command, attachment=None):

    command = command.strip()

    if not command and attachment:
        command = "Please analyze the attached content."

    if not command:
        return "I did not receive a command."

    # Attachments require the online AI vision/file-input path.
    if attachment:
        online_reply = ask_online_ai(
            command,
            attachment
        )

        if online_reply:
            remember_conversation(
                command,
                online_reply
            )

            return online_reply

        return (
            "I could not analyze that attachment. "
            "Please check that Online AI is configured "
            "and try again."
        )

    # -----------------------------------------------------
    # REMEMBER NAME
    # -----------------------------------------------------

    name_reply = remember_name(command)

    if name_reply:

        remember_conversation(
            command,
            name_reply
        )

        return name_reply

    # -----------------------------------------------------
    # SPECIAL COMMANDS
    # -----------------------------------------------------

    command_reply = special_command(command)

    if command_reply:

        remember_conversation(
            command,
            command_reply
        )

        return command_reply

    # -----------------------------------------------------
    # ONLINE AI FIRST
    # -----------------------------------------------------

    online_reply = ask_online_ai(command)

    if online_reply:

        remember_conversation(
            command,
            online_reply
        )

        return online_reply

    # -----------------------------------------------------
    # LOCAL FALLBACK
    # -----------------------------------------------------

    print(
        "ONLINE AI unavailable -> "
        "using TinyLlama fallback"
    )

    local_reply = ask_local_ai(command)

    remember_conversation(
        command,
        local_reply
    )

    return local_reply


# =========================================================
# HTTP SERVER
# =========================================================

class JarvisHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):

        print(
            "[JARVIS]",
            fmt % args
        )

    def send_json(
        self,
        data,
        status=200
    ):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
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
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

    def do_GET(self):

        if self.path == "/":

            self.send_json({

                "status": "online",

                "assistant": "JARVIS",

                "brain": "v7-hybrid-ai",

                "online_ai": bool(
                    OPENAI_API_KEY
                ),

                "local_ai": os.path.exists(
                    LLAMA_CLI
                ),

                "memory": memory,

                "context_messages":
                    len(conversation),

                "message":
                    "JARVIS V7 Hybrid AI Core is online."

            })

            return

        self.send_json({

            "status": "error",

            "message": "Not found"

        }, 404)

    def do_POST(self):

        if self.path != "/ask":

            self.send_json({

                "status": "error",

                "reply":
                    "Endpoint not found."

            }, 404)

            return

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            raw_body = self.rfile.read(
                length
            )

            data = json.loads(
                raw_body.decode("utf-8")
            )

            command = str(
                data.get(
                    "command",
                    ""
                )
            ).strip()

            attachment = data.get("attachment")

            if attachment is not None and not isinstance(
                attachment,
                dict
            ):
                attachment = None

            if not command and not attachment:

                self.send_json({

                    "status": "error",

                    "reply":
                        "I did not receive a command."

                }, 400)

                return

            reply = jarvis_core(
                command,
                attachment
            )

            self.send_json({

                "status": "success",

                "reply": reply,

                "assistant": "JARVIS",

                "brain": "v7-hybrid-ai",

                "memory": memory,

                "online_ai":
                    bool(OPENAI_API_KEY),

                "local_ai": True,

                "context_messages":
                    len(conversation)

            })

        except Exception as e:

            print(
                "SERVER ERROR:",
                e
            )

            self.send_json({

                "status": "error",

                "reply":
                    "JARVIS encountered a server error."

            }, 500)


# =========================================================
# STARTUP
# =========================================================

print()
print("========================================")
print(" JARVIS V7 HYBRID AI CORE")
print("========================================")
print(
    " Memory:",
    "LOADED" if memory else "EMPTY"
)
print(
    " Online AI:",
    "CONFIGURED"
    if OPENAI_API_KEY
    else "NOT CONFIGURED"
)
print(
    " Online Model:",
    OPENAI_MODEL
)
print(
    " Local AI:",
    "TinyLlama"
)
print(
    " Model:",
    MODEL_FILE
)
print(
    " Running on:"
)
print(
    f" http://{HOST}:{PORT}"
)
print("========================================")


server = HTTPServer(
    (HOST, PORT),
    JarvisHandler
)


try:

    server.serve_forever()

except KeyboardInterrupt:

    print(
        "\nJARVIS shutting down..."
    )

finally:

    server.server_close()

