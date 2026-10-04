# -*- coding: utf-8 -*-
"""Design Factory assistant bot: answers the simple questions, takes files, asks everything a copy centre needs to know,
and sends the request to the staff chat ONLY when it is complete."""
import asyncio
import logging
import time
from collections import defaultdict, deque

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import db, faq, flow
from .config import BOT_TOKEN, MAX_FILES_PER_LEAD, MAX_LEADS_PER_DAY, OWNER_ID, RATE_LIMIT, SHOP, STAFF_CHAT_ID
from .fsm_storage import SqliteStorage
from .services import GROUPS, SERVICES, T, steps_for

log = logging.getLogger("df")
router = Router()
LANGS = ("hy", "ru", "en")


class W(StatesGroup):
    ask = State()        # the wizard is asking questions
    pick = State()       # the client sent files first: waiting for the choice of service
    confirm = State()    # complete: waiting for "send"


# ------------------------------------------------------------------ texts of the interface
U = {
    "choose_lang": T("Выберите язык / Ընտրեք լեզուն / Choose a language", "Выберите язык / Ընտրեք լեզուն / Choose a language", "Выберите язык / Ընտրեք լեզուն / Choose a language"),
    "welcome": T("Здравствуйте! Я помощник центра «Дизайн Фектори» (Ереван, Маштоца 42).\n\nЯ отвечу на простые вопросы и соберу вашу заявку: формат, цвет, бумагу, размер, тираж. Когда всё будет понятно, менеджер сразу назовёт цену и срок.\n\nМожно просто прислать файл или фото и написать, что с ним сделать.",
                 "Hello! I am the assistant of the Design Factory print centre (42 Mashtots Ave., Yerevan).\n\nI answer simple questions and collect your request: format, colour, paper, size, quantity. When everything is clear, the manager will quote the price and timing right away.\n\nYou can simply send a file or a photo and tell me what to do with it.",
                 "Բարև ձեզ։ Ես «Դիզայն Ֆեքթորի» կենտրոնի օգնականն եմ (Երևան, Մաշտոցի 42)։\n\nԿպատասխանեմ պարզ հարցերին և կհավաքեմ ձեր հայտը․ ֆորմատ, գույն, թուղթ, չափս, տպաքանակ։ Երբ ամեն ինչ պարզ լինի, մենեջերը անմիջապես կնշի գինը և ժամկետը։\n\nԿարող եք պարզապես ուղարկել ֆայլ կամ լուսանկար և գրել՝ ինչ անել դրա հետ։"),
    "menu_title": T("Что вас интересует?", "What can I help with?", "Ի՞նչով կարող եմ օգնել։"),
    "btn_order": T("🖨 Заказать / узнать цену", "🖨 Order / get a price", "🖨 Պատվիրել / իմանալ գինը"),
    "btn_services": T("📋 Все услуги", "📋 All services", "📋 Բոլոր ծառայությունները"),
    "btn_faq": T("❓ Частые вопросы", "❓ FAQ", "❓ Հաճախ տրվող հարցեր"),
    "btn_contacts": T("📍 Адрес, часы, телефон", "📍 Address, hours, phone", "📍 Հասցե, ժամեր, հեռախոս"),
    "btn_lang": T("🌐 Язык", "🌐 Language", "🌐 Լեզու"), "btn_menu": T("🏠 В меню", "🏠 Menu", "🏠 Մենյու"),
    "btn_question": T("💬 Задать вопрос менеджеру", "💬 Ask the manager", "💬 Հարց մենեջերին"),
    "btn_back": T("↩️ Назад", "↩️ Back", "↩️ Հետ"), "btn_cancel": T("✖ Отмена", "✖ Cancel", "✖ Չեղարկել"), "btn_done": T("✅ Готово", "✅ Done", "✅ Պատրաստ է"),
    "btn_send": T("✅ Отправить заявку", "✅ Send the request", "✅ Ուղարկել հայտը"), "btn_restart": T("🔄 Начать заново", "🔄 Start over", "🔄 Սկսել նորից"),
    "btn_start_svc": T("✅ Оформить заявку", "✅ Make a request", "✅ Ձևակերպել հայտ"),
    "services_title": T("Выберите услугу:", "Choose a service:", "Ընտրեք ծառայությունը․"),
    "faq_title": T("Выберите вопрос:", "Choose a question:", "Ընտրեք հարցը․"),
    "pick_file": T("Получил файл ({n}). Что с ним сделать? Выберите услугу, дальше я задам нужные вопросы (формат, цвет, бумага, тираж). Можно добавить ещё файлы.",
                   "Got your file ({n}). What should we do with it? Choose a service and I will ask the questions we need (format, colour, paper, quantity). You can add more files.",
                   "Ստացա ֆայլը ({n})։ Ի՞նչ անել դրա հետ։ Ընտրեք ծառայությունը, հետո կտամ անհրաժեշտ հարցերը (ֆորմատ, գույն, թուղթ, տպաքանակ)։ Կարող եք ավելացնել ֆայլեր։"),
    "files_got": T("Файлов получено: {n}. Отправьте ещё или нажмите «Готово».", "Files received: {n}. Send more or press “Done”.", "Ստացված ֆայլեր․ {n}։ Ուղարկեք ևս կամ սեղմեք «Պատրաստ է»։"),
    "files_extra": T("Файл получен ({n}). Продолжим.", "File received ({n}). Let's continue.", "Ֆայլը ստացված է ({n})։ Շարունակենք։"),
    "need_file": T("Нужен хотя бы один файл.", "At least one file is needed.", "Անհրաժեշտ է գոնե մեկ ֆայլ։"),
    "too_many": T("Слишком много файлов: можно до {n}. Остальное пришлите менеджеру после заявки.", "Too many files: up to {n}. Send the rest to the manager after the request.", "Չափազանց շատ ֆայլեր․ մինչև {n}։ Մնացածը ուղարկեք մենեջերին հայտից հետո։"),
    "step_of": T("Вопрос {a} из {b}", "Question {a} of {b}", "Հարց {a}՝ {b}-ից"),
    "confirm_title": T("Проверьте заявку:", "Please check the request:", "Ստուգեք հայտը․"),
    "confirm_hint": T("Если всё верно, нажмите «Отправить». Менеджер свяжется с вами.", "If everything is correct, press “Send”. The manager will contact you.", "Եթե ամեն ինչ ճիշտ է, սեղմեք «Ուղարկել»։ Մենեջերը կկապվի ձեզ հետ։"),
    "sent": T("Спасибо! Заявка {code} передана менеджеру. Он свяжется с вами, назовёт цену и срок.\nНомер заявки сохраните: по нему вам ответят быстрее.",
              "Thank you! Request {code} has been passed to the manager. They will contact you with the price and timing.\nKeep the request number: it helps us answer faster.",
              "Շնորհակալություն։ Հայտ {code}-ը փոխանցվել է մենեջերին։ Նա կկապվի ձեզ հետ՝ գինը և ժամկետը նշելու համար։\nՊահեք հայտի համարը․ դրանով ավելի արագ կպատասխանենք։"),
    "limit": T("Сегодня вы уже отправили несколько заявок. Позвоните нам или напишите в WhatsApp, чтобы не ждать.", "You have already sent several requests today. Please call us or write on WhatsApp so you do not have to wait.",
               "Այսօր դուք արդեն մի քանի հայտ եք ուղարկել։ Զանգահարեք մեզ կամ գրեք WhatsApp-ով՝ չսպասելու համար։"),
    "cancelled": T("Хорошо, заявку отменил. Если понадобится, пришлите файл или выберите услугу.", "OK, the request is cancelled. If you need anything, send a file or choose a service.", "Լավ, հայտը չեղարկվեց։ Եթե պետք լինի, ուղարկեք ֆայլ կամ ընտրեք ծառայությունը։"),
    "fallback": T("Не уверен, что понял вопрос. Выберите, что вам нужно, или пришлите файл: я задам несколько коротких вопросов, и менеджер ответит с точной ценой. Если вопрос другой, передам его менеджеру.",
                  "I am not sure I understood. Choose what you need or send a file: I will ask a few short questions and the manager will reply with an exact price. If it is something else, I will pass it to the manager.",
                  "Վստահ չեմ՝ ճիշտ հասկացա։ Ընտրեք՝ ինչ է պետք, կամ ուղարկեք ֆայլ․ կտամ մի քանի կարճ հարց, և մենեջերը կպատասխանի ճշգրիտ գնով։ Եթե հարցը այլ է, կփոխանցեմ մենեջերին։"),
    "svc_offer": T("Могу собрать заявку на «{title}»: это займёт около минуты, дальше менеджер назовёт цену и срок.", "I can collect a request for “{title}”: it takes about a minute, then the manager will give the price and timing.",
                   "Կարող եմ հավաքել հայտ «{title}»-ի համար․ դա մոտ մեկ րոպե կտևի, հետո մենեջերը կնշի գինը և ժամկետը։"),
    "question_sent": T("Спасибо! Вопрос {code} передан менеджеру, ответим в ближайшее время.", "Thank you! Question {code} has been passed to the manager; we will reply shortly.", "Շնորհակալություն։ Հարց {code}-ը փոխանցվել է մենեջերին․ շուտով կպատասխանենք։"),
    "ready": T("Ваш заказ {code} готов. Ждём вас в центре: {addr}.", "Your order {code} is ready. We are waiting for you at: {addr}.", "Ձեր պատվեր {code}-ը պատրաստ է։ Սպասում ենք ձեզ՝ {addr}։"),
    "unknown_media": T("Я принимаю фото, файлы и текст. Опишите словами, что нужно, или пришлите файл.", "I accept photos, files and text. Describe what you need in words or send a file.", "Ես ընդունում եմ լուսանկարներ, ֆայլեր և տեքստ։ Նկարագրեք բառերով՝ ինչ է պետք, կամ ուղարկեք ֆայլ։"),
    "contacts": T("📍 {addr}\n🕘 Работаем {hours}\n☎️ {phone}\nWhatsApp: {wa}\nНа карте: {map}", "📍 {addr}\n🕘 Open {hours}\n☎️ {phone}\nWhatsApp: {wa}\nOn the map: {map}", "📍 {addr}\n🕘 Աշխատում ենք {hours}\n☎️ {phone}\nWhatsApp՝ {wa}\nՔարտեզի վրա՝ {map}"),
    "staff_only": T("Эта команда работает только в чате сотрудников.", "This command works only in the staff chat.", "Այս հրամանը աշխատում է միայն աշխատակիցների չատում։"),
}
FAQ_BUTTONS = [("hours", T("Когда работаете?", "Opening hours", "Աշխատանքային ժամեր")), ("address", T("Где находитесь?", "Where are you?", "Որտե՞ղ եք")),
               ("price", T("Сколько стоит?", "How much does it cost?", "Ինչքա՞ն արժե")), ("timing", T("Сроки, срочно", "How fast / urgent", "Ժամկետներ, շտապ")),
               ("files", T("Как прислать файл?", "How to send a file?", "Ինչպե՞ս ուղարկել ֆայլ")), ("payment", T("Оплата", "Payment", "Վճարում")),
               ("delivery", T("Доставка", "Delivery", "Առաքում")), ("minimum", T("Минимальный заказ", "Minimum order", "Նվազագույն պատվեր"))]


