# -*- coding: utf-8 -*-
"""End-to-end with a FAKE Telegram layer (nothing is sent anywhere): file-first intake, FAQ, the staff chat gets a request ONLY when it is complete."""
import asyncio
import itertools
from datetime import datetime

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.types import CallbackQuery, Chat, Document, Message, MessageId, PhotoSize, Update, User

from bot import db, main
from bot.fsm_storage import SqliteStorage

STAFF = -100777
_ids = itertools.count(5000)


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def close(self):
        return None

    async def stream_content(self, url, headers=None, timeout=30, chunk_size=65536, raise_for_status=True):
        yield b""

    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        self.calls.append((name, method))
        if name in ("SendMessage", "EditMessageText"):
            cid = int(getattr(method, "chat_id", None) or 1)
            return Message(message_id=next(_ids), date=datetime.now(), chat=Chat(id=cid, type="private" if cid > 0 else "supergroup"), text=getattr(method, "text", "x"))
        if name == "CopyMessage":
            return MessageId(message_id=next(_ids))
        return True

    def texts(self, chat_id):
        return [m.text for n, m in self.calls if n == "SendMessage" and m.chat_id == chat_id]

    def buttons(self, chat_id):
        out = []
        for n, m in self.calls:
            if n == "SendMessage" and m.chat_id == chat_id and m.reply_markup:
                out += [b.callback_data for row in m.reply_markup.inline_keyboard for b in row if b.callback_data]
        return out

    def copies(self):
        return [m for n, m in self.calls if n == "CopyMessage"]


class Client:
    def __init__(self, dp, bot, uid, chat_id=None):
        self.dp, self.bot, self.uid, self.chat_id = dp, bot, uid, chat_id or uid

    def _user(self):
        return User(id=self.uid, is_bot=False, first_name="Anna", username=f"u{self.uid}")

    def _msg(self, **kw):
        c = Chat(id=self.chat_id, type="private" if self.chat_id > 0 else "supergroup")
        return Message(message_id=next(_ids), date=datetime.now(), chat=c, from_user=self._user(), **kw)

    async def send(self, text=None, photo=False, document=None, caption=None):
        kw = {"text": text}
        if caption:
            kw["caption"] = caption
        if photo:
            kw["photo"] = [PhotoSize(file_id="p", file_unique_id="pu", width=10, height=10)]
        if document:
            kw["document"] = Document(file_id="d", file_unique_id="du", file_name=document)
        await self.dp.feed_update(self.bot, Update(update_id=next(_ids), message=self._msg(**kw)))

    async def press(self, data):
        cb = CallbackQuery(id=str(next(_ids)), from_user=self._user(), chat_instance="ci", data=data, message=self._msg(text="menu"))
        await self.dp.feed_update(self.bot, Update(update_id=next(_ids), callback_query=cb))


@pytest.fixture()
def world(env, tmp_path):
    session = FakeSession()
    bot = Bot("1:TEST", session=session)
    dp = Dispatcher(storage=SqliteStorage(tmp_path / "fsm.db"))
    main.router._parent_router = None
    main._hits.clear()
    dp.include_router(main.router)
    return session, bot, dp


def run(c):
    return asyncio.run(c)


async def finish_print_docs(cl):
    """Answers the questions of the 'print documents' wizard after a file was already sent."""
    await cl.send("12")                    # pages
    await cl.send("2")                     # sets
    for code in ("a4", "bw", "two", "std", "staple", "today", "pickup"):
        await cl.press(f"w:c:{code}")
    await cl.send("Анна")
    await cl.send("099 123 456")
    await cl.press("w:c:tg")
    await cl.press("w:c:none")             # no comment


def test_language_then_faq(world):
    session, bot, dp = world
    cl = Client(dp, bot, 500)
    run(cl.send("/start"))
    assert "lang:ru" in session.buttons(500)
    run(cl.press("lang:ru"))
    assert "m:services" in session.buttons(500)
    run(cl.send("где вы находитесь"))
    assert any("Маштоца" in t for t in session.texts(500))
    run(cl.send("ывапролдж"))                                                    # not understood: offers services, never silence
    assert "svc:print_docs" in session.buttons(500)
    assert not session.texts(STAFF)                                               # chatting alone never reaches the staff


def test_file_first_then_complete_request_goes_to_staff(world):
    session, bot, dp = world
    cl = Client(dp, bot, 501)
    run(cl.send("/start")); run(cl.press("lang:ru"))
    run(cl.send(photo=True))                                                      # just a photo, no words
    assert "svc:print_docs" in session.buttons(501) and "svc:photo_print" in session.buttons(501)
    run(cl.press("svc:print_docs"))
    assert not session.texts(STAFF)                                               # nothing yet: the request is not complete
    run(finish_print_docs(cl))
    assert "c:send" in session.buttons(501) and not session.texts(STAFF)          # confirmation shown, still nothing sent
    run(cl.press("c:send"))
    staff = session.texts(STAFF)
    assert len(staff) == 1 and "ЗАЯВКА DF-" in staff[0] and "Печать документов" in staff[0] and "+374 99 123456" in staff[0] and "Файлов: 1" in staff[0]
    assert len(session.copies()) == 1                                             # the client's photo was copied to the staff chat
    assert any("DF-" in t for t in session.texts(501))
    leads = db.leads_open()
    assert len(leads) == 1 and leads[0]["service"] == "print_docs"


