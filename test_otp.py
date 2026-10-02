"""Standalone Fast2SMS OTP test (no Django).

Run from the folder that contains your .env, inside your venv:
    python test_otp.py
"""
import os
import secrets

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FAST2SMS_API_KEY")

if not API_KEY:
    raise SystemExit("FAST2SMS_API_KEY not found. Check your .env file.")

print("Key loaded, ends with:", API_KEY[-4:])

mobile = input("10-digit mobile number (no +91): ").strip()
otp = secrets.randbelow(9000) + 1000

# Best-effort wallet check (shows if the account has balance)
try:
    w = requests.get("https://www.fast2sms.com/dev/wallet",
                     headers={"authorization": API_KEY}, timeout=10)
    print("Wallet:", w.status_code, w.text)
except requests.RequestException as e:
    print("Wallet check failed:", type(e).__name__)

# Send the OTP
try:
    r = requests.get(
        "https://www.fast2sms.com/dev/bulkV2",
        headers={"cache-control": "no-cache"},
        params={
            "authorization": API_KEY,
            "variables_values": str(otp),
            "route": "otp",
            "numbers": mobile,
        },
        timeout=10,
    )
    print("Status:", r.status_code)
    print("Response:", r.text)
    if r.ok and r.json().get("return"):
        print(f"SUCCESS. OTP sent: {otp}")
    else:
        print("FAILED. Read the message above.")
except requests.RequestException as e:
    print("Request error:", type(e).__name__)