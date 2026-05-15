"""
MCP Loader — loads and manages MCP server configurations.
Agents can reference MCPs by name; tool context is injected into their prompts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


CONFIG_PATH = Path(__file__).parent.parent / "config" / "mcps.json"


class MCPServer:
    """Represents a single MCP server configuration."""

    def __init__(
        self,
        name: str,
        description: str = "",
        command: str = "",
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        enabled: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.command = command
        self.args: List[str] = args or []
        self.env_vars: Dict[str, str] = env_vars or {}
        self.enabled = enabled

    def resolve_env(self) -> Dict[str, str]:
        """Replace ${VAR} placeholders with actual env values."""
        resolved: Dict[str, str] = {}
        for key, val in self.env_vars.items():
            if val.startswith("${") and val.endswith("}"):
                env_key = val[2:-1]
                resolved[key] = os.getenv(env_key, "")
            else:
                resolved[key] = val
        return resolved

    def is_available(self) -> bool:
        """Check whether all required env vars are set."""
        if not self.enabled:
            return False
        resolved = self.resolve_env()
        return all(v != "" for v in resolved.values())

    def to_tool_context(self) -> str:
        """Return a short description to inject into an agent's context."""
        return (
            f"MCP Tool: {self.name}\n"
            f"Description: {self.description}\n"
            f"Available: {self.is_available()}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "args": self.args,
            "env_vars": self.env_vars,
            "enabled": self.enabled,
        }

    def __repr__(self) -> str:
        return f"<MCPServer name={self.name!r} enabled={self.enabled}>"


class MCPLoader:
    """
    Loads MCP configs from mcps.json.
    Allows runtime registration of new MCP servers.
    """

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self._config_path = config_path
        self._servers: Dict[str, MCPServer] = {}
        self._load()

    def _load(self) -> None:
        if not self._config_path.exists():
            return
        with open(self._config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for srv_data in data.get("mcp_servers", []):
            server = MCPServer(**srv_data)
            self._servers[server.name] = server

    def _save(self) -> None:
        servers_list = [s.to_dict() for s in self._servers.values()]
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump({"mcp_servers": servers_list}, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_server(self, name: str) -> Optional[MCPServer]:
        return self._servers.get(name)

    def list_servers(self) -> List[MCPServer]:
        return list(self._servers.values())

    def add_server(
        self,
        name: str,
        description: str = "",
        command: str = "",
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        enabled: bool = True,
    ) -> MCPServer:
        """Register a new MCP server and persist the config."""
        server = MCPServer(
            name=name,
            description=description,
            command=command,
            args=args or [],
            env_vars=env_vars or {},
            enabled=enabled,
        )
        self._servers[name] = server
        self._save()
        return server

    def remove_server(self, name: str) -> bool:
        if name in self._servers:
            del self._servers[name]
            self._save()
            return True
        return False

    def enable_server(self, name: str, enabled: bool = True) -> bool:
        server = self._servers.get(name)
        if server:
            server.enabled = enabled
            self._save()
            return True
        return False

    def get_context_for_agent(self, mcp_names: List[str]) -> str:
        """
        Build a tool-context block to inject into an agent's system prompt.
        """
        if not mcp_names:
            return ""
        lines = ["\n## Available MCP Tools\n"]
        for name in mcp_names:
            srv = self._servers.get(name)
            if srv:
                lines.append(srv.to_tool_context())
                lines.append("")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<MCPLoader servers={list(self._servers.keys())}>"
