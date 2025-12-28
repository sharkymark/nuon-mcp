# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Added repository to config.yaml but Claude doesn't see it

#### Symptoms
- You edited config.yaml
- Restarted Claude
- New repository doesn't appear in `list_sources`

#### Solution 1: Check the Server Startup Logs

Run the server manually to see what's happening:

```bash
cd /path/to/nuon-mcp
python server.py
```

Look for errors like:
```
✗ my-repo: Path does not exist: /some/path
```

Press Ctrl+C to stop the manual test.

#### Solution 2: Paths with Spaces Need Quotes

**❌ Wrong (will fail):**
```yaml
- label: my-notes
  path: /Users/me/Google Drive/Notes
```

**❌ Also wrong (backslashes don't work in YAML):**
```yaml
- label: my-notes
  path: /Users/me/Google\ Drive/Notes
```

**✅ Correct (use quotes):**
```yaml
- label: my-notes
  path: "/Users/me/Google Drive/Notes"
```

#### Solution 3: Verify the Path Exists

Test the path in your terminal:

```bash
ls "/Users/me/Google Drive/Notes"
```

If you get "No such file or directory", the path is wrong.

#### Solution 4: Use the Actual Path

Google Drive and other cloud storage often use different paths than you might expect.

**What you think the path is:**
```
/Users/me/Google Drive/Notes
```

**What it actually is:**
```
/Users/me/Library/CloudStorage/GoogleDrive-email@gmail.com/My Drive/Notes
```

To find the actual path:
```bash
# Navigate to the folder in Finder
# Drag the folder into Terminal
# Terminal will show the actual path
```

Or use:
```bash
cd ~/Library/CloudStorage
ls
```

### Issue: Server shows "✗ Path does not exist"

#### Cause
The path in config.yaml doesn't exist or has typos.

#### Solution

1. **Check for typos:**
   - Extra/missing slashes
   - Wrong capitalization (macOS is usually case-insensitive but be careful)
   - Missing quotes around paths with spaces

2. **Test the path:**
   ```bash
   ls "/exact/path/from/config.yaml"
   ```

3. **Use tab completion:**
   ```bash
   ls /Users/me/[press Tab]
   ```
   This helps you see what's actually there.

### Issue: Repository loads but has 0 files

#### Symptoms
```
✓ my-repo: /path/to/repo (0 files)
```

#### Causes
1. The directory is empty
2. The directory only contains subdirectories (no files at root level)
3. Permission issues

#### Solution

Check what's in the directory:
```bash
ls -la "/path/to/repo"
find "/path/to/repo" -type f | head -20
```

This is actually **not a problem** if you have files in subdirectories - the tools will still find them!

### Issue: "ripgrep not found" error

#### Symptoms
When searching, you get:
```
Error: ripgrep (rg) not found. Please install ripgrep.
```

#### Solution

Install ripgrep:

**macOS:**
```bash
brew install ripgrep
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ripgrep
```

**Linux (Fedora/RHEL):**
```bash
sudo yum install ripgrep
```

**Verify installation:**
```bash
rg --version
```

### Issue: Changes to config.yaml not taking effect

#### Symptoms
- You edit config.yaml
- Restart Claude
- Changes don't appear

#### Solutions

1. **Make sure you saved the file!**
   - Check the file modification time:
     ```bash
     ls -l config.yaml
     ```

2. **Make sure you're editing the right config.yaml:**
   - The one next to server.py
   - Not config.example.yaml

3. **Check for YAML syntax errors:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

   If there's an error, you'll see it.

4. **Fully restart Claude:**
   - Exit Claude (Ctrl+D or type `exit`)
   - Start new session: `claude`

### Issue: "Configuration file not found"

#### Symptoms
```
Error: Configuration file not found: /path/to/config.yaml
Please copy config.example.yaml to config.yaml
```

#### Solution

You need to create config.yaml:

```bash
cd /path/to/nuon-mcp
cp config.example.yaml config.yaml
# Edit config.yaml with your paths
```

### Issue: Permission denied when reading files

#### Symptoms
Claude says "Cannot read file" or "Permission denied"

#### Causes
1. File has restrictive permissions
2. Directory has restrictive permissions
3. File is in a protected system location

#### Solution

Check permissions:
```bash
ls -la /path/to/file
```

If needed, fix permissions:
```bash
chmod 644 /path/to/file  # Make file readable
chmod 755 /path/to/directory  # Make directory accessible
```

### Issue: Google Drive files not syncing

#### Symptoms
- Files appear in Google Drive web interface
- Don't appear when MCP server searches
- Directory shows fewer files than expected

#### Cause
Google Drive for Desktop uses "streaming" - files aren't always downloaded locally.

#### Solution

**Option 1: Make files available offline**
1. Right-click folder in Finder
2. Select "Available offline"

**Option 2: Force sync**
1. Open Google Drive app
2. Preferences → Sync options
3. Select "Mirror files" instead of "Stream files"

**Option 3: Accept streaming behavior**
- MCP can only search files that are downloaded locally
- Files will download on-demand as you access them

### Issue: MCP server not starting

#### Symptoms
```bash
claude mcp list
```
Shows: `nuon: ✗ Not connected` or `✗ Failed`

#### Solutions

1. **Check Python path:**
   ```bash
   which python
   # Should match the path in your MCP config
   ```

2. **Test server manually:**
   ```bash
   cd /path/to/nuon-mcp
   python server.py
   ```
   Look for error messages.

3. **Check virtual environment:**
   ```bash
   cd /path/to/nuon-mcp
   source venv/bin/activate
   python server.py
   ```

4. **Reinstall dependencies:**
   ```bash
   cd /path/to/nuon-mcp
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Re-register the MCP server:**
   ```bash
   claude mcp remove nuon
   claude mcp add --scope user --transport stdio nuon -- /path/to/venv/bin/python /path/to/server.py
   ```

## Path Examples

### macOS Common Paths

```yaml
# Home directory (both work)
path: /Users/username/Documents
path: ~/Documents  # ~ gets expanded automatically

# iCloud Drive
path: /Users/username/Library/Mobile Documents/com~apple~CloudDocs

# Dropbox
path: /Users/username/Dropbox

# Google Drive (streaming)
path: /Users/username/Library/CloudStorage/GoogleDrive-email@gmail.com/My Drive

# OneDrive
path: /Users/username/Library/CloudStorage/OneDrive-Personal

# External drive
path: /Volumes/ExternalDrive/Notes

# Network share
path: /Volumes/SharedDrive/Documents
```

### Paths with Special Characters

```yaml
# Spaces - use quotes
path: "/Users/me/My Documents"

# @ symbol - use quotes
path: "/Users/me/email@domain.com - Google Drive"

# Parentheses - use quotes
path: "/Users/me/Notes (Personal)"

# Apostrophe - use quotes
path: "/Users/me/John's Notes"
```

## Debugging Checklist

When something isn't working:

- [ ] Did you save config.yaml?
- [ ] Did you restart Claude after editing config.yaml?
- [ ] Does the path exist? (`ls "/path"`)
- [ ] Are paths with spaces quoted?
- [ ] Did you test the server manually? (`python server.py`)
- [ ] Is ripgrep installed? (`rg --version`)
- [ ] Are there any error messages in the server output?
- [ ] Is the virtual environment activated?
- [ ] Are the dependencies installed? (`pip list | grep mcp`)

## Getting Help

If you're still stuck:

1. **Run the server manually and capture output:**
   ```bash
   cd /path/to/nuon-mcp
   python server.py 2>&1 | tee debug.log
   ```
   (Press Ctrl+C after a few seconds)

2. **Check the debug.log file** for error messages

3. **Verify your config.yaml syntax:**
   ```bash
   python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
   ```

4. **Test with a simple path first:**
   ```yaml
   repositories:
     - label: test
       path: /tmp
       description: Test repository
   ```

   If this works, the problem is with your specific path.

## Quick Fixes

### Reset Everything

If you want to start fresh:

```bash
# Remove MCP server
claude mcp remove nuon

# Reinstall
cd /path/to/nuon-mcp
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify config
cat config.yaml

# Re-register
claude mcp add --scope user --transport stdio nuon -- $(pwd)/venv/bin/python $(pwd)/server.py

# Test
claude mcp list
```

### Verify Everything is Working

```bash
# 1. Check MCP registration
claude mcp list

# 2. Test server manually
cd /path/to/nuon-mcp
python server.py
# Look for "Server ready. X repositories loaded."
# Press Ctrl+C

# 3. Start Claude and test
claude
# Then ask: "list all available sources"
```

If all three work, your setup is correct!

