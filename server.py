#!/usr/bin/env python3
"""
Nuon MCP Server - Generic MCP server for accessing multiple local repositories
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class RepositoryManager:
    """Manages multiple repository sources"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.repositories = {}
        self.load_config()

    def load_config(self):
        """Load and validate repository configuration"""
        if not self.config_path.exists():
            print(f"Error: Configuration file not found: {self.config_path}", file=sys.stderr)
            print(f"Please copy config.example.yaml to config.yaml and configure your paths", file=sys.stderr)
            sys.exit(1)

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        if not config or 'repositories' not in config:
            print("Error: Invalid configuration - 'repositories' key not found", file=sys.stderr)
            sys.exit(1)

        print("Starting Nuon MCP Server...", file=sys.stderr)
        print("Loading repositories:", file=sys.stderr)

        for repo in config['repositories']:
            label = repo['label']
            path = Path(repo['path']).expanduser().resolve()
            description = repo.get('description', '')

            if not path.exists():
                print(f"  ✗ {label}: Path does not exist: {path}", file=sys.stderr)
                continue

            if not path.is_dir():
                print(f"  ✗ {label}: Not a directory: {path}", file=sys.stderr)
                continue

            # Count files in the repository
            file_count = sum(1 for _ in path.rglob('*') if _.is_file())

            self.repositories[label] = {
                'path': path,
                'description': description,
                'file_count': file_count
            }

            print(f"  ✓ {label}: {path} ({file_count:,} files)", file=sys.stderr)

        if not self.repositories:
            print("\nError: No valid repositories loaded", file=sys.stderr)
            sys.exit(1)

        print(f"\nServer ready. {len(self.repositories)} repositories loaded.\n", file=sys.stderr)

    def get_repo_path(self, label: str) -> Path:
        """Get repository path by label"""
        if label not in self.repositories:
            raise ValueError(f"Repository not found: {label}")
        return self.repositories[label]['path']

    def validate_path(self, repo_path: Path, file_path: Path) -> Path:
        """Ensure file path is within repository bounds"""
        resolved = (repo_path / file_path).resolve()
        if not resolved.is_relative_to(repo_path):
            raise ValueError(f"Path {file_path} is outside repository bounds")
        return resolved


# Initialize repository manager
script_dir = Path(__file__).parent
repo_manager = RepositoryManager(script_dir / "config.yaml")

