from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, session_id TEXT, event_type TEXT, payload TEXT)")
        self.connection.commit()

    def append(self, session_id: str, event_type: str, payload: dict) -> None:
        self.connection.execute(
            "INSERT INTO events(session_id, event_type, payload) VALUES (?, ?, ?)",
            (session_id, event_type, json.dumps(payload, sort_keys=True)),
        )
        self.connection.commit()

    def history(self, session_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT event_type, payload FROM events WHERE session_id=? ORDER BY id", (session_id,)
        ).fetchall()
        return [{"event_type": kind, "payload": json.loads(payload)} for kind, payload in rows]
