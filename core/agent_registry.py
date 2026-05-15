"""
AgentRegistry — create, retrieve, list, update, and delete agents.
Persists agent definitions in config/agents.json.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .agent_base import BaseAgent


CONFIG_PATH = Path(__file__).parent.parent / "config" / "agents.json"


def _slugify(text: str) -> str:
    """Convert a string to a safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


class AgentRegistry:
    """
    Central registry that manages all agent instances.

    Thread-safe: all mutating operations hold `_lock`.
    """

    def __init__(
        self,
        config_path: Path = CONFIG_PATH,
        agent_class: Type[BaseAgent] = BaseAgent,
    ) -> None:
        self._config_path = config_path
        self._agent_class = agent_class
        self._lock = threading.Lock()
        # id → BaseAgent
        self._agents: Dict[str, BaseAgent] = {}
        self._load_from_config()

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def _load_from_config(self) -> None:
        """Load agents from config/agents.json and instantiate them."""
        if not self._config_path.exists():
            return
        with open(self._config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for agent_data in data.get("agents", []):
            agent = self._agent_class(**agent_data)
            self._agents[agent.id] = agent

    def _save_config(self) -> None:
        """Persist all agent definitions back to config/agents.json."""
        agents_list = [a.to_dict() for a in self._agents.values()]
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump({"agents": agents_list}, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # CRUD                                                                 #
    # ------------------------------------------------------------------ #

    def create_agent(
        self,
        name: str,
        role: str,
        skills: List[str],
        api_keys: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[str]] = None,
        description: str = "",
        personality: str = "",
        agent_id: Optional[str] = None,
    ) -> BaseAgent:
        """
        Create a new agent, persist it, and return the instance.

        If `agent_id` is not provided it is generated from name + role + timestamp.
        """
        with self._lock:
            if agent_id is None:
                ts = datetime.utcnow().strftime("%f")[:4]
                agent_id = f"{_slugify(name)}-{_slugify(role)}-{ts}"

            if agent_id in self._agents:
                raise ValueError(f"Agent with id '{agent_id}' already exists.")

            agent = self._agent_class(
                id=agent_id,
                name=name,
                role=role,
                skills=skills,
                api_keys=api_keys or {},
                mcp_servers=mcp_servers or [],
                description=description,
                personality=personality,
            )
            self._agents[agent_id] = agent
            self._save_config()
            return agent

    def get_agent(self, name_or_id: str) -> Optional[BaseAgent]:
        """
        Look up an agent by exact id or by name (case-insensitive).
        Returns None if not found.
        """
        # Exact id match
        if name_or_id in self._agents:
            return self._agents[name_or_id]
        # Name match (case-insensitive)
        lower = name_or_id.lower()
        for agent in self._agents.values():
            if agent.name.lower() == lower:
                return agent
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return a list of lightweight agent summaries."""
        result = []
        for agent in self._agents.values():
            stats = agent.get_stats()
            result.append(
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "status": agent.status,
                    "skills_count": len(agent.skills),
                    "tasks_completed": stats.get("tasks_completed", 0),
                    "success_rate": stats.get("success_rate", 0.0),
                    "last_active": stats.get("last_active"),
                }
            )
        return result

    def delete_agent(self, agent_id: str) -> bool:
        """
        Remove an agent by id.
        Returns True if deleted, False if not found.
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            del self._agents[agent_id]
            self._save_config()
            return True

    def update_agent(self, agent_id: str, **kwargs: Any) -> Optional[BaseAgent]:
        """
        Hot-update agent config fields and persist.
        Allowed fields: name, role, skills, api_keys, mcp_servers,
                        description, personality, status
        """
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent is None:
                return None
            allowed = {
                "name", "role", "skills", "api_keys",
                "mcp_servers", "description", "personality", "status",
            }
            for key, val in kwargs.items():
                if key in allowed:
                    setattr(agent, key, val)
            self._save_config()
            return agent

    def get_all_agents(self) -> List[BaseAgent]:
        """Return all agent instances."""
        return list(self._agents.values())

    def count(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"<AgentRegistry agents={list(self._agents.keys())}>"