def lang_of(uid) -> str:
    return db.user_lang(uid) or "ru"


def kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) if not d.startswith("http") else InlineKeyboardButton(text=t, url=d) for t, d in row] for row in rows])


def main_menu(lang):
    return kb([[(U["btn_order"][lang], "m:services")], [(U["btn_faq"][lang], "m:faq"), (U["btn_contacts"][lang], "m:contacts")],
               [(U["btn_question"][lang], "svc:question"), (U["btn_lang"][lang], "m:lang")]])


def services_kb(lang, extra=True):
    rows = []
    for gkey, _gt in GROUPS:
        row = [(f"{s['emoji']} {s['title'][lang]}", f"svc:{k}") for k, s in SERVICES.items() if s["group"] == gkey]
        rows += [row[i:i + 2] for i in range(0, len(row), 2)]
    if extra:
        rows.append([(U["btn_question"][lang], "svc:question")])
        rows.append([(U["btn_menu"][lang], "m:main")])
    return kb(rows)


def nav_row(lang, back=True):
    return ([(U["btn_back"][lang], "w:back")] if back else []) + [(U["btn_cancel"][lang], "w:cancel")]


# ------------------------------------------------------------------ middleware: a simple rate limit
_hits = defaultdict(deque)


def rate_ok(uid) -> bool:
    now, q = time.time(), _hits[uid]
    while q and now - q[0] > RATE_LIMIT[1]:
        q.popleft()
    q.append(now)
    return len(q) <= RATE_LIMIT[0]


