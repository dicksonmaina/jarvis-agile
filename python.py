#!/usr/bin/env python3
"""
JARVIS Ecosystem CLI for the Poultry Farm Management System.
Supports feed/egg estimates, Groq agent queries, Supabase logging placeholders,
and OpenClaw WhatsApp output when configured.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import logging

# Centralized logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'jarvis.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OPENCLAW_URL = os.getenv("OPENCLAW_URL", "http://127.0.0.1:18789")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
ALERT_PHONE = os.getenv("ALERT_PHONE", "")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── Live Feed / Egg helpers ──────────────────────────────────────────────────
def estimate_feed(birds: int, days: int, feed_per_bird_kg: float = 0.12) -> float:
    return feed_per_bird_kg * birds * days


def daily_egg_target(birds: int, production_rate: float = 0.75) -> int:
    return int(round(birds * production_rate))

# ── OpenClaw alerts ──────────────────────────────────────────────────────────
def is_openclaw_configured() -> bool:
    return bool(OPENCLAW_TOKEN and ALERT_PHONE)


def send_openclaw_message(message: str) -> bool:
    if not is_openclaw_configured():
        print("[OpenClaw] WARNING: OPENCLAW_TOKEN and ALERT_PHONE must be set.")
        return False

    payload = json.dumps({
        "to": ALERT_PHONE,
        "message": message,
    }).encode("utf-8")

    url = OPENCLAW_URL.rstrip("/") + "/api/whatsapp/send"
    request_obj = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENCLAW_TOKEN}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=15) as response:
            body = response.read().decode("utf-8")
            result = json.loads(body or "{}")
            success = result.get("success") or result.get("ok") or False
            if success:
                print("[OpenClaw] Message sent successfully.")
            else:
                print("[OpenClaw] Message was not delivered. Response:", result)
            return bool(success)
    except urllib.error.HTTPError as exc:
        print(f"[OpenClaw] HTTP error: {exc.code} {exc.reason}")
        return False
    except Exception as exc:
        print(f"[OpenClaw] Send failed: {exc}")
        return False


def build_feed_message(birds: int, days: int) -> str:
    total_feed = estimate_feed(birds, days)
    return (
        f"🐔 Poultry Farm Alert:\n"
        f"Feed needed for {birds} birds over {days} days: {total_feed:.1f} kg.\n"
        f"Keep the flock well-fed and the coop on schedule."
    )


def build_egg_message(birds: int, production_rate: float) -> str:
    eggs = daily_egg_target(birds, production_rate)
    return (
        f"🐔 Poultry Farm Alert:\n"
        f"Estimated daily egg target for {birds} birds at {production_rate:.2f} rate: {eggs} eggs.\n"
        f"Keep the hens comfortable and the coop clean."
    )

# ── Groq AI calls (only LLM backend — no local Ollama) ──────────────────────
def call_groq(prompt: str, max_tokens: int = 400) -> str:
    """Call Groq's chat completions API using llama3-8b-8192."""
    if not GROQ_API_KEY:
        return "Groq API is not configured. Set GROQ_API_KEY in your .env file."

    url = GROQ_API_URL.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }).encode("utf-8")

    request_obj = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=30) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body or "{}")
            if isinstance(data, dict):
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    if isinstance(choice, dict):
                        msg = choice.get("message") or {}
                        if isinstance(msg, dict):
                            return msg.get("content", "").strip()
                        return str(choice.get("text", "")).strip()
            return f"[Groq] Unexpected response format: {data}"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return f"[Groq] HTTP {exc.code} ({exc.reason}): {detail[:200]}"
    except Exception as exc:
        return f"[Groq] Request failed: {exc}"

# ── Supabase placeholder ──────────────────────────────────────────────────────
def save_to_supabase(record: dict) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[Supabase] Not configured. Set SUPABASE_URL and SUPABASE_KEY to log records.")
        return False
    print("[Supabase] Placeholder: record would be saved here if Supabase REST support were enabled.")
    print(json.dumps(record, indent=2))
    return False

# ── Config / status ───────────────────────────────────────────────────────────
def show_config() -> None:
    print("\nJARVIS Ecosystem Configuration")
    print("--------------------------------")
    print(f"OpenClaw URL: {OPENCLAW_URL}")
    print(f"OpenClaw configured: {'yes' if is_openclaw_configured() else 'no'}")
    print(f"Alert phone: {ALERT_PHONE or 'not set'}")
    print(f"Groq API configured: {'yes' if GROQ_API_KEY else 'no'}")
    print(f"Groq model: {GROQ_MODEL}")
    print(f"Supabase configured: {'yes' if SUPABASE_URL and SUPABASE_KEY else 'no'}")
    print("\nAvailable commands: feed, eggs, ask, alert-feed, alert-eggs, save, info, quit")

