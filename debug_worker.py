#!/usr/bin/env python3
"""
Debug version of n8n Worker Script
"""
import time
import pymysql
import requests
import json
import os
from datetime import datetime

print("Starting debug worker...")

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
        print("Attempting DB connection...")
        connection = pymysql.connect(**DB_CONFIG)
        print("DB connection successful!")
        return connection
    except Exception as e:
        print(f"[{datetime.now()}] Database connection error: {e}")
        return None

def test_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"Test query result: {result}")
        finally:
            conn.close()

if __name__ == '__main__':
    test_db()