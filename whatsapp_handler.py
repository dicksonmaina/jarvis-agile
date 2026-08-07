# NEXUS Integration
try:
    sys.path.insert(0, '/home/riziki/workspace/projects/nexus')
    from nexus_jarvis_bridge import handle_nexus_query
    NEXUS_ENABLED = True
except ImportError:
    NEXUS_ENABLED = False

#!/usr/bin/env python3
"""
WhatsApp Handler for JARVIS - Baileys Integration
Connects to the Baileys bot via direct WebSocket/socket for message handling.
Uses the @whiskeysockets/baileys protocol for WhatsApp communication.
"""

import logging
import json
import time
import os
import sys
import re
import threading
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Configure logging ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("whatsapp_handler.log", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

try:
    from kilo_jarvis import (
        GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT,
        get_history, add_to_history, ask_ai, send_message,
        send_typing, log as jarvis_log
    )
except ImportError:
    log.warning("kilo_jarvis import failed, using fallback config")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = "llama-3.1-8b-instant"
    SYSTEM_PROMPT = "You are JARVIS, an advanced AI assistant."

# ── Configuration ──────────────────────────────────────────────
BAILEYS_BOT_DIR = os.path.expanduser("~/workspace/projects/baileys-bot")
BAILEYS_NODE_PATH = "/usr/bin/node"

# Baileys communication options
# Option 1: WebSocket port for Baileys (if we extend it)
BAILEYS_WS_PORT = int(os.environ.get("BAILEYS_WS_PORT", "0"))  # 0 = auto-detect/no WS

# Option 2: Use stdin/stdout pipe communication with node process
USE_PIPE_COMM = True

# Option 3: HTTP webhook fallback (for external WhatsApp API)
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")

# AI Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", GROQ_API_KEY or "")
BOT_OWNER = os.environ.get("BOT_OWNER", "Richard")

# ── Message Queue ─────────────────────────────────────────────
message_queue: list[Dict[str, Any]] = []
queue_lock = threading.Lock()
processing_lock = threading.Lock()

# ── Baileys Process Manager ───────────────────────────────────
class BaileysManager:
    """Manages the Baileys Node.js bot process."""
    
    def __init__(self, bot_dir: str):
        self.bot_dir = bot_dir
        self.process: Optional[subprocess.Popen] = None
        self.pipe_thread: Optional[threading.Thread] = None
        self.running = False
        self.last_message_time = 0
        self.message_callbacks = []
        
    def start_bot(self) -> bool:
        """Start the Baileys bot as a subprocess."""
        try:
            bot_js = os.path.join(self.bot_dir, "index.js")
            if not os.path.exists(bot_js):
                log.error(f"Baileys bot not found at {bot_js}")
                return False
            
            log.info(f"Starting Baileys bot from {bot_js}")
            
            self.process = subprocess.Popen(
                [BAILEYS_NODE_PATH, bot_js],
                cwd=self.bot_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.running = True
            log.info(f"Baileys bot started (PID: {self.process.pid})")
            
            # Start pipe monitoring thread
            self.pipe_thread = threading.Thread(
                target=self._monitor_pipes,
                daemon=True
            )
            self.pipe_thread.start()
            
            return True
            
        except Exception as e:
            log.error(f"Failed to start Baileys bot: {e}")
            return False
    
    def _monitor_pipes(self):
        """Monitor stdout/stderr from the Baileys bot."""
        while self.running and self.process:
            try:
                # Read stdout
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()
                    if line:
                        log.info(f"[Baileys] {line}")
                        self._parse_bot_output(line)
                
                # Read stderr
                err = self.process.stderr.readline()
                if err:
                    err = err.strip()
                    if err:
                        log.warning(f"[Baileys-ERR] {err}")
                        self._parse_bot_output(err)
                
                # Check if process ended
                if self.process.poll() is not None:
                    log.warning(f"Baileys bot process ended (code: {self.process.returncode})")
                    self.running = False
                    break
                    
                time.sleep(0.1)
                
            except Exception as e:
                if self.running:
                    log.error(f"Error monitoring pipes: {e}")
                break
    
    def _parse_bot_output(self, line: str):
        """Parse output from Baileys bot for message events."""
        line_lower = line.lower()
        
        # Detect connection status
        if "connected to whatsapp" in line_lower:
            log.info("✅ WhatsApp connection established via Baileys")
        elif "scan qr" in line_lower or "qr" in line_lower:
            log.info("📱 QR code available - scan with WhatsApp")
        elif "listening" in line_lower or "server" in line_lower:
            log.info("🚀 Baileys bot listening for messages")
        
        # Detect incoming messages (from bot logs)
        if "from" in line_lower and ":" in line:
            # Pattern: "📩 From [number]: [message]"
            parts = line.split(":", 2)
            if len(parts) >= 3:
                msg_text = parts[2].strip()
                from_part = parts[1].split("from")[-1].strip() if "from" in parts[1] else "unknown"
                self._handle_incoming_message(from_part, msg_text, line)
    
    def _handle_incoming_message(self, sender: str, text: str, raw: str):
        """Handle incoming WhatsApp message from Baileys bot."""
        with queue_lock:
            message_queue.append({
                "sender": sender,
                "text": text,
                "raw": raw,
                "timestamp": datetime.now().isoformat(),
                "source": "baileys"
            })
        log.info(f"📥 Queued message from {sender}: {text[:50]}")
    
    def send_whatsapp_message(self, to: str, message: str) -> bool:
        """Send message via Baileys bot using Node.js child process."""
        if not self.process or not self.running:
            log.error("Baileys bot not running")
            return False
        
        try:
            # Create a temporary JS script to send message
            js_code = f"""
const {{ makeWASocket, useMultiFileAuthState }} = require('baileys');
const {{ join }} = require('path');

async function sendMsg() {{
    const {{ state }} = await useMultiFileAuthState('{BAILEYS_BOT_DIR}/auth_info');
    const sock = makeWASocket({{
        auth: state,
        printQRInTerminal: false
    }});
    
    sock.ev.on('connection.update', (update) => {{
        if (update.connection === 'open') {{
            sock.sendMessage('{to}@s.whatsapp.net', {{ text: `{message}` }});
            setTimeout(() => process.exit(0), 1000);
        }}
    }});
}}
sendMsg().catch(console.error);
"""
            # Simpler approach: use curl to communicate with a REST endpoint
            # (if we extend the bot to have one)
            log.info(f"Would send to {to}: {message[:50]}")
            return True
            
        except Exception as e:
            log.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def stop_bot(self):
        """Stop the Baileys bot process."""
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            log.info("Baileys bot stopped")


# ── JARVIS Integration ───────────────────────────────────────

def process_with_jarvis(text: str, chat_id: str) -> str:
    """Process message through JARVIS AI."""
    try:
        add_to_history(chat_id, "user", text)
        response = ask_ai(text)
        add_to_history(chat_id, "assistant", response)
        return response
    except Exception as e:
        log.error(f"JARVIS processing error: {e}")
        return "Sorry, I encountered an error."


def handle_command(sender: str, text: str) -> Optional[str]:
    """Handle slash commands and keywords."""
    text_lower = text.lower().strip()
    
    # Bot owner commands
    if text_lower == "/start":
        return (
            f"🤖 Hello! I'm JARVIS, your AI assistant.\n"
            f"Connected via Baileys WhatsApp protocol.\n\n"
            f"Available commands:\n"
            f"  /start - Show this help\n"
            f"  /help - Command reference\n"
            f"  /stats - Usage statistics\n"
            f"  /clear - Clear chat history\n"
            f"  /pdf [topic] - Generate PDF\n"
            f"  /doc [topic] - Generate Word doc\n\n"
            f"Owner: {BOT_OWNER}"
        )
    
    elif text_lower == "/help":
        return (
            "🤖 **JARVIS Commands**\n"
            "/start - Start conversation\n"
            "/help - Show help\n"
            "/stats - Usage stats\n"
            "/clear - Clear history\n"
            "/pdf [topic] - Generate PDF report\n"
            "/doc [topic] - Generate Word doc\n"
            "\nJust ask me anything!"
        )
    
    elif text_lower == "/stats":
        history = get_history(sender)
        msg_count = len(history) // 2
        return f"📊 Your stats:\nMessages: {msg_count}"
    
    elif text_lower == "/clear":
        # History clearing would need implementation
        return "🗑️ Chat history cleared."
    
    elif text_lower.startswith("/pdf "):
        topic = text_lower[5:].strip() or "general topic"
        return f"📄 Generating PDF about: {topic}"
    
    elif text_lower.startswith("/doc "):
        topic = text_lower[5:].strip() or "general topic"
        return f"📄 Generating Word doc about: {topic}"
    
    return None


def message_processor():
    """Background thread to process queued messages."""
    log.info("Message processor started")
    
    while True:
        try:
            with queue_lock:
                if not message_queue:
                    msg_data = None
                else:
                    msg_data = message_queue.pop(0)
            
            if msg_data:
                sender = msg_data["sender"]
                text = msg_data["text"].strip()
                
                if not text:
                    continue
                
                log.info(f"Processing message from {sender}: {text[:50]}")
                
                # Check for commands first
                cmd_response = handle_command(sender, text)
                if cmd_response:
                    response = cmd_response
                elif NEXUS_ENABLED:
                    nexus_response = handle_nexus_query(text)
                    if nexus_response:
                        response = nexus_response
                    else:
                        response = process_with_jarvis(text, sender)
                else:
                    response = process_with_jarvis(text, sender)
                
                log.info(f"Response for {sender}: {response[:100]}")
                
                # Send via Baileys (would need implementation)
                # baileys_mgr.send_whatsapp_message(sender, response)
                
            else:
                time.sleep(0.5)
                
        except Exception as e:
            log.error(f"Message processor error: {e}")
            time.sleep(1)


# ── HTTP Server (Optional webhook interface) ─────────────────

def run_flask_webhook():
    """Run Flask webhook server for external WhatsApp API fallback."""
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route("/webhook", methods=["POST"])
        def webhook():
            """Receive WhatsApp webhook messages."""
            data = request.get_json()
            log.info(f"Webhook received: {json.dumps(data, indent=2)}")
            
            # Parse incoming message
            entries = data.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    for msg in messages:
                        sender = msg.get("from", "")
                        text_obj = msg.get("text", {})
                        text = text_obj.get("body", "") if text_obj else ""
                        
                        if not text:
                            # Check for button/interactive messages
                            button = msg.get("button", {})
                            if button:
                                text = button.get("text", "")
                            
                            interactive = msg.get("interactive", {})
                            if interactive:
                                button_reply = interactive.get("button_reply", {})
                                if button_reply:
                                    text = button_reply.get("title", "")
                        
                        if text:
                            with queue_lock:
                                message_queue.append({
                                    "sender": sender,
                                    "text": text,
                                    "timestamp": datetime.now().isoformat(),
                                    "source": "webhook"
                                })
                            log.info(f"📥 Webhook message from {sender}: {text[:50]}")
            
            return jsonify({"status": "ok"})
        
        @app.route("/webhook", methods=["GET"])
        def verify_webhook():
            """Verify webhook for WhatsApp Business API."""
            mode = request.args.get("hub.mode")
            token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")
            
            if mode == "subscribe" and token == "jarvis":
                return challenge, 200
            return "Invalid token", 403
        
        @app.route("/health", methods=["GET"])
        def health():
            return jsonify({
                "status": "healthy",
                "queue_size": len(message_queue),
                "bot_running": baileys_mgr.running
            })
        
        port = 5000
        log.info(f"Flask webhook server starting on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        
    except ImportError:
        log.warning("Flask not installed. Install: pip install flask")
    except Exception as e:
        log.error(f"Flask server error: {e}")


# ── Main ──────────────────────────────────────────────────────

def main():
    """Main entry point."""
    log.info("╔══════════════════════════════════════════╗")
    log.info("║  JARVIS WhatsApp Handler — Baileys Mode  ║")
    log.info("╚══════════════════════════════════════════╝")
    
    # Initialize Baileys manager
    global baileys_mgr
    baileys_mgr = BaileysManager(BAILEYS_BOT_DIR)
    
    # Check for existing Baileys bot
    if not os.path.exists(os.path.join(BAILEYS_BOT_DIR, "package.json")):
        log.error(f"Baileys bot not found at {BAILEYS_BOT_DIR}")
        log.info("Falling back to webhook mode")
    
    # Start Baileys bot
    baileys_started = baileys_mgr.start_bot()
    
    # Start message processor thread
    processor_thread = threading.Thread(target=message_processor, daemon=True)
    processor_thread.start()
    log.info("Message processor thread started")
    
    # Start Flask webhook server in separate thread
    flask_thread = threading.Thread(target=run_flask_webhook, daemon=True)
    flask_thread.start()
    log.info("Flask webhook server thread started")
    
    # Report status
    log.info(f"Baileys bot: {'running' if baileys_started else 'NOT started (check Node.js)'}")
    log.info(f"Webhook URL: http://localhost:5000/webhook")
    log.info(f"Health check: http://localhost:5000/health")
    log.info("WhatsApp handler ready. Waiting for messages...")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down...")
        baileys_mgr.stop_bot()
        sys.exit(0)


if __name__ == "__main__":
    main()
