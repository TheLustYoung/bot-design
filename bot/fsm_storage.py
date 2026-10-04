"""SQLite-backed FSM storage: in-progress dialogs (cart checkout, forms, feedback) survive bot restarts."""
import json
import sqlite3
from typing import Any, Dict, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

from .config import STORAGE


class SqliteStorage(BaseStorage):
    def __init__(self, path=None):
        self.path = str(path or (STORAGE / "fsm.db"))
        with self._c() as c:
            c.execute("CREATE TABLE IF NOT EXISTS fsm (k TEXT PRIMARY KEY, state TEXT, data TEXT)")

    def _c(self):
        return sqlite3.connect(self.path)

    @staticmethod
    def _key(key: StorageKey) -> str:
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}:{key.thread_id or 0}:{key.destiny}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        value = state.state if isinstance(state, State) else state
        with self._c() as c:
            c.execute("INSERT INTO fsm(k, state, data) VALUES(?,?,'{}') "
                      "ON CONFLICT(k) DO UPDATE SET state=excluded.state", (self._key(key), value))

    async def get_state(self, key: StorageKey) -> Optional[str]:
        with self._c() as c:
            r = c.execute("SELECT state FROM fsm WHERE k=?", (self._key(key),)).fetchone()
        return r[0] if r else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        with self._c() as c:
            c.execute("INSERT INTO fsm(k, state, data) VALUES(?,NULL,?) "
                      "ON CONFLICT(k) DO UPDATE SET data=excluded.data", (self._key(key), json.dumps(data, ensure_ascii=False)))

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        with self._c() as c:
            r = c.execute("SELECT data FROM fsm WHERE k=?", (self._key(key),)).fetchone()
        return json.loads(r[0]) if r and r[0] else {}

    async def close(self) -> None:
        return None