# ── Interactive agent ─────────────────────────────────────────────────────────
def run_agent() -> None:
    print("\n=== JARVIS Poultry Agent ===")
    print("Enter commands to compute feed, egg targets, ask the brain, and send alerts.")
    print("Type 'help' for a list of commands.\n")

    while True:
        command = input("jarvis> ").strip().lower()
        if not command:
            continue
        if command in {"quit", "exit"}:
            print("Stopping JARVIS agent.")
            break
        if command == "help":
            show_config()
            continue
        if command == "info":
            show_config()
            continue
        if command == "feed":
            birds = int(input("Bird count: ").strip() or "0")
            days = int(input("Days: ").strip() or "0")
            message = build_feed_message(birds, days)
            print("\n" + message + "\n")
            if input("Send via OpenClaw? (y/n): ").strip().lower() == "y":
                send_openclaw_message(message)
            continue
        if command == "eggs":
            birds = int(input("Bird count: ").strip() or "0")
            rate = float(input("Production rate (0.75): ").strip() or "0.75")
            message = build_egg_message(birds, rate)
            print("\n" + message + "\n")
            if input("Send via OpenClaw? (y/n): ").strip().lower() == "y":
                send_openclaw_message(message)
            continue
        if command == "ask":
            prompt = input("Ask JARVIS a question: ").strip()
            if not prompt:
                print("Please enter a question.")
                continue
            answer = call_groq(prompt)
            print("\n--- JARVIS Answer ---")
            print(answer)
            print("---------------------\n")
            continue
        if command == "save":
            key = input("Record tag (e.g. feed-alert): ").strip() or "record"
            record = {
                "tag": key,
                "birds": input("Bird count: ").strip(),
                "notes": input("Notes: ").strip(),
            }
            save_to_supabase(record)
            continue
        if command == "alert-feed":
            birds = int(input("Bird count: ").strip() or "0")
            days = int(input("Days: ").strip() or "0")
            message = build_feed_message(birds, days)
            print("\n" + message + "\n")
            send_openclaw_message(message)
            continue
        if command == "alert-eggs":
            birds = int(input("Bird count: ").strip() or "0")
            rate = float(input("Production rate (0.75): ").strip() or "0.75")
            message = build_egg_message(birds, rate)
            print("\n" + message + "\n")
            send_openclaw_message(message)
            continue
        print(f"Unknown command: {command}. Type 'help' or 'info'.")

# ── CLI args ─────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JARVIS Poultry Farm helper")
    parser.add_argument("--feed", nargs=2, metavar=("BIRDS", "DAYS"), help="Estimate feed quantity")
    parser.add_argument("--eggs", nargs=1, metavar="BIRDS", help="Estimate daily egg target")
    parser.add_argument("--rate", type=float, default=0.75, help="Production rate for egg estimate")
    parser.add_argument("--alert-feed", nargs=2, metavar=("BIRDS", "DAYS"), help="Build and send a feed alert via OpenClaw")
    parser.add_argument("--alert-eggs", nargs=1, metavar="BIRDS", help="Build and send an egg alert via OpenClaw")
    parser.add_argument("--ask", nargs="+", help="Ask the Groq brain a question")
    parser.add_argument("--agent", action="store_true", help="Run the interactive JARVIS agent")
    parser.add_argument("--info", action="store_true", help="Show configuration and connection status")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.info:
        show_config()
        return 0

    if args.feed:
        birds = int(args.feed[0])
        days = int(args.feed[1])
        print(f"Total feed needed: {estimate_feed(birds, days):.1f} kg")
        return 0

    if args.eggs:
        birds = int(args.eggs[0])
        print(f"Estimated daily egg target: {daily_egg_target(birds, args.rate)} eggs")
        return 0

    if args.alert_feed:
        birds = int(args.alert_feed[0])
        days = int(args.alert_feed[1])
        message = build_feed_message(birds, days)
        print(message)
        send_openclaw_message(message)
        return 0

    if args.alert_eggs:
        birds = int(args.alert_eggs[0])
        message = build_egg_message(birds, args.rate)
        print(message)
        send_openclaw_message(message)
        return 0

    if args.ask:
        prompt = " ".join(args.ask)
        answer = call_groq(prompt)
        print(answer)
        return 0

    if args.agent:
        run_agent()
        return 0

    print("Use --help for available commands. Run with --agent to start the JARVIS agent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
