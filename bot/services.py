# -*- coding: utf-8 -*-
"""The service catalogue of a copy and print centre as data: each service is a list of questions the bot asks before the request goes to staff.
Texts exist in ru / en / hy (the Armenian is a studio draft: have a native speaker proofread it).

Step fields: id, kind (choice | int | text | size | files | files_opt), q (question), opts [(code, label)], label (ru, for staff), optional, when=(step_id, code).
Special step id 'source' (now | later | bring | design) and 'files' follow the rules in flow.py: a file sent first skips both."""


def T(ru, en, hy):
    return {"ru": ru, "en": en, "hy": hy}


def O(code, ru, en, hy):
    return (code, T(ru, en, hy))


# ------------------------------------------------------------------ shared option sets
OTHER = O("other", "Другое", "Other", "Այլ")
FORMAT = [O("a4", "A4", "A4", "A4"), O("a3", "A3", "A3", "A3"), O("a5", "A5", "A5", "A5"), OTHER]
COLOR = [O("bw", "Чёрно-белая", "Black & white", "Սև-սպիտակ"), O("color", "Цветная", "Colour", "Գունավոր")]
SIDES = [O("one", "Односторонняя", "Single-sided", "Միակողմանի"), O("two", "Двусторонняя", "Double-sided", "Երկկողմանի")]
ADVISE = O("advise", "Не знаю, посоветуйте", "Not sure, advise me", "Չգիտեմ, խորհուրդ տվեք")
PAPER = [O("std", "Обычная офисная", "Standard office paper", "Սովորական գրասենյակային թուղթ"),
         O("thick", "Плотная (картон)", "Thick (card stock)", "Խիտ (ստվարաթուղթ)"),
         O("coated", "Мелованная / глянцевая", "Coated / glossy", "Փայլուն / կավճապատ"), ADVISE]
FINISH = [O("none", "Без обработки", "No finishing", "Առանց մշակման"), O("lamination", "Ламинирование", "Lamination", "Լամինացիա"),
          O("varnish", "Лакирование", "Varnishing", "Լաքապատում"), O("emboss", "Тиснение", "Embossing / foil", "Դրոշմում"),
          O("diecut", "Вырубка / высечка", "Die-cutting", "Կտրում (վիրուբկա)"), O("fold", "Фальцовка", "Folding", "Ծալում"), OTHER]
SOURCE_FULL = [O("now", "Пришлю файл сейчас", "I'll send the file now", "Հիմա կուղարկեմ ֆայլը"),
               O("later", "Пришлю позже", "I'll send it later", "Կուղարկեմ ավելի ուշ"),
               O("bring", "Принесу сам(а) (флешка)", "I'll bring it (USB stick)", "Ինքս կբերեմ (ֆլեշ)"),
               O("design", "Нужен дизайн / макет", "I need design / layout", "Պետք է դիզայն / մակետ")]
SOURCE_PRINT = SOURCE_FULL[:3]


def src(opts=None):
    return {"id": "source", "kind": "choice", "label": "Файл", "opts": opts or SOURCE_FULL,
            "q": T("У вас уже есть файл? Пришлите его сюда (фото, PDF, Word, картинка) или выберите вариант ниже.",
                   "Do you have a file? Send it here (photo, PDF, Word, image) or pick an option below.",
                   "Ֆայլ արդեն ունե՞ք։ Ուղարկեք այստեղ (լուսանկար, PDF, Word, նկար) կամ ընտրեք տարբերակը ներքևում։")}


FILES = {"id": "files", "kind": "files", "label": "Файлы", "when": ("source", "now"),
         "q": T("Отправляйте файлы по одному или альбомом. Когда закончите, нажмите «Готово».",
                "Send the files one by one or as an album. When you are done, press “Done”.",
                "Ուղարկեք ֆայլերը մեկ-մեկ կամ ալբոմով։ Ավարտելուց հետո սեղմեք «Պատրաստ է»։")}
DESIGN_TEXT = {"id": "design_text", "kind": "text", "label": "Что должно быть на макете", "when": ("source", "design"), "min": 5,
               "q": T("Опишите, что должно быть на макете: текст, логотип, цвета, пожелания. Можно приложить примеры позже.",
                      "Describe what the layout should contain: text, logo, colours, wishes. You can attach examples later.",
                      "Նկարագրեք՝ ինչ պետք է լինի մակետում․ տեքստ, լոգո, գույներ, ցանկություններ։ Օրինակները կարող եք կցել հետո։")}


