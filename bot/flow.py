# -*- coding: utf-8 -*-
"""The intake logic without Telegram: which question comes next, how an answer is checked, what the summary looks like.
A request is COMPLETE only when every visible step is answered; only complete requests are ever sent to the staff."""
from . import validate as V
from .services import SERVICES, TAIL, T, O, label_of, steps_for

OTHER_Q = T("Уточните, пожалуйста: {label}.", "Please specify: {label}.", "Խնդրում ենք հստակեցնել․ {label}։")

# Russian labels for the staff summary, and the same labels in every language for the client's confirmation
LABELS = {
    "pages": T("Страниц", "Pages", "Էջեր"), "copies": T("Копий / комплектов", "Copies / sets", "Պատճեններ / հավաքածուներ"), "format": T("Формат", "Format", "Ֆորմատ"),
    "color": T("Цвет", "Colour", "Գույն"), "sides": T("Стороны", "Sides", "Կողմեր"), "paper": T("Бумага", "Paper", "Թուղթ"), "finishing": T("Обработка", "Finishing", "Մշակում"),
    "source": T("Файл", "File", "Ֆայլ"), "files": T("Файлы", "Files", "Ֆայլեր"), "design_text": T("Что на макете", "Layout content", "Մակետի բովանդակություն"),
    "qty": T("Количество", "Quantity", "Քանակ"), "size": T("Размер", "Size", "Չափս"), "product": T("Изделие", "Product", "Ապրանք"), "material": T("Материал", "Material", "Նյութ"),
    "retouch": T("Ретушь", "Retouching", "Ռետուշ"), "doc": T("Документ", "Document", "Փաստաթուղթ"), "doc_text": T("Документ (уточнение)", "Document (details)", "Փաստաթուղթ (մանրամասն)"),
    "shoot": T("Съёмка", "Photo", "Լուսանկարում"), "result": T("Куда отправить", "Send to", "Ուր ուղարկել"), "operation": T("Операция", "Operation", "Գործողություն"),
    "op": T("Операция", "Operation", "Գործողություն"), "what": T("Что нужно", "Request", "Հարցում"), "about": T("О бизнесе и задаче", "About the business and task", "Բիզնեսի և խնդրի մասին"),
    "refs": T("Примеры / пожелания", "Examples / wishes", "Օրինակներ / ցանկություններ"), "print": T("Печать", "Printing", "Տպագրություն"), "deadline": T("Срок", "Deadline", "Ժամկետ"),
    "deadline_text": T("Срок (дата)", "Deadline (date)", "Ժամկետ (ամսաթիվ)"), "fulfil": T("Получение", "Pick-up / delivery", "Ստացում"), "address": T("Адрес доставки", "Delivery address", "Առաքման հասցե"),
    "name": T("Имя", "Name", "Անուն"), "phone": T("Телефон", "Phone", "Հեռախոս"), "via": T("Связь", "Contact via", "Կապ"), "comment": T("Комментарий", "Comment", "Մեկնաբանություն"),
}
SKIP_WORD = T("—", "—", "—")


def new_state(service, files=None, caption=None):
    """files = list of dicts (chat_id, message_id, kind, name) already received (the client sent a file first)."""
    st = {"service": service, "data": {}, "files": list(files or []), "files_done": False, "prefilled": bool(files), "order": []}
    if files and "source" in {s["id"] for s in steps_for(service)}:
        st["data"]["source"] = "now"
    if caption:
        st["caption"] = V.free_text(caption, 1, 800) or ""
    return st


def _visible(step, data):
    w = step.get("when")
    return not w or data.get(w[0]) == w[1]


def _step_by_id(service, sid):
    for s in steps_for(service):
        if s["id"] == sid:
            return s
    return None


def _answered(step, st):
    sid, data = step["id"], st["data"]
    if step["kind"] in ("files", "files_opt"):
        if step["kind"] == "files" and not st["files"]:
            return False
        return st["files_done"] or (st["prefilled"] and bool(st["files"]))
    if sid not in data:
        return False
    if data[sid] == "other" and step["kind"] == "choice":
        return (sid + "_text") in data
    return True


def next_step(st):
    """The first visible, unanswered step; None when the request is complete."""
    for step in steps_for(st["service"]):
        if not _visible(step, st["data"]):
            continue
        if step["id"] == "source" and "source" in st["data"]:
            continue
        if not _answered(step, st):
            if step["kind"] == "choice" and st["data"].get(step["id"]) == "other":
                return {"id": step["id"] + "_text", "kind": "text", "min": 2, "parent": step["id"], "label": step["label"],
                        "q": {l: OTHER_Q[l].format(label=LABELS.get(step["id"], T(step["label"], step["label"], step["label"]))[l].lower()) for l in ("ru", "en", "hy")}}
            return step
    return None


