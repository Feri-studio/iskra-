"""
Долгосрочная память Искры на Caliby (встраиваемая векторная БД).
Fallback: JSON + текстовый поиск, если caliby не установлен.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()

_CALIBY_OK = False
try:
    import caliby
    import numpy as np
    _CALIBY_OK = True
except ImportError:
    caliby = None
    np = None


def _embed(text: str) -> List[float]:
    try:
        from sentence_transformers import SentenceTransformer
        if not hasattr(_embed, "_model"):
            _embed._model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = _embed._model.encode(text, normalize_embeddings=True)
        return vec.tolist()
    except Exception:
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        dim = settings.CALIBY_VECTOR_DIM
        raw = (h * ((dim // len(h)) + 1))[:dim]
        vec = [((b / 255.0) * 2 - 1) for b in raw]
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]


class MemoryService:
    def __init__(self):
        self._collection = None
        self._fallback: List[Dict[str, Any]] = []
        self._fallback_path = Path("./data/memory_fallback.json")
        self._init()

    def _init(self):
        Path("./data").mkdir(parents=True, exist_ok=True)
        if _CALIBY_OK:
            try:
                caliby.set_buffer_config(size_gb=settings.CALIBY_BUFFER_GB)
                path = settings.CALIBY_PATH
                Path(path).mkdir(parents=True, exist_ok=True)
                try:
                    caliby.open(path, cleanup_if_exist=False)
                except Exception:
                    caliby.open(path, cleanup_if_exist=True)

                schema = caliby.Schema()
                schema.add_field("key", caliby.FieldType.STRING)
                schema.add_field("memory_type", caliby.FieldType.STRING)
                schema.add_field("importance", caliby.FieldType.INT)
                schema.add_field("source", caliby.FieldType.STRING)

                self._collection = caliby.Collection(
                    "iskra_memory", schema, vector_dim=settings.CALIBY_VECTOR_DIM
                )
                try:
                    self._collection.create_hnsw_index("vec_idx", M=16, ef_construction=100)
                except Exception:
                    pass
                try:
                    self._collection.create_text_index("text_idx")
                except Exception:
                    pass
                print("[memory] Caliby готов")
                return
            except Exception as e:
                print(f"[memory] Caliby error: {e}, fallback")
                self._collection = None

        self._load_fallback()
        print("[memory] Fallback JSON. Установи: pip install caliby")

    def _load_fallback(self):
        if self._fallback_path.exists():
            try:
                self._fallback = json.loads(self._fallback_path.read_text(encoding="utf-8"))
            except Exception:
                self._fallback = []
        else:
            self._fallback = []

    def _save_fallback(self):
        self._fallback_path.write_text(
            json.dumps(self._fallback, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, key: str, value: str, memory_type: str = "fact",
            importance: int = 5, source: str = "chat", db=None) -> Dict[str, Any]:
        entry = {
            "key": key, "value": value, "memory_type": memory_type,
            "importance": importance, "source": source,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if self._collection is not None:
            try:
                vec = _embed(f"{key}: {value}")
                self._collection.add(
                    contents=[value],
                    metadatas=[{"key": key, "memory_type": memory_type,
                                "importance": importance, "source": source}],
                    vectors=[vec],
                )
                return entry
            except Exception as e:
                print(f"[memory] add error: {e}")

        self._fallback = [m for m in self._fallback if m.get("key") != key]
        self._fallback.append(entry)
        self._save_fallback()
        return entry

    def search(self, query: str, limit: int = 8, db=None) -> List[Dict[str, Any]]:
        if self._collection is not None:
            try:
                vec = _embed(query)
                results = self._collection.search_hybrid(
                    vec, "vec_idx", query, "text_idx", k=limit
                )
                out = []
                for r in results:
                    meta = getattr(r, "metadata", None) or {}
                    content = getattr(r, "content", None) or getattr(r, "text", "") or ""
                    out.append({
                        "key": meta.get("key", ""),
                        "value": content,
                        "memory_type": meta.get("memory_type", "fact"),
                        "importance": meta.get("importance", 5),
                        "source": meta.get("source", ""),
                        "score": getattr(r, "score", 0),
                    })
                return out
            except Exception as e:
                print(f"[memory] search error: {e}")

        q = query.lower()
        scored = []
        for m in self._fallback:
            score = 0
            if q in m.get("key", "").lower():
                score += 3
            if q in m.get("value", "").lower():
                score += 2
            if score:
                scored.append({**m, "score": score})
        scored.sort(key=lambda x: (x["score"], x.get("importance", 0)), reverse=True)
        return scored[:limit]

    def get_important(self, limit: int = 15, db=None) -> List[Dict[str, Any]]:
        if self._collection is not None:
            return self.search("память факт skill preference", limit=limit)
        return sorted(self._fallback, key=lambda x: x.get("importance", 0), reverse=True)[:limit]

    def build_context_block(self, query: str = "", limit: int = 10, db=None) -> str:
        items = self.search(query, limit=limit) if query else self.get_important(limit=limit)
        if not items:
            return ""
        lines = ["## Долгосрочная память Искры (Caliby):"]
        for m in items:
            lines.append(
                f"- [{m.get('memory_type', 'fact')}] {m.get('key', '')}: {str(m.get('value', ''))[:300]}"
            )
        return "\n".join(lines)

    def get(self, key: str, db=None) -> Optional[Dict[str, Any]]:
        for m in self.search(key, limit=5):
            if m.get("key") == key:
                return m
        return None

    def get_all(self, memory_type: Optional[str] = None, db=None) -> List[Dict[str, Any]]:
        items = self.get_important(limit=100)
        if memory_type:
            return [m for m in items if m.get("memory_type") == memory_type]
        return items

    def delete(self, key: str, db=None) -> bool:
        if self._collection is None:
            before = len(self._fallback)
            self._fallback = [m for m in self._fallback if m.get("key") != key]
            self._save_fallback()
            return len(self._fallback) < before
        return False


memory_service = MemoryService()