def test_cancelled_or_unfinished_request_is_never_sent(world):
    session, bot, dp = world
    cl = Client(dp, bot, 502)
    run(cl.send("/start")); run(cl.press("lang:ru"))
    run(cl.press("svc:copy")); run(cl.send("5")); run(cl.send("2"))
    run(cl.press("w:cancel"))
    run(cl.press("svc:copy")); run(cl.send("abc"))                                # invalid answer: asked again
    assert not session.texts(STAFF) and not db.leads_open()


def test_question_flow_needs_a_phone_before_it_reaches_staff(world):
    session, bot, dp = world
    cl = Client(dp, bot, 503)
    run(cl.send("/start")); run(cl.press("lang:en"))
    run(cl.send("I want to talk to a real person"))
    run(cl.send("Can you stamp a company seal?"))
    run(cl.send("Maria"))
    assert not session.texts(STAFF)
    run(cl.send("not a number"))
    assert not session.texts(STAFF)
    run(cl.send("+374 98 765432")); run(cl.press("w:c:wa"))
    run(cl.press("c:send"))
    staff = session.texts(STAFF)
    assert len(staff) == 1 and "ВОПРОС" in staff[0] and "company seal" in staff[0] and "+374 98 765432" in staff[0]


def test_armenian_flow_and_staff_done_notifies_client(world):
    session, bot, dp = world
    cl, staff_user = Client(dp, bot, 504), Client(dp, bot, 111, STAFF)
    run(cl.send("/start")); run(cl.press("lang:hy"))
    run(cl.press("svc:passport_photo")); run(cl.press("w:c:passport")); run(cl.send("2")); run(cl.press("w:c:shoot"))
    run(cl.press("w:c:today")); run(cl.press("w:c:pickup")); run(cl.send("Արմեն")); run(cl.send("77123456")); run(cl.press("w:c:call")); run(cl.press("w:c:none"))
    run(cl.press("c:send"))
    lead = db.leads_open()[0]
    run(staff_user.press(f"st:done:{lead['id']}"))
    assert db.lead_get(lead["id"])["status"] == "done"
    assert any(lead["code"] in t for t in session.texts(504)[-1:])                # the client is told it is ready
    stranger = Client(dp, bot, 999)
    run(stranger.press(f"st:spam:{lead['id']}"))                                  # a client can never change a status
    assert db.lead_get(lead["id"])["status"] == "done"


def test_daily_limit(world, monkeypatch):
    session, bot, dp = world
    monkeypatch.setattr(main, "MAX_LEADS_PER_DAY", 1)
    cl = Client(dp, bot, 505)
    run(cl.send("/start")); run(cl.press("lang:ru"))
    for _ in range(2):
        run(cl.press("svc:question")); run(cl.send("Вопрос про печать на ткани")); run(cl.send("Мария")); run(cl.send("099123456")); run(cl.press("w:c:tg")); run(cl.press("c:send"))
    assert len(session.texts(STAFF)) == 1


def test_website_deep_link_opens_the_service(world):
    session, bot, dp = world
    cl = Client(dp, bot, 506)
    run(cl.send("/start svc_cards_flyers"))
    assert any("Визитки" in x or "Что нужно напечатать" in x for x in session.texts(506))
    assert "w:c:cards" in session.buttons(506)
    run(cl.send("/start svc_nonsense"))                       # an unknown payload falls back to the normal start
    assert "lang:ru" in session.buttons(506) or "m:services" in session.buttons(506)


def test_lead_remembers_where_the_client_came_from(world):
    session, bot, dp = world
    cl = Client(dp, bot, 507)
    run(cl.send("/start ads_meta")); run(cl.press("lang:ru"))
    run(cl.press("svc:question")); run(cl.send("Можно ли напечатать на холсте?")); run(cl.send("Мария")); run(cl.send("099123456")); run(cl.press("w:c:tg")); run(cl.press("c:send"))
    assert "Источник: ads_meta" in session.texts(STAFF)[-1]
    cl2 = Client(dp, bot, 508)
    run(cl2.send("/start svc_copy")); run(cl2.press("w:cancel")); run(cl2.press("svc:question"))
    run(cl2.send("Сколько стоит копия?")); run(cl2.send("Мария")); run(cl2.send("099123457")); run(cl2.press("w:c:tg")); run(cl2.press("c:send"))
    assert "Источник: site" in session.texts(STAFF)[-1]
