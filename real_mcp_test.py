#!/usr/bin/env python3
"""
Real MCP Server Test - Actually calls your server's functions
"""
import sys
from pathlib import Path

# Add the current directory to the path so we can import from server.py
sys.path.insert(0, str(Path(__file__).parent))

# Import the actual repository manager from your server
from server import repo_manager

print("=" * 60)
print("REAL MCP SERVER TEST")
print("=" * 60)
print()

print("📡 Testing your actual server configuration...")
print()

# Test 1: List Sources (like the list_sources tool)
print("TEST 1: List Available Repositories")
print("-" * 60)
if repo_manager.repositories:
    for label, info in repo_manager.repositories.items():
        print(f"✓ {label}")
        print(f"  Path: {info['path']}")
        print(f"  Description: {info['description']}")
        print(f"  Files: {info['file_count']:,}")
        print()
else:
    print("❌ No repositories configured!")
print()

# Test 2: Try to read a file (like the read_file tool)
print("TEST 2: Read a File")
print("-" * 60)
if repo_manager.repositories:
    # Get the first repository
    first_label = list(repo_manager.repositories.keys())[0]
    repo_path = repo_manager.repositories[first_label]['path']
    
    print(f"Looking for README files in '{first_label}' repo...")
    
    # Try to find a README
    readme_files = list(repo_path.glob("README*"))
    
    if readme_files:
        readme = readme_files[0]
        rel_path = readme.relative_to(repo_path)
        print(f"✓ Found: {rel_path}")
        print()
        print("First 10 lines:")
        print("-" * 60)
        try:
            content = readme.read_text()
            lines = content.split('\n')[:10]
            for i, line in enumerate(lines, 1):
                print(f"{i:2}: {line}")
            if len(content.split('\n')) > 10:
                print("...")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    else:
        print("No README files found")
else:
    print("❌ No repositories configured!")

print()
print("=" * 60)
print("This shows your ACTUAL server data!")
print("=" * 60)