def progress(st):
    vis = [s for s in steps_for(st["service"]) if _visible(s, st["data"]) and not (s["id"] == "source" and st["prefilled"])]
    done = sum(1 for s in vis if _answered(s, st))
    return done, len(vis)


def apply(st, step, raw=None, code=None):
    """Checks one answer and stores it. Returns None when accepted, otherwise an error key (ru/en/hy text via ERRORS)."""
    sid, kind, data = step["id"], step["kind"], st["data"]
    if kind == "choice":
        if code not in {c for c, _ in step["opts"]}:
            return "choice"
        value = code
    elif kind == "text" and code and step.get("skip") and code == step["skip"][0]:
        value = "—"
    elif kind == "int":
        value = V.quantity(raw)
        if value is None:
            return "int"
    elif kind == "size":
        value = V.size_text(raw)
        if value is None:
            return "size"
    elif kind == "phone":
        value = V.phone_norm(raw)
        if value is None:
            return "phone"
    elif kind == "name":
        value = V.first_name(raw)
        if value is None:
            return "name"
    elif kind == "address":
        value = V.address_text(raw)
        if value is None:
            return "address"
    elif kind == "text":
        value = V.free_text(raw, step.get("min", 2))
        if value is None:
            return "text"
    else:
        return "kind"
    key = sid
    if step.get("parent"):
        key = sid                                  # sid is already '<parent>_text'
    data[key] = value
    st["order"].append(key)
    return None


def undo(st):
    """Removes the last answer (the 'back' button). Returns True if something was removed."""
    while st["order"]:
        k = st["order"].pop()
        if k in st["data"]:
            del st["data"][k]
            if k == "source":
                st["files_done"] = False
            return True
    return False


ERRORS = {
    "choice": T("Выберите вариант кнопкой ниже.", "Please pick an option with a button below.", "Ընտրեք տարբերակը ներքևի կոճակով։"),
    "int": T("Напишите число, например 20.", "Please write a number, for example 20.", "Գրեք թիվ, օրինակ՝ 20։"),
    "size": T("Напишите размер цифрами, например 50x70 см, или формат (A3).", "Please write the size in numbers, for example 50x70 cm, or a format (A3).", "Գրեք չափսը թվերով, օրինակ՝ 50x70 սմ, կամ ֆորմատ (A3)։"),
    "phone": T("Не удалось распознать номер. Напишите в виде +374 99 123456.", "I could not read the number. Please write it like +374 99 123456.", "Չհաջողվեց ճանաչել համարը։ Գրեք այսպես՝ +374 99 123456։"),
    "name": T("Напишите имя буквами (без цифр и ссылок).", "Please write the name in letters (no digits or links).", "Գրեք անունը տառերով (առանց թվերի և հղումների)։"),
    "address": T("Напишите адрес подробнее: улица, дом.", "Please write the address in more detail: street, building.", "Գրեք հասցեն ավելի մանրամասն․ փողոց, շենք։"),
    "text": T("Напишите чуть подробнее, пожалуйста.", "Please write a little more detail.", "Խնդրում ենք գրել մի փոքր ավելի մանրամասն։"),
    "kind": T("Не понял ответ. Попробуйте ещё раз.", "I did not understand. Please try again.", "Չհասկացա։ Փորձեք կրկին։"),
}


def _value_text(step, st, lang):
    sid, v = step["id"], st["data"].get(step["id"])
    if step["kind"] in ("files", "files_opt"):
        n = len(st["files"])
        return f"{n}" if n else "—"
    if step["kind"] == "choice":
        base = label_of(step["opts"], v, lang)
        extra = st["data"].get(sid + "_text")
        return f"{base}: {extra}" if extra else base
    return str(v)


def summary_lines(st, lang="ru"):
    """[(label, value)] for every visible answered step, in question order."""
    out = []
    for step in steps_for(st["service"]):
        if not _visible(step, st["data"]):
            continue
        if step["kind"] in ("files", "files_opt"):
            if st["files"] or step["kind"] == "files":
                out.append((LABELS["files"][lang], str(len(st["files"])) if st["files"] else "—"))
            continue
        if step["id"] == "source" and st["data"].get("source") == "now" and st["files"]:
            continue
        if step["id"] not in st["data"]:
            continue
        out.append((LABELS.get(step["id"], T(step["label"], step["label"], step["label"]))[lang], _value_text(step, st, lang)))
    if st.get("caption"):
        out.append((LABELS["comment"][lang] + " (" + {"ru": "к файлу", "en": "on the file", "hy": "ֆայլի տակ"}[lang] + ")", st["caption"]))
    return out


def summary_text(st, lang="ru"):
    title = SERVICES[st["service"]]["title"][lang]
    return f"{SERVICES[st['service']]['emoji']} {title}\n" + "\n".join(f"• {k}: {v}" for k, v in summary_lines(st, lang))


def is_complete(st) -> bool:
    return next_step(st) is None
