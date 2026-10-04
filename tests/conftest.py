import os
import pathlib
import sys
import tempfile

# never touch a real bot/token/DB: set the environment BEFORE the package is imported
os.environ["BOT_TOKEN"] = "1:TEST"
os.environ["OWNER_ID"] = "111"
os.environ["STAFF_CHAT_ID"] = "-100777"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="dfbot_"))

import pytest  # noqa: E402


@pytest.fixture()
def env(monkeypatch):
    from bot import db
    d = pathlib.Path(tempfile.mkdtemp(dir=TMP))
    monkeypatch.setattr(db, "DB_PATH", d / "t.db")
    db.init()
    return d
