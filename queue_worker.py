#!/usr/bin/env python3
"""
n8n Worker Script — Processes messages from MariaDB queue
Runs continuously, checking for pending messages every 5 seconds
"""
import time
import pymysql
import requests
import json
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'riziki',
    'password': '',  # We set the password to empty for riziki user
    'database': 'jarvis_queue',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# JARVIS API endpoint
JARVIS_API_URL = "http://localhost:5050/api/poultry/query"
JARVIS_API_KEY = "jarvis-default-key-12345"  # From our init

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"[{datetime.now()}] Database connection error: {e}")
        return None

def process_queue():
    """Process pending messages from the queue"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Grab next pending message
            cursor.execute("""
                SELECT id, source, sender, message
                FROM message_queue
                WHERE status = 'pending'
                ORDER BY created_at ASC LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return True  # No messages to process
            
            msg_id = row['id']
            source = row['source']
            sender = row['sender']
            message = row['message']
            
            print(f"[{datetime.now()}] Processing message {msg_id} from {source}: {sender}")
            
            # Mark as processing
            cursor.execute(
                "UPDATE message_queue SET status='processing' WHERE id=%s", 
                (msg_id,)
            )
            connection.commit()
            
            # Process with JARVIS
            try:
                response = call_jarvis(message)
                
                # Mark as done
                cursor.execute("""
                    UPDATE message_queue
                    SET status='done', response=%s, processed_at=NOW()
                    WHERE id=%s
                """, (response, msg_id))
                connection.commit()
                
                print(f"[{datetime.now()}] Processed message {msg_id} from {source}")
                return True
                
            except Exception as e:
                print(f"[{datetime.now()}] Error processing message {msg_id}: {e}")
                # Mark as failed
                cursor.execute("""
                    UPDATE message_queue
                    SET status='failed', response=%s, processed_at=NOW()
                    WHERE id=%s
                """, (f"Processing error: {str(e)}", msg_id))
                connection.commit()
                return False
                
    except Exception as e:
        print(f"[{datetime.now()}] Queue processing error: {e}")
        return False
    finally:
        connection.close()

def call_jarvis(message):
    """Send message to JARVIS API and return response"""
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': JARVIS_API_KEY
    }
    payload = {'message': message}
    
    response = requests.post(
        JARVIS_API_URL,
        headers=headers,
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get('response', 'No response from JARVIS')
    else:
        raise Exception(f"JARVIS API error: {response.status_code} - {response.text}")

def main():
    """Main worker loop"""
    print(f"[{datetime.now()}] Starting n8n queue worker...")
    print(f"[{datetime.now()}] Checking for messages every 5 seconds")
    
    while True:
        try:
            process_queue()
        except Exception as e:
            print(f"[{datetime.now()}] Worker error: {e}")
        
        time.sleep(5)

if __name__ == '__main__':
    main()