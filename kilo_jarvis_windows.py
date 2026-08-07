#!/usr/bin/env python3
"""
KILO_JARVIS.PY — Multi-Provider AI Interface
NIM (Primary) + Groq (Fallback) + Ollama (Offline)
"""

import os
import requests
import json
from typing import List, Dict, Optional

class JarvisAI:
    def __init__(self):
        self.nim_key = os.environ.get("NVIDIA_API_KEY", "")
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.history = []
    
    def ask_ai(self, message: str, use_history: bool = True) -> str:
        """
        Query AI with multi-provider fallback.
        PRIMARY: NVIDIA NIM (free, 40 req/min)
        FALLBACK: Groq (free tier)
        OFFLINE: Ollama (local)
        """
        if use_history:
            self.history.append({"role": "user", "content": message})
            messages = self.history[-6:] if len(self.history) > 6 else self.history
        else:
            messages = [{"role": "user", "content": message}]
        
        # PRIMARY: NVIDIA NIM
        if self.nim_key:
            try:
                r = requests.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.nim_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshotai/kimi-k2-thinking",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=15
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"]
                    print("[JARVIS] ✓ NIM: OK")
                    if use_history:
                        self.history.append({"role": "assistant", "content": reply})
                    return reply
                else:
                    print(f"[JARVIS] ✗ NIM error {r.status_code} — trying Groq")
            except Exception as e:
                print(f"[JARVIS] ✗ NIM failed: {e} — trying Groq")
        
        # FALLBACK: Groq
        if self.groq_key:
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=15
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"]
                    print("[JARVIS] ✓ Groq: OK (fallback)")
                    if use_history:
                        self.history.append({"role": "assistant", "content": reply})
                    return reply
            except Exception as e:
                print(f"[JARVIS] ✗ Groq failed: {e}")
        
        # OFFLINE: Ollama Local
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5-coder:3b",
                    "prompt": message,
                    "stream": False
                },
                timeout=30
            )
            if r.status_code == 200:
                reply = r.json().get("response", "Ollama gave no response")
                print("[JARVIS] ✓ Ollama: OK (offline mode)")
                if use_history:
                    self.history.append({"role": "assistant", "content": reply})
                return reply
        except:
            pass
        
        error_msg = "ERROR: All providers failed. Check API keys and connections."
        print(f"[JARVIS] ✗ {error_msg}")
        return error_msg


def main():
    """Main Jarvis interface."""
    jarvis = JarvisAI()
    
    print("=" * 50)
    print("JARVIS PRIME — Multi-Provider AI")
    print("=" * 50)
    print("[JARVIS] Providers:")
    print("[JARVIS]   1. NVIDIA NIM (primary, free 40 req/min)")
    print("[JARVIS]   2. Groq (fallback, free)")
    print("[JARVIS]   3. Ollama (offline, qwen2.5-coder:3b)")
    print("[JARVIS]")
    print("[JARVIS] Type 'exit' to quit, 'clear' to reset history")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("[JARVIS] Goodbye!")
                break
            
            if user_input.lower() == "clear":
                jarvis.history = []
                print("[JARVIS] History cleared")
                continue
            
            response = jarvis.ask_ai(user_input)
            print(f"\nJARVIS: {response}")
        
        except KeyboardInterrupt:
            print("\n[JARVIS] Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"[JARVIS] Error: {e}")


if __name__ == "__main__":
    main()
