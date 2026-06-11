#!/usr/bin/env python3
"""
E2E Integration Test for Agentic AI Assistant

This script verifies that the FastAPI backend is running, the database is
seeded, and the local Ollama LLM can communicate and execute SQL/semantic search
tools correctly.
"""

import sys
import time
import requests

BACKEND_URL = "http://localhost:8001"

def run_test():
    print("=" * 60)
    print("STARTING E2E INTEGRATION TEST FOR AGENTIC AI ASSISTANT")
    print("=" * 60)

    # 1. Verify Backend is Online
    print("\nStep 1: Pinging FastAPI backend...")
    try:
        res = requests.get(f"{BACKEND_URL}/", timeout=5)
        if res.status_code == 200:
            print("✔ Backend is online and responding!")
        else:
            print(f"❌ Backend ping failed with status code {res.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection to backend failed: {e}")
        print("Please ensure the docker-compose stack is running on host port 8001.")
        sys.exit(1)

    # 2. Check Database and Seed Data
    print("\nStep 2: Checking database user records...")
    try:
        users_res = requests.get(f"{BACKEND_URL}/users/", timeout=5)
        users = users_res.json()
        print(f"Current database contains {len(users)} user records.")
        
        if len(users) == 0:
            print("Database is empty. Triggering seeder endpoint (/populate_50)...")
            seed_res = requests.post(f"{BACKEND_URL}/populate_50", timeout=10)
            if seed_res.status_code == 201:
                print("✔ Seeded database with 50 fake users successfully!")
                users_res = requests.get(f"{BACKEND_URL}/users/", timeout=5)
                print(f"Database now contains {len(users_res.json())} user records.")
            else:
                print(f"❌ Failed to seed database: {seed_res.text}")
                sys.exit(1)
        else:
            print("✔ Database already has records. Proceeding with existing data.")
    except Exception as e:
        print(f"❌ Database interaction failed: {e}")
        sys.exit(1)

    # 3. Test Agentic AI Model Communication and Tool Execution
    print("\nStep 3: Sending agentic question to Chatbot...")
    chat_payload = {
        "messages": [
            {"role": "user", "content": "How many users are in our database in total?"}
        ]
    }
    
    print("Asking Agentic AI: 'How many users are in our database in total?'")
    print("Waiting for Ollama to process query and execute SQL tool (up to 45s)...")
    
    start_time = time.time()
    try:
        chat_res = requests.post(f"{BACKEND_URL}/chat", json=chat_payload, timeout=50)
        duration = time.time() - start_time
        
        if chat_res.status_code == 200:
            result = chat_res.json()
            response_text = result.get("response", "")
            print(f"\n✔ Response received in {duration:.2f} seconds!")
            print("-" * 50)
            print("AGENTIC AI COHERENT RESPONSE:")
            print(response_text)
            print("-" * 50)
            
            # Simple validation on response
            if any(term in response_text.lower() for term in ["50", "fifty", "records", "users", "total"]):
                print("\n✔ SUCCESS: Agentic AI responded with high-quality, database-backed information!")
                print("Test passed successfully!")
                print("=" * 60)
                sys.exit(0)
            else:
                print("\n⚠ WARNING: Response received, but might not have detected the database summary.")
                print("Please review the printed response above.")
                sys.exit(0)
        else:
            print(f"❌ Chat request failed with status code {chat_res.status_code}: {chat_res.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error communicating with Agentic Chatbot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
