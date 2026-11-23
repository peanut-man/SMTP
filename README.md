# MailFlow — SMTP Mail Management Platform

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MailFlow** is an enterprise-grade, self-hosted **SMTP Mail Management Platform**. It empowers organizations and developers to configure multiple SMTP relays, compose rich HTML/plain-text emails with dynamic Jinja2 templates, queue outbound messages asynchronously in a resilient PostgreSQL-backed job queue, and monitor delivery attempts in real time through an interactive SaaS-style dashboard.

---

## Table of Contents

- [1. What is MailFlow?](#1-what-is-mailflow)
- [2. System Architecture](#2-system-architecture)
- [3. Email Lifecycle & Retry Flowchart](#3-email-lifecycle--retry-flowchart)
- [4. Core Capabilities](#4-core-capabilities)
- [5. Technology Stack](#5-technology-stack)
- [6. Database Entity Relationship Diagram](#6-database-entity-relationship-diagram)
- [7. Quick Start: Docker Compose](#7-quick-start-docker-compose)
- [8. Local Development Run (Without Docker)](#8-local-development-run-without-docker)
- [9. Testing & Synthetic Verification](#9-testing--synthetic-verification)
- [10. Popular SMTP Provider Configurations](#10-popular-smtp-provider-configurations)
- [11. REST API Reference](#11-rest-api-reference)
- [12. Security Architecture](#12-security-architecture)
- [13. Troubleshooting & FAQs](#13-troubleshooting--faqs)

---

## 1. What is MailFlow?

Most web platforms either tightly couple email sending to third-party proprietary SDKs or send emails synchronously inside web request threads, causing connection timeouts, degraded UX, and lost messages during transient outages.

**MailFlow** acts as an independent, centralized email dispatch hub:
1. **Centralized Relay Management:** Configure Gmail, SendGrid, Amazon SES, Mailgun, or custom SMTP servers in one unified place.
2. **Encrypted Credential Vault:** SMTP passwords are never stored in plaintext and never leaked over APIs or logs; they are encrypted using **Fernet AES-128-CBC** encryption.
3. **Zero-Block Asynchronous Queuing:** Email dispatch returns `202 Accepted` in milliseconds. Heavy MIME assembly, attachment encoding, and SMTP handshakes happen in an isolated background worker.
4. **Resilient Retry Mechanics:** Transient server glitches (`421`, `450`, `451`, `452`) are retried automatically with exponential backoff, while hard rejections (`5xx`) fail fast without wasting resources.
5. **Jinja2 Templating Engine:** Reusable email templates with sandbox variable parsing and instant visual previews.
6. **Full Delivery Audit Trail:** Track attempt counts, raw SMTP server response codes (`250 OK`, `550 User Unknown`), latency, and error diagnostics per recipient.

> [!NOTE]
> **SMTP Acceptance vs. Inbox Delivery:** In compliance with RFC 5321, receiving an SMTP `250 OK` confirms that the next-hop mail transfer agent (MTA) has accepted responsibility for the message. MailFlow clearly displays this as **ACCEPTED by SMTP Server** rather than falsely claiming guaranteed inbox placement.

---

## 2. System Architecture

The application is decoupled into four modular subsystems: **Web Frontend (Nginx + React SPA)**, **Backend REST API (FastAPI)**, **Database & Queue (PostgreSQL 16)**, and **Background Processing Worker (aiosmtplib)**.

```mermaid
flowchart TD
    subgraph Browser["User Browser"]
        SPA["React SPA<br/>TypeScript + Tailwind + Recharts"]
    end

    subgraph ReverseProxy["Frontend Ingress (Nginx)"]
        NGINX_STATIC["Static Asset Server<br/>SPA Routing Fallback"]
        NGINX_PROXY["Reverse Proxy Router<br/>/api/v1/ Proxy"]
    end

    subgraph BackendAPI["Backend REST API (FastAPI)"]
        API_GATEWAY["FastAPI App & CORS Middleware"]
        AUTH_ROUTER["Auth Router<br/>/auth"]
        SMTP_ROUTER["SMTP Accounts Router<br/>/smtp-accounts"]
        EMAIL_ROUTER["Email Router<br/>/emails"]
        TMPL_ROUTER["Templates Router<br/>/templates"]
        CONT_ROUTER["Contacts Router<br/>/contacts"]
        HIST_ROUTER["History Router<br/>/history"]
        DASH_ROUTER["Dashboard Router<br/>/dashboard"]
    end

    subgraph Storage["PostgreSQL 16 Database"]
        DB_USERS[("users")]
        DB_ACCOUNTS[("smtp_accounts")]
        DB_JOBS[("email_jobs")]
        DB_RECIPS[("email_recipients")]
        DB_ATTEMPTS[("email_attempts")]
        DB_TEMPLATES[("email_templates")]
        DB_CONTACTS[("contacts")]
    end

    subgraph WorkerProcess["Independent Email Worker Daemon"]
        POLLER["Queue Poller<br/>5s Interval"]
        LOCKER["Atomic Row Locker<br/>SELECT FOR UPDATE SKIP LOCKED"]
        DECRYPTOR["Fernet Credential Decryptor<br/>AES-128 In-Memory"]
        BUILDER["MIME Multipart Message Builder<br/>Text + HTML + Attachments"]
        SENDER["aiosmtplib Sender Engine<br/>STARTTLS / SSL / Plain"]
        RETRY_MGR["Retry & Backoff Manager<br/>Exponential Delay"]
    end

    subgraph ExternalSMTP["External Mail Transfer Agents"]
        MTA_GMAIL["Google Workspace / Gmail"]
        MTA_SES["Amazon SES / SendGrid / Mailgun"]
        MTA_DEV["Local Mailpit / MailHog"]
    end

    SPA -->|HTTP Requests| NGINX_PROXY
    SPA -->|Static Assets| NGINX_STATIC
    NGINX_PROXY -->|Forwarded API Calls| API_GATEWAY

    API_GATEWAY --> AUTH_ROUTER
    API_GATEWAY --> SMTP_ROUTER
    API_GATEWAY --> EMAIL_ROUTER
    API_GATEWAY --> TMPL_ROUTER
    API_GATEWAY --> CONT_ROUTER
    API_GATEWAY --> HIST_ROUTER
    API_GATEWAY --> DASH_ROUTER

    AUTH_ROUTER --> DB_USERS
    SMTP_ROUTER --> DB_ACCOUNTS
    EMAIL_ROUTER --> DB_JOBS
    EMAIL_ROUTER --> DB_RECIPS
    TMPL_ROUTER --> DB_TEMPLATES
    CONT_ROUTER --> DB_CONTACTS
    HIST_ROUTER --> DB_JOBS
    HIST_ROUTER --> DB_ATTEMPTS
    DASH_ROUTER --> DB_JOBS
    DASH_ROUTER --> DB_ACCOUNTS

    POLLER --> LOCKER
    LOCKER -->|Fetch Pending Jobs| DB_JOBS
    LOCKER --> DECRYPTOR
    DECRYPTOR -->|Fetch Encrypted Password| DB_ACCOUNTS
    DECRYPTOR --> BUILDER
    BUILDER --> SENDER
    SENDER -->|SMTP Session| MTA_GMAIL
    SENDER -->|SMTP Session| MTA_SES
    SENDER -->|SMTP Session| MTA_DEV
    SENDER --> RETRY_MGR
    RETRY_MGR -->|Record Attempt Logs| DB_ATTEMPTS
    RETRY_MGR -->|Update Status| DB_JOBS
```

---

## 3. Email Lifecycle & Retry Flowchart

This flowchart demonstrates the exact message processing pipeline, from user creation to SMTP delivery and exponential retry handling:

```mermaid
flowchart TD
    START(["User Submits Email"]) --> VALIDATE{"Validate Request"}
    
    VALIDATE -->|Invalid| ERR_RESP["Return HTTP 400 or 422 Error"]
    
    VALIDATE -->|Valid| CREATE_JOB["Insert Job into PostgreSQL<br/>status = PENDING"]
    CREATE_JOB --> SAVE_ATTACH["Persist File Attachments<br/>/app/storage/attachments"]
    SAVE_ATTACH --> RET_ACCEPTED["Return HTTP 202 Accepted<br/>Job ID UUID"]

    subgraph AsyncWorker["Background Worker Loop (Every 5s)"]
        POLL_QUEUE["Query Database for Eligible Jobs<br/>status in PENDING or RETRYING<br/>AND next_retry_at <= NOW"]
        POLL_QUEUE --> ACQUIRE_LOCK{"Acquire Row Lock"}
        
        ACQUIRE_LOCK -->|Already Claimed| SKIP["Skip<br/>Handled by other worker"]
        ACQUIRE_LOCK -->|Claimed| SET_PROC["Update status = PROCESSING"]
        
        SET_PROC --> LOAD_CREDS["Load SMTP Configuration<br/>Decrypt Password via Fernet AES"]
        LOAD_CREDS --> BUILD_MIME["Construct MIME Message<br/>Headers, HTML, Plain, Attachments"]
        
        BUILD_MIME --> SMTP_CONNECT["Connect to SMTP Host:Port<br/>Negotiate STARTTLS / SSL_TLS"]
        SMTP_CONNECT --> SMTP_AUTH["Authenticate Credentials"]
        SMTP_AUTH --> SMTP_SEND["Execute aiosmtplib.send_message"]
        
        SMTP_SEND --> CHECK_RESP{"Evaluate SMTP Response"}
        
        CHECK_RESP -->|250 Accepted| STATUS_ACCEPTED["Set status = ACCEPTED<br/>Record EmailAttempt SUCCESS"]
        
        CHECK_RESP -->|Transient Error 4xx / Timeout| CHECK_RETRY{"Retry count < Max retries?"}
        CHECK_RETRY -->|Yes| SCHEDULE_RETRY["Calculate Exponential Backoff<br/>base_delay * 2^retry_count<br/>Set status = RETRYING"]
        CHECK_RETRY -->|No| STATUS_FAILED["Max Retries Exhausted<br/>Set status = FAILED<br/>Record EmailAttempt FAILED"]
        
        CHECK_RESP -->|Permanent Error 5xx / Auth Fail| STATUS_FAILED
    end

    RET_ACCEPTED -.-> POLL_QUEUE
```

---

## 4. Core Capabilities

### 🔐 Multi-Account SMTP Management
- Support for multiple active SMTP accounts per user.
- **Connection Security Modes:**
  - `STARTTLS` (Standard for port 587) with strict host verification.
  - `SSL_TLS` (Implicit SSL for port 465).
  - `PLAIN` (Unencrypted SMTP, restricted to trusted local development environments).
- Live on-demand connection testing without sending dummy emails.

### ✉️ Full-Featured Email Composer
- Supports `To`, `Cc`, `Bcc`, and custom `Reply-To` headers.
- Multi-part MIME generation (`text/plain` fallback with rich `text/html`).
- File attachments with automatic MIME-type detection and storage encryption.
- Seamless Jinja2 template selection with variable auto-population.
- Visual iframe email preview modal.

### 📝 Dynamic Email Templates
- Jinja2 syntax support (`{{ user_name }}`, `{{ verification_url }}`).
- Automated variable detection and listing from template syntax.
- Real-time preview rendering with mock JSON payloads.
- Template duplication and versioning.

### 👥 Contact Directory
- Manage recipients with Name, Email, Organization, and Group tagging.
- Fast multi-contact selection inside the email composer.
- Bulk CSV import with error detection and duplicate skipping.
- One-click CSV export.

### 📊 Real-Time Analytics & Audit Trail
- Summary cards: Total Submitted, SMTP-Accepted, Failed, Pending, Retrying, Active SMTP Relays.
- Volume Trends: Configurable 7-day, 30-day, and 90-day time-series line charts.
- Status distribution pie chart and per-SMTP-account success rate bar charts.
- Historical audit log with deep search, date range filters, and per-attempt diagnostic traces.

---

## 5. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Framework** | FastAPI | 0.115+ | High-performance asynchronous REST API framework |
| **ASGI Web Server** | Uvicorn | 0.32+ | ASGI production application server |
| **SMTP Client** | aiosmtplib | 3.0+ | Non-blocking asynchronous SMTP protocol client |
| **Database ORM** | SQLAlchemy | 2.0+ | Modern async ORM supporting connection pooling |
| **Database Migrations**| Alembic | 1.14+ | Schema version control and automated migrations |
| **Database Engine** | PostgreSQL | 16-alpine | Enterprise relational database and job queue store |
| **Security & Hashing** | Bcrypt & Cryptography | Latest | Password hashing (bcrypt) and Fernet AES-128 credential encryption |
| **Token Auth** | Python-Jose | 3.3+ | Stateless JWT authentication with Bearer tokens |
| **Templating** | Jinja2 | 3.1+ | Dynamic email template rendering with auto-escaping |
| **Frontend Framework** | React | 18.3 | Reactive single-page user interface |
| **Language** | TypeScript | 5.6 | End-to-end type safety |
| **Build Tool** | Vite | 5.4 | Ultra-fast frontend bundler and HMR server |
| **Styling** | Tailwind CSS | 3.4 | Modern utility-first responsive styling |
| **Visual Charts** | Recharts | 2.13 | SVG interactive charts and metrics visualization |
| **Icons** | Lucide React | Latest | Clean, consistent icons |
| **Web Server / Ingress**| Nginx | Alpine | Static asset hosting and reverse proxy router |

---

## 6. Database Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ smtp_accounts : "configures"
    users ||--o{ email_templates : "creates"
    users ||--o{ contacts : "manages"
    users ||--o{ email_jobs : "submits"
    
    smtp_accounts ||--o{ email_jobs : "relays"
    smtp_accounts ||--o{ email_attempts : "used in"
    
    email_templates ||--o{ email_jobs : "template for"
    
    email_jobs ||--o{ email_recipients : "contains"
    email_jobs ||--o{ email_attempts : "execution logs"

    users {
        uuid id PK
        string username
        string email
        string hashed_password
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    smtp_accounts {
        uuid id PK
        uuid user_id FK
        string account_name
        string smtp_host
        int smtp_port
        string username
        text encrypted_password
        string security_mode
        string sender_email
        string sender_name
        int connection_timeout
        boolean is_default
        boolean is_active
        timestamp last_tested_at
        string last_test_status
        text last_test_error
    }

    email_jobs {
        uuid id PK
        uuid user_id FK
        uuid smtp_account_id FK
        uuid template_id FK
        string subject
        string sender_email
        string sender_name
        string reply_to
        text html_body
        text text_body
        int recipient_count
        string message_type
        json attachments_meta
        string status
        timestamp scheduled_at
        timestamp next_retry_at
        int retry_count
        int max_retries
        text last_error
        timestamp created_at
        timestamp completed_at
    }

    email_recipients {
        uuid id PK
        uuid email_job_id FK
        string recipient_email
        string recipient_name
        string recipient_type
        string status
        text smtp_response
    }

    email_attempts {
        uuid id PK
        uuid email_job_id FK
        uuid smtp_account_id FK
        int attempt_number
        string status
        int smtp_response_code
        text smtp_response_message
        text error_message
        timestamp attempted_at
        timestamp completed_at
    }

    email_templates {
        uuid id PK
        uuid user_id FK
        string name
        text description
        string subject
        text html_content
        text text_content
        json variables
        timestamp created_at
        timestamp updated_at
    }

    contacts {
        uuid id PK
        uuid user_id FK
        string name
        string email
        string organization
        string group_name
        timestamp created_at
        timestamp updated_at
    }
```

---

## 7. Quick Start: Docker Compose

The simplest and recommended method to run the complete platform (PostgreSQL, Backend API, Background Worker, and Frontend) is via Docker Compose.

### Step 1: Clone Repository & Create `.env`

Create a `.env` file from [.env.example](file:///c:/Users/ANUJ%20SINGH/Desktop/SMTP/.env.example):

```bash
cp .env.example .env
```

Generate secure cryptographic keys using Python:

```bash
# Generate Fernet 32-byte encryption key for SMTP credentials:
python -c "import os, base64; print('ENCRYPTION_KEY=' + base64.urlsafe_b64encode(os.urandom(32)).decode())"

# Generate JWT secret key:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

Paste the outputs into your `.env` file:

```env
SECRET_KEY=your-32-char-random-jwt-secret
ENCRYPTION_KEY=your-base64-encoded-fernet-key
DATABASE_URL=postgresql+asyncpg://smtp_user:smtp_pass@postgres:5432/smtp_db
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://frontend:80"]
STORAGE_PATH=/app/storage/attachments
MAX_ATTACHMENT_SIZE_MB=25
WORKER_POLL_INTERVAL=5
DEFAULT_MAX_RETRIES=3
RETRY_BASE_DELAY=60
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Step 2: Build and Run Services

```bash
# Build all images and start containers in background
docker compose up -d --build
```

### Step 3: Verify Running Services

```bash
docker compose ps
```

You should see all 4 containers healthy and active:
- `smtp_postgres` (Port 5432)
- `smtp_backend` (Port 8000)
- `smtp_worker` (Background Daemon)
- `smtp_frontend` (Port 3000)

### Step 4: Access Applications

| Service | URL | Notes |
|---|---|---|
| **Frontend Dashboard** | [http://localhost:3000](http://localhost:3000) | Web management UI |
| **Interactive API Docs**| [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Swagger UI for exploring REST endpoints |
| **Alternative API Docs**| [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc) | ReDoc interface |
| **System Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | API & DB operational status |

### Container Management Commands

```bash
# View aggregated live logs:
docker compose logs -f

# View backend API logs:
docker logs -f smtp_backend

# View background worker activity:
docker logs -f smtp_worker

# Stop all services:
docker compose down

# Stop all services and delete volumes (resets database):
docker compose down -v
```

---

## 8. Local Development Run (Without Docker)

If you prefer to run services natively on your host machine for development:

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- A running PostgreSQL instance (or local SQLite for lightweight testing)

---

### A. Backend Setup

1. **Navigate to the backend directory and set up a virtual environment:**
   ```bash
   cd backend
   python -m venv .venv
   
   # Activate virtual environment:
   # On Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create `.env` in the project root or inside `backend/.env`:
   ```env
   SECRET_KEY=local-development-secret-key-32chars
   ENCRYPTION_KEY=Eivl44armmiTTCsvOhIuBOE7BijWTGbM4ilVVrabWKk=
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/smtp_db
   ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]
   STORAGE_PATH=./storage/attachments
   ENVIRONMENT=development
   ```

4. **Apply database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Start the Email Worker (in a separate terminal):**
   ```bash
   cd backend
   # Activate your virtual environment first
   python -m app.workers.email_worker
   ```

---

### B. Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install packages:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   Navigate to [http://localhost:5173](http://localhost:5173). The Vite development proxy will automatically route all `/api` calls to `http://localhost:8000`.

---

## 9. Testing & Synthetic Verification

### Automated Unit Test Suite

The platform includes unit tests covering password encryption/decryption, Jinja2 template parsing, syntax validation, SMTP error code classification, and API routing.

Run pytest from the `backend/` directory:

```bash
cd backend
python -m pytest tests/ -v
```

---

### End-to-End Synthetic Flow Test

MailFlow includes a synthetic test runner ([backend/scripts/synthetic_test.py](file:///c:/Users/ANUJ%20SINGH/Desktop/SMTP/backend/scripts/synthetic_test.py)) that executes an end-to-end integration scenario:

1. Verifies `/health` responsiveness.
2. Registers a test user account and receives a JWT access token.
3. Configures an SMTP relay account and tests connectivity.
4. Creates a dynamic Jinja2 template and previews variable substitution.
5. Adds a contact to the directory.
6. Enqueues a multipart email job (`POST /api/v1/emails/send`).
7. Polls the job status until picked up and processed by the worker.
8. Validates updated metrics on `/dashboard/summary`.

Run the synthetic test against your local or Docker platform:

```bash
# Syntax: python backend/scripts/synthetic_test.py <host> <port> <user> <pass> <mode>
python backend/scripts/synthetic_test.py localhost 1025 test test PLAIN
```

---

### Zero-Credential Local SMTP Testing with Mailpit

To test email composition and sending without creating accounts on real email providers, spin up **Mailpit**:

```bash
# Run Mailpit in Docker
docker run -d --name mailpit -p 1025:1025 -p 8025:8025 axllent/mailpit
```

Configure your SMTP account in MailFlow as:
- **SMTP Host:** `localhost` (or `host.docker.internal` / `mailpit` if running inside Docker)
- **SMTP Port:** `1025`
- **Security Mode:** `PLAIN`
- **Username / Password:** Any value (Mailpit accepts all credentials)

Open [http://localhost:8025](http://localhost:8025) in your browser to inspect captured emails, HTML formatting, and attachments in real time.

---

## 10. Popular SMTP Provider Configurations

When ready to deliver real outbound emails, configure your SMTP accounts in MailFlow with the settings below:

### 1. Gmail / Google Workspace
- **Host:** `smtp.gmail.com`
- **Port:** `587`
- **Security Mode:** `STARTTLS`
- **Username:** Your complete Gmail or Google Workspace address (`you@yourcompany.com`)
- **Password:** A 16-character **Google App Password**.
  > Go to **Google Account** $\rightarrow$ **Security** $\rightarrow$ **2-Step Verification** $\rightarrow$ **App passwords** $\rightarrow$ Generate a password for "Mail".

### 2. SendGrid
- **Host:** `smtp.sendgrid.net`
- **Port:** `587`
- **Security Mode:** `STARTTLS`
- **Username:** `apikey` *(literal string)*
- **Password:** Your SendGrid API Key (`SG.xxxxxxxxxxxxxxxx`)

### 3. Amazon SES (Simple Email Service)
- **Host:** `email-smtp.<your-region>.amazonaws.com` (e.g., `email-smtp.us-east-1.amazonaws.com`)
- **Port:** `587`
- **Security Mode:** `STARTTLS`
- **Username:** Your Amazon SES SMTP Username
- **Password:** Your Amazon SES SMTP Password *(Generated in AWS SES console)*

### 4. Mailgun
- **Host:** `smtp.mailgun.org` (US) or `smtp.eu.mailgun.org` (EU)
- **Port:** `587`
- **Security Mode:** `STARTTLS`
- **Username:** `postmaster@yourdomain.com`
- **Password:** Your Mailgun SMTP Password

### 5. Microsoft 365 / Outlook
- **Host:** `smtp.office365.com`
- **Port:** `587`
- **Security Mode:** `STARTTLS`
- **Username:** Your full Microsoft 365 email address
- **Password:** Your Microsoft account password or App Password

---

## 11. REST API Reference

All protected endpoints require an `Authorization: Bearer <JWT>` header.

### 🔑 Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Request Payload | Response |
|---|---|---|---|---|
| `POST` | `/auth/register` | Register new user account | `{username, email, password}` | `TokenResponse` |
| `POST` | `/auth/login` | Authenticate with credentials | `{email, password}` | `TokenResponse` |
| `GET` | `/auth/me` | Fetch authenticated user profile | None | `UserResponse` |
| `POST` | `/auth/logout` | Revoke client session | None | `{message}` |

### ⚙️ SMTP Accounts (`/api/v1/smtp-accounts`)

| Method | Endpoint | Description | Request Payload | Response |
|---|---|---|---|---|
| `GET` | `/smtp-accounts` | List user's SMTP accounts | None | `List[SMTPAccountResponse]` |
| `POST` | `/smtp-accounts` | Add new SMTP account | `SMTPAccountCreate` | `SMTPAccountResponse` |
| `GET` | `/smtp-accounts/{id}` | Get account details | None | `SMTPAccountResponse` |
| `PUT` | `/smtp-accounts/{id}` | Update account details / password | `SMTPAccountUpdate` | `SMTPAccountResponse` |
| `DELETE`| `/smtp-accounts/{id}` | Delete SMTP configuration | None | HTTP 204 No Content |
| `POST` | `/smtp-accounts/{id}/test` | Test host connection & TLS handshake | None | `SMTPTestResult` |
| `POST` | `/smtp-accounts/{id}/set-default`| Set account as primary default | None | `SMTPAccountResponse` |

### 📤 Email Operations (`/api/v1/emails`)

| Method | Endpoint | Description | Request Payload | Response |
|---|---|---|---|---|
| `POST` | `/emails/send` | Submit email job with attachments | Multipart Form (`subject`, `recipients_json`, `html_body`, `attachments`) | `EmailJobResponse` (202 Accepted) |
| `GET` | `/emails/{id}` | Inspect job, recipients & attempt logs | None | `EmailDetailResponse` |
| `POST` | `/emails/{id}/retry` | Re-queue a failed job for retry | None | `EmailJobResponse` |
| `POST` | `/emails/{id}/cancel`| Cancel a pending/retrying email | None | `EmailJobResponse` |

### 📜 History & Audit Logs (`/api/v1/history`)

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/history` | `page`, `per_page`, `status`, `smtp_account_id`, `search`, `date_from`, `date_to` | Paginated search across historical email jobs |
| `GET` | `/history/{id}` | None | Get specific historical job record |
| `GET` | `/history/{id}/attempts` | None | Audit log of raw SMTP attempts and error codes |

### 📝 Email Templates (`/api/v1/templates`)

| Method | Endpoint | Description | Request Payload | Response |
|---|---|---|---|---|
| `GET` | `/templates` | List email templates | None | `List[TemplateResponse]` |
| `POST` | `/templates` | Create new Jinja2 template | `TemplateCreate` | `TemplateResponse` |
| `GET` | `/templates/{id}` | Retrieve specific template | None | `TemplateResponse` |
| `PUT` | `/templates/{id}` | Update template content | `TemplateUpdate` | `TemplateResponse` |
| `DELETE`| `/templates/{id}` | Remove template | None | HTTP 204 No Content |
| `POST` | `/templates/{id}/preview` | Preview rendered HTML/text | `{variables: {key: value}}` | `TemplatePreviewResponse` |

### 👥 Contacts (`/api/v1/contacts`)

| Method | Endpoint | Description | Request Payload / Response |
|---|---|---|---|
| `GET` | `/contacts` | List contacts with search & group filter | Paginated `List[ContactResponse]` |
| `POST` | `/contacts` | Create contact | `{name, email, organization, group_name}` |
| `PUT` | `/contacts/{id}` | Update contact | `{name, email, organization, group_name}` |
| `DELETE`| `/contacts/{id}` | Delete contact | HTTP 204 No Content |
| `POST` | `/contacts/import` | Bulk import contacts from CSV file | Multipart File Upload (`file: contacts.csv`) |
| `GET` | `/contacts/export` | Download all contacts as CSV | Streams `text/csv` attachment |

### 📈 Analytics & Health (`/api/v1/dashboard`, `/health`)

| Method | Endpoint | Description | Response |
|---|---|---|---|
| `GET` | `/dashboard/summary` | Real-time counts (total, accepted, failed, pending, retrying) | `DashboardSummary` |
| `GET` | `/dashboard/email-trends` | Volume trends across specified days (`?days=30`) | `DashboardTrends` |
| `GET` | `/dashboard/account-performance`| Per-account delivery and failure metrics | `DashboardAccountPerformance` |
| `GET` | `/health` | Application & database connection health check | `{"status": "ok", "database": "ok"}` |

---

## 12. Security Architecture

1. **Encrypted Credentials (Zero Plaintext at Rest):**
   - SMTP server passwords are never stored in plain text.
   - Credentials are encrypted before database insertion using **Fernet AES-128-CBC** with HMAC authentication.
   - Credentials are decrypted in-memory only at the exact instant an SMTP connection is established.
2. **Credential Sanitization in Logs & APIs:**
   - Custom logging filters inspect log records and strip any sensitive strings (`password`, `token`, `secret`, `key`).
   - Pydantic models omit `encrypted_password` and plaintext passwords from all GET responses.
3. **No Open Relay Vulnerability:**
   - The platform strictly rejects unauthenticated relay attempts.
   - Outbound mail can only be sent through explicitly verified, user-owned SMTP credentials.
4. **Per-User Isolation:**
   - Every database query strictly filters by `user_id` extracted from validated JWT bearer tokens. Users can never view or dispatch through other users' SMTP relays or address books.
5. **Secure Template Sandbox:**
   - The Jinja2 templating environment explicitly restricts unsafe global builtins and executes in an isolated environment with `StrictUndefined` enforcement.

---

## 13. Troubleshooting & FAQs

### Q: Why did registration fail with `password cannot be longer than 72 bytes`?
**A:** This is a legacy quirk of older `passlib` releases when paired with newer `bcrypt` versions. MailFlow resolves this by using direct `bcrypt` hashing (`bcrypt.hashpw` / `bcrypt.checkpw`) with automatic 72-byte truncation in compliance with the bcrypt specification.

### Q: Can I run MailFlow without configuring a real email provider?
**A:** Yes! Run Mailpit locally via `docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit`, and configure an account pointing to host `localhost`, port `1025`, and security mode `PLAIN`. You can view all outgoing emails at `http://localhost:8025`.

### Q: Port 5432 or Port 3000 is already in use on my machine. What should I do?
**A:** In [docker-compose.yml](file:///c:/Users/ANUJ%20SINGH/Desktop/SMTP/docker-compose.yml), adjust the host-side port bindings:
```yaml
ports:
  - "3001:80"   # Access frontend at http://localhost:3001
ports:
  - "5433:5432" # Access PostgreSQL at port 5433
```

### Q: Does "Accepted" mean the email was delivered to the inbox?
**A:** No. An SMTP `250 OK` status means the receiving mail server has verified the recipients and accepted the message into its delivery pipeline. Delivery to spam or inbox depends on external factors (DKIM, SPF, IP reputation) managed by your SMTP relay provider.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