# ------------------------------------------------------------------ helpers
def file_ref(m: Message):
    """What we keep of an incoming file: where it is (to copy it to the staff chat later) and what it is."""
    if m.photo:
        return {"chat": m.chat.id, "mid": m.message_id, "kind": "photo", "name": ""}
    if m.document:
        return {"chat": m.chat.id, "mid": m.message_id, "kind": "document", "name": (m.document.file_name or "")[:80]}
    if m.video:
        return {"chat": m.chat.id, "mid": m.message_id, "kind": "video", "name": ""}
    return None


def staff_chat() -> int:
    return int(db.setting_get("staff_chat", STAFF_CHAT_ID or OWNER_ID or 0))


def is_staff(chat_id, user_id) -> bool:
    sc = staff_chat()
    return (sc and chat_id == sc) or (OWNER_ID and user_id == OWNER_ID)


async def show_menu(target, lang, text=None):
    await target.answer(text or U["menu_title"][lang], reply_markup=main_menu(lang))


async def ask(target, state: FSMContext, lang: str):
    """Sends the next question of the wizard (or the confirmation when the request is complete)."""
    st = (await state.get_data())["st"]
    step = flow.next_step(st)
    if step is None:
        await state.set_state(W.confirm)
        text = U["confirm_title"][lang] + "\n\n" + flow.summary_text(st, lang) + "\n\n" + U["confirm_hint"][lang]
        await target.answer(text, reply_markup=kb([[(U["btn_send"][lang], "c:send")], [(U["btn_back"][lang], "w:back"), (U["btn_restart"][lang], "c:restart")], [(U["btn_cancel"][lang], "w:cancel")]]))
        return
    await state.set_state(W.ask)
    a, b = flow.progress(st)
    head = U["step_of"][lang].format(a=min(a + 1, b), b=b)
    rows = []
    if step["kind"] == "choice":
        opts = step["opts"]
        rows = [[(lab[lang], f"w:c:{code}") for code, lab in opts[i:i + 2]] for i in range(0, len(opts), 2)]
    elif step["kind"] in ("files", "files_opt"):
        rows = [[(U["btn_done"][lang], "w:done")]]
    elif step.get("skip"):
        rows = [[(step["skip"][1][lang], f"w:c:{step['skip'][0]}")]]
    rows.append(nav_row(lang, back=bool(st["order"])))
    await target.answer(f"{head}\n{step['q'][lang]}", reply_markup=kb(rows))