def qty(q_ru, q_en, q_hy, sid="qty", label="Количество"):
    return {"id": sid, "kind": "int", "label": label, "q": T(q_ru, q_en, q_hy)}


def choice(sid, label, q, opts, **kw):
    return {"id": sid, "kind": "choice", "label": label, "q": q, "opts": opts, **kw}


Q_FORMAT = T("Какой формат?", "Which format?", "Ո՞ր ֆորմատը։")
Q_COLOR = T("Цветная или чёрно-белая печать?", "Colour or black & white?", "Գունավո՞ր, թե՞ սև-սպիտակ։")
Q_SIDES = T("Печать с одной или с двух сторон?", "Print on one side or both?", "Տպել մե՞կ կողմից, թե՞ երկու։")
Q_PAPER = T("Какая бумага?", "Which paper?", "Ո՞ր թուղթը։")
Q_SIZE = T("Какой нужен размер? (например 50x70 см)", "What size do you need? (for example 50x70 cm)", "Ի՞նչ չափս է պետք (օրինակ՝ 50x70 սմ)։")

# ------------------------------------------------------------------ the services
SERVICES = {
    "copy": {"title": T("Ксерокопия", "Photocopying", "Քսերոպատճեն"), "emoji": "📄", "group": "docs",
             "steps": [qty("Сколько страниц нужно скопировать?", "How many pages do you need copied?", "Քանի՞ էջ է պետք պատճենել։", "pages", "Страниц"),
                       qty("Сколько копий каждой страницы?", "How many copies of each page?", "Յուրաքանչյուր էջից քանի՞ պատճեն։", "copies", "Копий каждой"),
                       choice("format", "Формат", Q_FORMAT, FORMAT), choice("color", "Цвет", Q_COLOR, COLOR), choice("sides", "Стороны", Q_SIDES, SIDES),
                       choice("paper", "Бумага", Q_PAPER, PAPER)],
             "note": T("Оригиналы нужно принести в центр, мы сделаем копии.", "Please bring the originals to the centre and we will make the copies.",
                       "Բնօրինակները պետք է բերել կենտրոն, մենք կպատճենենք։")},
    "print_docs": {"title": T("Печать документов", "Document printing", "Փաստաթղթերի տպագրություն"), "emoji": "🖨", "group": "docs",
                   "steps": [src(SOURCE_PRINT), FILES,
                             qty("Сколько страниц в документе?", "How many pages is the document?", "Քանի՞ էջ է փաստաթուղթը։", "pages", "Страниц"),
                             qty("Сколько комплектов напечатать?", "How many sets to print?", "Քանի՞ հավաքածու տպել։", "copies", "Комплектов"),
                             choice("format", "Формат", Q_FORMAT, FORMAT), choice("color", "Цвет", Q_COLOR, COLOR), choice("sides", "Стороны", Q_SIDES, SIDES),
                             choice("paper", "Бумага", Q_PAPER, PAPER),
                             choice("finishing", "Обработка", T("Нужна обработка после печати?", "Any finishing after printing?", "Տպելուց հետո մշակում պե՞տք է։"),
                                    [O("none", "Не нужна", "No", "Պետք չէ"), O("staple", "Степлер", "Stapling", "Կարիչ"), O("binding", "Переплёт", "Binding", "Կազմում"),
                                     O("lamination", "Ламинирование", "Lamination", "Լամինացիա"), OTHER])]},
    "scan": {"title": T("Сканирование", "Scanning", "Սկանավորում"), "emoji": "🧾", "group": "docs",
             "steps": [qty("Сколько страниц нужно отсканировать?", "How many pages do you need scanned?", "Քանի՞ էջ է պետք սկանավորել։", "pages", "Страниц"),
                       choice("format", "Формат", Q_FORMAT, FORMAT), choice("color", "Цвет", Q_COLOR, COLOR),
                       choice("result", "Куда отправить скан", T("Куда отправить готовый скан?", "Where should we send the scan?", "Ու՞ր ուղարկել սկանը։"),
                              [O("tg", "В Telegram", "To Telegram", "Telegram-ով"), O("email", "На e-mail", "By e-mail", "Էլ. փոստով"),
                               O("usb", "На флешку", "To a USB stick", "Ֆլեշի վրա"), O("print", "Распечатать", "Print it", "Տպել")])],
             "note": T("Оригиналы нужно принести в центр.", "Please bring the originals to the centre.", "Բնօրինակները պետք է բերել կենտրոն։")},
    "photo_print": {"title": T("Печать фото", "Photo printing", "Լուսանկարների տպագրություն"), "emoji": "🖼", "group": "photo",
                    "steps": [src(SOURCE_PRINT), FILES,
                              choice("size", "Размер фото", T("Какой размер фото?", "Which photo size?", "Ո՞ր չափսի լուսանկար։"),
                                     [O("9x13", "9x13", "9x13", "9x13"), O("10x15", "10x15", "10x15", "10x15"), O("13x18", "13x18", "13x18", "13x18"),
                                      O("a5", "A5 (15x21)", "A5 (15x21)", "A5 (15x21)"), O("a4", "A4", "A4", "A4"), OTHER]),
                              qty("Сколько фото напечатать (всего)?", "How many photos to print (in total)?", "Ընդամենը քանի՞ լուսանկար տպել։", "qty", "Фото"),
                              choice("paper", "Бумага", Q_PAPER, [O("gloss", "Глянцевая", "Glossy", "Փայլուն"), O("matte", "Матовая", "Matte", "Մատ"), ADVISE]),
                              choice("retouch", "Обработка", T("Нужна ретушь или обработка?", "Do you need retouching?", "Ռետուշ պե՞տք է։"),
                                     [O("no", "Нет, как есть", "No, as is", "Ոչ, ինչպես կա"), O("yes", "Да, нужна", "Yes", "Այո")])]},
    "passport_photo": {"title": T("Фото на документы", "Passport / ID photos", "Լուսանկար փաստաթղթերի համար"), "emoji": "🪪", "group": "photo",
                       "steps": [choice("doc", "Для какого документа", T("Для какого документа нужно фото?", "What document is the photo for?", "Ո՞ր փաստաթղթի համար է լուսանկարը։"),
                                        [O("passport", "Паспорт РА", "Armenian passport", "ՀՀ անձնագիր"), O("foreign", "Загранпаспорт", "Foreign passport", "Արտասահմանյան անձնագիր"),
                                         O("visa", "Виза", "Visa", "Վիզա"), O("id", "ID-карта", "ID card", "ID քարտ"), OTHER]),
                                 {"id": "doc_text", "kind": "text", "label": "Документ (уточнение)", "when": ("doc", "other"), "min": 2,
                                  "q": T("Напишите, для какого документа и какой страны нужно фото.", "Tell us which document and country the photo is for.", "Գրեք՝ ո՞ր փաստաթղթի և ո՞ր երկրի համար է լուսանկարը։")},
                                 qty("Сколько комплектов фото нужно?", "How many photo sets do you need?", "Քանի՞ հավաքածու լուսանկար է պետք։", "qty", "Комплектов"),
                                 choice("shoot", "Съёмка", T("Фото уже есть или нужно сфотографироваться у нас?", "Do you already have a photo, or do you need to be photographed here?", "Լուսանկար արդեն ունե՞ք, թե՞ պետք է մեզ մոտ լուսանկարվել։"),
                                        [O("shoot", "Сфотографируюсь у вас", "Photograph me there", "Մեզ մոտ կլուսանկարվեմ"), O("file", "Есть фото, пришлю", "I have a photo, will send it", "Լուսանկար ունեմ, կուղարկեմ")]),
                                 {"id": "files", "kind": "files", "label": "Файлы", "when": ("shoot", "file"),
                                  "q": FILES["q"]}],
                       "note": T("Для документов обычно нужна съёмка на месте. Если вы пришлёте готовое фото, сотрудник подскажет, подойдёт ли оно.",
                                 "Documents usually need a shoot on site. If you send a ready photo, the staff will tell you whether it fits.",
                                 "Փաստաթղթերի համար սովորաբար պետք է լուսանկարվել տեղում։ Եթե պատրաստի լուսանկար ուղարկեք, աշխատակիցը կասի՝ հարմար է արդյոք։")},
    "large_format": {"title": T("Плакаты и большой формат", "Posters and large format", "Պլակատներ և մեծ ֆորմատ"), "emoji": "🗺", "group": "print",
                     "steps": [src(), FILES, DESIGN_TEXT,
                               {"id": "size", "kind": "size", "label": "Размер", "q": Q_SIZE},
                               choice("material", "Материал", T("На чём печатать?", "What should it be printed on?", "Ինչի՞ վրա տպել։"),
                                      [O("paper", "Бумага", "Paper", "Թուղթ"), O("photo", "Фотобумага", "Photo paper", "Լուսանկարչական թուղթ"), O("banner", "Баннер", "Banner", "Բաններ"),
                                       O("film", "Самоклеящаяся плёнка", "Self-adhesive film", "Ինքնակպչուն թաղանթ"), O("canvas", "Холст", "Canvas", "Կտավ"), ADVISE]),
                               qty("Сколько штук?", "How many pieces?", "Քանի՞ հատ։"),
                               choice("finishing", "Обработка", T("Нужна обработка?", "Any finishing?", "Մշակում պե՞տք է։"),
                                      [O("none", "Не нужна", "No", "Պետք չէ"), O("lamination", "Ламинирование", "Lamination", "Լամինացիա"), O("mount", "Накатка на основу", "Mounting on board", "Հիմքին փակցնել"), OTHER])]},
    "cards_flyers": {"title": T("Визитки, листовки, буклеты", "Business cards, flyers, booklets", "Այցեքարտեր, թռուցիկներ, բուկլետներ"), "emoji": "📇", "group": "print",
                     "steps": [choice("product", "Изделие", T("Что нужно напечатать?", "What do you need printed?", "Ի՞նչ է պետք տպել։"),
                                      [O("cards", "Визитки", "Business cards", "Այցեքարտեր"), O("flyers", "Листовки / флаеры", "Flyers / leaflets", "Թռուցիկներ"),
                                       O("booklet", "Буклеты / брошюры", "Booklets / brochures", "Բուկլետներ / բրոշյուրներ"), O("cert", "Сертификаты / карты клиента", "Certificates / loyalty cards", "Սերտիֆիկատներ / քարտեր"),
                                       O("calendar", "Календари / открытки", "Calendars / postcards", "Օրացույցներ / բացիկներ"), OTHER]),
                               src(), FILES, DESIGN_TEXT,
                               qty("Какой тираж (сколько штук)?", "What quantity (how many pieces)?", "Ի՞նչ տպաքանակ (քանի՞ հատ)։", "qty", "Тираж"),
                               {"id": "size", "kind": "text", "label": "Размер", "min": 2, "skip": O("unknown", "Не знаю, подскажите", "Not sure, advise me", "Չգիտեմ, խորհուրդ տվեք"),
                                "q": T("Какой размер? (например 90x50 мм или A5). Если не знаете, нажмите кнопку.", "What size? (for example 90x50 mm or A5). If you are not sure, press the button.",
                                       "Ի՞նչ չափս (օրինակ՝ 90x50 մմ կամ A5)։ Եթե չգիտեք, սեղմեք կոճակը։")},
                               choice("sides", "Стороны", T("Печать с одной или с двух сторон?", "One side or both?", "Տպել մե՞կ կողմից, թե՞ երկու։"), SIDES),
                               choice("paper", "Бумага", Q_PAPER, PAPER),
                               choice("finishing", "Обработка", T("Нужна доработка?", "Any finishing?", "Լրացուցիչ մշակում պե՞տք է։"), FINISH)]},
    "stickers": {"title": T("Наклейки и плоттерная резка", "Stickers and plotter cutting", "Կպչուններ և պլոտերային կտրում"), "emoji": "✂️", "group": "print",
                 "steps": [choice("product", "Изделие", T("Что нужно?", "What do you need?", "Ի՞նչ է պետք։"),
                                  [O("stickers", "Наклейки", "Stickers", "Կպչուններ"), O("cut", "Плоттерная резка", "Plotter cutting", "Պլոտերային կտրում"), OTHER]),
                           src(), FILES, DESIGN_TEXT,
                           {"id": "size", "kind": "size", "label": "Размер", "q": Q_SIZE},
                           qty("Сколько штук?", "How many pieces?", "Քանի՞ հատ։"),
                           choice("material", "Материал", T("Какой материал?", "Which material?", "Ո՞ր նյութը։"),
                                  [O("paper", "Бумага", "Paper", "Թուղթ"), O("vinyl", "Винил", "Vinyl", "Վինիլ"), O("clear", "Прозрачная плёнка", "Clear film", "Թափանցիկ թաղանթ"), ADVISE])]},
    "laser": {"title": T("Лазерная резка и гравировка", "Laser cutting and engraving", "Լազերային կտրում և փորագրություն"), "emoji": "🔦", "group": "print",
              "steps": [choice("operation", "Операция", T("Что нужно сделать?", "What do you need?", "Ի՞նչ է պետք անել։"),
                               [O("cut", "Резка", "Cutting", "Կտրում"), O("engrave", "Гравировка", "Engraving", "Փորագրություն"), O("both", "Резка и гравировка", "Cutting and engraving", "Կտրում և փորագրություն")]),
                        choice("material", "Материал", T("Из какого материала?", "Which material?", "Ո՞ր նյութից։"),
                               [O("wood", "Дерево / фанера", "Wood / plywood", "Փայտ / ֆաներա"), O("acrylic", "Акрил", "Acrylic", "Ակրիլ"), O("leather", "Кожа", "Leather", "Կաշի"),
                                O("card", "Картон", "Cardboard", "Ստվարաթուղթ"), OTHER]),
                        src(), FILES, DESIGN_TEXT,
                        {"id": "size", "kind": "size", "label": "Размер изделия", "q": T("Какой размер изделия? (например 10x10 см)", "What size is the item? (for example 10x10 cm)", "Ի՞նչ չափսի իր է (օրինակ՝ 10x10 սմ)։")},
                        qty("Сколько штук?", "How many pieces?", "Քանի՞ հատ։")]},
    "postpress": {"title": T("Переплёт, ламинирование, обработка", "Binding, lamination, finishing", "Կազմում, լամինացիա, մշակում"), "emoji": "📎", "group": "docs",
                  "steps": [choice("op", "Операция", T("Что нужно сделать?", "What do you need?", "Ի՞նչ է պետք անել։"),
                                   [O("spring", "Переплёт на пружину", "Spiral binding", "Զսպանակով կազմում"), O("thermo", "Термопереплёт", "Thermal binding", "Ջերմային կազմում"),
                                    O("lamination", "Ламинирование", "Lamination", "Լամինացիա"), O("fold", "Фальцовка", "Folding", "Ծալում"), O("drill", "Сверление отверстий", "Hole drilling", "Անցքերի հորատում"),
                                    O("emboss", "Тиснение", "Embossing / foil", "Դրոշմում"), O("diecut", "Вырубка", "Die-cutting", "Կտրում"), O("varnish", "Лакирование", "Varnishing", "Լաքապատում"), OTHER]),
                            qty("Сколько штук или листов?", "How many items or sheets?", "Քանի՞ հատ կամ թերթ։"),
                            choice("format", "Формат", Q_FORMAT, FORMAT),
                            choice("source", "Материал", T("Что обрабатываем?", "What are we processing?", "Ի՞նչ ենք մշակում։"),
                                   [O("bring", "Принесу свои листы", "I'll bring my sheets", "Կբերեմ իմ թերթերը"), O("print", "Нужно ещё и напечатать", "It also needs printing", "Նաև տպել է պետք")])]},
    "design": {"title": T("Дизайн и фирменный стиль", "Design and branding", "Դիզայն և ֆիրմային ոճ"), "emoji": "🎨", "group": "design",
               "steps": [choice("what", "Что нужно", T("Что нужно разработать?", "What do you need designed?", "Ի՞նչ է պետք մշակել։"),
                                [O("logo", "Логотип", "Logo", "Լոգո"), O("brand", "Фирменный стиль", "Brand identity", "Ֆիրմային ոճ"), O("cards", "Визитки / бланки", "Business cards / stationery", "Այցեքարտեր / բլանկներ"),
                                 O("flyer", "Листовка / плакат / буклет", "Flyer / poster / booklet", "Թռուցիկ / պլակատ / բուկլետ"), O("social", "Макеты для соцсетей", "Social media layouts", "Մակետներ սոցցանցերի համար"), OTHER]),
                         {"id": "about", "kind": "text", "label": "О бизнесе и задаче", "min": 10,
                          "q": T("Расскажите коротко о бизнесе и о задаче: чем занимаетесь, для кого нужен дизайн.", "Briefly tell us about your business and the task: what you do and who the design is for.",
                                 "Կարճ պատմեք բիզնեսի և խնդրի մասին․ ինչով եք զբաղվում, ում համար է դիզայնը։")},
                         {"id": "refs", "kind": "text", "label": "Примеры / пожелания", "min": 2, "skip": O("none", "Пропустить", "Skip", "Բաց թողնել"),
                          "q": T("Есть примеры, которые нравятся, или пожелания по цветам и стилю? Напишите или пропустите.", "Any examples you like, or wishes about colours and style? Write them or skip.",
                                 "Կա՞ն օրինակներ, որոնք դուր են գալիս, կամ ցանկություններ գույների և ոճի վերաբերյալ։ Գրեք կամ բաց թողեք։")},
                         {"id": "files", "kind": "files_opt", "label": "Файлы", "q": T("Если есть логотип, фото или примеры, пришлите их (по желанию). Потом нажмите «Готово».", "If you have a logo, photos or examples, send them (optional), then press “Done”.",
                                                                                  "Եթե ունեք լոգո, լուսանկարներ կամ օրինակներ, ուղարկեք (ըստ ցանկության), ապա սեղմեք «Պատրաստ է»։")}]},
    "retouch": {"title": T("Ретушь и обработка фото", "Photo retouching", "Լուսանկարների ռետուշ"), "emoji": "✨", "group": "photo",
                "steps": [{"id": "files", "kind": "files", "label": "Файлы", "q": T("Пришлите фото, которые нужно обработать. Потом нажмите «Готово».", "Send the photos to retouch, then press “Done”.", "Ուղարկեք մշակման ենթակա լուսանկարները, ապա սեղմեք «Պատրաստ է»։")},
                          {"id": "what", "kind": "text", "label": "Что исправить", "min": 5, "q": T("Что нужно исправить или сделать? (убрать фон, ретушь лица, цвет, реставрация старого фото...)", "What should be done? (remove background, face retouch, colour, restoring an old photo...)", "Ի՞նչ է պետք անել (ֆոնի հեռացում, դեմքի ռետուշ, գույն, հին լուսանկարի վերականգնում...)։")},
                          qty("Сколько фото?", "How many photos?", "Քանի՞ լուսանկար։"),
                          choice("print", "Печать", T("Нужно ли потом напечатать?", "Do you need prints afterwards?", "Հետո տպե՞լ է պետք։"), [O("yes", "Да", "Yes", "Այո"), O("no", "Нет, только файл", "No, file only", "Ոչ, միայն ֆայլ")])]},
    "merch": {"title": T("Мерч и сувениры", "Merch and souvenirs", "Մերչ և հուշանվերներ"), "emoji": "🎁", "group": "print",
              "steps": [{"id": "what", "kind": "text", "label": "Что нужно", "min": 3, "q": T("Что нужно: футболки, кружки, значки, пакеты...? Напишите.", "What do you need: T-shirts, mugs, badges, bags...? Write it down.", "Ի՞նչ է պետք․ շապիկներ, բաժակներ, նշաններ, տոպրակներ...։ Գրեք։")},
                        qty("Какой тираж (сколько штук)?", "What quantity (how many pieces)?", "Ի՞նչ տպաքանակ (քանի՞ հատ)։", "qty", "Тираж"), src(), FILES, DESIGN_TEXT]},
    "other": {"title": T("Другое", "Something else", "Այլ"), "emoji": "💬", "group": "other",
              "steps": [{"id": "what", "kind": "text", "label": "Что нужно", "min": 5, "q": T("Опишите, что нужно сделать.", "Describe what you need.", "Նկարագրեք՝ ինչ է պետք անել։")},
                        {"id": "files", "kind": "files_opt", "label": "Файлы", "q": T("Если есть файлы или фото, пришлите их (по желанию), затем нажмите «Готово».", "If you have files or photos, send them (optional), then press “Done”.", "Եթե ունեք ֆայլեր կամ լուսանկարներ, ուղարկեք (ըստ ցանկության), ապա սեղմեք «Պատրաստ է»։")}]},
}

