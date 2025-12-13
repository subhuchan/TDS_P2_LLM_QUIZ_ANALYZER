# Simple Deployment Guide

This guide provides a straightforward deployment approach without Docker.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd TDS_P2
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

### 5. Configure Environment Variables

Copy `.env.example` to `.env` and update with your credentials:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` with your actual values:
```
STUDENT_EMAIL=23f3003784@ds.study.iitm.ac.in
STUDENT_SECRET=subhashree_secret_123
API_ENDPOINT_URL=https://tds-llm-analysis.s-anand.net/submit
OPENAI_API_KEY=your-openai-api-key
```

### 6. Run the Application

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test

```bash
pytest tests/test_e2e_integration.py -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

## Production Deployment (Simple)

### Option 1: Direct Server Deployment

1. **Set up a Linux server** (Ubuntu 20.04+ recommended)

2. **Install Python and dependencies**:
```bash
sudo apt update
sudo apt install python3.10 python3-pip python3-venv
```

3. **Clone and setup**:
```bash
git clone <your-repo-url>
cd TDS_P2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps  # Install system dependencies
```

4. **Configure environment**:
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

5. **Run with systemd** (recommended for production):

Create `/etc/systemd/system/llm-quiz.service`:
```ini
[Unit]
Description=LLM Analysis Quiz System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/TDS_P2
Environment="PATH=/path/to/TDS_P2/venv/bin"
ExecStart=/path/to/TDS_P2/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable llm-quiz
sudo systemctl start llm-quiz
sudo systemctl status llm-quiz
```

6. **Set up reverse proxy** (optional, for HTTPS):

Install nginx:
```bash
sudo apt install nginx
```

Configure nginx (`/etc/nginx/sites-available/llm-quiz`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/llm-quiz /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Option 2: Platform-as-a-Service (PaaS)

#### Render.com (Recommended - Free Tier Available)

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: llm-quiz-system
    env: python
    buildCommand: "pip install -r requirements.txt && playwright install chromium && playwright install-deps"
    startCommand: "python -m src.main"
    envVars:
      - key: STUDENT_EMAIL
        sync: false
      - key: STUDENT_SECRET
        sync: false
      - key: API_ENDPOINT_URL
        value: https://tds-llm-analysis.s-anand.net/submit
      - key: OPENAI_API_KEY
        sync: false
      - key: API_HOST
        value: 0.0.0.0
      - key: API_PORT
        value: 8000
```

2. Push to GitHub
3. Connect repository to Render
4. Add environment variables in Render dashboard
5. Deploy

#### Railway.app

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Add environment variables:
```bash
railway variables set STUDENT_EMAIL=23f3003784@ds.study.iitm.ac.in
railway variables set STUDENT_SECRET=subhashree_secret_123
railway variables set OPENAI_API_KEY=your-key
```

4. Deploy:
```bash
railway up
```

#### Heroku

1. Create `Procfile`:
```
web: python -m src.main
```

2. Create `runtime.txt`:
```
python-3.10.12
```

3. Deploy:
```bash
heroku create your-app-name
heroku config:set STUDENT_EMAIL=23f3003784@ds.study.iitm.ac.in
heroku config:set STUDENT_SECRET=subhashree_secret_123
heroku config:set OPENAI_API_KEY=your-key
git push heroku main
```

### Option 3: Serverless (AWS Lambda)

Use Mangum adapter for FastAPI on AWS Lambda:

1. Install additional dependency:
```bash
pip install mangum
```

2. Create `lambda_handler.py`:
```python
from mangum import Mangum
from src.api import app

handler = Mangum(app)
```

3. Deploy using AWS SAM or Serverless Framework

## Monitoring

### View Logs

**Systemd service**:
```bash
sudo journalctl -u llm-quiz -f
```

**Direct run**:
Logs are output to console with structured JSON format

### Health Check

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Playwright Issues

If browser automation fails:
```bash
playwright install-deps
playwright install chromium --force
```

### Port Already in Use

Change port in `.env`:
```
API_PORT=8001
```

### Permission Issues

Ensure the user has write permissions for logs and temp files:
```bash
chmod -R 755 /path/to/TDS_P2
```

## Quick Start (One Command)

For development:
```bash
# Windows
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && playwright install chromium && python -m src.main

# Linux/Mac
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && playwright install chromium && python -m src.main
```

## Security Notes

- Never commit `.env` file to version control
- Use environment variables for sensitive data
- Enable HTTPS in production (use Let's Encrypt with nginx)
- Restrict API access with firewall rules if needed
- Rotate secrets regularly

## Performance Tips

- Use `BROWSER_HEADLESS=true` in production
- Adjust `QUIZ_TIMEOUT` based on your needs
- Monitor memory usage (Playwright can be memory-intensive)
- Consider using a process manager like PM2 or supervisord
