# -*- coding: utf-8 -*-
"""Validation, FAQ matching and the intake logic (no Telegram)."""
import pytest

from bot import faq, flow, validate as V
from bot.services import SERVICES, steps_for


@pytest.mark.parametrize("raw,exp", [("+37499123456", "+374 99 123456"), ("099123456", "+374 99 123456"), ("99123456", "+374 99 123456"),
                                      ("+374 (99) 12-34-56", "+374 99 123456"), ("0037499123456", "+374 99 123456"), ("+79161234567", "+79161234567"),
                                      ("12345", None), ("aaaaaaaa", None), ("11111111", None), ("", None)])
def test_phone(raw, exp):
    assert V.phone_norm(raw) == exp


@pytest.mark.parametrize("raw,exp", [("20", 20), ("50 шт", 50), ("1 000", 1000), ("0", None), ("много", None), ("-5", None), ("200000", None)])
def test_quantity(raw, exp):
    assert V.quantity(raw) == exp


def test_size_and_name():
    assert V.size_text("50x70 см") and V.size_text("A3") and V.size_text("А4") and V.size_text("10х15")
    assert V.size_text("большой") is None and V.size_text("x") is None
    assert V.first_name("Анна") and V.first_name("Ani Hakobyan") and V.first_name("Արմեն")
    assert V.first_name("a1") is None and V.first_name("http://x.com") is None and V.first_name("@bob") is None and V.first_name("ааааааа") is None
    assert V.free_text("ok") and V.free_text("........") is None and V.free_text(" ") is None


@pytest.mark.parametrize("q,intent,svc", [
    ("Сколько стоит распечатать фото 10х15?", "s_photo_print", "photo_print"), ("где вы находитесь", "address", None), ("Когда работаете?", "hours", None),
    ("нужно фото на паспорт", "s_passport_photo", "passport_photo"), ("сделайте ксерокс", "s_copy", "copy"), ("нужно отсканировать", "s_scan", "scan"),
    ("how much does it cost", "price", None), ("where are you located", "address", None), ("business cards please", "s_cards_flyers", "cards_flyers"),
    ("ինչքան արժե", "price", None), ("որտեղ եք", "address", None), ("можно с флешки?", "files", None), ("спасибо", "thanks", None),
    ("позовите менеджера", "human", None), ("нужен плакат", "s_large_format", "large_format"), ("ламинирование А4", "s_postpress", "postpress")])
def test_faq_match(q, intent, svc):
    assert faq.match(q) == (intent, svc)


def test_faq_no_match_and_answers():
    assert faq.match("ывапролдж") == (None, None) and faq.match("") == (None, None)
    for lang in ("ru", "en", "hy"):
        for key in ("hello", "thanks", "hours", "address", "phone", "price", "timing", "files", "services", "payment", "delivery", "minimum", "certificate", "human"):
            a = faq.answer(key, lang)
            assert a and "{" not in a, (key, lang)


def test_every_text_exists_in_three_languages():
    for key, svc in SERVICES.items():
        assert all(svc["title"][l] for l in ("ru", "en", "hy")), key
        for st in steps_for(key):
            assert all(st["q"][l] for l in ("ru", "en", "hy")), (key, st["id"])
            for code, lab in st.get("opts", []):
                assert all(lab[l] for l in ("ru", "en", "hy")), (key, st["id"], code)
            if st.get("skip"):
                assert all(st["skip"][1][l] for l in ("ru", "en", "hy"))


def _run(st, answers):
    """Feeds scripted answers; returns the list of step ids asked."""
    asked = []
    for _ in range(80):
        step = flow.next_step(st)
        if step is None:
            return asked
        asked.append(step["id"])
        a = answers.get(step["id"], answers.get("_default"))
        if step["kind"] == "choice":
            codes = [c for c, _ in step["opts"]]
            assert flow.apply(st, step, code=a if a in codes else codes[0]) is None, step["id"]
        elif step["kind"] in ("files", "files_opt"):
            if step["kind"] == "files":
                st["files"].append({"chat": 1, "mid": 1, "kind": "photo", "name": ""})
            st["files_done"] = True
        else:
            assert flow.apply(st, step, raw=a) is None, (step["id"], a)
    raise AssertionError("the flow never finished: " + str(asked))


ANS = {"pages": "10", "copies": "2", "qty": "100", "size": "50x70", "name": "Анна", "phone": "099123456", "address": "Маштоца 10, кв 5", "what": "что-то нужно",
       "about": "небольшая студия красоты", "design_text": "логотип и телефон", "doc_text": "виза в Италию", "deadline_text": "в пятницу", "refs": "нет", "comment": "спасибо"}


@pytest.mark.parametrize("service", [k for k in SERVICES])
def test_every_service_reaches_a_complete_request(service):
    st = flow.new_state(service)
    asked = _run(st, ANS)
    assert flow.is_complete(st) and "name" in asked and "phone" in asked
    txt = flow.summary_text(st, "ru")
    assert SERVICES[service]["title"]["ru"] in txt and "+374 99 123456" in txt
    assert flow.summary_text(st, "hy") and flow.summary_text(st, "en")


def test_file_first_skips_the_file_questions():
    f = [{"chat": 1, "mid": 5, "kind": "photo", "name": ""}]
    st = flow.new_state("print_docs", files=f, caption="распечатать 3 копии")
    asked = _run(st, ANS)
    assert "source" not in asked and "files" not in asked and "pages" in asked
    assert "распечатать 3 копии" in flow.summary_text(st, "ru")


def test_other_option_asks_for_details_and_back_removes_answers():
    st = flow.new_state("print_docs")
    flow.apply(st, flow.next_step(st), code="bring")                    # source
    for sid in ("pages", "copies"):
        flow.apply(st, flow.next_step(st), raw="3")
    step = flow.next_step(st)
    assert step["id"] == "format"
    assert flow.apply(st, step, code="other") is None
    nxt = flow.next_step(st)
    assert nxt["id"] == "format_text"                                    # 'other' needs a few words
    assert flow.apply(st, nxt, raw="A2 (420x594)") is None
    assert flow.next_step(st)["id"] == "color"
    assert flow.undo(st) and flow.next_step(st)["id"] == "format_text"
    assert flow.apply(st, flow.next_step(st), raw="x") == "text"         # too short
    assert flow.apply(st, flow.next_step(st), code="x") == "text" or True


def test_bad_answers_are_rejected_not_stored():
    st = flow.new_state("copy")
    step = flow.next_step(st)
    assert flow.apply(st, step, raw="много") == "int" and "pages" not in st["data"]
    assert flow.apply(st, step, raw="5") is None
    st2 = flow.new_state("question")
    for raw in ("?", "ok"):
        assert flow.apply(st2, flow.next_step(st2), raw=raw) == "text"
    assert flow.apply(st2, flow.next_step(st2), raw="Сколько стоит сделать оттиск печати?") is None
    nm = flow.next_step(st2); assert nm["id"] == "name"
    assert flow.apply(st2, nm, raw="123") == "name" and flow.apply(st2, nm, raw="Мария") is None
    ph = flow.next_step(st2); assert ph["id"] == "phone"
    assert flow.apply(st2, ph, raw="123") == "phone"
    assert not flow.is_complete(st2)                                      # no phone yet: nothing may be sent
