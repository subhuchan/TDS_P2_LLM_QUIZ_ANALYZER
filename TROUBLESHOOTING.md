# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the LLM Analysis Quiz System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Runtime Errors](#runtime-errors)
- [API Issues](#api-issues)
- [Browser Automation Issues](#browser-automation-issues)
- [LLM Integration Issues](#llm-integration-issues)
- [Deployment Issues](#deployment-issues)
- [Performance Issues](#performance-issues)

## Installation Issues

### Issue: `pip install` fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
1. Update pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Use Python 3.10 or higher:
   ```bash
   python --version
   ```

3. Install in virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

### Issue: Playwright installation fails

**Symptoms:**
```
ERROR: Failed to install browsers
```

**Solutions:**
1. Install system dependencies (Linux):
   ```bash
   playwright install-deps
   ```

2. Install specific browser:
   ```bash
   playwright install chromium
   ```

3. Check disk space:
   ```bash
   df -h  # Linux/Mac
   ```

4. Run with sudo (Linux):
   ```bash
   sudo playwright install chromium
   ```

### Issue: Module not found errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
```

**Solutions:**
1. Ensure you're in the project root directory
2. Activate virtual environment
3. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration Issues

### Issue: Environment variables not loaded

**Symptoms:**
```
ValidationError: STUDENT_EMAIL field required
```

**Solutions:**
1. Create `.env` file from example:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values

3. Verify `.env` is in project root (same directory as `src/`)

4. Check for typos in variable names

5. Restart application after changing `.env`

### Issue: Invalid OpenAI API key

**Symptoms:**
```
AuthenticationError: Invalid API key
```

**Solutions:**
1. Verify API key in `.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```

2. Check key hasn't expired at https://platform.openai.com/api-keys

3. Ensure no extra spaces or quotes around the key

4. Generate new API key if needed

### Issue: Wrong API endpoint URL

**Symptoms:**
```
Connection refused or 404 errors
```

**Solutions:**
1. Verify URL in `.env`:
   ```
   API_ENDPOINT_URL=https://tds-llm-analysis.s-anand.net/submit
   ```

2. Test URL manually:
   ```bash
   curl https://tds-llm-analysis.s-anand.net/submit
   ```

3. Check for typos (http vs https, trailing slashes)

## Runtime Errors

### Issue: Application crashes on startup

**Symptoms:**
```
Error: Address already in use
```

**Solutions:**
1. Change port in `.env`:
   ```
   API_PORT=8001
   ```

2. Kill process using port 8000:
   ```bash
   # Linux/Mac
   lsof -ti:8000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

### Issue: Timeout errors

**Symptoms:**
```
TimeoutError: Quiz sequence exceeded 180 second time limit
```

**Solutions:**
1. Increase timeout in `.env`:
   ```
   QUIZ_TIMEOUT=300
   ```

2. Check internet connection speed

3. Optimize quiz solving logic

4. Use faster LLM model (gpt-3.5-turbo instead of gpt-4)

### Issue: Memory errors

**Symptoms:**
```
MemoryError: Unable to allocate memory
```

**Solutions:**
1. Close unused browser instances

2. Reduce concurrent requests

3. Increase system memory

4. Use headless browser mode:
   ```
   BROWSER_HEADLESS=true
   ```

5. Limit file sizes:
   ```
   MAX_FILE_SIZE_MB=5
   ```

## API Issues

### Issue: 403 Forbidden errors

**Symptoms:**
```json
{"error": "Invalid secret"}
```

**Solutions:**
1. Verify secret matches in `.env` and request:
   ```
   STUDENT_SECRET=your-secret-here
   ```

2. Check for extra spaces or special characters

3. Ensure secret is sent in request body:
   ```json
   {
     "email": "...",
     "secret": "your-secret-here",
     "url": "..."
   }
   ```

### Issue: 400 Bad Request errors

**Symptoms:**
```json
{"error": "Invalid JSON payload"}
```

**Solutions:**
1. Verify JSON is valid:
   ```bash
   echo '{"email":"...","secret":"...","url":"..."}' | jq .
   ```

2. Check all required fields are present:
   - `email`
   - `secret`
   - `url`

3. Ensure Content-Type header is set:
   ```
   Content-Type: application/json
   ```

4. Check for trailing commas in JSON

### Issue: No response from API

**Symptoms:**
- Request hangs indefinitely
- No logs appear

**Solutions:**
1. Check if server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify firewall isn't blocking port

3. Check logs for errors:
   ```bash
   # If running with systemd
   sudo journalctl -u llm-quiz -f
   ```

4. Restart server

## Browser Automation Issues

### Issue: Browser fails to launch

**Symptoms:**
```
Error: Failed to launch browser
```

**Solutions:**
1. Reinstall Playwright browsers:
   ```bash
   playwright install chromium --force
   ```

2. Install system dependencies:
   ```bash
   playwright install-deps
   ```

3. Check if running in headless mode:
   ```
   BROWSER_HEADLESS=true
   ```

4. Verify sufficient disk space

5. Check permissions (Linux):
   ```bash
   chmod +x ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome
   ```

### Issue: Page load timeout

**Symptoms:**
```
TimeoutError: Page load exceeded 30000ms
```

**Solutions:**
1. Increase browser timeout:
   ```
   BROWSER_TIMEOUT=60000
   ```

2. Check internet connection

3. Verify URL is accessible:
   ```bash
   curl -I https://tds-llm-analysis.s-anand.net/demo
   ```

4. Try different network

### Issue: JavaScript not executing

**Symptoms:**
- Page content is empty
- Base64 content not found

**Solutions:**
1. Ensure using Playwright (not requests library)

2. Wait for page to load completely:
   ```python
   await page.wait_for_load_state("networkidle")
   ```

3. Check browser console for errors

4. Verify JavaScript is enabled

## LLM Integration Issues

### Issue: LLM API rate limit

**Symptoms:**
```
RateLimitError: Rate limit exceeded
```

**Solutions:**
1. Wait and retry (automatic in code)

2. Upgrade OpenAI plan for higher limits

3. Implement exponential backoff

4. Use different API key

### Issue: LLM returns incorrect format

**Symptoms:**
- Answer validation fails
- Type conversion errors

**Solutions:**
1. Use structured outputs in prompt

2. Add explicit format instructions

3. Validate and retry with corrected prompt

4. Use JSON mode for structured responses:
   ```python
   response = client.chat.completions.create(
       model="gpt-4",
       response_format={"type": "json_object"},
       messages=[...]
   )
   ```

### Issue: LLM context length exceeded

**Symptoms:**
```
InvalidRequestError: maximum context length exceeded
```

**Solutions:**
1. Reduce input size:
   - Summarize long documents
   - Extract only relevant sections
   - Use smaller data samples

2. Use model with larger context:
   - gpt-4-turbo (128k tokens)
   - gpt-4-32k (32k tokens)

3. Split task into smaller chunks

## Deployment Issues

### Issue: Render deployment fails

**Symptoms:**
- Build fails
- Service crashes on startup

**Solutions:**
1. Check build logs in Render dashboard

2. Verify `render.yaml` is correct

3. Ensure all environment variables are set

4. Check Python version compatibility:
   ```yaml
   runtime: python-3.11
   ```

5. Verify build command includes Playwright:
   ```
   playwright install chromium && playwright install-deps
   ```

### Issue: Render service out of memory

**Symptoms:**
```
Error: Process killed (OOM)
```

**Solutions:**
1. Upgrade to paid plan (more RAM)

2. Optimize memory usage:
   - Close browsers after use
   - Limit concurrent requests
   - Reduce file sizes

3. Use memory profiling:
   ```python
   import tracemalloc
   tracemalloc.start()
   ```

### Issue: Render cold starts are slow

**Symptoms:**
- First request takes 30+ seconds
- Service spins down after inactivity

**Solutions:**
1. Upgrade to paid plan (always-on)

2. Use cron job to keep service warm:
   ```bash
   # Ping every 10 minutes
   */10 * * * * curl https://your-service.onrender.com/health
   ```

3. Optimize startup time:
   - Lazy load heavy dependencies
   - Cache Playwright browsers

## Performance Issues

### Issue: Slow quiz solving

**Symptoms:**
- Takes close to 3 minutes
- Frequently times out

**Solutions:**
1. Profile code to find bottlenecks:
   ```python
   import cProfile
   cProfile.run('solve_quiz()')
   ```

2. Optimize data processing:
   - Use vectorized operations (pandas/numpy)
   - Avoid loops where possible
   - Cache repeated calculations

3. Parallelize independent tasks:
   ```python
   results = await asyncio.gather(
       download_file(url1),
       download_file(url2)
   )
   ```

4. Use faster LLM model:
   ```
   OPENAI_MODEL=gpt-3.5-turbo
   ```

### Issue: High memory usage

**Symptoms:**
- System becomes slow
- Out of memory errors

**Solutions:**
1. Monitor memory usage:
   ```python
   import psutil
   print(f"Memory: {psutil.virtual_memory().percent}%")
   ```

2. Close resources properly:
   ```python
   async with browser_manager:
       # Use browser
       pass  # Automatically closed
   ```

3. Limit data size:
   - Process data in chunks
   - Delete large objects when done
   - Use generators instead of lists

4. Profile memory:
   ```bash
   pip install memory_profiler
   python -m memory_profiler script.py
   ```

## Debugging Tips

### Enable Debug Logging

Set in `.env`:
```
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### View Structured Logs

Logs are in JSON format by default. Use `jq` to parse:
```bash
python -m src.main | jq .
```

### Test Individual Components

```python
# Test browser
from src.browser_manager import BrowserManager
browser = BrowserManager()
html = await browser.fetch_and_render("https://example.com")

# Test parser
from src.task_parser import TaskParser
parser = TaskParser()
task = parser.parse_quiz_page(html)

# Test LLM
from src.llm_agent import LLMAgent
agent = LLMAgent()
answer = await agent.solve_task(task)
```

### Use Python Debugger

```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with launch.json:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "src.main",
      "console": "integratedTerminal"
    }
  ]
}
```

## Getting Help

If you're still stuck:

1. **Check logs** - Most issues are logged with context
2. **Search issues** - Check GitHub issues for similar problems
3. **Test components** - Isolate the failing component
4. **Simplify** - Remove complexity until it works
5. **Ask for help** - Provide logs and steps to reproduce

## Common Error Messages

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| `ValidationError` | Missing/invalid env vars | Check `.env` file |
| `AuthenticationError` | Invalid OpenAI key | Verify API key |
| `TimeoutError` | Operation too slow | Increase timeout |
| `ConnectionError` | Network issue | Check internet |
| `MemoryError` | Out of RAM | Close resources |
| `FileNotFoundError` | Missing file | Check file path |
| `JSONDecodeError` | Invalid JSON | Validate JSON |
| `ImportError` | Missing dependency | Run `pip install` |

## Prevention Tips

1. **Use virtual environments** - Avoid dependency conflicts
2. **Pin dependencies** - Use exact versions in requirements.txt
3. **Test locally first** - Before deploying
4. **Monitor logs** - Catch issues early
5. **Set up alerts** - For critical errors
6. **Keep backups** - Of working configurations
7. **Document changes** - Know what you changed
8. **Use version control** - Git for all code changes

## Quick Diagnostic Commands

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check environment variables
python -c "from src.config import settings; print(settings)"

# Test API endpoint
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","secret":"test","url":"https://example.com"}'

# Check browser installation
playwright --version

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep python

# Check port usage
netstat -tulpn | grep 8000
```
