# How Claude Knows What Tools to Call - MCP Tool Discovery Explained

## The Core Question: How Does Claude Know What Tools Exist?

The answer: **Claude asks the server "What tools do you have?"**

## The Discovery Process

When you start a Claude session, here's what happens:

```
1. You run: claude
2. Claude CLI starts: python server.py
3. Claude (AI) sends request: "list_tools"
4. Server responds: "Here are my tools: search_all, read_file, etc."
5. Claude (AI) now knows what it can do
```

## The Code That Makes This Work

### Step 1: Declaring Available Tools

In `server.py`, look at this decorator:

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_all",
            description="Search for text across all configured repositories using ripgrep",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for (supports regex)"
                    },
                    ...
                }
            }
        ),
        Tool(name="read_file", ...),
        Tool(name="list_files", ...),
        # etc.
    ]
```

**What this does:**
- When Claude asks "What tools do you have?", this function responds
- Each `Tool` object describes:
  - **name**: What to call it ("search_all")
  - **description**: What it does (Claude reads this to decide if it's useful)
  - **inputSchema**: What parameters it needs (query, label, etc.)

### Step 2: Handling Tool Calls

When Claude decides to use a tool, it sends a request. This decorator handles it:

```python
@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "search_all":
        query = arguments["query"]
        # Do the search
        return [TextContent(type="text", text=results)]

    elif name == "read_file":
        label = arguments["label"]
        path = arguments["path"]
        # Read the file
        return [TextContent(type="text", text=file_content)]

    # etc.
```

**What this does:**
- Receives the tool name ("search_all") and arguments ({"query": "database"})
- Executes the appropriate logic
- Returns results back to Claude

## How Claude (The AI) Decides to Use Tools

Claude doesn't randomly call tools. Here's the decision process:

### Example Conversation:

**You:** "Search for examples that use RDS"

**Claude's Internal Process:**

```
1. Parse user request: User wants to search for "RDS"
2. Check available tools:
   - search_all: "Search for text across all configured repositories"
   - read_file: "Read the contents of a specific file"
   - list_files: "List files in a repository"
   ...
3. Decide: "search_all" matches what the user wants
4. Determine parameters: query = "RDS"
5. Call tool: search_all(query="RDS")
6. Receive results from server
7. Format results for user
```

**Claude's Response:** "I found 15 matches for 'RDS' across your repositories..."

## Why These Specific Tools?

When Claude (the AI that helped you) designed this server, it chose tools based on **common file/repository operations**:

### Tool Selection Rationale:

| Tool | Why It Exists | Use Case |
|------|---------------|----------|
| **list_sources** | User needs to know what repos are available | "What repos do I have?" |
| **search_all** | User wants to find something across all repos | "Find all examples using RDS" |
| **search_repo** | User wants to search one specific repo | "Search the docs for 'database'" |
| **read_file** | User wants to see file contents | "Show me the Coder config" |
| **list_files** | User wants to see what files exist | "List all YAML files" |
| **get_directory_tree** | User wants to understand structure | "Show me the docs structure" |

These tools mirror what you'd do manually:
- `grep -r "search term"` → `search_all`
- `cat file.txt` → `read_file`
- `ls` → `list_files`
- `tree` → `get_directory_tree`

## The MCP Protocol Flow

Here's a detailed sequence diagram:

```
┌──────┐                  ┌──────────┐                 ┌──────────┐
│ You  │                  │  Claude  │                 │  Server  │
│      │                  │   (AI)   │                 │ (Python) │
└──┬───┘                  └────┬─────┘                 └────┬─────┘
   │                           │                            │
   │ "Find RDS examples"       │                            │
   ├──────────────────────────>│                            │
   │                           │                            │
   │                           │ list_tools()               │
   │                           ├───────────────────────────>│
   │                           │                            │
   │                           │ [search_all, read_file...] │
   │                           │<───────────────────────────┤
   │                           │                            │
   │                           │ call_tool(                 │
   │                           │   name="search_all",       │
   │                           │   arguments={              │
   │                           │     "query": "RDS"         │
   │                           │   }                        │
   │                           │ )                          │
   │                           ├───────────────────────────>│
   │                           │                            │
   │                           │                            │ [Executes ripgrep]
   │                           │                            │ [Searches repos]
   │                           │                            │
   │                           │ Results: "file1.yaml:10..." │
   │                           │<───────────────────────────┤
   │                           │                            │
   │ "I found 15 matches..."   │                            │
   │<──────────────────────────┤                            │
   │                           │                            │
```

## Real Example: Tool Call in Action

Let's trace a real interaction:

### You Ask:
```
"Show me the README from the examples repo"
```

### Claude's Tool Selection Process:

```python
# Claude analyzes the request
request = "Show me the README from the examples repo"

# Claude checks its available tools
available_tools = [
    "list_sources",
    "search_all",
    "search_repo",
    "read_file",      # ← This matches!
    "list_files",
    "get_directory_tree"
]

# Claude picks: read_file
# Why? User wants to "show" (read) a specific file (README) from a repo (examples)

