// Design Factory website: one page, three languages (hy / ru / en). The services come from data/services.json (exported from the bot,
// so the site and the bot always list the same services and questions). Every "order" button opens the Telegram bot on that service.
const CONFIG = {
  bot: 'designfactorytest_bot',               // TEST bot; when the final bot is created in @BotFather, change the username here
  wa: '37495054044', phone: '+374 95 054044',
  map: 'https://yandex.com/maps/org/dizayn_fektyri/14146943060/',
};
const LANGS = ['hy', 'ru', 'en'], LABEL = { hy: 'ՀԱՅ', ru: 'РУС', en: 'ENG' };
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const S = {
  nav: { ru: ['Услуги', 'Как это работает', 'Вопросы', 'Контакты'], en: ['Services', 'How it works', 'FAQ', 'Contacts'], hy: ['Ծառայություններ', 'Ինչպես է աշխատում', 'Հարցեր', 'Կապ'] },
  cta: { ru: 'Заказать в Telegram', en: 'Order on Telegram', hy: 'Պատվիրել Telegram-ով' }, wa: { ru: 'Написать в WhatsApp', en: 'Write on WhatsApp', hy: 'Գրել WhatsApp-ով' },
  eyebrow: { ru: 'Копицентр и типография · Ереван, Маштоца 42', en: 'Copy centre and print shop · 42 Mashtots Ave., Yerevan', hy: 'Կրկնօրինակման կենտրոն և տպարան · Երևան, Մաշտոցի 42' },
  h1: { ru: 'Печать и дизайн<br>за один визит', en: 'Printing and design<br>in a single visit', hy: 'Տպագրություն և դիզայն<br>մեկ այցով' },
  lead: { ru: 'Пришлите файл или фото в Telegram: бот задаст нужные вопросы, а менеджер сразу назовёт цену и срок. Не нужно ничего объяснять по десять раз.', en: 'Send a file or a photo on Telegram: the bot asks the questions we need and the manager quotes the price and timing right away. No need to explain things ten times.', hy: 'Ուղարկեք ֆայլ կամ լուսանկար Telegram-ով․ բոտը կտա անհրաժեշտ հարցերը, իսկ մենեջերը անմիջապես կնշի գինը և ժամկետը։ Պետք չէ տասն անգամ բացատրել։' },
  facts: { ru: ['★ 5,0 на Яндекс Картах (75 оценок)', 'Можно заказать даже один лист', 'Ксерокс, печать, фото на документы, дизайн'], en: ['★ 5.0 on Yandex Maps (75 ratings)', 'Even a single sheet is fine', 'Copying, printing, ID photos, design'], hy: ['★ 5,0 Yandex Maps-ում (75 գնահատական)', 'Կարելի է պատվիրել նույնիսկ մեկ թերթ', 'Քսերոպատճեն, տպագրություն, լուսանկար փաստաթղթերի համար, դիզայն'] },
  chat1: { ru: '[фото] Сколько стоит распечатать?', en: '[photo] How much to print this?', hy: '[լուսանկար] Ինչքա՞ն արժե տպել' },
  chat2: { ru: 'Какой формат и сколько штук?', en: 'Which format and how many?', hy: 'Ի՞նչ ֆորմատ և քանի՞ հատ' },
  chat3: { ru: 'Передал менеджеру: цену и срок напишем сразу ✅', en: 'Passed to the manager: price and timing coming right up ✅', hy: 'Փոխանցվեց մենեջերին․ գինը և ժամկետը շուտով կգրենք ✅' },
  servicesH: { ru: 'Что мы делаем', en: 'What we do', hy: 'Ինչ ենք անում' },
  servicesP: { ru: 'Нажмите на услугу: бот откроется на нужных вопросах (формат, цвет, бумага, тираж). Цену называет менеджер после заявки.', en: 'Tap a service: the bot opens on the right questions (format, colour, paper, quantity). The manager gives the price after your request.', hy: 'Սեղմեք ծառայության վրա․ բոտը կբացվի համապատասխան հարցերով (ֆորմատ, գույն, թուղթ, տպաքանակ)։ Գինը նշում է մենեջերը հայտից հետո։' },
  asks: { ru: 'Бот уточнит:', en: 'The bot will ask:', hy: 'Բոտը կճշտի․' }, order: { ru: 'Заказать', en: 'Order', hy: 'Պատվիրել' },
  howH: { ru: 'Как это работает', en: 'How it works', hy: 'Ինչպես է աշխատում' },
  steps: { ru: [['Пришлите файл или напишите', 'В Telegram: фото, PDF, Word или просто словами, что нужно. Бот поймёт, о какой услуге речь.'], ['Ответьте на несколько вопросов', 'Формат, цвет, бумага, размер, тираж, срок. Это занимает около минуты, кнопками.'], ['Менеджер называет цену и срок', 'Заявка уходит сотрудникам, когда всё заполнено. Вам отвечают с точной стоимостью.'], ['Заберите заказ', 'В центре на Маштоца, 42 (подъезд 1). Бот напишет, когда заказ готов.']],
          en: [['Send a file or write', 'On Telegram: a photo, PDF, Word or simply words. The bot works out which service you mean.'], ['Answer a few questions', 'Format, colour, paper, size, quantity, deadline. It takes about a minute, with buttons.'], ['The manager quotes price and timing', 'The request reaches the staff only when everything is filled in. You get an exact price.'], ['Pick up your order', 'At the centre at 42 Mashtots Ave. (entrance 1). The bot messages you when it is ready.']],
          hy: [['Ուղարկեք ֆայլ կամ գրեք', 'Telegram-ով․ լուսանկար, PDF, Word կամ պարզապես բառերով։ Բոտը կհասկանա, թե որ ծառայության մասին է խոսքը։'], ['Պատասխանեք մի քանի հարցի', 'Ֆորմատ, գույն, թուղթ, չափս, տպաքանակ, ժամկետ։ Տևում է մոտ մեկ րոպե, կոճակներով։'], ['Մենեջերը նշում է գինը և ժամկետը', 'Հայտը հասնում է աշխատակիցներին միայն այն ժամանակ, երբ ամեն ինչ լրացված է։ Ձեզ պատասխանում են ճշգրիտ գնով։'], ['Վերցրեք պատվերը', 'Մաշտոցի 42 կենտրոնում (մուտք 1)։ Պատրաստ լինելիս բոտը կգրի ձեզ։']] },
  faqH: { ru: 'Частые вопросы', en: 'Frequently asked questions', hy: 'Հաճախ տրվող հարցեր' },
  faqQ: { price: { ru: 'Сколько стоит?', en: 'How much does it cost?', hy: 'Ինչքա՞ն արժե' }, timing: { ru: 'Как быстро делаете?', en: 'How fast are you?', hy: 'Որքա՞ն արագ եք անում' }, files: { ru: 'Как прислать файл и в каком формате?', en: 'How do I send a file and in which format?', hy: 'Ինչպե՞ս ուղարկել ֆայլ և ի՞նչ ձևաչափով' },
          payment: { ru: 'Как оплатить?', en: 'How do I pay?', hy: 'Ինչպե՞ս վճարել' }, delivery: { ru: 'Есть доставка?', en: 'Do you deliver?', hy: 'Առաքում կա՞' }, minimum: { ru: 'Есть минимальный заказ?', en: 'Is there a minimum order?', hy: 'Նվազագույն պատվեր կա՞' } },
  contH: { ru: 'Как нас найти', en: 'Find us', hy: 'Ինչպես գտնել մեզ' },
  addr: { ru: 'Ереван, просп. Маштоца, 42, подъезд 1', en: '42 Mashtots Ave., entrance 1, Yerevan', hy: 'Երևան, Մաշտոցի պող. 42, մուտք 1' },
  hours: { ru: 'Работаем до 19:00', en: 'Open until 19:00', hy: 'Աշխատում ենք մինչև 19:00' },
  route: { ru: 'Маршрут на Яндекс Картах', en: 'Directions on Yandex Maps', hy: 'Երթուղի Yandex Maps-ում' },
  footL: { ru: 'Демонстрационный макет сайта для «Дизайн Фектори», Ереван', en: 'Demonstration mock-up of the Design Factory website, Yerevan', hy: 'Ցուցադրական մակետ «Դիզայն Ֆեքթորի» կայքի համար, Երևան' },
  footR: { ru: 'Сайт и бот: Afonin Web Studio', en: 'Website and bot: Afonin Web Studio', hy: 'Կայք և բոտ․ Afonin Web Studio' },
};