# Create MCP server
server = Server("nuon-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="list_sources",
            description="List all configured repository sources with their labels and descriptions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
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
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether search should be case sensitive (default: false)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_repo",
            description="Search for text in a specific repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Repository label (use list_sources to see available labels)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to search for (supports regex)"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether search should be case sensitive (default: false)"
                    }
                },
                "required": ["label", "query"]
            }
        ),
        Tool(
            name="read_file",
            description="Read the contents of a specific file from a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Repository label"
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file within the repository"
                    }
                },
                "required": ["label", "path"]
            }
        ),
        Tool(
            name="list_files",
            description="List files in a repository matching a glob pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Repository label"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '*.py', '**/*.md', default: '*')"
                    }
                },
                "required": ["label"]
            }
        ),
        Tool(
            name="get_directory_tree",
            description="Get the directory structure of a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Repository label"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to traverse (default: 3)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Subdirectory to start from (default: root)"
                    }
                },
                "required": ["label"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "list_sources":
            result = "# Available Repository Sources\n\n"
            for label, info in repo_manager.repositories.items():
                result += f"## {label}\n"
                result += f"- **Path**: {info['path']}\n"
                result += f"- **Description**: {info['description']}\n"
                result += f"- **Files**: {info['file_count']:,}\n\n"
            return [TextContent(type="text", text=result)]

        elif name == "search_all":
            query = arguments["query"]
            case_sensitive = arguments.get("case_sensitive", False)

            results = []
            for label, info in repo_manager.repositories.items():
                result = await search_repository(info['path'], query, case_sensitive)
                if result:
                    results.append(f"## Results from {label}:\n{result}")

            if results:
                return [TextContent(type="text", text="\n\n".join(results))]
            else:
                return [TextContent(type="text", text=f"No matches found for '{query}' across all repositories")]

        elif name == "search_repo":
            label = arguments["label"]
            query = arguments["query"]
            case_sensitive = arguments.get("case_sensitive", False)

            repo_path = repo_manager.get_repo_path(label)
            result = await search_repository(repo_path, query, case_sensitive)

            if result:
                return [TextContent(type="text", text=f"# Results from {label}:\n{result}")]
            else:
                return [TextContent(type="text", text=f"No matches found for '{query}' in {label}")]

        elif name == "read_file":
            label = arguments["label"]
            file_path = arguments["path"]

            repo_path = repo_manager.get_repo_path(label)
            full_path = repo_manager.validate_path(repo_path, Path(file_path))

            if not full_path.exists():
                return [TextContent(type="text", text=f"File not found: {file_path}")]

            if not full_path.is_file():
                return [TextContent(type="text", text=f"Not a file: {file_path}")]

            try:
                content = full_path.read_text()
                return [TextContent(
                    type="text",
                    text=f"# {label}:{file_path}\n\n```\n{content}\n```"
                )]
            except UnicodeDecodeError:
                return [TextContent(type="text", text=f"Cannot read binary file: {file_path}")]

        elif name == "list_files":
            label = arguments["label"]
            pattern = arguments.get("pattern", "*")

            repo_path = repo_manager.get_repo_path(label)

            if "**" in pattern:
                files = sorted(repo_path.rglob(pattern))
            else:
                files = sorted(repo_path.glob(pattern))

            # Filter to only files and get relative paths
            file_list = [str(f.relative_to(repo_path)) for f in files if f.is_file()]

            if file_list:
                result = f"# Files in {label} matching '{pattern}':\n\n"
                result += "\n".join(f"- {f}" for f in file_list)
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"No files found matching '{pattern}' in {label}")]

        elif name == "get_directory_tree":
            label = arguments["label"]
            max_depth = arguments.get("max_depth", 3)
            subpath = arguments.get("path", "")

            repo_path = repo_manager.get_repo_path(label)

            if subpath:
                start_path = repo_manager.validate_path(repo_path, Path(subpath))
            else:
                start_path = repo_path

            if not start_path.exists():
                return [TextContent(type="text", text=f"Path not found: {subpath}")]

            tree = build_directory_tree(start_path, repo_path, max_depth)
            result = f"# Directory tree for {label}"
            if subpath:
                result += f" (starting from {subpath})"
            result += f":\n\n```\n{tree}\n```"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def search_repository(repo_path: Path, query: str, case_sensitive: bool = False) -> str:
    """Search repository using ripgrep"""
    cmd = ["rg", "--json"]

    if not case_sensitive:
        cmd.append("-i")

    cmd.extend([query, str(repo_path)])

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0 and process.returncode != 1:
            # returncode 1 means no matches, which is fine
            return ""

        # Parse ripgrep JSON output
        results = []
        for line in stdout.decode().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get('type') == 'match':
                    path = data['data']['path']['text']
                    line_num = data['data']['line_number']
                    text = data['data']['lines']['text'].strip()
                    results.append(f"{path}:{line_num}: {text}")
            except json.JSONDecodeError:
                continue

        if results:
            # Limit to first 50 matches
            if len(results) > 50:
                results = results[:50]
                results.append(f"\n... ({len(results) - 50} more matches omitted)")
            return "\n".join(results)

        return ""

    except FileNotFoundError:
        return "Error: ripgrep (rg) not found. Please install ripgrep."


def build_directory_tree(path: Path, repo_path: Path, max_depth: int, current_depth: int = 0, prefix: str = "") -> str:
    """Build a visual directory tree"""
    if current_depth >= max_depth:
        return ""

    try:
        entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        return f"{prefix}[Permission Denied]"

    tree = []
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = prefix + ("    " if is_last else "│   ")

        rel_path = entry.relative_to(repo_path)

        if entry.is_dir():
            tree.append(f"{prefix}{current_prefix}{entry.name}/")
            subtree = build_directory_tree(entry, repo_path, max_depth, current_depth + 1, next_prefix)
            if subtree:
                tree.append(subtree)
        else:
            tree.append(f"{prefix}{current_prefix}{entry.name}")

    return "\n".join(tree)


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
