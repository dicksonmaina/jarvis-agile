# JARVIS Systemd Service Setup

This directory contains systemd service files and the WhatsApp handler for the JARVIS AI assistant ecosystem.

## Files

- `whatsapp_handler.py` – WhatsApp message handler with AI integration
- `jarvis-whatvis.service` – Systemd service for WhatsApp handler
- `jarvis-core.service` – Systemd service for core JARVIS (Telegram bot)
- `kilo_jarvis.py` – Core Telegram AI assistant
- `start-jarvis-original.sh` – Original startup script

## Quick Start

### 1. Install Dependencies

```bash
cd ~/workspace/projects/jarvis
pip install requests reportlab python-docx flask python-dotenv
```

### 2. Configure Environment

Create `~/.env` with your API keys:

```bash
# WhatsApp Configuration
WHATSAPP_API_URL=http://localhost:3000
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=jarvis

# AI API Keys
GROQ_API_KEY=gsk_your_groq_key
NVIDIA_API_KEY=your_nvidia_key

# Telegram (for core bot)
TELEGRAM_TOKEN=your_telegram_bot_token

# General
BOT_OWNER=Richard
```

Or create `jarvis/.env` for project-specific settings.

### 3. Install Systemd Services

```bash
# Copy service files to systemd
sudo cp jarvis-whatsapp.service /etc/systemd/system/
sudo cp jarvis-core.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable jarvis-whatsapp.service
sudo systemctl enable jarvis-core.service

# Start services
sudo systemctl start jarvis-whatsapp.service
sudo systemctl start jarvis-core.service
```

### 4. Check Service Status

```bash
# Check if services are running
sudo systemctl status jarvis-whatsapp.service
sudo systemctl status jarvis-core.service

# View logs
journalctl -u jarvis-whatsapp.service -f
journalctl -u jarvis-core.service -f

# Check specific log files
tail -f ~/workspace/projects/jarvis/whatsapp_handler.log
tail -f ~/workspace/projects/jarvis/jarvis-core.log
```

### 5. Manage Services

```bash
# Stop services
sudo systemctl stop jarvis-whatsapp.service
sudo systemctl stop jarvis-core.service

# Restart services
sudo systemctl restart jarvis-whatsapp.service
sudo systemctl restart jarvis-core.service

# Disable from auto-start
sudo systemctl disable jarvis-whatsapp.service
sudo systemctl disable jarvis-core.service
```

## WhatsApp Handler Features

- **Message Processing**: Routes incoming WhatsApp messages to JARVIS AI
- **Typing Indicators**: Shows typing status to users
- **Media Handling**: Downloads and processes images/videos/documents
- **Slash Commands**:
  - `/start` – Start conversation
  - `/help` – Show help menu
  - `/stats` – Usage statistics
  - `/clear` – Clear chat history
  - `/pdf [topic]` – Generate PDF report
  - `/doc [topic]` – Generate Word document
- **Webhook Support**: Receives messages via WhatsApp Business API webhooks
- **History Management**: Maintains conversation context

## Systemd Service Features

- **Auto-restart**: Services restart automatically on failure
- **Resource Limits**: Configured NOFILE and NPROC limits
- **Security**: PrivateTmp, NoNewPrivileges, ProtectSystem enabled
- **Logging**: Separate log files for stdout/stderr
- **Environment Isolation**: Dedicated user/group (riziki)

## Troubleshooting

### Service won't start
```bash
# Check journal logs
sudo journalctl -u jarvis-whatsapp.service -n 50 --no-pager

# Check for permission issues
ls -la ~/workspace/projects/jarvis/

# Verify Python path
which python3
```

### Python import errors
```bash
# Install missing packages
pip install flask requests reportlab python-docx python-dotenv
```

### Environment variables not loading
```bash
# Check if .env file exists and is readable
cat ~/.env

# Verify file permissions
chmod 600 ~/.env
```

### WhatsApp webhook not receiving messages
```bash
# Test webhook endpoint
curl http://localhost:5000/webhook

# Check WhatsApp Business API logs
# Ensure WHATSAPP_API_URL is correctly configured
```

## Development

### Run Manually (without systemd)

```bash
# WhatsApp handler
python3 whatsapp_handler.py

# Core JARVIS bot
python3 kilo_jarvis.py
```

### Testing Webhook Locally

```bash
# Use ngrok for public webhook URL
ngrok http 5000

# Send test message
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"123456789","text":{"body":"Hello"}}]}}]}]}'
```

## Architecture

```

  WhatsApp       
  Business API   

         
         webhook
         

  whatsapp_       
  handler.py      
  (systemd)       

         
         AI processing
         

  kilo_jarvis.py  
  (systemd)       

         
         responses
         

   Telegram       
   Users          

```

## Security Notes

- API keys are loaded from environment files, not hardcoded
- Services run as non-root user (riziki)
- ReadWritePaths restricts file access to project directory
- NoNewPrivileges prevents privilege escalation
- PrivateTmp isolates temporary files
- ProtectSystem restricts system directory access

## License

JARVIS AI Assistant – Richard Dickson
