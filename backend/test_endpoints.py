import sys
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

endpoints = [
    "/companies",
    "/events",
    "/alerts",
    "/thesis-notes",
    "/daily-brief",
    "/portfolios",
    "/scoring-config"
]

print("Testing Overview endpoints...")
for ep in endpoints:
    try:
        response = client.get(ep)
        print(f"{ep}: {response.status_code}")
        if response.status_code >= 400:
            print(f"  Error details: {response.json()}")
    except Exception as e:
        print(f"{ep}: CRASHED with Exception: {e}")