async def begin(target, state: FSMContext, lang: str, service: str, files=None, caption=None, user=None):
    st = flow.new_state(service, files, caption)
    await state.set_data({"st": st})
    svc = SERVICES[service]
    note = svc.get("note")
    if note:
        await target.answer(f"{svc['emoji']} {svc['title'][lang]}\nℹ️ {note[lang]}")
    await ask(target, state, lang)


# ------------------------------------------------------------------ commands and menu
@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext, command: CommandObject = None):
    """/start, or a deep link from the website: /start svc_<service> opens that service's questions at once."""
    await state.clear()
    db.user_touch(m.from_user.id, m.from_user.full_name, m.from_user.username)
    lang = db.user_lang(m.from_user.id)
    payload = (command.args or "") if command else ""
    if payload:                                              # where the client came from: site, ads_meta, ads_google, maps, qr...
        db.setting_set(f"src:{m.from_user.id}", "site" if payload.startswith("svc_") else payload[:40])
    if payload.startswith("svc_") and payload[4:] in SERVICES and payload[4:] != "question":
        if not lang:
            db.user_touch(m.from_user.id, lang="ru")
            lang = "ru"
        return await begin(m, state, lang, payload[4:])
    if not lang:
        await m.answer(U["choose_lang"]["ru"], reply_markup=kb([[("🇦🇲 Հայերեն", "lang:hy"), ("🇷🇺 Русский", "lang:ru"), ("🇬🇧 English", "lang:en")]]))
        return
    await show_menu(m, lang, U["welcome"][lang])


