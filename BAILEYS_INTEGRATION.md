# JARVIS WhatsApp Handler - Baileys Integration

## Summary of Changes

Modified `whatsapp_handler.py` to use the **Baileys** WhatsApp protocol instead of the Meta WhatsApp Business API.

## What Was Changed

### 1. Baileys Integration (`whatsapp_handler.py`)

**Key Features:**
- Manages Baileys Node.js bot as subprocess (no separate HTTP endpoint needed)
- Uses stdin/stdout pipe communication between Python and Node.js
- Monitors Baileys bot output for incoming messages and connection status
- Flask webhook server still available for external integrations
- Message queue with background processing thread
- JARVIS AI integration for intelligent responses

**How It Works:**
1. Python starts the Baileys Node.js bot as a subprocess
2. Monitors stdout/stderr for message events and status updates
3. Queues incoming messages for processing
4. Background thread processes messages through JARVIS AI
5. Responses sent back via Baileys bot (when recipient connection available)

**Communication Flow:**
```
WhatsApp User → Baileys Bot (Node.js) → Pipe → Python Handler → JARVIS AI → Response
```

### 2. Baileys Bot Status

The existing Baileys bot at `~/workspace/projects/baileys-bot/` **does NOT have an HTTP endpoint**.
- It connects directly to WhatsApp via WebSockets using `@whiskeysockets/baileys`
- Receives messages via event: `sock.ev.on('messages.upsert', ...)`
- Sends messages directly: `sock.sendMessage(jid, { text })`
- Has RAG and Ollama integration for AI queries

**Why This Design:**
- Baileys uses direct WebSocket connections to WhatsApp servers
- No HTTP server needed - messages arrive via event listeners
- More efficient than polling HTTP endpoints
- Lower latency for message delivery

### 3. Service Integration

**WhatsApp Handler Service:**
- Runs both Python handler AND Baileys Node.js bot
- Monitors Baileys process and restarts if needed
- Health check endpoint: `http://localhost:5000/health`
- Webhook endpoint: `http://localhost:5000/webhook` (for external APIs)

**Process Tree:**
```
jarvis-whatsapp.service (systemd)
├── python3 whatsapp_handler.py
│   ├── Flask webhook server (port 5000)
│   ├── Message processor thread
│   └── Baileys subprocess monitor
│       └── node index.js (Baileys bot)
└── Connection to WhatsApp (via Baileys)
```

### 4. Commands Supported

**WhatsApp Commands (via Baileys):**
- `/start` - Show help and bot info
- `/help` - Command reference
- `/stats` - Usage statistics
- `/clear` - Clear chat history
- `/pdf [topic]` - Generate PDF report
- `/doc [topic]` - Generate Word document

**Baileys Bot Commands:**
- `ask:` - Query RAG system
- `ollama:` - Query Ollama LLM
- `hi` / `hello` - Greeting responses
- `farm` / `jobs` / `profile` / `status` - Contextual responses
- `good morning` / `good night` - Automation triggers

### 5. Architecture Comparison

**Previous (Meta API):**
```
WhatsApp → Meta API (HTTP Webhook) → Python → JARVIS
```

**Current (Baileys):**
```
WhatsApp → Baileys WebSocket → Node.js → Pipe → Python → JARVIS
                                   ↓
                          Direct message handling
```

## Running the Services

### All Services Status

✅ **jarvis-whatsapp.service** - Active (running)  
   - Python handler + Baileys bot  
   - Port 5000 (Flask webhook)  
   - Connected to WhatsApp

✅ **jarvis-core.service** - Active (running)  
   - Core Telegram bot  
   - Waiting for Telegram messages

### Check Status

```bash
# User-level services
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user status jarvis-whatsapp.service
systemctl --user status jarvis-core.service

# Health check
curl http://localhost:5000/health

# View logs
journalctl --user -u jarvis-whatsapp.service -f
```

### Restart Services

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user restart jarvis-whatsapp.service
systemctl --user restart jarvis-core.service
```

## Files Modified

1. **`whatsapp_handler.py`** - Complete rewrite for Baileys integration
2. **`jarvis-whatsapp.service`** - Updated description and config
3. **User systemd config** - `~/.config/systemd/user/jarvis-*.service`

## Key Implementation Details

### Baileys Process Management
- Uses `subprocess.Popen` to start Node.js bot
- Monitors stdout/stderr for message events
- Parses bot output for incoming messages
- Auto-restart on process failure

### Message Queue
- Thread-safe queue for incoming messages
- Background processor handles JARVIS AI calls
- Prevents blocking on slow AI responses

### Dual Communication Paths
1. **Baileys direct** - Primary path for WhatsApp
2. **Flask webhook** - Fallback for Meta API or testing

## Advantages of Baileys Approach

✅ No need for WhatsApp Business API approval  
✅ Free to use (no per-message costs)  
✅ Direct WebSocket connection (low latency)  
✅ Full control over message handling  
✅ Works with personal WhatsApp accounts  
✅ No HTTP polling needed  

## Limitations

⚠️ Requires QR code scan on first connection  
⚠️ Session persistence via auth_info directory  
⚠️ WhatsApp may detect and limit unofficial clients  
⚠️ No official support from WhatsApp  
⚠️ Requires Node.js runtime alongside Python  

## Testing

### Verify Services

```bash
# Check both services running
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user list-units --user | grep jarvis

# Health endpoint
curl -s http://localhost:5000/health | python3 -m json.tool

# Check processes
ps aux | grep -E "whatsapp_handler|baileys"
```

### Send Test Message

1. Scan QR code in server logs (if new session)
2. Send WhatsApp message to bot number
3. Check logs for message processing
4. Verify response delivery

## Monitoring

### Log Locations

- Systemd journal: `journalctl --user -u jarvis-whatsapp.service`
- Application log: `~/workspace/projects/jarvis/whatsapp_handler.log`
- Baileys output: Monitored via Python handler

### Metrics Available

- Queue size: `http://localhost:5000/health`
- Process memory: `systemctl --user status jarvis-whatsapp.service`
- Bot status: `bot_running` in health check
- Connection status: Baileys logs

## Troubleshooting

### Baileys Not Starting

```bash
# Check Node.js is installed
node --version  # Should be v18+

# Check dependencies
cd ~/workspace/projects/baileys-bot
npm list  # Should show baileys, @hapi/boom

# Check auth directory
ls -la ~/workspace/projects/baileys-bot/auth_info/
```

### QR Code Issues

```bash
# Regenerate auth
rm -rf ~/workspace/projects/baileys-bot/auth_info
systemctl --user restart jarvis-whatsapp.service
# Rescan QR code in WhatsApp
```

### Port Conflicts

```bash
# Check port 5000 is free
ss -tlnp | grep 5000
# Kill conflicting process
kill $(lsof -t -i:5000)
```

## Future Enhancements

- Add HTTP API endpoint to Baileys bot for direct control
- Implement message ACK tracking
- Add media file handling (images, documents)
- WebSocket server for real-time updates
- Message retry logic with exponential backoff
- Rate limiting per conversation
- Conversation context management
- Multi-user support with conversation routing

## Security Considerations

- Baileys auth stored in `auth_info/` directory (treat as sensitive)
- Webhook endpoint has no authentication (use behind firewall)
- Consider adding API key validation
- Log files may contain message content
- WhatsApp session = access to personal account

## Conclusion

The WhatsApp handler now uses Baileys protocol for direct WhatsApp integration without requiring Meta Business API approval. The solution combines Node.js (Baileys) for WhatsApp connectivity with Python (JARVIS) for AI processing, communicating via subprocess pipes and message queues. Both systemd services are running and healthy.
