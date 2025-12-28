# Privacy Check - What's in the Documentation

## ✅ Safe to Share (Generic Examples)

All markdown files in `readme/` use generic placeholders:

- `/Users/you/...` - Generic user
- `/Users/username/...` - Generic username  
- `email@gmail.com` - Generic email
- `/path/to/nuon-mcp` - Generic paths
- `/path/to/example-app-configs` - Generic repo paths

## ❌ NOT in Documentation (Your Personal Info)

The following are **NOT** included in any markdown files:

- Your username (markmilligan)
- Your email (mtm20176@gmail.com)
- Your actual file paths
- Your Google Drive paths

## 📝 Files That DO Contain Personal Info

These files are in `.gitignore` and won't be committed:

- `config.yaml` - Your personal repository paths
- `__pycache__/` - Python cache
- `venv/` - Your virtual environment

## ✅ Safe to Commit

These files are safe to share publicly:

- `README.md` - Main documentation
- `readme/*.md` - All documentation (sanitized)
- `server.py` - Generic server code
- `config.example.yaml` - Template with example paths
- `.mcp.json.example` - Template configuration
- `requirements.txt` - Python dependencies
- Test scripts - Generic examples

## Verification

To check for personal info before committing:

```bash
# Check for your username
grep -r "your-username" .

# Check for your email
grep -r "your-email" .

# Check for specific paths
grep -r "/Users/your-username" .
```

Replace `your-username` and `your-email` with your actual values.

## Public Repository Names

The documentation does reference public Nuon repositories:
- `example-app-configs` (public)
- `nuon/docs` (public)
- `acme-ch` (public)

These are fine to include as they're public projects.
