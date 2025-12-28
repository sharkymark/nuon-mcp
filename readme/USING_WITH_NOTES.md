# Using Your MCP Server With Personal Notes

## The Short Answer: YES! No Code Changes Needed!

Your MCP server is **completely generic** - it doesn't care if it's reading Nuon configs or your personal notes. You can point it to **any directory** and the existing tools work perfectly.

## How to Add Your Notes Directory

Just edit `config.yaml` and add your notes folder:

```yaml
repositories:
  # Your existing Nuon repos
  - label: example-apps
    path: /path/to/example-app-configs
    description: Example app configurations for Nuon users

  - label: nuon-docs
    path: /path/to/nuon/docs
    description: Official Nuon documentation

  # ADD YOUR NOTES HERE!
  - label: my-notes
    path: /Users/you/Documents/Notes
    description: My personal notes and documentation

  - label: obsidian-vault
    path: /Users/you/ObsidianVault
    description: My Obsidian knowledge base

  - label: work-notes
    path: /Users/you/Documents/WorkNotes
    description: Work-related notes and meeting minutes
```

**That's it!** No code changes needed. Restart your Claude session and the new directories are available.

## What You Can Do With Notes

### Search Across All Your Notes

**You ask:**
```
Search my notes for "project deadline"
```

**Claude will:**
- Call `search_repo` with label="my-notes" and query="project deadline"
- Return all matches across all your note files
- Show you the file names and matching lines

### Find Information You Forgot

**You ask:**
```
What did I write about the Smith meeting?
```

**Claude will:**
- Search for "Smith meeting" across your notes
- Show you the relevant notes
- Can even read the full file if you want more context

### Cross-Reference Multiple Note Collections

**You ask:**
```
Search all my notes and work notes for "API key"
```

**Claude will:**
- Search both `my-notes` and `work-notes` repositories
- Show matches from both
- Help you find where you stored that API key reference

### Summarize or Extract Information

**You ask:**
```
Read my notes from January 2024 meeting notes and summarize the action items
```

**Claude will:**
- Use `list_files` to find files matching the pattern
- Use `read_file` to read the relevant notes
- Summarize the content for you

## Do the Tools Need to Change?

**NO!** The existing tools are perfect for notes:

| Existing Tool | How It Works With Notes |
|---------------|-------------------------|
| **search_all** | Search across all your note folders at once |
| **search_repo** | Search within a specific notes folder |
| **read_file** | Read a specific note file |
| **list_files** | List all notes matching a pattern (e.g., "*.md") |
| **get_directory_tree** | See your notes folder structure |
| **list_sources** | Show all your note folders |

## Example Use Cases

### 1. Personal Knowledge Base (Obsidian, Notion exports, etc.)

```yaml
- label: obsidian
  path: /Users/you/ObsidianVault
  description: My Obsidian knowledge base
```

**Ask Claude:**
- "Find all my notes about Python"
- "What have I written about machine learning?"
- "Show me my book notes from 2023"

### 2. Work Notes & Meeting Minutes

```yaml
- label: work-notes
  path: /Users/you/Documents/Work
  description: Work meeting notes and project docs
```

**Ask Claude:**
- "What were the action items from last week's standup?"
- "Find all mentions of the Q4 roadmap"
- "Show me notes from meetings with the design team"

### 3. Research Notes

```yaml
- label: research
  path: /Users/you/Research
  description: Academic research notes and papers
```

**Ask Claude:**
- "Find all my notes citing Smith et al 2020"
- "What did I write about quantum computing?"
- "List all my research papers on neural networks"

### 4. Journal/Diary

```yaml
- label: journal
  path: /Users/you/Journal
  description: Personal journal entries
```

**Ask Claude:**
- "What did I write in my journal about vacation planning?"
- "Find entries from March 2024"
- "Search for mentions of 'meditation'"

## Supported File Formats

The server works with **any text file**:

✅ Markdown (`.md`)
✅ Plain text (`.txt`)
✅ Code files (`.py`, `.js`, `.yaml`, etc.)
✅ Org-mode (`.org`)
✅ LaTeX (`.tex`)
✅ CSV (`.csv`)
✅ JSON (`.json`)
✅ Any other text format

