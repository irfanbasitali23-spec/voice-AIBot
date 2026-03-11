# Voice AI Agent — Patient Registration System

A voice-based AI agent accessible via a real phone number that collects U.S. patient demographic information through natural conversation, persists data to a database, and exposes it through a REST API with a web dashboard.

## 🏗️ Architecture

```
Phone Call (Caller)  ↔  Vapi (Telephony + STT/TTS)  ↔  OpenAI GPT-4o-mini (LLM)
                                    ↕
                         Flask Backend (Webhooks)
                                    ↕
                         SQLite Database (Persistent)
                                    ↕
                         REST API + Web Dashboard
```

### System Flow
1. **Caller dials the phone number** → Vapi answers with our configured voice agent
2. **Voice agent (Sarah)** greets the caller and collects patient demographics conversationally
3. **LLM makes tool calls** → Vapi sends webhook requests to our Flask server
4. **Backend processes tool calls** → checks for duplicates, validates data, saves to SQLite
5. **Agent confirms** registration and ends the call gracefully
6. **Call transcript/summary** is stored via end-of-call webhook
7. **REST API & Dashboard** allow querying and viewing all registered patients

## 🛠️ Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Telephony + Voice AI** | [Vapi](https://vapi.ai) | Abstracts STT/TTS/telephony complexity; free tier includes a US phone number; fastest path to a working system |
| **LLM** | OpenAI GPT-4o-mini | Excellent function-calling support, fast response times for voice, cost-effective |
| **Voice** | Vapi Built-in (Clara) | Natural-sounding voice, no extra API key needed |
| **Transcription** | Deepgram Nova-2 | High-accuracy real-time transcription via Vapi |
| **Backend** | Python + Flask | Clean, readable code; excellent ecosystem; easy deployment |
| **Database** | SQLite (stdlib) | Zero-config, persistent, survives restarts, perfect for this scope |
| **Validation** | Custom validators | Comprehensive validation with clear error messages |
| **Security** | CORS + Rate Limiting (flask-limiter) | Production-oriented security defaults |
| **Logging** | Python logging + RotatingFileHandler | Structured logging to console + file, essential for debugging voice agent interactions |
| **Dashboard** | Vanilla HTML + TailwindCSS | Zero build step, fast to develop, clean UI |
| **Deployment** | Render | Free tier with persistent disk for SQLite, easy GitHub integration |

## 📋 Features

### Core Requirements ✅
- [x] Real dialable U.S. phone number via Vapi
- [x] Natural conversational voice agent (not IVR)
- [x] LLM-powered with GPT-4o-mini
- [x] Collects all required patient demographics
- [x] Validates data inline (DOB, phone, state, ZIP)
- [x] Confirms all information before saving
- [x] Handles corrections and re-prompts
- [x] Persistent SQLite database (survives restarts)
- [x] Full REST API (GET, POST, PUT, DELETE)
- [x] Soft-delete support

