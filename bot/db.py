"""SQLite storage: users (language), leads (finished requests only), settings, usage counters."""
import json
import sqlite3
import time
from datetime import datetime

from .config import DB_PATH


def _c():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init():
    with _c() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(uid INTEGER PRIMARY KEY, lang TEXT, name TEXT, username TEXT, first_seen REAL, last_seen REAL);
        CREATE TABLE IF NOT EXISTS leads(
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, uid INTEGER, kind TEXT, service TEXT, data TEXT, files TEXT,
            status TEXT DEFAULT 'new', created REAL, staff_msg INTEGER, staff_chat INTEGER);
        CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
        """)


def setting_get(k, default=None):
    with _c() as c:
        r = c.execute("SELECT v FROM settings WHERE k=?", (k,)).fetchone()
    return r[0] if r else default


def setting_set(k, v):
    with _c() as c:
        c.execute("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))


def user_touch(uid, name=None, username=None, lang=None):
    now = time.time()
    with _c() as c:
        r = c.execute("SELECT uid FROM users WHERE uid=?", (uid,)).fetchone()
        if r:
            c.execute("UPDATE users SET last_seen=?, name=COALESCE(?,name), username=COALESCE(?,username), lang=COALESCE(?,lang) WHERE uid=?",
                      (now, name, username, lang, uid))
        else:
            c.execute("INSERT INTO users(uid,lang,name,username,first_seen,last_seen) VALUES(?,?,?,?,?,?)", (uid, lang, name, username, now, now))


def user_lang(uid):
    with _c() as c:
        r = c.execute("SELECT lang FROM users WHERE uid=?", (uid,)).fetchone()
    return r[0] if r and r[0] else None


def leads_today(uid) -> int:
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    with _c() as c:
        return c.execute("SELECT COUNT(*) FROM leads WHERE uid=? AND created>=?", (uid, start)).fetchone()[0]


def lead_add(uid, kind, service, data: dict, files: list) -> dict:
    """Stores a FINISHED request and returns it with its order code DF-YYMMDD-NNN (NNN restarts every day)."""
    now = datetime.now()
    day0 = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    with _c() as c:
        n = c.execute("SELECT COUNT(*) FROM leads WHERE created>=?", (day0,)).fetchone()[0] + 1
        code = f"DF-{now:%y%m%d}-{n:03d}"
        cur = c.execute("INSERT INTO leads(code,uid,kind,service,data,files,created) VALUES(?,?,?,?,?,?,?)",
                        (code, uid, kind, service, json.dumps(data, ensure_ascii=False), json.dumps(files), now.timestamp()))
        return {"id": cur.lastrowid, "code": code}


def lead_get(lead_id=None, code=None):
    with _c() as c:
        r = c.execute("SELECT * FROM leads WHERE id=?" if lead_id is not None else "SELECT * FROM leads WHERE code=?", (lead_id if lead_id is not None else code,)).fetchone()
    return dict(r) if r else None


def lead_set(lead_id, **kw):
    if not kw:
        return
    with _c() as c:
        c.execute(f"UPDATE leads SET {', '.join(k + '=?' for k in kw)} WHERE id=?", (*kw.values(), lead_id))


def leads_open(limit=30):
    with _c() as c:
        rows = c.execute("SELECT * FROM leads WHERE status IN ('new','taken') ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