let lang = (() => { try { const l = localStorage.getItem('df-lang'); if (LANGS.includes(l)) return l; } catch { /* ignore */ } const n = (navigator.language || 'ru').slice(0, 2); return LANGS.includes(n) ? n : 'ru'; })();
let data;
const t = (k) => S[k][lang];
const tg = (start) => `https://t.me/${CONFIG.bot}${start ? '?start=' + start : ''}`;
const waLink = () => `https://wa.me/${CONFIG.wa}?text=${encodeURIComponent({ ru: 'Здравствуйте! Хочу узнать цену на печать.', en: 'Hello! I would like a price for printing.', hy: 'Բարև ձեզ։ Ցանկանում եմ իմանալ տպագրության գինը։' }[lang])}`;
const COLORS = ['c', 'm', 'y', 'k'];

function render() {
  document.documentElement.lang = lang;
  document.title = { ru: 'Дизайн Фектори — печать и дизайн в центре Еревана', en: 'Design Factory — printing and design in central Yerevan', hy: 'Դիզայն Ֆեքթորի — տպագրություն և դիզայն Երևանի կենտրոնում' }[lang];
  const ids = ['#nav a'];
  $('#nav').innerHTML = [['#services', 0], ['#how', 1], ['#faq', 2], ['#contacts', 3]].map(([h, i]) => `<a href="${h}">${t('nav')[i]}</a>`).join('');
  $('#lang').innerHTML = LANGS.map((l) => `<button data-lang="${l}" class="${l === lang ? 'on' : ''}">${LABEL[l]}</button>`).join('');
  for (const id of ['ctaTop', 'ctaTg', 'ctaTg2']) { const el = $('#' + id); el.textContent = t('cta'); el.href = tg('site'); }
  $('#floatCta').textContent = t('cta'); $('#floatCta').href = tg('site');
  $('#ctaWa').textContent = t('wa'); $('#ctaWa').href = waLink();
  $('#heroEyebrow').textContent = t('eyebrow'); $('#heroH1').innerHTML = t('h1'); $('#heroLead').textContent = t('lead');
  $('#facts').innerHTML = t('facts').map((f) => `<li>${esc(f)}</li>`).join('');
  $('#chat1').textContent = t('chat1'); $('#chat2').textContent = t('chat2'); $('#chat3').textContent = t('chat3');
  $('#servicesH').textContent = t('servicesH'); $('#servicesP').textContent = t('servicesP');
  $('#servicesGrid').innerHTML = data.services.map((s, i) => `<article class="card ${COLORS[i % 4]}"><div class="ico">${s.emoji}</div><h3>${esc(s.title[lang])}</h3>
    <p class="asks"><b>${t('asks')}</b> ${s.asks.map((a) => esc(a[lang].toLowerCase())).join(', ')}</p><a class="btn sm" href="${tg('svc_' + s.key)}" target="_blank" rel="noopener">${t('order')}</a></article>`).join('');
  $('#howH').textContent = t('howH');
  $('#steps').innerHTML = t('steps').map(([h, p], i) => `<li><b class="n">${i + 1}</b><h3>${esc(h)}</h3><p>${esc(p)}</p></li>`).join('');
  $('#faqH').textContent = t('faqH');
  $('#faqList').innerHTML = Object.keys(S.faqQ).map((k, i) => `<details class="qa" ${i === 0 ? 'open' : ''}><summary>${esc(S.faqQ[k][lang])}</summary><p>${esc(data.faq[k][lang]).replace(/\n/g, '<br>')}</p></details>`).join('');
  $('#contH').textContent = t('contH');
  $('#contBody').innerHTML = `<p class="addr">${esc(t('addr'))}</p><p>${esc(t('hours'))}</p><p><a href="tel:${CONFIG.phone.replace(/\s/g, '')}">${CONFIG.phone}</a></p>
    <p class="rate"><b>★ 5,0</b> <span>${{ ru: '75 оценок на Яндекс Картах', en: '75 ratings on Yandex Maps', hy: '75 գնահատական Yandex Maps-ում' }[lang]}</span></p>
    <div class="cta"><a class="btn" href="${tg('site')}" target="_blank" rel="noopener">${t('cta')}</a><a class="btn ghost" href="${CONFIG.map}" target="_blank" rel="noopener">${t('route')}</a></div>`;
  $('#footL').textContent = t('footL'); $('#footR').textContent = t('footR');
}

document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-lang]');
  if (b) { lang = b.dataset.lang; try { localStorage.setItem('df-lang', lang); } catch { /* ignore */ } render(); }
  if (e.target.closest('#burger')) document.body.classList.toggle('menu');
  if (e.target.closest('#nav a')) document.body.classList.remove('menu');
});
addEventListener('scroll', () => $('#top').classList.toggle('solid', scrollY > 8), { passive: true });
fetch('data/services.json').then((r) => r.json()).then((d) => { data = d; render(); });