@router.message(Command("menu"))
async def cmd_menu(m: Message, state: FSMContext):
    await state.clear()
    await show_menu(m, lang_of(m.from_user.id))


@router.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext):
    lang = lang_of(m.from_user.id)
    await state.clear()
    await show_menu(m, lang, U["cancelled"][lang])


@router.message(Command("lang"))
async def cmd_lang(m: Message):
    await m.answer(U["choose_lang"]["ru"], reply_markup=kb([[("🇦🇲 Հայերեն", "lang:hy"), ("🇷🇺 Русский", "lang:ru"), ("🇬🇧 English", "lang:en")]]))


@router.message(Command("myid"))
async def cmd_myid(m: Message):
    await m.answer(f"user id: {m.from_user.id}\nchat id: {m.chat.id}")


@router.message(Command("setstaff"))
async def cmd_setstaff(m: Message):
    if not OWNER_ID or m.from_user.id != OWNER_ID:
        return
    db.setting_set("staff_chat", m.chat.id)
    await m.answer(f"Готово: заявки теперь приходят в этот чат ({m.chat.id}).")


@router.message(Command("orders"))
async def cmd_orders(m: Message):
    if not is_staff(m.chat.id, m.from_user.id):
        return
    rows = db.leads_open()
    if not rows:
        await m.answer("Открытых заявок нет.")
        return
    await m.answer("Открытые заявки:\n" + "\n".join(f"{r['code']} · {SERVICES.get(r['service'], {'title': {'ru': r['service']}})['title']['ru']} · {r['status']}" for r in rows))


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(c: CallbackQuery, state: FSMContext):
    lang = c.data.split(":")[1]
    if lang not in LANGS:
        return await c.answer()
    first = db.user_lang(c.from_user.id) is None
    db.user_touch(c.from_user.id, c.from_user.full_name, c.from_user.username, lang)
    await c.answer()
    await state.clear()
    await show_menu(c.message, lang, U["welcome"][lang] if first else None)


@router.callback_query(F.data.startswith("m:"))
async def cb_menu(c: CallbackQuery, state: FSMContext):
    lang, what = lang_of(c.from_user.id), c.data.split(":")[1]
    await c.answer()
    if what == "main":
        await state.clear()
        await show_menu(c.message, lang)
    elif what == "services":
        await c.message.answer(U["services_title"][lang], reply_markup=services_kb(lang))
    elif what == "faq":
        rows = [[(lab[lang], f"f:{k}")] for k, lab in FAQ_BUTTONS] + [[(U["btn_menu"][lang], "m:main")]]
        await c.message.answer(U["faq_title"][lang], reply_markup=kb(rows))
    elif what == "contacts":
        await c.message.answer(U["contacts"][lang].format(addr=SHOP["address"][lang], hours=SHOP["hours"][lang], phone=SHOP["phone"], wa=f"https://wa.me/{SHOP['whatsapp']}", map=SHOP["map"]),
                               reply_markup=kb([[(U["btn_order"][lang], "m:services")], [(U["btn_menu"][lang], "m:main")]]))
    elif what == "lang":
        await c.message.answer(U["choose_lang"]["ru"], reply_markup=kb([[("🇦🇲 Հայերեն", "lang:hy"), ("🇷🇺 Русский", "lang:ru"), ("🇬🇧 English", "lang:en")]]))


@router.callback_query(F.data.startswith("f:"))
async def cb_faq(c: CallbackQuery):
    lang, key = lang_of(c.from_user.id), c.data.split(":")[1]
    await c.answer()
    await send_faq(c.message, key, lang)


async def send_faq(target, intent, lang):
    text = faq.answer(intent, lang)
    if intent in ("price", "services"):
        await target.answer(text, reply_markup=services_kb(lang))
    elif intent == "human":
        await target.answer(text, reply_markup=kb([[(U["btn_question"][lang], "svc:question")], [(U["btn_menu"][lang], "m:main")]]))
    else:
        await target.answer(text, reply_markup=kb([[(U["btn_order"][lang], "m:services")], [(U["btn_menu"][lang], "m:main")]]))


