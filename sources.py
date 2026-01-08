"""
Source implementations for Nuon MCP Server
Provides abstraction layer for different data sources (filesystem, Salesforce, etc.)
"""

import asyncio
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import aiohttp


class Source(ABC):
    """Abstract base class for all repository sources"""

    @abstractmethod
    async def search(self, query: str, case_sensitive: bool = False) -> str:
        """Search across this source and return formatted results"""
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """Read a specific 'file' (record) and return its contents"""
        pass

    @abstractmethod
    async def list_files(self, pattern: str = "*") -> list[str]:
        """List available files/records matching the pattern"""
        pass

    @abstractmethod
    async def get_metadata(self) -> dict:
        """Get source metadata (file count, description, etc.)"""
        pass

    @abstractmethod
    async def get_tree(self, subpath: str = "", max_depth: int = 3) -> str:
        """Get directory tree structure"""
        pass


class FileSystemSource(Source):
    """File system based repository source"""

    def __init__(self, label: str, path: str, description: str = ""):
        self.label = label
        self.path = Path(path).expanduser().resolve()
        self.description = description

        if not self.path.exists():
            raise ValueError(f"Path does not exist: {self.path}")
        if not self.path.is_dir():
            raise ValueError(f"Not a directory: {self.path}")

        # Count files in the repository
        self.file_count = sum(1 for _ in self.path.rglob('*') if _.is_file())

    def validate_path(self, file_path: Path) -> Path:
        """Ensure file path is within repository bounds"""
        resolved = (self.path / file_path).resolve()
        if not resolved.is_relative_to(self.path):
            raise ValueError(f"Path {file_path} is outside repository bounds")
        return resolved

    async def search(self, query: str, case_sensitive: bool = False) -> str:
        """Search repository using ripgrep"""
        cmd = ["rg", "--json"]

        if not case_sensitive:
            cmd.append("-i")

        cmd.extend([query, str(self.path)])

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

    async def read_file(self, path: str) -> str:
        """Read file contents"""
        file_path = Path(path)
        full_path = self.validate_path(file_path)

        if not full_path.exists():
            raise ValueError(f"File not found: {path}")

        if not full_path.is_file():
            raise ValueError(f"Not a file: {path}")

        try:
            content = full_path.read_text()
            return f"# {self.label}:{path}\n\n```\n{content}\n```"
        except UnicodeDecodeError:
            raise ValueError(f"Cannot read binary file: {path}")

    async def list_files(self, pattern: str = "*") -> list[str]:
        """List files matching glob pattern"""
        if "**" in pattern:
            files = sorted(self.path.rglob(pattern))
        else:
            files = sorted(self.path.glob(pattern))

        # Filter to only files and get relative paths
        return [str(f.relative_to(self.path)) for f in files if f.is_file()]

    async def get_metadata(self) -> dict:
        """Get repository metadata"""
        return {
            'label': self.label,
            'type': 'filesystem',
            'path': str(self.path),
            'description': self.description,
            'file_count': self.file_count
        }

    async def get_tree(self, subpath: str = "", max_depth: int = 3) -> str:
        """Get directory tree structure"""
        if subpath:
            start_path = self.validate_path(Path(subpath))
        else:
            start_path = self.path

        if not start_path.exists():
            raise ValueError(f"Path not found: {subpath}")

        return self._build_tree(start_path, self.path, max_depth)

    def _build_tree(self, path: Path, repo_path: Path, max_depth: int, current_depth: int = 0, prefix: str = "") -> str:
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

            if entry.is_dir():
                tree.append(f"{prefix}{current_prefix}{entry.name}/")
                subtree = self._build_tree(entry, repo_path, max_depth, current_depth + 1, next_prefix)
                if subtree:
                    tree.append(subtree)
            else:
                tree.append(f"{prefix}{current_prefix}{entry.name}")

        return "\n".join(tree)