# Claude determines parameters
tool_call = {
    "name": "read_file",
    "arguments": {
        "label": "examples",    # The repo
        "path": "README.md"     # The file
    }
}
```

### Server Executes:

```python
# In server.py, the call_tool function receives this
async def call_tool(name: str, arguments: Any):
    if name == "read_file":
        label = arguments["label"]        # "examples"
        file_path = arguments["path"]     # "README.md"

        # Get the repo path
        repo_path = repo_manager.get_repo_path(label)
        # /Users/you/dev/example-app-configs

        # Build full path
        full_path = repo_path / file_path
        # /Users/you/dev/example-app-configs/README.md

        # Read the file
        content = full_path.read_text()

        # Return to Claude
        return [TextContent(type="text", text=content)]
```

### Claude Receives Results:

```
# README.md contents
This is the examples repository...
...
```

### Claude Responds to You:

```
Here's the README from the examples repo:

[Shows the content]
```

## Tool Descriptions: How Claude Decides

The **description** field is crucial. Claude reads these like instructions:

```python
Tool(
    name="search_all",
    description="Search for text across all configured repositories using ripgrep",
    # ↑ Claude reads this and thinks: "Use this when user wants to search everywhere"
)

Tool(
    name="search_repo",
    description="Search for text in a specific repository",
    # ↑ Claude reads this and thinks: "Use this when user specifies one repo"
)
```

### Examples of How Descriptions Guide Claude:

| User Request | Claude Thinks | Tool Selected |
|--------------|---------------|---------------|
| "Find 'database' everywhere" | "everywhere" = all repos | `search_all` |
| "Search the docs for 'database'" | "the docs" = specific repo | `search_repo` |
| "What repos are available?" | Need to list sources | `list_sources` |
| "Show me app.yaml" | Need to read a file | `read_file` |

## The inputSchema: Teaching Claude the Parameters

The `inputSchema` tells Claude what parameters each tool needs:

```python
Tool(
    name="search_repo",
    inputSchema={
        "type": "object",
        "properties": {
            "label": {
                "type": "string",
                "description": "Repository label (use list_sources to see available labels)"
                # ↑ Claude learns: "I need a repo label, I can get this from list_sources"
            },
            "query": {
                "type": "string",
                "description": "Text to search for (supports regex)"
                # ↑ Claude learns: "I need search text from the user's request"
            }
        },
        "required": ["label", "query"]
        # ↑ Claude learns: "Both parameters are mandatory"
    }
)
```

### Claude's Parameter Extraction:

**You say:** "Search the examples repo for 'postgres'"

**Claude extracts:**
```python
{
    "label": "examples",    # From: "the examples repo"
    "query": "postgres"     # From: "for 'postgres'"
}
```

## Why Did Claude (The AI) Create These Specific Tools?

When you asked Claude to build a Nuon MCP server, Claude reasoned:

### 1. **Understand the Goal**
- User needs help writing Nuon configs
- User has local docs and example apps
- Claude should access these to give accurate advice

### 2. **Identify Required Operations**
- **Discovery**: "What repos are available?" → `list_sources`
- **Search**: "Find examples of X" → `search_all`, `search_repo`
- **Read**: "Show me this config" → `read_file`
- **Browse**: "What files exist?" → `list_files`, `get_directory_tree`

### 3. **Design Tool Signatures**
- Each tool needs clear inputs and outputs
- Descriptions must be clear for future Claude sessions
- Parameters should be intuitive

### 4. **Implement with Best Practices**
- Use fast tools (ripgrep for search)
- Add safety (path validation)
- Handle errors gracefully

## The "Magic" Explained

There's no magic - it's a simple protocol:

1. **Tool Registration**: Server says "Here's what I can do"
2. **Tool Discovery**: Claude asks "What can you do?"
3. **Tool Selection**: Claude picks the right tool based on descriptions
4. **Tool Execution**: Server does the work
5. **Result Return**: Server sends results back
6. **Response Formatting**: Claude presents results to you

## Comparison: Traditional CLI vs MCP

### Traditional Approach:
```bash
You: grep -r "RDS" /path/to/repos
Terminal: [Raw grep output]
You: [Manually parse and understand results]
```

### MCP Approach:
```
You: "Find RDS examples"
Claude: [Calls search_all tool]
Server: [Executes ripgrep]
Server: [Returns structured results]
Claude: "I found 15 examples of RDS usage. Here are the most relevant..."
```

## Testing Tool Discovery

You can see this in action! Start a Claude session and ask:

```
"What tools do you have access to right now?"
```

Claude will list:
- list_sources
- search_all
- search_repo
- read_file
- list_files
- get_directory_tree

This proves Claude queried the server and got the tool list!

## Key Takeaways

1. **Tools are declared** in the `list_tools()` function
2. **Claude discovers tools** by calling `list_tools()` when it starts
3. **Descriptions guide Claude** on when to use each tool
4. **inputSchema teaches Claude** what parameters are needed
5. **call_tool() executes** the actual logic
6. **The MCP SDK handles** all the protocol details (JSON-RPC over stdio)

The tools aren't magic - they're just functions that Claude can call, with good descriptions so Claude knows when to use them!

