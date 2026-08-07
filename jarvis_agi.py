#!/usr/bin/env python3
"""
JARVIS AGI Service — Port 5052
Poultry Farm AI Assistant
Provider chain: NVIDIA NIM → DeepSeek → Groq
"""
from dotenv import load_dotenv

# Load .env from project root (/home/riziki/.env)
load_dotenv("/home/riziki/.env")

from flask import Flask, request, jsonify
import requests, json, os, psutil, datetime

app = Flask(__name__)

# ── NVIDIA NIM (Primary) ────────────────────────────────────────────────────
NVIDIA_KEY      = os.environ.get("NVIDIA_NIM_API_KEY", "")
NVIDIA_CHAT_URL = os.environ.get("NVIDIA_NIM_API_URL",
                                 "https://integrate.api.nvidia.com/v1/chat/completions")
# Health-check root: strip /v1/chat/completions or /v1/chat (OpenAI-style) to get /v1
_raw_root  = NVIDIA_CHAT_URL.replace("/chat/completions", "").replace("/chat", "")
NVIDIA_ROOT = _raw_root.rstrip("/") if _raw_root else "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct")

# ── DeepSeek (Fallback 1) ────────────────────────────────────────────────────
DEEPSEEK_KEY  = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL  = os.environ.get("DEEPSEEK_API_URL",
                               "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# ── Groq (Fallback 2) ────────────────────────────────────────────────────────
GROQ_KEY   = os.environ.get("GROQ_API_KEY", "")
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

MAX_TOKENS  = int(os.environ.get("MAX_TOKENS", "1024"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.7"))
USE_FALLBACK = os.environ.get("USE_FALLBACK", "true").lower() in ("1", "true", "yes")

SYSTEM_PROMPT = """You are JARVIS AGI, an expert poultry farm management assistant for Richard's farm in Nairobi, Kenya.
You help with: flock analysis, egg production predictions, feed optimization, FCR calculations, mortality analysis, and farm management.
Be concise, practical, and use KSH for currency. Always give actionable advice."""


def _chat_completion(url: str, api_key: str, model: str, prompt: str, req_timeout: int = 90) -> str:
    """Generic OpenAI-format chat completion call."""
    if not api_key:
        return f"JARVIS AGI: API key not configured for {model}."
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={"model": model, "messages":
                  [{"role": "system", "content": SYSTEM_PROMPT},
                   {"role": "user", "content": prompt}],
                  "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE},
            timeout=req_timeout,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        snippet = r.text[:200]
        return f"{model} error {r.status_code}: {snippet}"
    except requests.exceptions.Timeout:
        return f"{model} error: request timed out after {req_timeout}s"
    except Exception as e:
        return f"JARVIS AGI {model} error: {str(e)}"


def ask_nvidia_nim(prompt: str) -> str:
    """Call NVIDIA NIM — primary backend. Needs longer timeout for complex queries."""
    return _chat_completion(NVIDIA_CHAT_URL, NVIDIA_KEY, NVIDIA_MODEL, prompt, req_timeout=90)


def ask_deepseek(prompt: str) -> str:
    """Call DeepSeek — first fallback."""
    return _chat_completion(DEEPSEEK_URL, DEEPSEEK_KEY, DEEPSEEK_MODEL, prompt)


def ask_groq(prompt: str) -> str:
    """Call Groq — second fallback."""
    return _chat_completion(GROQ_URL, GROQ_KEY, GROQ_MODEL, prompt)


def ask_llm(prompt: str):
    """
    Provider fallback chain:
      1. NVIDIA NIM  (primary)
      2. DeepSeek    (fallback 1)
      3. Groq        (fallback 2)
      Returns (response_text, backend_used)
    """
    response = ask_nvidia_nim(prompt)
    backend  = "nvidia_nim"

    if response.startswith(("JARVIS AGI", NVIDIA_MODEL)):
        response = ask_deepseek(prompt)
        backend  = "deepseek"
        if response.startswith(("JARVIS AGI", DEEPSEEK_MODEL)) and USE_FALLBACK:
            response = ask_groq(prompt)
            backend  = "groq"

    return response, backend


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service":      "JARVIS AGI",
        "status":       "online",
        "port":         5052,
        "version":      "2.2.0",
        "provider_chain": {
            "primary":    NVIDIA_MODEL      if NVIDIA_KEY  else "none",
            "fallback_1": DEEPSEEK_MODEL    if DEEPSEEK_KEY else "none",
            "fallback_2": GROQ_MODEL        if GROQ_KEY    else "none",
        },
    })


@app.route("/health", methods=["GET"])
def health():
    nim_up = groq_up = ds_up = False

    if NVIDIA_KEY:
        try:
            r = requests.get(f"{NVIDIA_ROOT}/models", timeout=3)
            nim_up = r.status_code == 200
        except Exception:
            pass
    if DEEPSEEK_KEY:
        try:    ds_up  = requests.get("https://api.deepseek.com", timeout=3).status_code == 200
        except: pass
    if GROQ_KEY:
        try:    groq_up = requests.get("https://api.groq.com", timeout=3).status_code < 500
        except: pass

    return jsonify({
        "status":                 "ok",
        "service":                "jarvis-agi",
        "port":                   5052,
        "nvidia_nim_connected":    NVIDIA_KEY  and nim_up,
        "deepseek_connected":      DEEPSEEK_KEY and ds_up,
        "groq_connected":          GROQ_KEY    and groq_up,
        "primary_backend":         "nvidia_nim" if NVIDIA_KEY else "none",
        "fallback_1_backend":      "deepseek"  if DEEPSEEK_KEY else "none",
        "fallback_2_backend":      "groq"      if GROQ_KEY else "none",
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        response, backend = ask_llm(message)
        return jsonify({
            "response":      response,
            "backend":       backend,
            "primary_api":   "nvidia_nim",
            "fallback_1_api":"deepseek",
            "fallback_2_api":"groq",
            "timestamp":     datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/stats", methods=["GET"])
def stats():
    cpu  = psutil.cpu_percent(interval=1)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return jsonify({
        "cpu_percent":        cpu,
        "ram_used_mb":        round(ram.used   / 1024 / 1024),
        "ram_total_mb":       round(ram.total  / 1024 / 1024),
        "disk_used_gb":       round(disk.used   / 1024 / 1024 / 1024, 1),
        "disk_total_gb":      round(disk.total  / 1024 / 1024 / 1024, 1),
        "uptime":             datetime.datetime.now().isoformat(),
        "nvidia_nim_api_key": bool(NVIDIA_KEY),
        "deepseek_api_key":   bool(DEEPSEEK_KEY),
        "groq_api_key":       bool(GROQ_KEY),
        "primary_backend":    "nvidia_nim",
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    analysis_type = data.get("type", "general")
    farm_data     = data.get("data", {})
    prompt = (
        f"Analyze this farm data ({analysis_type}): {json.dumps(farm_data)}. "
        "Give a brief actionable insight. Use KSH for currency."
    )
    response, backend = ask_llm(prompt)
    return jsonify({"analysis": response, "type": analysis_type, "backend": backend})


if __name__ == "__main__":
    print(f"JARVIS AGI starting on port 5052 "
          f"(primary=nvidia_nim/{NVIDIA_MODEL}, "
          f"fallback_1=deepseek/{DEEPSEEK_MODEL}, "
          f"fallback_2=groq/{GROQ_MODEL})...")
    app.run(host="0.0.0.0", port=5052, debug=False)
