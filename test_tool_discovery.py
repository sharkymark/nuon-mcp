#!/usr/bin/env python3
"""
Demonstration: How MCP Tool Discovery Works

This shows the simplified version of what happens when Claude
connects to your MCP server.
"""

# Simulating the MCP Tool class
class Tool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema
    
    def __repr__(self):
        return f"Tool(name='{self.name}')"

# This is like your server's list_tools() function
def list_tools():
    """When Claude asks 'what tools do you have?', this responds"""
    return [
        Tool(
            name="search_all",
            description="Search for text across all configured repositories using ripgrep",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text to search for"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="read_file",
            description="Read the contents of a specific file from a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Repository label"},
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["label", "path"]
            }
        ),
    ]

# Simulating Claude (the AI) discovering tools
def claude_discovers_tools():
    """This is what Claude does when it connects to your server"""
    
    print("🤖 Claude: Connecting to MCP server...")
    print("🤖 Claude: Sending request -> list_tools()")
    print()
    
    # Claude calls the server's list_tools()
    available_tools = list_tools()
    
    print("📡 Server: Here are my tools:")
    for tool in available_tools:
        print(f"   - {tool.name}: {tool.description}")
    print()
    
    print("🤖 Claude: Great! Now I know what I can do.")
    print("🤖 Claude: When user asks to search, I'll call 'search_all'")
    print("🤖 Claude: When user asks to read a file, I'll call 'read_file'")
    print()
    
    return available_tools

# Simulating Claude deciding which tool to use
def claude_handles_user_request(user_message, available_tools):
    """This is how Claude picks the right tool"""
    
    print(f"👤 User: {user_message}")
    print()
    print("🤖 Claude thinking...")
    
    # Simple keyword matching (real Claude uses much more sophisticated reasoning)
    if "search" in user_message.lower() or "find" in user_message.lower():
        chosen_tool = "search_all"
        reasoning = "User wants to search, so I'll use search_all"
        parameters = {"query": "RDS"}  # Extracted from user message
    elif "read" in user_message.lower() or "show" in user_message.lower():
        chosen_tool = "read_file"
        reasoning = "User wants to read a file, so I'll use read_file"
        parameters = {"label": "examples", "path": "README.md"}
    else:
        chosen_tool = None
        reasoning = "No tool needed for this request"
        parameters = None
    
    print(f"   💭 {reasoning}")
    
    if chosen_tool:
        print(f"   🔧 Calling tool: {chosen_tool}")
        print(f"   📝 Parameters: {parameters}")
        print()
        print(f"📡 Server: Executing {chosen_tool}({parameters})...")
        print("📡 Server: [Performing actual work...]")
        print("📡 Server: Done! Here are the results...")
    
    print()

# Run the demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("MCP TOOL DISCOVERY DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Step 1: Claude discovers what tools are available
    tools = claude_discovers_tools()
    
    print("=" * 60)
    print("TOOL USAGE DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Step 2: Claude handles different user requests
    claude_handles_user_request("Find all examples that use RDS", tools)
    claude_handles_user_request("Show me the README file", tools)
    
    print("=" * 60)
    print("This is exactly what happens in your nuon-mcp server!")
    print("=" * 60)
