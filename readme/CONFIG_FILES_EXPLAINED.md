# Configuration Files Explained - No Duplicates!

## Your Question

> "If I add directories to config.yaml, will it create duplicates in .claude.json?"

## The Short Answer: NO!

These are **two completely separate configuration files** that do different things. Editing `config.yaml` does NOT affect Claude's MCP configuration at all.

## The Two Configuration Files

### 1. Claude's MCP Configuration (One Time Setup)

**Location:** Managed by `claude mcp add` command (stored somewhere by Claude CLI)

**Purpose:** Tells Claude "How do I start the nuon MCP server?"

**Contains:**
```json
{
  "mcpServers": {
    "nuon": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

**What it does:**
- You set this ONCE with `claude mcp add`
- It tells Claude how to launch the Python server
- It's just the server name ("nuon") and how to start it
- **You rarely need to change this**

### 2. Your Server's Config (config.yaml)

**Location:** `/path/to/nuon-mcp/config.yaml`

**Purpose:** Tells the server "What directories should I expose to Claude?"

**Contains:**
```yaml
repositories:
  - label: example-apps
    path: /path/to/examples
    description: Example configs

  - label: my-notes
    path: /path/to/notes
    description: My personal notes
```

**What it does:**
- The server reads this EVERY TIME it starts
- Defines which directories are available
- **You edit this whenever you want to add/remove directories**

## The Relationship

```
┌─────────────────────────────────────┐
│  Claude CLI Configuration           │
│  (Set once with 'claude mcp add')   │
│                                     │
│  "Start server named 'nuon' by      │
│   running: python server.py"        │
└──────────────┬──────────────────────┘
               │
               │ When you run 'claude', it executes:
               │ python server.py
               ↓
┌─────────────────────────────────────┐
│  server.py starts                   │
└──────────────┬──────────────────────┘
               │
               │ Server reads:
               ↓
┌─────────────────────────────────────┐
│  config.yaml                        │
│  (Read every time server starts)    │
│                                     │
│  repositories:                      │
│    - example-apps                   │
│    - nuon-docs                      │
│    - my-notes    ← You can add this!│
└─────────────────────────────────────┘
```

## What Happens When You Edit config.yaml

### Before (config.yaml):
```yaml
repositories:
  - label: example-apps
    path: /path/to/examples
  - label: nuon-docs
    path: /path/to/docs
```

### You Edit config.yaml:
```yaml
repositories:
  - label: example-apps
    path: /path/to/examples
  - label: nuon-docs
    path: /path/to/docs
  - label: my-notes          # ← ADD THIS
    path: /path/to/notes     # ← ADD THIS
```

### What Changes:

1. **Claude MCP config:** No change (still just knows "start python server.py")
2. **Next time you run `claude`:**
   - Claude starts server.py (same as before)
   - server.py reads config.yaml (now with 3 repos instead of 2)
   - Claude can now access all 3 directories

### Result:

```
You: list all available sources

Claude: You have 3 repositories:
  - example-apps (was always here)
  - nuon-docs (was always here)
  - my-notes (NEW! Just added to config.yaml)
```

## No Duplicates Are Created

There's only **ONE MCP server** called "nuon":

```bash
$ claude mcp list
nuon: /path/to/python /path/to/server.py - ✓ Connected
```

That's it! Just one entry, no matter how many directories you add to config.yaml.

## Think of It Like This

**Claude's MCP config** = Your phone's contact for "Pizza Place"
- Name: Pizza Place
- Phone: 555-1234
- You save this once

**config.yaml** = The pizza menu
- Pepperoni
- Veggie
- Hawaiian
- ← Add new pizzas here anytime!

When you call Pizza Place (run `claude`), they read their current menu (config.yaml) and tell you what's available. Adding new pizzas doesn't change their phone number or create duplicate contacts in your phone!

## Practical Example

### Day 1: Initial Setup

```bash
# Set up Claude MCP (ONE TIME)
claude mcp add nuon -- python /path/to/server.py
```

**config.yaml:**
```yaml
repositories:
  - label: nuon-docs
    path: /path/to/docs
