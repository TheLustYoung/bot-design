# -*- coding: utf-8 -*-
"""Answers to the questions a copy centre hears all day. A message is matched against keyword stems (ru / en / hy); no AI, no guessing:
anything unclear goes to the intake questions instead. Facts (address, phone, hours) come from shop.json, so the shop can correct them.
Prices are never invented: the bot says what the price depends on and offers to collect the details."""
import re

from .config import SHOP
from .services import T


def _norm(s: str) -> str:
    s = (s or "").lower().replace("ё", "е")
    return re.sub(r"[^\w\s]", " ", s)


def _a(d):
    return d


# intent -> (keywords, service to offer or None)
INTENTS = {
    "hello": (["привет", "здравствуй", "добрый день", "добрый вечер", "салам", "hello", "hi ", "hey", "բարև", "ողջույն"], None),
    "thanks": (["спасибо", "благодар", "thanks", "thank you", "շնորհակալ"], None),
    "hours": (["работает", "часы работы", "график", "до скольки", "во сколько", "открыт", "закрыт", "выходн", "суббот", "воскресен", "open", "hours", "close", "closing", "what time", "weekend", "բաց եք", "աշխատա", "ժամը քանիին", "մինչև ժամը", "ժամեր"], None),
    "address": (["адрес", "где находит", "где вы", "как добрат", "как найти", "где расположен", "маштоца", "подъезд", "метро", "парковк", "address", "where are you", "located", "location", "find you", "how to get", "parking", "հասցե", "որտեղ եք", "որտեղ է", "ինչպես հասնել"], None),
    "phone": (["телефон", "номер", "позвонить", "звонить", "вотсап", "ватсап", "whatsapp", "viber", "вайбер", "phone", "call you", "number", "հեռախոս", "զանգ", "վատսափ"], None),
    "price": (["сколько стоит", "цена", "цены", "стоимость", "прайс", "почем", "расценки", "тариф", "сколько будет", "сколько это", "price", "cost", "how much", "rates", "quote", "estimate", "գին", "արժե", "քանի դրամ", "ինչքան"], None),
    "timing": (["срок", "как быстро", "сколько времени", "срочно", "быстро", "успеете", "за час", "к завтра", "how long", "how fast", "urgent", "rush", "turnaround", "ready by", "ժամկետ", "շտապ", "արագ", "քանի ժամում"], None),
    "files": (["формат файл", "какой формат", "pdf", "word", "docx", "разрешени", "dpi", "вылет", "макет", "как отправить", "как прислать", "куда отправить", "флешк", "usb", "на почту", "по почте", "email", "e-mail", "в телеграм", "file format", "resolution", "bleed", "send file", "send the file", "flash drive", "ֆայլ", "ձևաչափ", "ֆլեշ"], None),
    "services": (["что печата", "услуги", "что делаете", "чем занимаетесь", "список услуг", "что у вас есть", "что можно", "what do you", "services", "what can", "offer", "ինչ ծառայ", "ծառայություն", "ինչ եք անում"], None),
    "payment": (["оплат", "картой", "наличны", "как заплатить", "предоплат", "pay", "card", "cash", "payment", "prepay", "վճար", "քարտ", "կանխիկ", "կանխավճար"], None),
    "delivery": (["доставк", "привезти", "курьер", "привезете", "delivery", "courier", "deliver", "առաք", "առաքում"], None),
    "minimum": (["минимальн", "от скольки", "один экземпляр", "одну копию", "minimum", "min order", "just one", "նվազագույն", "մեկ հատ"], None),
    "certificate": (["подарочн", "сертификат на", "gift cert", "gift card", "նվեր սերտ", "նվերի սերտ"], None),
    "human": (["оператор", "менеджер", "человек", "живой", "сотрудник", "позовите", "operator", "manager", "human", "real person", "staff", "օպերատոր", "մենեջեր", "աշխատակից"], None),
    # quick starts of a service
    "s_passport_photo": (["фото на паспорт", "фото на документ", "на паспорт", "на визу", "фото для паспорта", "фото на загран", "passport photo", "id photo", "visa photo", "անձնագրի լուսանկար", "լուսանկար փաստաթղթ", "վիզայի լուսանկար"], "passport_photo"),
    "s_copy": (["ксерокс", "ксерокопи", "скопировать", "копию", "копии", "сделать копи", "photocopy", "xerox", "copy ", "copies", "քսերո", "պատճեն"], "copy"),
    "s_print_docs": (["распечатать", "печать документ", "принтер", "печатать", "print a document", "print documents", "printing", "տպել", "տպագր փաստաթ"], "print_docs"),
    "s_scan": (["скан", "отсканир", "scan", "սկան"], "scan"),
    "s_photo_print": (["печать фото", "распечатать фото", "фотографии распеч", "фотопечат", "print photo", "photo print", "լուսանկար տպ"], "photo_print"),
    "s_cards_flyers": (["визитк", "листовк", "флаер", "буклет", "брошюр", "business card", "flyer", "leaflet", "booklet", "brochure", "այցեքարտ", "թռուցիկ", "բուկլետ"], "cards_flyers"),
    "s_large_format": (["плакат", "постер", "баннер", "чертеж", "большой формат", "poster", "banner", "large format", "plot", "պլակատ", "պոստեր", "բաններ"], "large_format"),
    "s_stickers": (["наклейк", "стикер", "плоттер", "sticker", "plotter", "կպչուն", "ստիկեր"], "stickers"),
    "s_laser": (["лазер", "гравиров", "laser", "engrav", "լազեր", "փորագր"], "laser"),
    "s_postpress": (["переплет", "ламинир", "брошюров", "сверлен", "фальцов", "тиснен", "bind", "laminat", "folding", "embos", "կազմ", "լամինաց"], "postpress"),
    "s_design": (["дизайн", "логотип", "фирменный стиль", "брендбук", "макет сделать", "design", "logo", "branding", "դիզայն", "լոգո", "ֆիրմային"], "design"),
    "s_retouch": (["ретуш", "обработк фото", "убрать фон", "реставрац", "retouch", "photoshop", "remove background", "ռետուշ"], "retouch"),
    "s_merch": (["мерч", "футболк", "кружк", "значк", "сувенир", "merch", "t-shirt", "mug", "souvenir", "մերչ", "շապիկ", "բաժակ"], "merch"),
}


