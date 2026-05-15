"""
Persistent memory module for agents.
Each agent has its own JSON memory file in data/memory/.
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentMemory:
    """
    Thread-safe persistent memory for a single agent.
    Stores data as JSON in data/memory/{agent_id}.json
    """

    MEMORY_DIR = Path(__file__).parent.parent / "data" / "memory"

    def __init__(self, agent_id: str, max_task_history: int = 100) -> None:
        self.agent_id = agent_id
        self.max_task_history = max_task_history
        self._lock = threading.Lock()
        self._memory_path = self.MEMORY_DIR / f"{agent_id}.json"
        self.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load memory from disk."""
        if self._memory_path.exists():
            try:
                with open(self._memory_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "agent_id": self.agent_id,
            "created_at": datetime.utcnow().isoformat(),
            "task_history": [],
            "stats": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_response_time_ms": 0,
                "last_active": None,
            },
            "self_evaluation": None,
            "custom": {},
        }

    def _save(self) -> None:
        """Persist memory to disk."""
        self._data["last_updated"] = datetime.utcnow().isoformat()
        with open(self._memory_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._save()

    def update(self, key: str, value: Any) -> None:
        """Alias for set()."""
        self.set(key, value)

    def get_custom(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get("custom", {}).get(key, default)

    def set_custom(self, key: str, value: Any) -> None:
        with self._lock:
            self._data.setdefault("custom", {})[key] = value
            self._save()

    # ------------------------------------------------------------------ #
    # Task history                                                         #
    # ------------------------------------------------------------------ #

    def add_task_record(
        self,
        task: str,
        result: str,
        success: bool,
        response_time_ms: float,
        metadata: Optional[Dict] = None,
    ) -> None:
        with self._lock:
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "task": task[:500],  # cap length
                "result": result[:2000],
                "success": success,
                "response_time_ms": response_time_ms,
                "metadata": metadata or {},
            }
            history: List[Dict] = self._data.setdefault("task_history", [])
            history.append(record)
            # Keep only the most recent N records
            if len(history) > self.max_task_history:
                self._data["task_history"] = history[-self.max_task_history :]

            # Update stats
            stats = self._data.setdefault("stats", {})
            if success:
                stats["tasks_completed"] = stats.get("tasks_completed", 0) + 1
            else:
                stats["tasks_failed"] = stats.get("tasks_failed", 0) + 1
            stats["total_response_time_ms"] = (
                stats.get("total_response_time_ms", 0) + response_time_ms
            )
            stats["last_active"] = datetime.utcnow().isoformat()

            self._save()

    def get_task_history(self, last_n: Optional[int] = None) -> List[Dict]:
        with self._lock:
            history = self._data.get("task_history", [])
            if last_n is not None:
                return history[-last_n:]
            return list(history)

    # ------------------------------------------------------------------ #
    # Stats                                                                #
    # ------------------------------------------------------------------ #

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            stats = dict(self._data.get("stats", {}))
            total = stats.get("tasks_completed", 0) + stats.get("tasks_failed", 0)
            stats["success_rate"] = (
                round(stats.get("tasks_completed", 0) / total * 100, 1)
                if total > 0
                else 0.0
            )
            rt = stats.get("total_response_time_ms", 0)
            stats["avg_response_time_ms"] = (
                round(rt / total, 1) if total > 0 else 0.0
            )
            stats["total_tasks"] = total
            return stats

    # ------------------------------------------------------------------ #
    # Self-evaluation                                                      #
    # ------------------------------------------------------------------ #

    def set_self_evaluation(self, evaluation: Dict) -> None:
        with self._lock:
            self._data["self_evaluation"] = {
                "timestamp": datetime.utcnow().isoformat(),
                **evaluation,
            }
            self._save()

    def get_self_evaluation(self) -> Optional[Dict]:
        with self._lock:
            return self._data.get("self_evaluation")

    # ------------------------------------------------------------------ #
    # Dump / export                                                        #
    # ------------------------------------------------------------------ #

    def dump(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)

    def __repr__(self) -> str:
        return f"AgentMemory(agent_id={self.agent_id!r})"