```

**Result:** Claude can access nuon-docs

### Day 2: Add Your Notes

**Edit config.yaml:**
```yaml
repositories:
  - label: nuon-docs
    path: /path/to/docs
  - label: my-notes    # ← Just add this
    path: /path/to/notes
```

**Restart Claude:**
```bash
claude
```

**Result:** Claude can now access BOTH nuon-docs AND my-notes

**Claude MCP config:** Still the same! Still just "nuon" server.

### Day 3: Add More Directories

**Edit config.yaml again:**
```yaml
repositories:
  - label: nuon-docs
    path: /path/to/docs
  - label: my-notes
    path: /path/to/notes
  - label: work-notes   # ← Add another
    path: /path/to/work
  - label: journal      # ← And another
    path: /path/to/journal
```

**Restart Claude:**
```bash
claude
```

**Result:** Claude can access all 4 directories

**Claude MCP config:** STILL the same! Still just one "nuon" server.

## When Would You Get Duplicates?

You would only get duplicates if you ran `claude mcp add` multiple times with different names:

```bash
# DON'T do this!
claude mcp add nuon -- python server.py
claude mcp add nuon-notes -- python server.py    # ← Creates a second server
claude mcp add nuon-work -- python server.py     # ← Creates a third server
```

Then you'd have:
```
nuon: python server.py
nuon-notes: python server.py
nuon-work: python server.py
```

**But you don't want this!** You want ONE server that reads config.yaml for all your directories.

## Verifying Your Setup

Check how many MCP servers you have:

```bash
claude mcp list
```

**Good (what you want):**
```
nuon: /path/to/python /path/to/server.py - ✓ Connected
```

**Bad (duplicates):**
```
nuon: /path/to/python /path/to/server.py - ✓ Connected
nuon-2: /path/to/python /path/to/server.py - ✓ Connected
nuon-notes: /path/to/python /path/to/server.py - ✓ Connected
```

If you have duplicates, remove them:
```bash
claude mcp remove nuon-2
claude mcp remove nuon-notes
```

## Summary Table

| Action | Affects Claude MCP Config? | Affects config.yaml? | Result |
|--------|---------------------------|---------------------|---------|
| Edit config.yaml (add directory) | ❌ No | ✅ Yes | Server exposes more directories |
| Edit config.yaml (remove directory) | ❌ No | ✅ Yes | Server exposes fewer directories |
| Run `claude mcp add` | ✅ Yes | ❌ No | Registers a new MCP server |
| Run `claude mcp remove` | ✅ Yes | ❌ No | Unregisters an MCP server |

## Best Practices

1. **Set up the MCP server ONCE:**
   ```bash
   claude mcp add nuon -- python /path/to/server.py
   ```

2. **Edit config.yaml as much as you want:**
   - Add directories
   - Remove directories
   - Change descriptions
   - Reorder entries

3. **Restart Claude to pick up config.yaml changes:**
   ```bash
   # Exit current session (Ctrl+D)
   claude  # Start new session
   ```

4. **Check your setup:**
   ```bash
   claude mcp list  # Should show only ONE "nuon" entry
   ```

## Quick Reference

**Want to add a new directory?**
→ Edit `config.yaml` (NOT Claude's config)

**Want to change a directory path?**
→ Edit `config.yaml` (NOT Claude's config)

**Want to rename a directory label?**
→ Edit `config.yaml` (NOT Claude's config)

**Want to change the Python path or server.py location?**
→ Run `claude mcp remove nuon` then `claude mcp add nuon ...` (Claude's config)

## The Bottom Line

**Editing config.yaml does NOT create duplicates.**

You have ONE MCP server ("nuon") that reads config.yaml every time it starts. Edit config.yaml as much as you want - it's designed to be edited frequently!

