import json
import os
import time
from typing import List, Dict, Any, Optional

META_FILE = "devbeast_meta.json"

class MetaService:
    @staticmethod
    def _load() -> Dict[str, Any]:
        if not os.path.exists(META_FILE):
            return {
                "history": [],
                "snippets": [],
                "snapshots": []
            }
        try:
            with open(META_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"history": [], "snippets": [], "snapshots": []}

    @staticmethod
    def _save(data: Dict[str, Any]):
        with open(META_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def add_history(cls, query: str, duration_ms: float, affected_rows: int, success: bool, error: Optional[str] = None):
        data = cls._load()
        entry = {
            "id": f"hist_{int(time.time() * 1000)}",
            "query": query,
            "duration_ms": round(duration_ms, 2),
            "affected_rows": affected_rows,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": success,
            "error": error
        }
        # Keep maximum 100 history items
        data["history"] = [entry] + data["history"][:99]
        cls._save(data)

    @classmethod
    def save_snippet(cls, name: str, query: str, tags: List[str] = []):
        data = cls._load()
        snippet = {
            "id": f"snip_{int(time.time() * 1000)}",
            "name": name,
            "query": query,
            "tags": tags,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data["snippets"].append(snippet)
        cls._save(data)

    @classmethod
    def get_history(cls) -> List[Dict[str, Any]]:
        return cls._load().get("history", [])

    @classmethod
    def get_snippets(cls) -> List[Dict[str, Any]]:
        return cls._load().get("snippets", [])

    @classmethod
    def delete_snippet(cls, snippet_id: str):
        data = cls._load()
        data["snippets"] = [s for s in data["snippets"] if s["id"] != snippet_id]
        cls._save(data)

    @classmethod
    def save_snapshot(cls, name: str, schema_data: Dict[str, Any]):
        data = cls._load()
        snapshot = {
            "id": f"snap_{int(time.time() * 1000)}",
            "name": name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "schema": schema_data
        }
        data["snapshots"].append(snapshot)
        cls._save(data)

    @classmethod
    def get_snapshots(cls) -> List[Dict[str, Any]]:
        return cls._load().get("snapshots", [])