class SalesforceSource(Source):
    """Salesforce API based repository source"""

    # Field mappings for search and display
    OBJECT_FIELDS = {
        'Opportunity': {
            'search_fields': ['Name', 'Description', 'StageName'],
            'display_fields': ['Id', 'Name', 'StageName', 'Amount', 'CloseDate', 'AccountId'],
            'name_field': 'Name'
        },
        'Account': {
            'search_fields': ['Name', 'Description', 'Industry'],
            'display_fields': ['Id', 'Name', 'Industry', 'Type', 'Website', 'Phone'],
            'name_field': 'Name'
        },
        'Contact': {
            'search_fields': ['Name', 'Email', 'Title'],
            'display_fields': ['Id', 'Name', 'Email', 'Title', 'Phone', 'AccountId'],
            'name_field': 'Name'
        },
        'Lead': {
            'search_fields': ['Name', 'Email', 'Company', 'Status'],
            'display_fields': ['Id', 'Name', 'Email', 'Company', 'Status', 'Phone'],
            'name_field': 'Name'
        },
        'Task': {
            'search_fields': ['Subject', 'Description'],
            'display_fields': ['Id', 'Subject', 'Status', 'Priority', 'ActivityDate'],
            'name_field': 'Subject'
        },
        'Event': {
            'search_fields': ['Subject', 'Description'],
            'display_fields': ['Id', 'Subject', 'StartDateTime', 'EndDateTime', 'Location'],
            'name_field': 'Subject'
        }
    }

    def __init__(self, label: str, description: str = "", objects: list = None):
        self.label = label
        self.description = description
        self.objects = objects or ['Opportunity', 'Account', 'Contact', 'Lead', 'Task', 'Event']

        # Validate configured objects
        invalid_objects = [obj for obj in self.objects if obj not in self.OBJECT_FIELDS]
        if invalid_objects:
            print(f"  ⚠ Warning: Unknown Salesforce objects will be skipped: {', '.join(invalid_objects)}", file=sys.stderr)
            self.objects = [obj for obj in self.objects if obj in self.OBJECT_FIELDS]

        # Load credentials from environment variables
        self.client_id = os.getenv('SF_CLIENT_ID')
        self.client_secret = os.getenv('SF_CLIENT_SECRET')
        self.login_url = os.getenv('SF_LOGIN_URL')

        # Validate required environment variables
        missing_vars = []
        if not self.client_id:
            missing_vars.append('SF_CLIENT_ID')
        if not self.client_secret:
            missing_vars.append('SF_CLIENT_SECRET')
        if not self.login_url:
            missing_vars.append('SF_LOGIN_URL')

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for Salesforce source '{label}': {', '.join(missing_vars)}\n"
                f"Please set these environment variables in your MCP server configuration."
            )

        # OAuth tokens
        self.access_token: Optional[str] = None
        self.instance_url: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._auth_lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _authenticate(self) -> None:
        """Authenticate using OAuth 2.0 Client Credentials flow"""
        async with self._auth_lock:
            session = await self._get_session()

            auth_url = f"{self.login_url}/services/oauth2/token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            try:
                async with session.post(auth_url, data=data) as response:
                    if response.status == 400:
                        error_data = await response.json()
                        error_msg = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                        raise ValueError(
                            f"Salesforce authentication failed for '{self.label}': {error_msg}\n"
                            f"Please check your SF_CLIENT_ID and SF_CLIENT_SECRET are correct."
                        )
                    elif response.status == 401:
                        raise ValueError(
                            f"Salesforce authentication failed for '{self.label}': Invalid credentials\n"
                            f"Please verify your Connected App credentials are correct."
                        )
                    elif response.status != 200:
                        error_text = await response.text()
                        raise ValueError(
                            f"Salesforce authentication failed for '{self.label}': HTTP {response.status}\n"
                            f"Response: {error_text}"
                        )

                    auth_response = await response.json()
                    self.access_token = auth_response['access_token']
                    self.instance_url = auth_response['instance_url']

            except aiohttp.ClientError as e:
                raise ValueError(
                    f"Network error connecting to Salesforce for '{self.label}': {str(e)}\n"
                    f"Please check your SF_LOGIN_URL is correct and you have internet connectivity."
                )
            except KeyError as e:
                raise ValueError(
                    f"Unexpected authentication response from Salesforce for '{self.label}': missing {str(e)}"
                )

    async def _make_api_call(self, endpoint: str, method: str = 'GET', params: dict = None, retry_auth: bool = True) -> dict:
        """Make an API call to Salesforce with automatic token refresh on 401"""
        # Authenticate if we don't have a token yet
        if not self.access_token:
            await self._authenticate()

        session = await self._get_session()
        url = f"{self.instance_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        try:
            async with session.request(method, url, headers=headers, params=params) as response:
                if response.status == 401 and retry_auth:
                    # Token expired, re-authenticate and retry once
                    await self._authenticate()
                    return await self._make_api_call(endpoint, method, params, retry_auth=False)

                elif response.status == 429:
                    # Rate limit exceeded
                    raise ValueError(
                        f"Salesforce API rate limit exceeded for '{self.label}'. "
                        f"Please wait a moment and try again."
                    )

                elif response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Salesforce API error for '{self.label}': HTTP {response.status}\n"
                        f"Response: {error_text}"
                    )

                return await response.json()

        except aiohttp.ClientError as e:
            raise ValueError(f"Network error calling Salesforce API for '{self.label}': {str(e)}")

    async def search(self, query: str, case_sensitive: bool = False) -> str:
        """Search across configured Salesforce objects using SOQL"""
        results = []

        for obj_type in self.objects:
            if obj_type not in self.OBJECT_FIELDS:
                continue

            config = self.OBJECT_FIELDS[obj_type]
            search_fields = config['search_fields']
            display_fields = config['display_fields']
            name_field = config['name_field']

            # Build WHERE clause with LIKE for each search field
            # Note: Salesforce LIKE is case-insensitive by default
            where_clauses = [f"{field} LIKE '%{self._escape_soql(query)}%'" for field in search_fields]
            where_condition = " OR ".join(where_clauses)

            soql = f"SELECT {', '.join(display_fields)} FROM {obj_type} WHERE {where_condition} LIMIT 50"

            try:
                endpoint = f"/services/data/v59.0/query"
                params = {'q': soql}
                response = await self._make_api_call(endpoint, params=params)

                records = response.get('records', [])
                for record in records:
                    record_id = record['Id']
                    name = record.get(name_field, 'Unknown')
                    # Format similar to ripgrep output
                    results.append(f"{obj_type}/{record_id}: {name}")

            except ValueError as e:
                # If there's an error with this object, log it but continue with others
                print(f"  ⚠ Warning searching {obj_type}: {str(e)}", file=sys.stderr)
                continue

        if results:
            if len(results) > 50:
                results = results[:50]
                results.append(f"\n... ({len(results) - 50} more matches omitted)")
            return "\n".join(results)

        return ""

    async def read_file(self, path: str) -> str:
        """Read a Salesforce record by path (e.g., 'Opportunity/006xx000001234ABC')"""
        parts = path.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid Salesforce path format. Expected 'ObjectType/RecordId', got: {path}")

        obj_type, record_id = parts

        if obj_type not in self.OBJECT_FIELDS:
            raise ValueError(f"Unknown Salesforce object type: {obj_type}")

        config = self.OBJECT_FIELDS[obj_type]
        fields = config['display_fields']

        # Fetch the record
        endpoint = f"/services/data/v59.0/sobjects/{obj_type}/{record_id}"
        record = await self._make_api_call(endpoint)

        # Format as JSON for readability
        formatted = json.dumps(record, indent=2)
        return f"# {self.label}:{path}\n\n```json\n{formatted}\n```"

    async def list_files(self, pattern: str = "*") -> list[str]:
        """List Salesforce records. Pattern format: 'ObjectType/*' or '*'"""
        if pattern == "*":
            # List all object types as directories
            return [f"{obj}/" for obj in self.objects]

        # Parse pattern like "Opportunity/*"
        if '/' in pattern:
            obj_type = pattern.split('/')[0]
            if obj_type not in self.OBJECT_FIELDS:
                raise ValueError(f"Unknown Salesforce object type: {obj_type}")

            config = self.OBJECT_FIELDS[obj_type]
            name_field = config['name_field']

            # Query recent records
            soql = f"SELECT Id, {name_field} FROM {obj_type} ORDER BY LastModifiedDate DESC LIMIT 100"
            endpoint = f"/services/data/v59.0/query"
            params = {'q': soql}
            response = await self._make_api_call(endpoint, params=params)

            records = response.get('records', [])
            return [f"{obj_type}/{record['Id']}" for record in records]

        return []

    async def get_metadata(self) -> dict:
        """Get Salesforce source metadata"""
        # Count total objects configured
        return {
            'label': self.label,
            'type': 'salesforce',
            'description': self.description,
            'file_count': len(self.objects),
            'objects': self.objects
        }

    async def get_tree(self, subpath: str = "", max_depth: int = 3) -> str:
        """Get directory tree showing Salesforce objects as directories"""
        if subpath:
            raise ValueError("Salesforce sources do not support subpath navigation")

        tree = []
        for i, obj in enumerate(self.objects):
            is_last = i == len(self.objects) - 1
            prefix = "└── " if is_last else "├── "
            tree.append(f"{prefix}{obj}/")

        return "\n".join(tree)

    def _escape_soql(self, value: str) -> str:
        """Escape special characters in SOQL queries"""
        # Escape single quotes by doubling them
        return value.replace("'", "''")

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
