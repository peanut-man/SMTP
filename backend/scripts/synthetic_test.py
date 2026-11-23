"""Synthetic end-to-end test script for the SMTP Mail Management Platform.

This script tests the entire system lifecycle:
1. System health check
2. User registration and login (obtaining JWT)
3. Adding an SMTP configuration (can use mock or local SMTP e.g. Mailpit/MailHog)
4. Testing SMTP connection
5. Creating an email template with Jinja2 variables
6. Adding contacts and querying contacts
7. Creating and queuing an email job
8. Polling email job status and inspecting sending attempts
9. Checking dashboard analytics and metrics
"""
import sys
import time
import json
import httpx

BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"


def run_synthetic_test(smtp_host="localhost", smtp_port=1025, smtp_user="test", smtp_pass="test", security_mode="PLAIN"):
    print("=" * 60)
    print("STARTING SYNTHETIC TEST FOR SMTP MAIL MANAGEMENT PLATFORM")
    print("=" * 60)

    client = httpx.Client(timeout=10.0)

    # 1. Health Check
    print("\n[Step 1] Checking system health...")
    try:
        res = client.get(HEALTH_URL)
        print(f"Health status ({res.status_code}):", res.json())
        assert res.status_code == 200, "Health check failed"
    except Exception as e:
        print(f"FAILED to reach backend at {HEALTH_URL}: {e}")
        print("Please ensure the backend API is running on localhost:8000.")
        return False

    # 2. User Registration & Login
    ts = int(time.time())
    test_user = f"tester_{ts}"
    test_email = f"tester_{ts}@example.com"
    test_password = "SecurePassword123!"

    print(f"\n[Step 2] Registering user '{test_user}' ({test_email})...")
    reg_res = client.post(f"{BASE_URL}/auth/register", json={
        "username": test_user,
        "email": test_email,
        "password": test_password
    })
    print(f"Register status ({reg_res.status_code}):", reg_res.json())
    assert reg_res.status_code == 201, "Registration failed"
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify /auth/me
    me_res = client.get(f"{BASE_URL}/auth/me", headers=headers)
    assert me_res.status_code == 200
    print("Authenticated user info:", me_res.json())

    # 3. Add SMTP Account
    print(f"\n[Step 3] Adding SMTP account on {smtp_host}:{smtp_port} ({security_mode})...")
    smtp_payload = {
        "account_name": f"Test SMTP {ts}",
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "username": smtp_user,
        "password": smtp_pass,
        "security_mode": security_mode,
        "sender_email": f"noreply@{smtp_host}",
        "sender_name": "Mail Management Platform",
        "connection_timeout": 15,
        "is_default": True
    }
    smtp_res = client.post(f"{BASE_URL}/smtp-accounts", json=smtp_payload, headers=headers)
    print(f"SMTP Create status ({smtp_res.status_code}):", smtp_res.json())
    assert smtp_res.status_code == 201, "Failed to create SMTP account"
    smtp_account_id = smtp_res.json()["id"]

    # 4. Test SMTP Connection
    print(f"\n[Step 4] Testing SMTP connection for account {smtp_account_id}...")
    test_conn_res = client.post(f"{BASE_URL}/smtp-accounts/{smtp_account_id}/test", headers=headers)
    print(f"Test connection response ({test_conn_res.status_code}):", test_conn_res.json())

    # 5. Create Email Template
    print("\n[Step 5] Creating Jinja2 email template...")
    tmpl_payload = {
        "name": "Synthetic Welcome Template",
        "description": "Template used in synthetic testing",
        "subject": "Hello {{ name }}, welcome to {{ platform }}!",
        "html_content": "<div style='font-family: sans-serif;'><h2>Welcome {{ name }}</h2><p>Your organization: {{ company }}</p></div>",
        "text_content": "Welcome {{ name }} to {{ platform }} ({{ company }})!"
    }
    tmpl_res = client.post(f"{BASE_URL}/templates", json=tmpl_payload, headers=headers)
    print(f"Template status ({tmpl_res.status_code}):", tmpl_res.json())
    assert tmpl_res.status_code == 201
    template_id = tmpl_res.json()["id"]

    # Preview Template
    prev_res = client.post(f"{BASE_URL}/templates/{template_id}/preview", json={
        "variables": {"name": "Alice Developer", "platform": "MailFlow", "company": "Acme Inc"}
    }, headers=headers)
    print("Template preview result:", prev_res.json())

    # 6. Add Contacts
    print("\n[Step 6] Adding recipient contact...")
    contact_res = client.post(f"{BASE_URL}/contacts", json={
        "name": "Recipient Alice",
        "email": f"alice_{ts}@destination.example",
        "organization": "Acme Inc",
        "group_name": "VIP Testers"
    }, headers=headers)
    print(f"Contact status ({contact_res.status_code}):", contact_res.json())
    assert contact_res.status_code == 201

    # 7. Compose and Queue an Email
    print("\n[Step 7] Enqueuing email job...")
    send_payload = {
        "smtp_account_id": smtp_account_id,
        "subject": "Synthetic Automation Test Email",
        "recipients_json": json.dumps([
            {"email": f"alice_{ts}@destination.example", "name": "Recipient Alice", "type": "to"},
            {"email": f"audit_{ts}@destination.example", "name": "Audit CC", "type": "cc"}
        ]),
        "html_body": "<h3>Synthetic Test Content</h3><p>Automated verification message.</p>",
        "text_body": "Synthetic Test Content: Automated verification message."
    }

    send_res = client.post(f"{BASE_URL}/emails/send", data=send_payload, headers=headers)
    print(f"Email queue status ({send_res.status_code}):", send_res.json())
    assert send_res.status_code == 202
    job_id = send_res.json()["id"]
    print(f"Job successfully created with ID: {job_id}")

    # 8. Poll Job Status
    print(f"\n[Step 8] Polling email job {job_id} for completion...")
    for attempt in range(6):
        time.sleep(2)
        job_res = client.get(f"{BASE_URL}/emails/{job_id}", headers=headers)
        if job_res.status_code == 200:
            job_info = job_res.json()["job"]
            status = job_info["status"]
            print(f"  Attempt {attempt + 1}: status={status}")
            if status in ("ACCEPTED", "FAILED", "CANCELLED"):
                print("Job finished with status:", status)
                print("Attempts recorded:", job_res.json()["attempts"])
                break
        else:
            print("Failed to fetch job:", job_res.status_code)

    # 9. Dashboard Summary Verification
    print("\n[Step 9] Fetching Dashboard Metrics...")
    dash_res = client.get(f"{BASE_URL}/dashboard/summary", headers=headers)
    print(f"Dashboard summary ({dash_res.status_code}):", dash_res.json())
    assert dash_res.status_code == 200
    assert dash_res.json()["total_emails"] >= 1

    print("\n" + "=" * 60)
    print("SYNTHETIC TEST SUITE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1025
    user = sys.argv[3] if len(sys.argv) > 3 else "test"
    pw = sys.argv[4] if len(sys.argv) > 4 else "test"
    mode = sys.argv[5] if len(sys.argv) > 5 else "PLAIN"
    run_synthetic_test(smtp_host=host, smtp_port=port, smtp_user=user, smtp_pass=pw, security_mode=mode)
