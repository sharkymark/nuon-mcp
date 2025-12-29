# Nuon MCP Server

A generic MCP (Model Context Protocol) server that provides Claude or Amp with access to multiple local repositories. Built for Nuon but designed to be reusable for any collection of repositories.

## What This Does

This MCP server allows Claude (or any LLM CLI) to:

- Search across multiple repositories simultaneously
- Read files from any configured repository
- List files matching patterns
- Explore directory structures
- Reference actual code and documentation during conversations

Instead of Claude guessing or using potentially outdated training data, it can fetch live, accurate information from your actual repositories.

## Prerequisites

- **Python 3.10+**
- **ripgrep** (`rg`) - For fast file searching
  - macOS: `brew install ripgrep`
  - Linux: `apt-get install ripgrep` or `yum install ripgrep`
  - Windows: `choco install ripgrep`
- **Claude Code CLI** - The MCP client

## Quick Start

### 1. Clone and Install

```bash
git clone <this-repo>
cd nuon-mcp

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Repositories

Copy the example configuration and edit it with your repository paths:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your actual repository paths:

```yaml
repositories:
  - label: examples
    path: /Users/you/dev/example-app-configs
    description: Example app configurations

  - label: nuon-docs
    path: /Users/you/dev/nuon/docs
    description: Official Nuon documentation

  # Add more repositories as needed
```

**Important**: Use absolute paths. The `~` character will be expanded automatically.

### 3. Add to Claude

Add the server to your Claude configuration (use the Python from your virtual environment):

```bash
claude mcp add --scope user --transport stdio nuon -- /absolute/path/to/nuon-mcp/venv/bin/python /absolute/path/to/nuon-mcp/server.py
```

**On Windows:**

```bash
claude mcp add --scope user --transport stdio nuon -- /absolute/path/to/nuon-mcp/venv/Scripts/python.exe /absolute/path/to/nuon-mcp/server.py
```

Replace `/absolute/path/to/nuon-mcp/` with the actual path to your installation.

### 4. Verify

Start a new Claude session and try:

```
list all available sources
```

You should see all your configured repositories.

### Amp Support

```bash
amp mcp add nuon -- /absolute/path/to/nuon-mcp/venv/bin/python /absolute/path/to/nuon-mcp/server.py
```

Then start Amp and test with similar commands as Claude.

## Configuration

### Repository Configuration

Each repository in `config.yaml` has three fields:

```yaml
- label: short-name # Used to reference this repo in tools
  path: /absolute/path # Full path to the repository
  description: What it is # Human-readable description
```

- **label**: A short, memorable identifier (e.g., "examples", "docs", "main-app")
- **path**: Absolute path to the repository root
- **description**: Brief description of what the repository contains

You can add as many repositories as needed - there's no hard limit.

### Project vs Global Configuration

You have two options for sharing this MCP server with a team:

#### Option 1: Project-Scoped (Recommended for Teams)

Create a `.mcp.json` file in your project repository:

```json
{
	"mcpServers": {
		"nuon": {
			"type": "stdio",
			"command": "python",
			"args": ["/shared/path/to/nuon-mcp/server.py"]
		}
	}
}
```

When team members clone the repo and run `claude`, they'll be prompted once to approve the configuration, then it works automatically.

#### Option 2: Personal Configuration

Each developer runs the `claude mcp add` command individually with their own local paths.

## Usage Examples

Once configured, you can ask Claude to:

### List Available Sources

```
Show me all available repositories
```

### Search Across All Repos

```
Search all repos for "rds"
```

### Search Specific Repo

```
Search the examples repo for "rds setup"
```

### Compare and Analyze

```
Compare the Coder and BYOC Nuon configs and explain the differences
```

```
Find all examples that use RDS and show me the patterns
```

## Tools Available

The server exposes these tools to Claude:

| Tool                 | Description                        |
| -------------------- | ---------------------------------- |
| `list_sources`       | Show all configured repositories   |
| `search_all`         | Search across all repositories     |
| `search_repo`        | Search a specific repository       |
| `read_file`          | Read a file from a repository      |
| `list_files`         | List files matching a glob pattern |
| `get_directory_tree` | Show directory structure           |

## Architecture

- **Language**: Python 3
- **Dependencies**: MCP SDK, PyYAML
- **Search**: Uses ripgrep for fast, efficient searching
- **Security**: Read-only operations, path validation prevents directory traversal

## Troubleshooting

### "ripgrep not found"

Install ripgrep (`rg`):

- macOS: `brew install ripgrep`
- Linux: `apt-get install ripgrep`
- Windows: `choco install ripgrep`

### "Configuration file not found"

Make sure you've copied `config.example.yaml` to `config.yaml` in the same directory as `server.py`.

### "Repository not found"

Check that:

1. The paths in `config.yaml` are absolute paths
2. The directories actually exist
3. You have read permissions

### Server won't start

Check the startup output for validation errors:

```bash
python server.py
```

You should see:

```
Starting Nuon MCP Server...
Loading repositories:
  ✓ examples: /path/to/repo (142 files)
  ✓ nuon-docs: /path/to/docs (38 files)

Server ready. 2 repositories loaded.
```

## Use Cases

### For Nuon Users

Connect Claude to:

- Example app configurations
- Official documentation
- Reference applications (BYOC, split-plane, etc.)

Now when building new apps, Claude can reference actual working examples and current docs instead of guessing.

### Beyond Nuon

This is a generic MCP server - use it for any collection of repositories:

- Your company's monorepo + docs + example apps
- Multiple microservice repositories
- Documentation sites + code repositories
- Open source projects you work on

## Additional Documentation

For more detailed information, see the `readme/` directory:

- **[MCP_EXPLAINED.md](readme/MCP_EXPLAINED.md)** - What is MCP and how does it work?
- **[HOW_TOOLS_WORK.md](readme/HOW_TOOLS_WORK.md)** - How Claude discovers and uses tools
- **[USING_WITH_NOTES.md](readme/USING_WITH_NOTES.md)** - Use this server with personal notes, not just code
- **[CONFIG_FILES_EXPLAINED.md](readme/CONFIG_FILES_EXPLAINED.md)** - Understanding the configuration files
- **[TROUBLESHOOTING.md](readme/TROUBLESHOOTING.md)** - Common issues and solutions

## Contributing

This is designed to be simple and extensible. To add new tools:

1. Add the tool definition in `list_tools()`
2. Add the handler in `call_tool()`
3. Follow the existing patterns for path validation and error handling

## License

[Add your license here]

## Credits

Built for Nuon.co to help users leverage Claude for building new applications with accurate, live access to examples and documentation.