# ------------------------------------------------------------------ starting a request
@router.callback_query(F.data.startswith("svc:"))
async def cb_service(c: CallbackQuery, state: FSMContext):
    lang, key = lang_of(c.from_user.id), c.data.split(":")[1]
    if key not in SERVICES:
        return await c.answer()
    await c.answer()
    cur = await state.get_state()
    pending = (await state.get_data()).get("pending") if cur == W.pick.state else None
    if pending:
        await begin(c.message, state, lang, key, files=pending["files"], caption=pending.get("caption"))
    else:
        await begin(c.message, state, lang, key)


# ------------------------------------------------------------------ wizard: answers by button
@router.callback_query(W.ask, F.data.startswith("w:"))
@router.callback_query(W.confirm, F.data.startswith("w:"))
async def cb_wizard(c: CallbackQuery, state: FSMContext):
    lang, parts = lang_of(c.from_user.id), c.data.split(":")
    action = parts[1]
    data = await state.get_data()
    st = data.get("st")
    if not st:
        await c.answer()
        return await show_menu(c.message, lang)
    if action == "cancel":
        await c.answer()
        await state.clear()
        return await show_menu(c.message, lang, U["cancelled"][lang])
    if action == "back":
        flow.undo(st)
        await state.update_data(st=st)
        await c.answer()
        return await ask(c.message, state, lang)
    step = flow.next_step(st)
    if action == "done" and step and step["kind"] in ("files", "files_opt"):
        if step["kind"] == "files" and not st["files"]:
            return await c.answer(U["need_file"][lang], show_alert=True)
        st["files_done"] = True
    elif action == "c" and step:
        err = flow.apply(st, step, code=parts[2])
        if err:
            return await c.answer(flow.ERRORS[err][lang], show_alert=True)
        if step["id"] == "source" and parts[2] == "bring":
            st["files_done"] = True
    else:
        return await c.answer()
    await state.update_data(st=st)
    await c.answer()
    await ask(c.message, state, lang)


@router.callback_query(W.confirm, F.data == "c:restart")
async def cb_restart(c: CallbackQuery, state: FSMContext):
    lang = lang_of(c.from_user.id)
    st = (await state.get_data()).get("st")
    await c.answer()
    if st:
        await begin(c.message, state, lang, st["service"], files=st["files"], caption=st.get("caption"))


@router.callback_query(W.confirm, F.data == "c:send")
async def cb_send(c: CallbackQuery, state: FSMContext):
    lang = lang_of(c.from_user.id)
    st = (await state.get_data()).get("st")
    if not st or not flow.is_complete(st):
        await c.answer()
        return await ask(c.message, state, lang) if st else await show_menu(c.message, lang)
    if db.leads_today(c.from_user.id) >= MAX_LEADS_PER_DAY:
        await c.answer()
        await state.clear()
        return await show_menu(c.message, lang, U["limit"][lang])
    await c.answer()
    lead = await submit(c.bot, c.from_user, st, lang)
    await state.clear()
    key = "question_sent" if st["service"] == "question" else "sent"
    await c.message.answer(U[key][lang].format(code=lead["code"]), reply_markup=kb([[(U["btn_menu"][lang], "m:main")]]))


async def submit(bot: Bot, user, st: dict, lang: str) -> dict:
    """Stores the finished request and sends it to the staff chat together with the client's files."""
    source = db.setting_get(f"src:{user.id}", "direct")
    lead = db.lead_add(user.id, "question" if st["service"] == "question" else "order", st["service"], {"st": st, "lang": lang, "username": user.username, "full_name": user.full_name, "source": source}, st["files"])
    sc = staff_chat()
    if not sc:
        log.warning("no staff chat configured: request %s is only in the database (/orders)", lead["code"])
        return lead
    text = staff_text(lead["code"], st, user, lang, source)
    markup = kb([[("✅ Взял в работу", f"st:take:{lead['id']}"), ("🏁 Готово", f"st:done:{lead['id']}")], [("🚫 Спам", f"st:spam:{lead['id']}")]])
    try:
        msg = await bot.send_message(sc, text, reply_markup=markup)
        db.lead_set(lead["id"], staff_msg=msg.message_id, staff_chat=sc)
        for f in st["files"][:MAX_FILES_PER_LEAD]:
            try:
                await bot.copy_message(sc, f["chat"], f["mid"], reply_to_message_id=msg.message_id)
            except Exception as e:      # a deleted message must not lose the request
                log.warning("could not copy a file for %s: %s", lead["code"], e)
    except Exception as e:
        log.error("could not deliver %s to the staff chat: %s", lead["code"], e)
    return lead


