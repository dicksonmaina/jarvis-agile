#!/usr/bin/env python3
"""
PHONE_BRIDGE.PY — Android Device Bridge via ADB
Richard's phone is now part of JARVIS stack
Sync WhatsApp, screenshots, pull media, monitor battery
"""

import subprocess
import os
import time
import json
from datetime import datetime
from pathlib import Path


class PhoneBridge:
    def __init__(self):
        self.adb_cmd = "adb"
        self.device = None
        self.media_dir = Path("/mnt/c/Users/user/richiedickson/phone")
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.check_device()
    
    def adb(self, cmd):
        """Execute ADB command and return output"""
        try:
            result = subprocess.run(
                f"{self.adb_cmd} {cmd}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"[ADB ERROR] {e}")
            return None
    
    def check_device(self):
        """Verify ADB device is connected"""
        devices = self.adb("devices")
        if "offline" in devices:
            print("[PHONE] ✗ Device offline. Enable USB debugging.")
            return False
        elif "device" in devices:
            print("[PHONE] ✓ Device connected via ADB")
            self.device = True
            return True
        else:
            print("[PHONE] ✗ No device found. Run: adb devices")
            return False
    
    def phone_status(self):
        """Get current phone status"""
        if not self.device:
            print("[PHONE] Device not connected")
            return
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "device": self.adb("shell getprop ro.product.model"),
            "manufacturer": self.adb("shell getprop ro.product.manufacturer"),
            "android_version": self.adb("shell getprop ro.build.version.release"),
            "battery": self.adb("shell dumpsys battery | grep level"),
            "screen": self.adb("shell dumpsys display | grep 'mScreenState'"),
            "storage": self.adb("shell df /sdcard | tail -1")
        }
        
        print("[PHONE] ══════════════════════════════════════")
        print(f"[PHONE] Device:    {status['device']} ({status['manufacturer']})")
        print(f"[PHONE] Android:   {status['android_version']}")
        print(f"[PHONE] Battery:   {status['battery']}")
        print(f"[PHONE] Storage:   {status['storage']}")
        print("[PHONE] ══════════════════════════════════════")
        
        return status
    
    def pull_whatsapp_media(self):
        """Sync WhatsApp media from phone"""
        if not self.device:
            return
        
        wa_dir = self.media_dir / "whatsapp"
        wa_dir.mkdir(parents=True, exist_ok=True)
        
        print("[PHONE] Syncing WhatsApp media...")
        result = self.adb(f"pull /sdcard/Android/media/com.whatsapp/WhatsApp/Media {wa_dir}")
        
        if result:
            print(f"[PHONE] ✓ WhatsApp media synced to {wa_dir}")
        else:
            print("[PHONE] ✗ Could not sync WhatsApp media")
    
    def pull_screenshots(self):
        """Sync screenshots from phone"""
        if not self.device:
            return
        
        ss_dir = self.media_dir / "screenshots"
        ss_dir.mkdir(parents=True, exist_ok=True)
        
        print("[PHONE] Syncing screenshots...")
        result = self.adb(f"pull /sdcard/Pictures/Screenshots {ss_dir}")
        
        if result:
            print(f"[PHONE] ✓ Screenshots synced to {ss_dir}")
        else:
            print("[PHONE] ✗ Could not sync screenshots")
    
    def pull_downloads(self):
        """Sync downloads folder from phone"""
        if not self.device:
            return
        
        dl_dir = self.media_dir / "downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)
        
        print("[PHONE] Syncing downloads...")
        result = self.adb(f"pull /sdcard/Download {dl_dir}")
        
        if result:
            print(f"[PHONE] ✓ Downloads synced to {dl_dir}")
    
    def push_file(self, local_path, remote_path="/sdcard/Download/"):
        """Push file to phone"""
        if not self.device:
            return
        
        print(f"[PHONE] Pushing {local_path} to phone...")
        result = self.adb(f"push {local_path} {remote_path}")
        
        if result:
            print(f"[PHONE] ✓ Pushed to {remote_path}")
        else:
            print("[PHONE] ✗ Push failed")
    
    def keep_screen_on(self):
        """Keep screen on indefinitely (for automation)"""
        if not self.device:
            return
        
        print("[PHONE] Setting screen to stay on...")
        self.adb("shell settings put system screen_off_timeout 2147483647")
        print("[PHONE] ✓ Screen will stay on")
    
    def disable_lockscreen(self):
        """Disable lockscreen (if rooted)"""
        if not self.device:
            return
        
        print("[PHONE] Attempting to disable lockscreen...")
        self.adb("shell locksettings set-disabled true")
        print("[PHONE] ✓ Lockscreen disabled (if rooted)")
    
    def send_notification(self, title, message):
        """Send notification to phone"""
        if not self.device:
            return
        
        cmd = f'shell am broadcast -a android.intent.action.SEND --es android.intent.extra.TEXT "{title}: {message}"'
        self.adb(cmd)
        print(f"[PHONE] Notification sent: {title}")
    
    def start_auto_sync(self, interval=300):
        """Start automatic sync every N seconds (default 5 min)"""
        print(f"[PHONE] Auto-sync started (interval: {interval}s)")
        
        sync_count = 0
        while True:
            try:
                sync_count += 1
                print(f"\n[PHONE] ──── SYNC #{sync_count} @ {datetime.now().strftime('%H:%M:%S')} ────")
                
                self.phone_status()
                self.pull_screenshots()
                self.pull_whatsapp_media()
                self.pull_downloads()
                
                print(f"[PHONE] ──── SYNC #{sync_count} COMPLETE ────")
                print(f"[PHONE] Next sync in {interval}s...")
                
                time.sleep(interval)
            
            except KeyboardInterrupt:
                print("\n[PHONE] ✓ Auto-sync stopped")
                break
            except Exception as e:
                print(f"[PHONE] ✗ Sync error: {e}")
                time.sleep(interval)
    
    def reverse_port(self, local_port=8080, remote_port=8080):
        """Set up reverse port forwarding"""
        if not self.device:
            return
        
        print(f"[PHONE] Setting reverse port forward: {local_port} → {remote_port}")
        self.adb(f"reverse tcp:{local_port} tcp:{remote_port}")
        print(f"[PHONE] ✓ Reverse port forward ready")


def main():
    print("\n" + "="*50)
    print("RICHIE'S PHONE BRIDGE — JARVIS ANDROID INTEGRATION")
    print("="*50 + "\n")
    
    bridge = PhoneBridge()
    
    if not bridge.device:
        print("[PHONE] ✗ No device connected. Waiting...")
        return
    
    # Initial status check
    bridge.phone_status()
    
    # Keep screen on for automation
    bridge.keep_screen_on()
    
    # Start auto-sync (every 5 minutes)
    print("\n[PHONE] Starting auto-sync service...\n")
    bridge.start_auto_sync(interval=300)


if __name__ == "__main__":
    main()
