# ════════════════════════════════════════════════════════════
# JARVIS SEED — Boot Knowledge Loader
# Run: python3 jarvis_seed.py
# Location: /home/riziki/jarvis/jarvis_seed.py
# Purpose: Seeds JARVIS with Richard's complete world context
#          so it wakes up knowing everything on first boot.
# ════════════════════════════════════════════════════════════

from jarvis_memory import MemoryManager
import json

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MARIADB_PASSWORD",
    "database": "jarvis_memory"
}

mm = MemoryManager(db_config=DB_CONFIG)
seeded = 0

def seed(label, fn, *args):
    global seeded
    fn(*args)
    seeded += 1
    print(f"  [SEEDED] {label}")

print("\n JARVIS SEED — Loading Richard's World\n")
print("── ENTITIES (Infrastructure) ──────────────")

# ─── SERVERS & NETWORK ────────────────────────────────────────
seed("Kali Server RICHIE", mm.write_entity,
    "server-richie",
    "Kali Linux server. Hostname: RICHIE. User: riziki. "
    "Local IP: 192.168.0.110. Tailscale IP: 100.97.115.38. "
    "MacBook Air 2015. CPU-only. Running: Apache2 port 80, "
    "MariaDB port 3306, Ollama port 11434, Flask JARVIS port 5050.",
    "server")

seed("Windows Laptop", mm.write_entity,
    "laptop-windows",
    "Windows laptop. 8GB RAM, 128GB storage, Core i5. "
    "Thin client only — no models, no databases. "
    "WSL distros: FedoraLinux-43 (default), archlinux. "
    "C drive critically limited (~2.9GB free). "
    "Role: runs jarvis_client.py only.",
    "device")

seed("Tailscale Network", mm.write_entity,
    "network-tailscale",
    "Tailscale VPN connects Windows to Kali server RICHIE. "
    "RICHIE Tailscale IP: 100.97.115.38. Access from anywhere. "
    "Local LAN faster: 192.168.0.110 when on same network.",
    "network")

seed("Ollama on RICHIE", mm.write_entity,
    "service-ollama",
    "Ollama running on RICHIE port 11434. CPU-only (no GPU). "
    "Models: qwen2.5-coder:7b (primary LLM), nomic-embed-text (embeddings). "
    "Config: OLLAMA_KEEP_ALIVE=-1 recommended to avoid cold starts. "
    "Start: sudo systemctl start ollama",
    "service")

print("── ENTITIES (Projects) ────────────────────")

# ─── PROJECTS ─────────────────────────────────────────────────
seed("Poultry Farm System", mm.write_entity,
    "project-poultry",
    "Poultry Farm Management System. Case study: Kiambo Poultry Farm, Kiambu County. "
    "Tech: PHP, MySQL/MariaDB, Tailwind CSS. 12 modules: Dashboard, Flocks, Birds, "
    "Eggs, Feed, Vaccinations, Mortality, Weight, Finance, Sales, Reports, Settings. "
    "14 MySQL tables. Live at: /var/www/html/poultry-farm-system. "
    "Login: admin / admin123. GitHub: dicksonmaina/poultry-farm-system. "
    "School diploma project. Supervisor: Mr. Patrick. Exam: July 2026. Course: 2920.",
    "project")

seed("JARVIS Ecosystem", mm.write_entity,
    "project-jarvis",
    "JARVIS AI agent ecosystem. Personal AI OS. "
    "Framework: 6-memory-type agent (Conversational, Knowledge, Entity, Workflow, Toolbox, Summary). "
    "Storage: MariaDB (SQLite tested) + ChromaDB + Neo4j. "
    "Flask API port 5050. Windows runs jarvis_client.py only. "
    "Files: /home/riziki/jarvis/. All tests passed.",
    "project")

seed("Neo4j MiroFish", mm.write_entity,
    "service-neo4j",
    "Neo4j graph database on RICHIE via Docker. Name: MiroFish. "
    "Ports: 7474 (HTTP), 7687 (Bolt). Credentials: neo4j / richard123. "
    "Used for entity relationship graphs in JARVIS memory. "
    "Start: sudo docker compose up -d (from ~/docker-compose.yml)",
    "service")

print("── ENTITIES (Identity) ────────────────────")

# ─── IDENTITY ─────────────────────────────────────────────────
seed("Richard's Identity", mm.write_entity,
    "person-richard",
    "Richard Dickson Mwangi Maina. Admission no. 118820. "
    "Diploma in ICT, Nairobi Institute of Business Studies Technical College. "
    "Based in Nairobi, Kenya. GitHub: dicksonmaina. "
    "Goals: financial independence, freelancing (Upwork/Fiverr/Gumroad), "
    "management systems for Kenyan market (poultry→schools→clinics→hotels). "
    "Faith: Jesus Is King. Prefers direct, no-nonsense technical communication.",
    "person")

print("\n── WORKFLOWS (Procedures) ─────────────────")

# ─── WORKFLOWS ────────────────────────────────────────────────
seed("Restart Ollama", mm.write_workflow,
    "workflow-restart-ollama",
    "How to restart Ollama service on RICHIE Kali server",
    ["sudo systemctl restart ollama",
     "sleep 3 — wait for startup",
     "curl http://localhost:11434/api/tags — verify models loaded",
     "Expected: JSON list with qwen2.5-coder:7b and nomic-embed-text"])

seed("Start JARVIS Server", mm.write_workflow,
    "workflow-start-jarvis",
    "How to start the JARVIS Flask server on RICHIE",
    ["cd /home/riziki/jarvis",
     "python3 jarvis_server.py (or: sudo systemctl start jarvis)",
     "Verify: curl http://localhost:5050/health",
     "Expected: {status: alive, server: RICHIE, model: qwen2.5-coder:7b}"])