def staff_text(code, st, user, lang, source="direct"):
    d = st["data"]
    who = f"{d.get('name', user.full_name)}, {d.get('phone', '—')}"
    link = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
    via = {"tg": "Telegram", "wa": "WhatsApp", "call": "позвонить"}.get(d.get("via"), "—")
    kind = "❓ ВОПРОС" if st["service"] == "question" else "📥 ЗАЯВКА"
    return (f"{kind} {code}\n{flow.summary_text(st, 'ru')}\n\n👤 {who}\n🔗 {link} · язык клиента: {lang}\n📞 Связаться: {via}"
            + (f"\n📎 Файлов: {len(st['files'])}" if st["files"] else "") + f"\n📈 Источник: {source}")


# ------------------------------------------------------------------ staff buttons
@router.callback_query(F.data.startswith("st:"))
async def cb_staff(c: CallbackQuery):
    if not is_staff(c.message.chat.id, c.from_user.id):
        return await c.answer()
    _, action, lid = c.data.split(":")
    lead = db.lead_get(int(lid))
    if not lead:
        return await c.answer("нет такой заявки", show_alert=True)
    status = {"take": "taken", "done": "done", "spam": "spam"}[action]
    db.lead_set(lead["id"], status=status)
    mark = {"taken": f"✅ В работе: {c.from_user.full_name}", "done": f"🏁 Выполнено ({c.from_user.full_name})", "spam": "🚫 Спам"}[status]
    base = (c.message.text or "").split("\n\n[")[0]
    try:
        await c.message.edit_text(f"{base}\n\n[{mark}]", reply_markup=None if status != "taken" else c.message.reply_markup)
    except Exception:
        pass
    await c.answer(mark)
    if status == "done" and lead["kind"] == "order":
        info = __import__("json").loads(lead["data"])
        lang = info.get("lang", "ru")
        try:
            await c.bot.send_message(lead["uid"], U["ready"][lang].format(code=lead["code"], addr=SHOP["address"][lang]))
        except Exception as e:
            log.info("could not notify the client of %s: %s", lead["code"], e)


# ------------------------------------------------------------------ messages inside the wizard
@router.message(W.ask)
async def msg_wizard(m: Message, state: FSMContext):
    lang = lang_of(m.from_user.id)
    st = (await state.get_data()).get("st")
    if not st:
        await state.clear()
        return await show_menu(m, lang)
    step = flow.next_step(st)
    f = file_ref(m)
    if f:
        if len(st["files"]) >= MAX_FILES_PER_LEAD:
            return await m.answer(U["too_many"][lang].format(n=MAX_FILES_PER_LEAD))
        st["files"].append(f)
        if m.caption and not st.get("caption"):
            st["caption"] = (m.caption or "")[:800]
        if "source" in {s["id"] for s in steps_for(st["service"])} and "source" not in st["data"]:
            st["data"]["source"] = "now"
        await state.update_data(st=st)
        if step and step["kind"] in ("files", "files_opt"):
            return await m.answer(U["files_got"][lang].format(n=len(st["files"])), reply_markup=kb([[(U["btn_done"][lang], "w:done")], nav_row(lang)]))
        await m.answer(U["files_extra"][lang].format(n=len(st["files"])))
        return await ask(m, state, lang)
    if step is None:
        return await ask(m, state, lang)
    if step["kind"] in ("choice", "files", "files_opt"):
        await m.answer(flow.ERRORS["choice"][lang] if step["kind"] == "choice" else U["files_got"][lang].format(n=len(st["files"])))
        return
    if not m.text:
        return await m.answer(U["unknown_media"][lang])
    err = flow.apply(st, step, raw=m.text)
    if err:
        return await m.answer(flow.ERRORS[err][lang])
    await state.update_data(st=st)
    await ask(m, state, lang)