# a question for the manager (the bot cannot answer it): the question itself + the way to reach the client
SERVICES["question"] = {"title": T("Вопрос менеджеру", "Question for the manager", "Հարց մենեջերին"), "emoji": "❓", "group": "hidden", "tail": False,
                        "steps": [{"id": "what", "kind": "text", "label": "Вопрос", "min": 5,
                                   "q": T("Напишите ваш вопрос.", "Write your question.", "Գրեք ձեր հարցը։")}]}

GROUPS = [("docs", T("Документы и копии", "Documents and copies", "Փաստաթղթեր և պատճեններ")), ("photo", T("Фото", "Photo", "Լուսանկար")),
          ("print", T("Полиграфия и печать", "Printing", "Տպագրություն")), ("design", T("Дизайн", "Design", "Դիզայն")), ("other", T("Другое", "Other", "Այլ"))]

# ------------------------------------------------------------------ the common ending of every request
TAIL = [
    choice("deadline", "Срок", T("К какому сроку нужно?", "When do you need it?", "Ե՞րբ է պետք։"),
           [O("today", "Сегодня", "Today", "Այսօր"), O("tomorrow", "Завтра", "Tomorrow", "Վաղը"), O("week", "В течение недели", "Within a week", "Շաբաթվա ընթացքում"),
            O("free", "Не срочно", "Not urgent", "Շտապ չէ"), O("date", "Указать дату", "A specific date", "Նշել ամսաթիվ")]),
    {"id": "deadline_text", "kind": "text", "label": "Срок (дата)", "when": ("deadline", "date"), "min": 3,
     "q": T("Напишите дату или время, к которому нужно.", "Write the date or time you need it by.", "Գրեք ամսաթիվը կամ ժամը, երբ է պետք։")},
    choice("fulfil", "Получение", T("Как получите заказ?", "How will you get the order?", "Ինչպե՞ս եք ստանալու պատվերը։"),
           [O("pickup", "Заберу в центре (Маштоца, 42)", "I'll pick it up (42 Mashtots Ave.)", "Կվերցնեմ կենտրոնից (Մաշտոցի 42)"), O("delivery", "Нужна доставка", "I need delivery", "Առաքում է պետք")]),
    {"id": "address", "kind": "address", "label": "Адрес доставки", "when": ("fulfil", "delivery"),
     "q": T("Напишите адрес доставки (улица, дом, подъезд). Стоимость и возможность доставки подтвердит менеджер.", "Write the delivery address (street, building, entrance). The manager will confirm cost and availability.",
            "Գրեք առաքման հասցեն (փողոց, շենք, մուտք)։ Արժեքը և հնարավորությունը կհաստատի մենեջերը։")},
    {"id": "name", "kind": "name", "label": "Имя", "q": T("Как к вам обращаться? (имя)", "What is your name?", "Ինչպե՞ս դիմել ձեզ (անուն)։")},
    {"id": "phone", "kind": "phone", "label": "Телефон", "q": T("Ваш номер телефона, чтобы менеджер связался с вами. Например: +374 99 123456", "Your phone number so the manager can reach you. For example: +374 99 123456",
                                                               "Ձեր հեռախոսահամարը, որպեսզի մենեջերը կապվի ձեզ հետ։ Օրինակ՝ +374 99 123456")},
    choice("via", "Связь", T("Как удобнее связаться?", "How should we contact you?", "Ինչպե՞ս է հարմար կապ հաստատել։"),
           [O("tg", "Написать в Telegram", "Message on Telegram", "Գրել Telegram-ով"), O("wa", "WhatsApp", "WhatsApp", "WhatsApp"), O("call", "Позвонить", "Call me", "Զանգահարել")]),
    {"id": "comment", "kind": "text", "label": "Комментарий", "min": 2, "skip": O("none", "Без комментария", "No comment", "Առանց մեկնաբանության"),
     "q": T("Есть ещё что-то важное? Напишите комментарий или пропустите.", "Anything else important? Write a comment or skip.", "Կա՞ ևս ինչ-որ կարևոր բան։ Գրեք մեկնաբանություն կամ բաց թողեք։")},
]


def label_of(opts, code, lang="ru"):
    for c, lab in opts:
        if c == code:
            return lab[lang]
    return code


CONTACT_TAIL = [t for t in TAIL if t["id"] in ("name", "phone", "via")]


def steps_for(service_key):
    svc = SERVICES[service_key]
    if svc.get("tail") is False:
        return svc["steps"] + CONTACT_TAIL
    return svc["steps"] + TAIL
