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
                "snapshots": [],
                "improvement_logs": [],
                "narrative": [],
                "preferences": {"safe_mode": True}
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
    def add_history(cls, query: str, duration_ms: float, affected_rows: int, success: bool, 
                    error: Optional[str] = None, table_name: Optional[str] = None,
                    performance_tier: str = "FAST", explain_summary: Optional[str] = None,
                    optimization_hints: List[str] = []):
        data = cls._load()
        entry = {
            "id": f"hist_{int(time.time() * 1000)}",
            "query": query,
            "duration_ms": round(duration_ms, 2),
            "affected_rows": affected_rows,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": success,
            "error": error,
            "table_name": table_name,
            "performance_tier": performance_tier,
            "explain_summary": explain_summary,
            "optimization_hints": optimization_hints
        }
        # Keep maximum 100 history items
        data["history"] = [entry] + data["history"][:99]
        cls._save(data)

    @classmethod
    def get_aggregated_insights(cls):
        """Computes deterministic insights from historical database activity."""
        data = cls._load()
        history = data.get("history", [])
        
        if not history:
            return {
                "slowest_queries": [],
                "frequent_queries": [],
                "impacted_tables": []
            }
            
        # 1. Slowest Queries (Top 5)
        slowest = sorted(
            [h for h in history if h.get("success")], 
            key=lambda x: x.get("duration_ms", 0), 
            reverse=True
        )[:5]
        
        # 2. Frequent Queries
        freq_map = {}
        for h in history:
            q = h.get("query")
            freq_map[q] = freq_map.get(q, 0) + 1
        
        frequent = sorted(
            [{"query": q, "count": count} for q, count in freq_map.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        # 3. Impacted Tables (Based on affected rows and frequency)
        table_impact = {}
        for h in history:
            tn = h.get("table_name")
            if not tn or tn == "Global": continue
            
            if tn not in table_impact:
                table_impact[tn] = {"count": 0, "total_rows": 0}
            
            table_impact[tn]["count"] += 1
            table_impact[tn]["total_rows"] += h.get("affected_rows", 0)
            
        impacted = sorted(
            [{"table": tn, "activity": stats["count"], "rows": stats["total_rows"]} 
             for tn, stats in table_impact.items()],
            key=lambda x: (x["activity"], x["rows"]),
            reverse=True
        )[:5]
        
        return {
            "slowest_queries": slowest,
            "frequent_queries": frequent,
            "impacted_tables": impacted
        }

    @classmethod
    def save_snippet(cls, name: str, query: str, tags: List[str] = []):
        data = cls._load()
        snippet = {
            "id": f"snip_{int(time.time() * 1000)}",
            "name": name,
            "query": query,
            "tags": tags,
            "is_favorite": False,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_used": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data["snippets"].append(snippet)
        cls._save(data)

    @classmethod
    def toggle_snippet_favorite(cls, snippet_id: str):
        data = cls._load()
        for s in data["snippets"]:
            if s["id"] == snippet_id:
                s["is_favorite"] = not s.get("is_favorite", False)
                break
        cls._save(data)

    @classmethod
    def update_snippet_usage(cls, snippet_id: str):
        data = cls._load()
        for s in data["snippets"]:
            if s["id"] == snippet_id:
                s["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
                break
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
