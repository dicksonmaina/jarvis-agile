# JARVIS Project Context
# See full workspace context: ~/workspace/CLAUDE.md
# Skills: ~/workspace/.claude/skills/

project: JARVIS AGI Core
stack: Python 3, Flask (port 5000), Redis, Groq API
entry_point: whatsapp_handler.py (WhatsApp), kilo_jarvis.py (Telegram)
ai_providers: Groq (primary) → OpenRouter → Gemini → DeepSeek
logs: ~/workspace/logs/jarvis-*.log
services: jarvis-core.service, jarvis-whatsapp.service

key_rules:
- Never use Ollama as the only provider
- Always have cloud API fallback
- Load secrets from ~/workspace/.env
- Check HELIX before restarting services