#!/usr/bin/env python3
"""Quick start script for the Sarvam Auto Dealership Bot."""
import os
import sys

# Windows consoles default to cp1252, which cannot encode the emoji/Hindi text
# in our log lines. Force UTF-8 so prints don't crash the server.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn
from app.config import settings

if __name__ == "__main__":
    # Honor a PORT env var if set (used by preview tooling and cloud hosts),
    # otherwise fall back to the configured APP_PORT.
    port = int(os.environ.get("PORT", settings.app_port))

    print("🚗 Starting Sarvam Auto Dealership Voice Bot...")
    print(f"   Host: {settings.app_host}:{port}")
    print(f"   Debug: {settings.debug}")
    print(f"   Default Language: {settings.default_language}")
    print(f"\n📊 Dashboard: http://localhost:{port}/dashboard")
    print("📞 Twilio webhook URL format: http://YOUR_NGROK_URL/voice/inbound")
    print("\n🚀 Server starting...\n")

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=port,
        reload=settings.debug,
        log_level="info"
    )
