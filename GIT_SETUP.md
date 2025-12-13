# Git Setup and Deployment Guide

## Initialize Git Repository

If you haven't initialized Git yet, follow these steps:

### 1. Initialize Git

```bash
git init
```

### 2. Create .gitignore (if not exists)

The `.gitignore` file should already exist. Verify it contains:

```
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
*.log

# Metrics
metrics.json

# OS
.DS_Store
Thumbs.db
```

### 3. Add Remote Repository

Create a new repository on GitHub, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name.

### 4. Add All Files

```bash
git add .
```

### 5. Commit

```bash
git commit -m "Initial commit: LLM Analysis Quiz System complete"
```

### 6. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

## Verify Repository

Check that these files are in your repository:

### ✅ Source Code
- `src/` directory with all Python files
- `tests/` directory with test files

### ✅ Configuration
- `.env.example` (template)
- `requirements.txt`
- `render.yaml`

### ✅ Documentation
- `README.md`
- `DEPLOYMENT.md`
- `RENDER_DEPLOYMENT.md`
- `TROUBLESHOOTING.md`
- `DEPLOYMENT_CHECKLIST.md`
- `PROJECT_SUMMARY.md`
- `LICENSE`

### ✅ Scripts
- `start.sh`
- `start.bat`
- `validate_system.py`
- `test_demo_endpoint.py`

### ❌ NOT in Repository
- `.env` (contains secrets)
- `__pycache__/`
- `venv/`
- `*.pyc`

## Deploy to Render.com

Once your code is on GitHub:

### 1. Go to Render Dashboard

Visit [render.com](https://render.com) and sign in with GitHub.

### 2. Create New Blueprint

1. Click "New +" → "Blueprint"
2. Select your repository
3. Render will detect `render.yaml`

### 3. Add Secret Environment Variables

In the Render dashboard, add:

- `STUDENT_SECRET`: `subhashree_secret_123`
- `OPENAI_API_KEY`: Your OpenAI API key

### 4. Deploy

Click "Apply" and wait 5-10 minutes for deployment.

### 5. Get Your API URL

Your API will be available at:
```
https://your-service-name.onrender.com/quiz
```

## Test Deployment

### Health Check

```bash
curl https://your-service-name.onrender.com/health
```

Expected response:
```json
{"status": "healthy"}
```

### Quiz Endpoint

```bash
curl -X POST https://your-service-name.onrender.com/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "23f3003784@ds.study.iitm.ac.in",
    "secret": "subhashree_secret_123",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

Expected response:
```json
{
  "status": "accepted",
  "message": "Quiz request received and is being processed"
}
```

### Metrics Endpoint

```bash
curl https://your-service-name.onrender.com/metrics
```

## Update Deployment

To update your deployed application:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically detect the push and redeploy.

## Troubleshooting

### Git Issues

**Problem**: `fatal: not a git repository`

**Solution**: Run `git init` in your project directory

**Problem**: `remote origin already exists`

**Solution**: 
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

**Problem**: `.env` file committed to Git

**Solution**:
```bash
git rm --cached .env
git commit -m "Remove .env from repository"
git push origin main
```

### Render Issues

**Problem**: Build fails

**Solution**: Check build logs in Render dashboard, verify `render.yaml` is correct

**Problem**: Service crashes

**Solution**: Check service logs, verify environment variables are set

**Problem**: Out of memory

**Solution**: Upgrade to paid plan or optimize memory usage

## Quick Reference

### Git Commands

```bash
# Check status
git status

# Add files
git add .

# Commit
git commit -m "Your message"

# Push
git push origin main

# Pull latest
git pull origin main

# View remote
git remote -v

# View branches
git branch -a
```

### Render CLI (Optional)

Install Render CLI:
```bash
npm install -g @render/cli
```

Commands:
```bash
# Login
render login

# List services
render services list

# View logs
render logs -s your-service-name

# Deploy
render deploy -s your-service-name
```

## Next Steps

1. ✅ Initialize Git repository
2. ✅ Push to GitHub
3. ✅ Deploy to Render
4. ✅ Test endpoints
5. ✅ Submit API URL

Your API endpoint to submit:
```
https://your-service-name.onrender.com/quiz
```

## Support

- **Git Help**: https://git-scm.com/doc
- **GitHub Help**: https://docs.github.com
- **Render Help**: https://render.com/docs

For project-specific issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