### Bonus Features ✅
- [x] **Duplicate Detection** — Checks phone number for returning callers, offers to update
- [x] **Call Transcript Storage** — Stores transcripts and summaries linked to patient records
- [x] **Web Dashboard** — Beautiful UI to view registered patients and call logs
- [x] **Automated Tests** — pytest for API layer testing

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- A [Vapi](https://vapi.ai) account (free tier)
- An OpenAI API key (configured in Vapi dashboard)

### 1. Clone & Install

```bash
git clone <repository-url>
cd VoiceAgent
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
PORT=3000
NODE_ENV=development
VAPI_API_KEY=your_vapi_api_key_here
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id_here
VAPI_WEBHOOK_SECRET=your_optional_secret
DATABASE_PATH=./data/patients.db
LOG_LEVEL=info
```

### 3. Seed Database (Optional)

```bash
python -m src_python.seed
```

This adds 2 sample patient records for demonstration.

### 4. Start the Server

```bash
# Development (with auto-reload)
python -m src_python.app

# Production (with gunicorn)
gunicorn --bind 0.0.0.0:3000 "src_python.app:create_app()"
```

The server starts on `http://localhost:3000`:
- **Dashboard**: `http://localhost:3000`
- **API**: `http://localhost:3000/patients`
- **Health**: `http://localhost:3000/health`
- **Vapi Webhook**: `http://localhost:3000/vapi/webhook`

### 5. Configure Vapi

#### Option A: Automated Setup (Recommended)
After deploying your server, run:
```bash
python -m src_python.vapi.setup_assistant https://your-deployed-url.com
```

This creates the assistant in Vapi and links it to your phone number.

#### Option B: Manual Setup via Vapi Dashboard
1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Create a new Assistant
3. Set the model to GPT-4o-mini with the system prompt from `src_python/vapi/system_prompt.py`
4. Add the tools from `src_python/vapi/tool_definitions.py`
5. Set the Server URL to `https://your-app.com/vapi/webhook`
6. Buy/import a phone number and assign the assistant

#### Option C: Use assistant-request webhook
1. In Vapi Dashboard, create a phone number
2. Instead of assigning an assistant, set the **Server URL** to `https://your-app.com/vapi/webhook`
3. The webhook will dynamically return the assistant configuration on each call

### 6. Deploy to Render

1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Web Service"
4. Connect your repository
5. Render will auto-detect `render.yaml` settings
6. Add environment variables (VAPI_API_KEY, etc.)
7. Deploy!

The persistent disk ensures SQLite data survives deploys.

### 7. Run Tests

```bash
python -m pytest tests/test_patients.py -v
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/patients` | List all patients. Supports `?last_name=`, `?date_of_birth=`, `?phone_number=`, `?page=`, `?limit=` |
| `GET` | `/patients/:id` | Get a single patient by UUID |
| `POST` | `/patients` | Create a new patient |
| `PUT` | `/patients/:id` | Update a patient (partial updates) |
| `DELETE` | `/patients/:id` | Soft-delete a patient |
| `GET` | `/call-logs` | List all call logs |
| `GET` | `/call-logs/patient/:id` | Get call logs for a patient |
| `GET` | `/health` | Health check |
| `POST` | `/vapi/webhook` | Vapi webhook endpoint |

### Example: Create Patient
```bash
curl -X POST http://localhost:3000/patients \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1985-03-15",
    "sex": "Female",
    "phone_number": "5551234567",
    "address_line_1": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701"
  }'
```

### Example: List with Filters
```bash
curl "http://localhost:3000/patients?last_name=Doe&page=1&limit=10"
```

## 🗃️ Database Schema

```sql
patients (
  patient_id       TEXT PRIMARY KEY (UUID),
  first_name       TEXT NOT NULL (1-50 chars),
  last_name        TEXT NOT NULL (1-50 chars),
  date_of_birth    TEXT NOT NULL (YYYY-MM-DD),
  sex              TEXT NOT NULL (Male|Female|Other|Decline to Answer),
  phone_number     TEXT NOT NULL (10-digit),
  email            TEXT,
  address_line_1   TEXT NOT NULL,
  address_line_2   TEXT,
  city             TEXT NOT NULL,
  state            TEXT NOT NULL (2-letter),
  zip_code         TEXT NOT NULL (5-digit or ZIP+4),
  insurance_provider      TEXT,
  insurance_member_id     TEXT,
  preferred_language      TEXT DEFAULT 'English',
  emergency_contact_name  TEXT,
  emergency_contact_phone TEXT,
  created_at       TEXT (UTC ISO 8601),
  updated_at       TEXT (UTC ISO 8601),
  deleted_at       TEXT (NULL = active, set = soft-deleted)
)
```

## 🤖 Voice Agent Design

### System Prompt
The full system prompt is in `src_python/vapi/system_prompt.py`. Key design decisions:

- **Persona**: "Sarah" — a warm, professional intake coordinator
- **Flow**: Greeting → Required fields → Optional fields offer → Confirmation → Save → Farewell
- **Validation**: Inline re-prompting for invalid data (future DOB, short phone numbers, invalid states)
- **Edge cases**: Handles corrections, spelling confirmations, out-of-order responses, restart requests
- **Duplicate detection**: Checks phone number at start to detect returning callers

### Tool Definitions
Three tools are available to the LLM during conversation:
1. `check_existing_patient` — Lookup by phone number (duplicate detection)
2. `save_patient` — Create a new patient record
3. `update_patient` — Update an existing patient record

## 🔒 Security Considerations

- **No hardcoded API keys** — all credentials via environment variables
- **Rate limiting** — 100 requests per 15 minutes on API endpoints (flask-limiter)
- **Input validation** — comprehensive custom validators on all endpoints
- **CORS** enabled for cross-origin dashboard access (flask-cors)
- **Soft-delete** — no hard deletes, data recovery possible

## 📊 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Server port (default: 3000) |
| `NODE_ENV` | No | Environment (default: development) |
| `VAPI_API_KEY` | Yes | Your Vapi API key |
| `VAPI_PHONE_NUMBER_ID` | Yes | Vapi phone number ID |
| `VAPI_WEBHOOK_SECRET` | No | Webhook verification secret |
| `DATABASE_PATH` | No | SQLite file path (default: ./data/patients.db) |
| `LOG_LEVEL` | No | Logging level (default: info) |

## ⚠️ Known Limitations & Trade-offs

1. **SQLite vs PostgreSQL**: Chose SQLite for simplicity and zero-config. For production scale, migrate to PostgreSQL. The Render persistent disk provides durability.

2. **No HIPAA compliance**: This is a technical assessment. No real patient data should be stored. In production, would need encryption at rest, audit logs, BAA with cloud provider.

3. **Single-instance only**: SQLite doesn't support multiple write processes. For horizontal scaling, switch to PostgreSQL/MySQL.

4. **Voice latency**: Tool call round-trips add ~1-2s latency during save operations. Acceptable for this use case but could be optimized with async processing.

5. **No authentication on API**: The REST API is open. In production, add JWT/API key authentication.

6. **Rate limiting is per-IP**: In production behind a load balancer, would need to use X-Forwarded-For header properly.

## 🔮 Next Steps (If More Time)

- **Authentication**: JWT-based API auth + admin dashboard login
- **PostgreSQL migration**: For production scalability
- **Appointment Scheduling**: Post-registration appointment booking (mock)
- **Multi-language Support**: Spanish language detection and response
- **WebSocket updates**: Real-time dashboard updates when new patients register
- **HIPAA compliance**: Encryption at rest, audit logging, access controls
- **CI/CD pipeline**: GitHub Actions for automated testing and deployment
- **Monitoring**: Error tracking (Sentry), uptime monitoring, performance metrics

## 📁 Project Structure

```
VoiceAgent/
├── src_python/
│   ├── config.py              # Environment configuration
│   ├── logger.py              # Logging setup (console + rotating files)
│   ├── database.py            # SQLite initialization, tables, WAL mode
│   ├── validation.py          # Request validation rules
│   ├── seed.py                # Database seed script
│   ├── app.py                 # Flask app entry point
│   ├── models/
│   │   ├── patient.py         # Patient data model
│   │   └── call_log.py        # Call log data model
│   ├── routes/
│   │   ├── patients.py        # Patient CRUD endpoints
│   │   ├── call_logs.py       # Call log endpoints
│   │   └── vapi_webhook.py    # Vapi webhook handler
│   └── vapi/
│       ├── system_prompt.py   # LLM system prompt (documented)
│       ├── tool_definitions.py # Function calling tool schemas
│       └── setup_assistant.py # One-time Vapi setup script
├── src/
│   └── public/                # Dashboard static files
│       └── index.html
├── tests/
│   └── test_patients.py       # API integration tests (pytest)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore
├── render.yaml                # Render deployment config
└── README.md
```

## 📞 Live Demo

- **Phone Number**: `[TO BE ADDED AFTER DEPLOYMENT]`
- **API Base URL**: `[TO BE ADDED AFTER DEPLOYMENT]`
- **Dashboard**: `[TO BE ADDED AFTER DEPLOYMENT]`


## Run the command in the termical before running the main application
python -m src_python.vapi.setup_assistant https://derived-decisions-accounting-anti.trycloudflare.com

## after this 
Main file that runs frontend and backend both 
python -m src_python.app      