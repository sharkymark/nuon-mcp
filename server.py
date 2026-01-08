#!/usr/bin/env python3
"""
Nuon MCP Server - Generic MCP server for accessing multiple local repositories
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from sources import Source, FileSystemSource, SalesforceSource


class RepositoryManager:
    """Manages multiple repository sources"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.sources: dict[str, Source] = {}
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
            source_type = repo.get('type', 'filesystem')
            description = repo.get('description', '')

            # Auto-detect type: if 'path' field exists, default to filesystem
            if 'path' in repo and source_type == 'filesystem':
                source_type = 'filesystem'
            elif 'type' not in repo and 'path' in repo:
                source_type = 'filesystem'

            try:
                if source_type == 'filesystem':
                    path = repo.get('path')
                    if not path:
                        print(f"  ✗ {label}: Missing 'path' field for filesystem source", file=sys.stderr)
                        continue

                    source = FileSystemSource(label, path, description)
                    print(f"  ✓ {label}: {source.path} ({source.file_count:,} files)", file=sys.stderr)

                elif source_type == 'salesforce':
                    objects = repo.get('objects', ['Opportunity', 'Account', 'Contact', 'Lead', 'Task', 'Event'])
                    source = SalesforceSource(label, description, objects)
                    print(f"  ✓ {label}: Salesforce ({len(source.objects)} objects)", file=sys.stderr)

                else:
                    print(f"  ✗ {label}: Unknown source type: {source_type}", file=sys.stderr)
                    continue

                self.sources[label] = source

            except ValueError as e:
                print(f"  ✗ {label}: {str(e)}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"  ✗ {label}: Unexpected error: {str(e)}", file=sys.stderr)
                continue

        if not self.sources:
            print("\nError: No valid repositories loaded", file=sys.stderr)
            sys.exit(1)

        print(f"\nServer ready. {len(self.sources)} repositories loaded.\n", file=sys.stderr)

    def get_source(self, label: str) -> Source:
        """Get source by label"""
        if label not in self.sources:
            raise ValueError(f"Repository not found: {label}")
        return self.sources[label]


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
            for label, source in repo_manager.sources.items():
                metadata = await source.get_metadata()
                result += f"## {label}\n"
                result += f"- **Type**: {metadata['type']}\n"
                if metadata['type'] == 'filesystem':
                    result += f"- **Path**: {metadata['path']}\n"
                    result += f"- **Files**: {metadata['file_count']:,}\n"
                elif metadata['type'] == 'salesforce':
                    result += f"- **Objects**: {', '.join(metadata['objects'])}\n"
                result += f"- **Description**: {metadata['description']}\n\n"
            return [TextContent(type="text", text=result)]

        elif name == "search_all":
            query = arguments["query"]
            case_sensitive = arguments.get("case_sensitive", False)

            results = []
            for label, source in repo_manager.sources.items():
                result = await source.search(query, case_sensitive)
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

            source = repo_manager.get_source(label)
            result = await source.search(query, case_sensitive)

            if result:
                return [TextContent(type="text", text=f"# Results from {label}:\n{result}")]
            else:
                return [TextContent(type="text", text=f"No matches found for '{query}' in {label}")]

        elif name == "read_file":
            label = arguments["label"]
            file_path = arguments["path"]

            source = repo_manager.get_source(label)
            content = await source.read_file(file_path)
            return [TextContent(type="text", text=content)]

        elif name == "list_files":
            label = arguments["label"]
            pattern = arguments.get("pattern", "*")

            source = repo_manager.get_source(label)
            file_list = await source.list_files(pattern)

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

            source = repo_manager.get_source(label)
            tree = await source.get_tree(subpath, max_depth)
            result = f"# Directory tree for {label}"
            if subpath:
                result += f" (starting from {subpath})"
            result += f":\n\n```\n{tree}\n```"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