seed("Deploy Neo4j Docker", mm.write_workflow,
    "workflow-neo4j-docker",
    "How to start Neo4j MiroFish via Docker on RICHIE",
    ["cd ~ && cat docker-compose.yml — verify config",
     "sudo docker compose up -d",
     "curl http://localhost:7474 — verify web UI accessible",
     "Credentials: neo4j / richard123",
     "Connect via: bolt://localhost:7687"])

seed("Access Poultry System", mm.write_workflow,
    "workflow-poultry-access",
    "How to access and demo the Poultry Farm Management System",
    ["Ensure Apache2 running: sudo systemctl start apache2",
     "Ensure MariaDB running: sudo systemctl start mariadb",
     "Open browser: http://100.97.115.38/poultry-farm-system",
     "Login: admin / admin123",
     "For diploma demo: also accessible at 192.168.0.110/poultry-farm-system"])

seed("Git Push via Token", mm.write_workflow,
    "workflow-git-push",
    "How to push to GitHub when PAT is required",
    ["Use classic ghp_ token format only (fine-grained fails)",
     "git remote set-url origin https://TOKEN@github.com/dicksonmaina/REPO.git",
     "git push origin main (or --force if needed)",
     "Renew token at: github.com/settings/tokens — PAT name: arch-wsl"])

seed("Samba File Transfer", mm.write_workflow,
    "workflow-samba-transfer",
    "How to drag-and-drop files from Windows to Kali server",
    ["Windows: Win+R → type \\\\192.168.0.110\\jarvis",
     "Enter Samba credentials: riziki / [samba password]",
     "Drag files directly into the share window",
     "Files land in /home/riziki/jarvis/docs/ on Kali"])

print("\n── KNOWLEDGE BASE ─────────────────────────")

# ─── KNOWLEDGE ────────────────────────────────────────────────
seed("JARVIS Architecture", mm.write_knowledge,
    "know-jarvis-arch",
    "JARVIS uses 6 memory types based on Richmond Alake's framework. "
    "Conversational + Summary → MariaDB (exact retrieval). "
    "Knowledge + Entity + Workflow + Toolbox → ChromaDB (vector similarity). "
    "Embeddings: nomic-embed-text via Ollama API at localhost:11434. "
    "LLM: qwen2.5-coder:7b, CPU-only, ~2-10s inference. "
    "Context is assembled from all 6 types before every LLM call. "
    "Auto-summary triggers at 20 conversation turns to prevent overflow.",
    {"category": "architecture"})

seed("Port Reference", mm.write_knowledge,
    "know-ports",
    "RICHIE server port reference: "
    "Apache2: 80 (HTTP), 443 (HTTPS). "
    "MariaDB: 3306. Ollama: 11434. "
    "JARVIS Flask API: 5050. Neo4j HTTP: 7474. Neo4j Bolt: 7687. "
    "Samba: 445. Tailscale tunnels all ports through 100.97.115.38.",
    {"category": "infrastructure"})

seed("Monetization Plan", mm.write_knowledge,
    "know-business",
    "Richard's business roadmap: "
    "1. Sell management systems on Gumroad for Kenyan market. "
    "2. Freelance on Upwork/Fiverr with PHP/Python systems. "
    "3. Telegram channel: 1000+ subs → Fragment/TON ads + InviteMember subscriptions. "
    "4. WhatsApp Business automation bots for local businesses. "
    "5. Payment stack: M-Pesa → Equity/KCB → Wise → Payoneer → Grey. "
    "6. Systems pipeline: Poultry → Schools → Clinics → Inventory → Hotels.",
    {"category": "business"})

seed("Security Checklist", mm.write_knowledge,
    "know-security",
    "PENDING security hardening tasks for RICHIE: "
    "1. Change Neo4j password from richard123 to strong password. "
    "2. Restrict Ollama to localhost (add firewall rule). "
    "3. Rotate all API keys (Anthropic, Groq, GitHub PAT, Supabase). "
    "4. Docker network segmentation. "
    "5. WhatsApp bot input sanitization. "
    "6. Do all of this AFTER all tools are stable.",
    {"category": "security"})

print("\n── TOOLBOX (Registered Skills) ─────────────")

# ─── TOOLBOX ──────────────────────────────────────────────────
tools = [
    ("check_server_health",
     "Checks if JARVIS Flask server is alive on RICHIE. Returns status and model info.",
     "Use when: 'is JARVIS running', 'check server', 'health check'"),

    ("ingest_document",
     "Adds a file or text to JARVIS knowledge base via POST /ingest. Supports knowledge/workflow/entity/tool types.",
     "Use when: 'remember this', 'add to memory', 'ingest file', 'store document'"),

    ("query_memory",
     "Queries a specific JARVIS memory type (knowledge/workflow/entity/toolbox) via POST /memory/query.",
     "Use when: 'what do you know about', 'find workflow for', 'search memory'"),

    ("poultry_system_status",
     "Checks if Apache2 and MariaDB are running for the Poultry Farm Management System on RICHIE.",
     "Use when: 'is poultry system running', 'check Apache', 'check web server'"),

    ("run_kali_command",
     "Executes a shell command on RICHIE via SSH. Requires riziki credentials.",
     "Use when: 'run on server', 'execute on Kali', 'restart service', 'check disk space'"),
]

for name, doc, example in tools:
    seed(f"Tool: {name}", mm.register_tool, name, doc, example)

print(f"\n {'─'*44}")
print(f" ✓ SEED COMPLETE — {seeded} items loaded into JARVIS memory")
print(f" JARVIS now knows Richard's world.")
print(f" Run jarvis_server.py to go live.\n")