@router.message(W.confirm)
async def msg_confirm(m: Message, state: FSMContext):
    lang = lang_of(m.from_user.id)
    await ask(m, state, lang)


# ------------------------------------------------------------------ files and texts outside the wizard
@router.message(W.pick)
async def msg_pick(m: Message, state: FSMContext):
    lang = lang_of(m.from_user.id)
    pending = (await state.get_data()).get("pending")
    f = file_ref(m)
    if f:
        if len(pending["files"]) < MAX_FILES_PER_LEAD:
            pending["files"].append(f)
        if m.caption and not pending.get("caption"):
            pending["caption"] = m.caption[:800]
        await state.update_data(pending=pending)
        return
    if m.text:
        intent, svc = faq.match(m.text)
        if svc:
            return await begin(m, state, lang, svc, files=pending["files"], caption=pending.get("caption"))
        pending["caption"] = ((pending.get("caption") or "") + " " + m.text).strip()[:800]
        await state.update_data(pending=pending)
        await m.answer(U["pick_file"][lang].format(n=len(pending["files"])), reply_markup=services_kb(lang, extra=False))


@router.message(F.photo | F.document | F.video)
async def msg_file_first(m: Message, state: FSMContext):
    """The most common start: the client sends a photo or a file (often with 'how much is it / how to print')."""
    lang = lang_of(m.from_user.id)
    db.user_touch(m.from_user.id, m.from_user.full_name, m.from_user.username)
    if not db.user_lang(m.from_user.id):
        db.user_touch(m.from_user.id, lang="ru")
        lang = "ru"
    f = file_ref(m)
    caption = (m.caption or "")[:800]
    intent, svc = faq.match(caption) if caption else (None, None)
    if svc:
        return await begin(m, state, lang, svc, files=[f], caption=caption)
    await state.set_state(W.pick)
    await state.set_data({"pending": {"files": [f], "caption": caption}})
    await m.answer(U["pick_file"][lang].format(n=1), reply_markup=services_kb(lang, extra=False))


@router.message(F.text)
async def msg_text(m: Message, state: FSMContext):
    lang = lang_of(m.from_user.id)
    if m.chat.type != "private":
        return
    if not db.user_lang(m.from_user.id):
        db.user_touch(m.from_user.id, m.from_user.full_name, m.from_user.username, "ru")
        lang = "ru"
    intent, svc = faq.match(m.text)
    if intent is None:
        return await m.answer(U["fallback"][lang], reply_markup=services_kb(lang))
    if intent == "human":
        await m.answer(faq.answer("human", lang))
        return await begin(m, state, lang, "question")
    if svc:
        title = SERVICES[svc]["title"][lang]
        extra = faq.answer("price", lang) if any(w in m.text.lower() for w in ("стоит", "цена", "price", "cost", "how much", "գին", "արժե")) else ""
        text = (extra + "\n\n" if extra else "") + U["svc_offer"][lang].format(title=title)
        return await m.answer(text, reply_markup=kb([[(U["btn_start_svc"][lang], f"svc:{svc}")], [(U["btn_order"][lang], "m:services"), (U["btn_menu"][lang], "m:main")]]))
    await send_faq(m, intent, lang)


@router.message()
async def msg_other(m: Message):
    if m.chat.type == "private":
        await m.answer(U["unknown_media"][lang_of(m.from_user.id)])


# ------------------------------------------------------------------ wiring
def build(token=None, session=None):
    db.init()
    bot = Bot(token or BOT_TOKEN, session=session) if session else Bot(token or BOT_TOKEN)
    dp = Dispatcher(storage=SqliteStorage())

    @dp.message.outer_middleware()
    async def limiter(handler, event, data):
        u = getattr(event, "from_user", None)
        if u and not rate_ok(u.id):
            return None
        return await handler(event, data)

    dp.include_router(router)
    return bot, dp


async def run():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is empty: create the bot in @BotFather and put the token into .env")
    bot, dp = build()
    me = await bot.get_me()
    log.info("bot @%s started", me.username)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(run())