❌ Binary files (images, PDFs, Word docs) won't be readable as text

## Privacy Note

**Your notes never leave your computer!**

- The MCP server runs **locally** on your Mac
- Claude (the AI) only sees what the server sends
- Nothing is uploaded to the cloud
- Your notes stay private and secure

## Performance

The server uses **ripgrep** for searching, which is extremely fast:

- Can search thousands of files in milliseconds
- Handles large note collections easily
- Regex support for complex searches

## Mixed Use: Nuon + Notes

You can have **both** at the same time:

```yaml
repositories:
  # Nuon stuff
  - label: example-apps
    path: /path/to/nuon/examples
    description: Nuon examples

  # Personal stuff
  - label: my-notes
    path: /path/to/my/notes
    description: Personal notes

  # Work stuff
  - label: work-docs
    path: /path/to/work/docs
    description: Work documentation
```

Then you can:
- Ask about Nuon configs when building apps
- Ask about your notes when you need personal info
- Cross-reference between them

**Claude knows the difference** because each has a distinct label and description.

## Example Session With Notes

```
You: list all available sources

Claude: You have 5 repositories configured:
  - example-apps (3,976 files)
  - nuon-docs (469 files)
  - my-notes (1,234 files)
  - work-notes (567 files)
  - journal (89 files)

You: search my notes for "dentist appointment"

Claude: Found 3 matches in my-notes:
  - 2024-03-15.md:5: Dentist appointment scheduled for April 3rd
  - 2024-04-01.md:12: Reminder: dentist appointment in 2 days
  - health-tracking.md:45: Last dentist appointment: April 3, 2024

You: read the file from April 1st

Claude: Here's 2024-04-01.md:
  [Shows the full note content]
```

## When Would You Need Code Changes?

You'd only need to modify the server if you wanted:

1. **Special note processing** (e.g., parse YAML frontmatter, extract tags)
2. **Note linking** (e.g., follow [[wiki-style]] links between notes)
3. **Custom search** (e.g., search only within code blocks)
4. **Metadata extraction** (e.g., pull out dates, authors, categories)

But for basic searching, reading, and listing - **the current tools are perfect as-is**.

## Quick Start: Add Notes Now

1. **Edit config.yaml:**
   ```yaml
   - label: my-notes
     path: /Users/you/Documents/Notes  # Your actual notes path
     description: My personal notes
   ```

2. **Restart Claude session:**
   ```bash
   # Exit current Claude session (Ctrl+D or type 'exit')
   # Start new session
   claude
   ```

3. **Test it:**
   ```
   list all available sources
   search my-notes for "TODO"
   ```

That's it! Your notes are now searchable through Claude.

## Real-World Scenarios

### Scenario 1: "Where did I save that info?"

**Before MCP:**
- Manually grep through folders
- Open multiple note files
- Try to remember which folder you used

**With MCP:**
```
You: Search all my notes for "AWS access key rotation"
Claude: Found in work-notes/security-procedures.md:23
```

### Scenario 2: "What were my takeaways?"

**Before MCP:**
- Open note file
- Read through it
- Try to summarize mentally

**With MCP:**
```
You: Read my note from the Q4 planning meeting and list the key decisions
Claude: [Reads the file and extracts key points]
```

### Scenario 3: "I wrote something about this..."

**Before MCP:**
- Can't remember which note
- Search manually
- Give up and rewrite it

**With MCP:**
```
You: I wrote something about React hooks best practices, can you find it?
Claude: Found 2 notes: dev-notes/react-patterns.md and learning/react-course.md
```

## Summary

| Question | Answer |
|----------|--------|
| **Can I use this with notes?** | YES! Absolutely |
| **Do I need to change code?** | NO! Just edit config.yaml |
| **What tools work with notes?** | ALL of them (search, read, list, etc.) |
| **Is it secure?** | YES! Everything runs locally |
| **Can I mix Nuon + Notes?** | YES! Add as many folders as you want |
| **What file types work?** | Any text file (.md, .txt, .org, etc.) |

The server is **already generic** - Claude just named it "nuon-mcp" because that was your original use case. But it works with **any directory of text files**.

