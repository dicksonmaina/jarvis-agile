"""
JARVIS Flask API Sidecar — Port 5050
Provides auth, logging, rate limiting for all client projects
"""
from flask import Flask, request, jsonify
from functools import wraps
import time, sqlite3, os, hashlib

app = Flask(__name__)

# Database setup
DB_PATH = os.environ.get('DB_PATH', '/home/riziki/jarvis/jarvis.db')

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ip_timestamp ON request_logs(ip, timestamp)
    """)
    conn.commit()
    conn.close()

def hash_key(key):
    """Hash an API key for secure storage"""
    return hashlib.sha256(key.encode()).hexdigest()

def verify_key(key):
    """Verify an API key against the database"""
    if not key:
        return False
    
    key_hash = hash_key(key)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM api_keys WHERE key_hash = ? AND is_active = 1", 
        (key_hash,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def log_request(req, status):
    """Log every request for monitoring and analytics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO request_logs (ip, endpoint, status)
            VALUES (?, ?, ?)
        """, (req.remote_addr, req.path, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logging error: {e}")

# Rate limiter (in-memory, per IP)
rate_store = {}
RATE_LIMIT_PER_MINUTE = 30

def check_rate_limit(ip):
    """Check if IP has exceeded rate limit"""
    now = time.time()
    # Clean old entries
    if ip in rate_store:
        rate_store[ip] = [t for t in rate_store[ip] if now - t < 60]
    
    # Check limit
    hits = rate_store.get(ip, [])
    if len(hits) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # Add current request
    rate_store[ip] = hits + [now]
    return True

# === SIDECAR FUNCTIONS (attach to ANY project) ===

def require_api_key(f):
    """Auth sidecar - same key system across ALL projects"""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not verify_key(key):
            log_request(request, "BLOCKED")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# === YOUR ACTUAL API ENDPOINTS ===

@app.route('/api/poultry/query', methods=['POST'])
@require_api_key
def poultry_query():
    """Example endpoint for poultry farm system"""
    ip = request.remote_addr
    if not check_rate_limit(ip):
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    log_request(request, "OK")
    
    # Forward to poultry farm logic (example)
    data = request.json or {}
    # In a real implementation, this would call your poultry farm logic
    result = {
        "result": "processed", 
        "data": data,
        "timestamp": time.time(),
        "service": "poultry-farm-system"
    }
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "JARVIS running", 
        "version": "2.0",
        "timestamp": time.time()
    })

@app.route('/api/stats', methods=['GET'])
@require_api_key
def stats():
    """Get usage statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total requests
    cursor.execute("SELECT COUNT(*) FROM request_logs")
    total_requests = cursor.fetchone()[0]
    
    # Requests today
    cursor.execute("""
        SELECT COUNT(*) FROM request_logs 
        WHERE date(timestamp) = date('now')
    """)
    today_requests = cursor.fetchone()[0]
    
    # Blocked requests
    cursor.execute("""
        SELECT COUNT(*) FROM request_logs 
        WHERE status = 'BLOCKED'
    """)
    blocked_requests = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "total_requests": total_requests,
        "today_requests": today_requests,
        "blocked_requests": blocked_requests,
        "rate_limit_per_minute": RATE_LIMIT_PER_MINUTE
    })

# Initialize database on startup
if __name__ == '__main__':
    init_db()
    
    # Create a default API key if none exists
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM api_keys")
    if cursor.fetchone()[0] == 0:
        # Create a default key for testing
        default_key = "jarvis-default-key-12345"
        cursor.execute(
            "INSERT INTO api_keys (key_hash, name) VALUES (?, ?)",
            (hash_key(default_key), "default-key")
        )
        conn.commit()
        print(f"Default API key created: {default_key}")
        print("Save this key - you'll need it for authentication!")
    conn.close()
    
    print("Starting JARVIS API Sidecar on port 5050...")
    app.run(host='0.0.0.0', port=5050, debug=False)