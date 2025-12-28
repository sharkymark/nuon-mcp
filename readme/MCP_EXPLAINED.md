# Understanding Model Context Protocol (MCP) and Your nuon-mcp Server

## What is Model Context Protocol (MCP)?

**Model Context Protocol (MCP)** is a standardized way for AI assistants like Claude to connect to external data sources and tools. Think of it as a "plugin system" for Claude.

### The Problem MCP Solves

Without MCP, Claude only knows:
- What was in its training data (which can be outdated)
- What you tell it in the conversation

With MCP, Claude can:
- **Read your local files in real-time** (like your Nuon docs and example configs)
- **Search across multiple repositories** simultaneously
- **Access live, accurate information** instead of guessing

## Your nuon-mcp Server

Your `nuon-mcp` server is a Python program that:
1. **Exposes your local repositories** to Claude (Nuon docs, example configs, etc.)
2. **Provides tools** like `search_all`, `read_file`, `list_files`, etc.
3. **Runs in the background** whenever you use Claude

### What It Does

When you configured it, you told it about specific repositories:
```yaml
repositories:
  - label: examples
    path: /path/to/example-app-configs
  - label: nuon-docs
    path: /path/to/nuon/docs
```

Now when you ask Claude about Nuon configurations, Claude can:
- Search your actual example configs
- Read your local documentation
- Compare different approaches across your repos

## Does Claude Start the Python Program? YES!

**Yes, Claude (the CLI) automatically starts your Python server when:**

1. **You start a new Claude session** (run `claude` command)
2. **Claude needs to use MCP tools** (like searching your repos)

### How It Works

```
You run: claude
    ↓
Claude CLI reads: ~/.config/claude/config.json
    ↓
Finds MCP server config: "nuon" server
    ↓
Starts: /path/to/venv/bin/python /path/to/server.py
    ↓
Server runs in background during your session
    ↓
Claude can now use tools: search_all, read_file, etc.
```

## Proof Your Server is Running

### Method 1: Check MCP Status (Easiest)

```bash
claude mcp list
```

**Your Output:**
```
nuon: /Users/username/.../server.py - ✓ Connected
```

✅ **This confirms your server is running and Claude can talk to it!**

### Method 2: Check Running Processes

```bash
ps aux | grep server.py
```

**Your Output:**
```
username  30315  ... Python /Users/username/.../server.py
```

✅ **This shows the actual Python process running your server!**

### Method 3: Test It In Action

Start a Claude conversation and ask:
```
list all available sources
```

If Claude shows your configured repositories, the server is working!

### Method 4: Check Server Logs

Your server prints diagnostic info to stderr when it starts:
```
Starting Nuon MCP Server...
Loading repositories:
  ✓ examples: /path/to/repo (142 files)
  ✓ nuon-docs: /path/to/docs (38 files)

Server ready. 2 repositories loaded.
```

To see these logs, you can manually run:
```bash
python server.py
```

(Note: This starts it in interactive mode, not as an MCP server. Press Ctrl+C to stop)

## When Does The Server Start and Stop?

| Event | Server Status |
|-------|--------------|
| You run `claude` | ✅ Server starts automatically |
| You're chatting with Claude | ✅ Server runs in background |
| Claude uses a tool (search, read file, etc.) | ✅ Server handles the request |
| You exit Claude session | ❌ Server stops automatically |
| You start new Claude session | ✅ Server starts again |

**Important:** The server is **stateless** - it doesn't remember anything between sessions. Each time Claude starts, it's a fresh server instance.

## Architecture Diagram

```
┌─────────────────┐
│   You (User)    │
└────────┬────────┘
         │
         │ Run "claude"
         ↓
┌─────────────────────────┐
│   Claude CLI            │
│  (MCP Client)           │
└────────┬────────────────┘
         │
         │ Starts via stdio
         ↓
┌─────────────────────────┐
│   server.py             │
│  (MCP Server)           │
│                         │
│  Tools:                 │
│  - list_sources         │
│  - search_all           │
│  - search_repo          │
│  - read_file            │
│  - list_files           │
│  - get_directory_tree   │
└────────┬────────────────┘
         │
         │ Reads from
         ↓
┌─────────────────────────┐
│  Your Local Repos       │
│  - Nuon docs            │
│  - Example configs      │
│  - Reference apps       │
└─────────────────────────┘
```

## Communication Protocol

The server uses **stdio** (standard input/output) to communicate:

1. **Claude sends requests** via stdin (JSON messages)
2. **Server processes** the request (search files, read content, etc.)
3. **Server sends response** via stdout (JSON messages)

This is why you configured it with:
```bash
claude mcp add --transport stdio nuon -- python server.py
```

The `--transport stdio` tells Claude to communicate via stdin/stdout.

## What Makes Your Server Special

Your `nuon-mcp` server is **generic and reusable**:

✅ Works with **any number of repositories**
✅ **Fast search** using ripgrep (`rg`)
✅ **Safe** - read-only operations, path validation prevents directory traversal
✅ **Configurable** - easy YAML config file
✅ Can be **shared with teams** via `.mcp.json` in project repos

## Common Questions

### Q: Do I need to start the server manually?
**A:** No! Claude starts it automatically when you run `claude`.

### Q: Can I have multiple MCP servers?
**A:** Yes! You can add as many as you want. Each gets a unique name (yours is "nuon").

### Q: Does the server have access to my entire computer?
**A:** No! It only has access to the repositories you explicitly configure in `config.yaml`.

### Q: What if I change config.yaml?
**A:** Restart your Claude session. The server loads config on startup.

### Q: Can other people see my local files through MCP?
**A:** No! MCP servers run locally on your machine. They never send data over the network.

## Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. Check MCP server is registered and running
claude mcp list

# 2. Check the Python process is running
ps aux | grep server.py

# 3. Verify your config file exists
cat config.yaml

# 4. Test the server manually (optional)
python server.py
# (Press Ctrl+C to stop)
```

## Current Status (Your System)

Based on the checks we just ran:

✅ **MCP server is registered:** `nuon`
✅ **Server is running:** Process ID 30315
✅ **Server is connected:** `✓ Connected`
✅ **Configuration loaded:** `/path/to/nuon-mcp/server.py`

**Your nuon-mcp server is working perfectly!**

## Try It Out

Start a new Claude conversation and try:

```
list all available sources
```

```
search all repos for "database"
```

```
show me the directory structure of the examples repo
```

```
read the README from the nuon-docs repo
```

Claude will use your MCP server to answer these questions with real data from your local repositories!

