#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/Jarvis/backend"

echo "=============================================="
echo "       RAKIB 4.0 SCHOOL MODE"
echo "       ZERO API CREDITS"
echo "=============================================="

if command -v llama-server >/dev/null 2>&1; then
    echo "✅ Local AI runtime: READY"
else
    echo "⚠️ Local AI runtime: NOT INSTALLED"
fi

MODEL=""
for f in "$HOME/Jarvis/local-ai"/*.gguf "$HOME/Jarvis/models"/*.gguf; do
    if [ -f "$f" ]; then
        MODEL="$f"
        break
    fi
done

if [ -n "$MODEL" ]; then
    echo "✅ Local model: FOUND"
    echo "   $MODEL"
else
    echo "⚠️ Local model: NOT FOUND"
fi

echo
echo "Starting RAKIB backend..."
python server.py