def match(text: str):
    """Returns (intent, service_key_or_None) for the best keyword match, or (None, None)."""
    t = " " + _norm(text) + " "
    best, score = None, 0
    for key, (kws, _svc) in INTENTS.items():
        hits = [len(k) for k in kws if k in t]
        s = (max(hits) * 10 + len(hits)) if hits else 0          # the longest (most specific) phrase wins
        if s > score:
            best, score = key, s
    if best is None:
        return None, None
    return best, INTENTS[best][1]


def answer(intent: str, lang: str) -> str:
    a, ph, hrs = SHOP["address"][lang], SHOP["phone"], SHOP["hours"][lang]
    wa = f"https://wa.me/{SHOP['whatsapp']}"
    A = {
        "hello": T("Здравствуйте! Я помощник «Дизайн Фектори». Подскажу по услугам и соберу заявку, чтобы менеджер сразу назвал цену и срок.",
                   "Hello! I am the Design Factory assistant. I can tell you about our services and collect your request so the manager can quote the price and timing right away.",
                   "Բարև ձեզ։ Ես «Դիզայն Ֆեքթորի»-ի օգնականն եմ։ Կպատմեմ ծառայությունների մասին և կհավաքեմ հայտը, որպեսզի մենեջերը անմիջապես նշի գինը և ժամկետը։"),
        "thanks": T("Пожалуйста! Если нужно что-то напечатать или сделать, напишите или пришлите файл.", "You are welcome! If you need something printed or made, write to me or send a file.", "Խնդրեմ։ Եթե ինչ-որ բան է պետք տպել կամ անել, գրեք կամ ուղարկեք ֆայլ։"),
        "hours": T(f"Мы работаем {hrs}. Адрес: {a}.", f"We are open {hrs}. Address: {a}.", f"Մենք աշխատում ենք {hrs}։ Հասցե՝ {a}։"),
        "address": T(f"Мы находимся по адресу: {a}.\nНа карте: {SHOP['map']}", f"We are at: {a}.\nOn the map: {SHOP['map']}", f"Մեր հասցեն՝ {a}։\nՔարտեզի վրա՝ {SHOP['map']}"),
        "phone": T(f"Телефон: {ph}\nWhatsApp: {wa}\nМожно и просто написать здесь: соберу заявку и передам менеджеру.", f"Phone: {ph}\nWhatsApp: {wa}\nOr just write here: I will collect your request and pass it to the manager.",
                   f"Հեռախոս՝ {ph}\nWhatsApp՝ {wa}\nԿարող եք նաև պարզապես գրել այստեղ․ ես կհավաքեմ հայտը և կփոխանցեմ մենեջերին։"),
        "price": T("Цена зависит от того, что именно печатаем: формата, количества, цвета и бумаги. Ответьте на несколько коротких вопросов (или пришлите файл), и менеджер назовёт точную стоимость и срок.",
                   "The price depends on what exactly we print: format, quantity, colour and paper. Answer a few short questions (or send a file) and the manager will give you the exact price and timing.",
                   "Գինը կախված է նրանից՝ ինչ ենք տպում․ ֆորմատ, քանակ, գույն և թուղթ։ Պատասխանեք մի քանի կարճ հարցի (կամ ուղարկեք ֆայլ), և մենեջերը կնշի ճշգրիտ արժեքը և ժամկետը։"),
        "timing": T("Многие заказы (печать документов, визитки, плакаты) делаются в день обращения. Точный срок зависит от тиража и обработки: менеджер подтвердит его после заявки. Если срочно, отметьте это в заявке.",
                    "Many orders (document printing, business cards, posters) are done the same day. The exact time depends on quantity and finishing: the manager will confirm it after your request. If it is urgent, mark it in the request.",
                    "Շատ պատվերներ (փաստաթղթերի տպագրություն, այցեքարտեր, պլակատներ) կատարվում են նույն օրը։ Ճշգրիտ ժամկետը կախված է տպաքանակից և մշակումից․ մենեջերը կհաստատի հայտից հետո։ Եթե շտապ է, նշեք հայտում։"),
        "files": T("Файл можно прислать прямо сюда: фото, PDF, Word, картинку. Для печати лучше PDF; фото и макеты желательно в хорошем разрешении (от 300 dpi), для полиграфии с запасом под обрез по 3 мм. Если не уверены, присылайте как есть: менеджер проверит и подскажет.",
                   "You can send the file right here: a photo, PDF, Word document or image. PDF is best for printing; photos and layouts should be in good resolution (300 dpi or more), and for print products with a 3 mm bleed. If you are not sure, send it as it is: the manager will check it and advise.",
                   "Ֆայլը կարող եք ուղարկել հենց այստեղ․ լուսանկար, PDF, Word, նկար։ Տպագրության համար լավագույնը PDF-ն է․ լուսանկարները և մակետները նախընտրելի է լավ թույլտվությամբ (300 dpi և ավելի), պոլիգրաֆիայի համար՝ 3 մմ պահուստով։ Եթե վստահ չեք, ուղարկեք ինչպես կա․ մենեջերը կստուգի և կխորհուրդ կտա։"),
        "services": T("Мы делаем: ксерокопию, печать документов, сканирование, печать фото, фото на документы, плакаты и большой формат, визитки/листовки/буклеты, наклейки и плоттерную резку, лазерную резку и гравировку, переплёт и ламинирование, дизайн и фирменный стиль, ретушь фото, мерч.\nВыберите нужное ниже.",
                      "We do: photocopying, document printing, scanning, photo printing, passport/ID photos, posters and large format, business cards/flyers/booklets, stickers and plotter cutting, laser cutting and engraving, binding and lamination, design and branding, photo retouching, merch.\nPick what you need below.",
                      "Մենք անում ենք՝ քսերոպատճեն, փաստաթղթերի տպագրություն, սկանավորում, լուսանկարների տպագրություն, լուսանկար փաստաթղթերի համար, պլակատներ և մեծ ֆորմատ, այցեքարտեր/թռուցիկներ/բուկլետներ, կպչուններ և պլոտերային կտրում, լազերային կտրում և փորագրություն, կազմում և լամինացիա, դիզայն և ֆիրմային ոճ, լուսանկարների ռետուշ, մերչ։\nԸնտրեք անհրաժեշտը ներքևում։"),
        "payment": T("Оплата картой. Другие способы и условия предоплаты для больших заказов подтвердит менеджер.", "Card payment is accepted. The manager will confirm other methods and prepayment terms for large orders.",
                     "Վճարումը՝ քարտով։ Այլ եղանակները և խոշոր պատվերների կանխավճարի պայմանները կհաստատի մենեջերը։"),
        "delivery": T("Заказ можно забрать в центре. Доставку и её стоимость подтвердит менеджер: отметьте это в заявке.", "You can pick the order up at the centre. The manager will confirm delivery and its cost: mark it in the request.",
                      "Պատվերը կարելի է վերցնել կենտրոնից։ Առաքումը և դրա արժեքը կհաստատի մենեջերը․ նշեք հայտում։"),
        "minimum": T("Минимальный заказ небольшой: можно напечатать или скопировать даже один лист. Для тиражей цену и условия назовёт менеджер.", "The minimum order is small: you can print or copy even a single sheet. For larger runs the manager will give the price and terms.",
                     "Նվազագույն պատվերը փոքր է․ կարելի է տպել կամ պատճենել նույնիսկ մեկ թերթ։ Տպաքանակների համար գինը և պայմանները կնշի մենեջերը։"),
        "certificate": T("У нас есть подарочные сертификаты. Подробности (номиналы и условия) подскажет менеджер: оставьте вопрос, и мы свяжемся.", "We have gift certificates. The manager will tell you the details (values and terms): leave a question and we will contact you.",
                         "Մենք ունենք նվեր-սերտիֆիկատներ։ Մանրամասները (արժեքներ և պայմաններ) կասի մենեջերը․ թողեք հարց, և մենք կկապվենք։"),
        "human": T("Передам вопрос менеджеру. Напишите его, а затем оставьте имя и телефон, чтобы вам ответили.", "I will pass your question to the manager. Write it, then leave your name and phone so we can reply.",
                   "Հարցը կփոխանցեմ մենեջերին։ Գրեք այն, ապա թողեք անուն և հեռախոս, որպեսզի պատասխանեն։"),
    }
    if intent in A:
        return A[intent][lang]
    return ""
