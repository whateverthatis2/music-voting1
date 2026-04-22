# -*- coding: utf-8 -*-
"""
Збереження даних — MongoDB з прозорим in-memory резервом.

На Vercel бувають ситуації, коли:
  * відсутня змінна оточення MONGODB_URI;
  * MongoDB Atlas закриває з'єднання після cold-start;
  * мережеві обмеження не дають створити з'єднання вчасно.

У всіх цих випадках сторінки лабораторної мають продовжувати працювати,
тому реалізована «двоконтурна» логіка: спершу пробуємо MongoDB,
у разі будь-якої помилки використовуємо процесний кеш.

Кеш — це звичайний модульний словник, який живе в межах одного
serverless-інстансу.
"""

from __future__ import annotations

import datetime as _dt
import os
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Внутрішнє сховище в пам'яті (запасний контур)
# ---------------------------------------------------------------------------
_MEMORY: Dict[str, List[Dict[str, Any]]] = {
    "rankings": [],   # збережені колективні ранжування
    "events":   [],   # системний журнал
    "aco_runs": [],   # історія прогонів мурашиного алгоритму
}

# ---------------------------------------------------------------------------
# Кешований клієнт MongoDB
# ---------------------------------------------------------------------------
_db_handle = None
_db_unavailable_reason: Optional[str] = None


def _connect():
    """Лінива ініціалізація MongoDB. Повертає handle або None."""
    global _db_handle, _db_unavailable_reason
    if _db_handle is not None:
        return _db_handle
    if _db_unavailable_reason is not None:
        return None

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        _db_unavailable_reason = "MONGODB_URI не встановлено"
        return None

    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi

        client = MongoClient(
            uri,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=2500,
            connectTimeoutMS=2500,
            socketTimeoutMS=2500,
        )
        # ping — перевіримо, що з'єднання справді працює
        client.admin.command("ping")
        _db_handle = client["lab3_collective_ranking"]
        return _db_handle
    except Exception as exc:  # pragma: no cover — мережеві помилки
        _db_unavailable_reason = f"{type(exc).__name__}: {exc}"
        _db_handle = None
        return None


def db_status() -> Dict[str, Any]:
    """Стан сховища для UI."""
    handle = _connect()
    return {
        "online": handle is not None,
        "reason": _db_unavailable_reason if handle is None else None,
    }


# ---------------------------------------------------------------------------
# Запис / читання
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _save(collection: str, document: Dict[str, Any]) -> bool:
    document = {**document, "time": document.get("time") or _now_iso()}
    handle = _connect()
    if handle is not None:
        try:
            handle[collection].insert_one(dict(document))
            return True
        except Exception:
            pass
    _MEMORY.setdefault(collection, []).append(document)
    return False  # збережено лише в пам'ять


def _load(collection: str, limit: int = 200) -> List[Dict[str, Any]]:
    handle = _connect()
    if handle is not None:
        try:
            cursor = (
                handle[collection]
                .find({}, {"_id": 0})
                .sort("time", -1)
                .limit(limit)
            )
            docs = list(cursor)
            if docs:
                return docs
        except Exception:
            pass
    return list(reversed(_MEMORY.get(collection, [])))[:limit]


# ---------------------------------------------------------------------------
# Публічний API
# ---------------------------------------------------------------------------
def save_ranking(source: str, ranking: List[str], cost: int, max_d: int,
                 method: str = "manual") -> bool:
    return _save("rankings", {
        "source": source, "ranking": ranking,
        "cost": cost, "max": max_d, "method": method,
    })


def load_rankings(limit: int = 100) -> List[Dict[str, Any]]:
    return _load("rankings", limit)


def save_aco_run(payload: Dict[str, Any]) -> bool:
    return _save("aco_runs", payload)


def load_aco_runs(limit: int = 50) -> List[Dict[str, Any]]:
    return _load("aco_runs", limit)


def log_event(event_type: str, message: str, meta: Optional[Dict] = None) -> bool:
    return _save("events", {
        "type": event_type, "message": message, "meta": meta or {},
    })


def load_events(limit: int = 200) -> List[Dict[str, Any]]:
    return _load("events", limit)
