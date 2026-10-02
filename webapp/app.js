/* DELTA Mini App — без сборки и библиотек. Работает в Telegram и в Safari (вход по ссылке /web из бота). */
(() => {
  'use strict';
  const tg = window.Telegram && window.Telegram.WebApp;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const NB = ' ';
  const $ = (s, r = document) => r.querySelector(s);

  // ---------------------------------------------------------------- иконки
  const ICONS = {
    coffee: '<path d="M4 9h12v4.5A5.5 5.5 0 0 1 10.5 19h-1A5.5 5.5 0 0 1 4 13.5z"/><path d="M16 10.5h1.5a2.5 2.5 0 0 1 0 5H16"/><path d="M8 3.5v2.5M12 3.5v2.5"/>',
    car: '<path d="M4 15l1.6-5A2 2 0 0 1 7.5 8.6h9a2 2 0 0 1 1.9 1.4L20 15v3H4z"/><path d="M4 15h16"/><circle cx="8" cy="18.5" r="1.4"/><circle cx="16" cy="18.5" r="1.4"/>',
    bag: '<path d="M5.5 8h13l-1 12h-11z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>',
    home: '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-5h4v5"/>',
    star: '<path d="M12 4l2.4 4.9 5.4.8-3.9 3.8.9 5.4L12 16.4l-4.8 2.5.9-5.4-3.9-3.8 5.4-.8z"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    repeat: '<path d="M17 3l3 3-3 3"/><path d="M4 12v-2a4 4 0 0 1 4-4h12"/><path d="M7 21l-3-3 3-3"/><path d="M20 12v2a4 4 0 0 1-4 4H4"/>',
    dots: '<circle cx="6" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="18" cy="12" r="1.3"/>',
    briefcase: '<path d="M4 8h16v11H4z"/><path d="M9 8V6a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/><path d="M4 13h16"/>',
    laptop: '<path d="M5.5 6h13v9h-13z"/><path d="M3 18.5h18"/>',
    gift: '<path d="M4 10h16v4H4z"/><path d="M6 14v6h12v-6"/><path d="M12 10v10"/><path d="M12 10c-1.5-3.5-6-4-6-1.5 0 1.2 1.6 1.5 6 1.5zm0 0c1.5-3.5 6-4 6-1.5 0 1.2-1.6 1.5-6 1.5z"/>',
    percent: '<path d="M18.5 5.5l-13 13"/><circle cx="7.5" cy="7.5" r="2.3"/><circle cx="16.5" cy="16.5" r="2.3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    swap: '<path d="M5 8h13l-3.5-3.5"/><path d="M19 16H6l3.5 3.5"/>',
    chart: '<path d="M5 20v-8M12 20V5M19 20v-5"/>',
    globe: '<circle cx="12" cy="12" r="8"/><path d="M4 12h16"/><path d="M12 4c2.6 2.6 2.6 13.4 0 16M12 4c-2.6 2.6-2.6 13.4 0 16"/>',
    eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
    back: '<path d="M8.5 5H20v14H8.5L3 12z"/><path d="M11.5 9.5l5 5M16.5 9.5l-5 5"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    up2: '<path d="M12 19V5M6 11l6-6 6 6"/>',
    down2: '<path d="M12 5v14M6 13l6 6 6-6"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    more: '<circle cx="5" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="19" cy="12" r="1.2"/>',
    spark: '<path d="M12 3l1.8 5.4L19 10l-5.2 1.6L12 17l-1.8-5.4L5 10l5.2-1.6z"/>',
    trash: '<path d="M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    pen: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
    phone: '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 18h2"/>',
  };
  function icon(name, size = 22, color = 'currentColor', sw = 1.8) {
    return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex-shrink:0">${ICONS[name] || ICONS.dots}</svg>`;
  }

  // ---------------------------------------------------------------- форматирование
  const SYM = { RUB: '₽', USD: '$', EUR: '€', CNY: '¥', USDT: '₮', BTC: '₿', AED: 'AED' };
  const CURS = ['RUB', 'USD', 'EUR', 'CNY', 'USDT', 'BTC'];
  const fmt = (n, d = 0) => new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: d }).format(n);
  const fmt2 = (n) => new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
  const signed = (s, n) => (n < 0 ? '−' : '') + s;
  const money = (n, c = 'RUB') => signed(fmt(Math.abs(n), c === 'BTC' ? 8 : 2), n) + NB + (SYM[c] || c);
  const rub = (n) => signed(fmt(Math.abs(Math.round(n))), Math.round(n)) + NB + '₽';
  const int = (n) => signed(fmt(Math.abs(Math.round(n))), Math.round(n));
  const short = (n) => (n >= 1e6 ? fmt(n / 1e6, 1) + 'М' : n >= 1e4 ? fmt(Math.round(n / 1e3)) + 'К' : fmt(Math.round(n)));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const LIGHT_CAT = { food: '#B86200', transport: '#0272B0', shop: '#C21F6A', home: '#6D35D9', fun: '#C2410C', health: '#047857',
    subs: '#1D4ED8', other: '#5B6170', salary: '#0B8A63', freelance: '#0272B0', gift: '#C21F6A', cashback: '#B86200', other_inc: '#5B6170' };
  const HOLO = { tb: 'var(--holo-tb)', cash: 'var(--holo-cash)', usdt: 'var(--holo-usdt)' };
  let theme = 'dark';
  const catColor = (c) => (theme === 'light' ? LIGHT_CAT[c.key] || c.color : c.color);
  const haptic = (kind) => { try { if (kind === 'ok') tg.HapticFeedback.notificationOccurred('success'); else tg.HapticFeedback.impactOccurred(kind || 'light'); } catch (e) { /* нет Telegram */ } };

  // ---------------------------------------------------------------- графики
  function monotone(pts) {
    const n = pts.length;
    if (n < 2) return n ? `M${pts[0][0]},${pts[0][1]}` : '';
    const dx = [], m = [], t = new Array(n).fill(0);
    for (let i = 0; i < n - 1; i++) { dx.push(pts[i + 1][0] - pts[i][0]); m.push(dx[i] ? (pts[i + 1][1] - pts[i][1]) / dx[i] : 0); }
    t[0] = m[0]; t[n - 1] = m[n - 2];
    for (let i = 1; i < n - 1; i++) {
      const s0 = m[i - 1], s1 = m[i], h0 = dx[i - 1], h1 = dx[i];
      if (s0 * s1 <= 0) t[i] = 0;
      else { const p = (s0 * h1 + s1 * h0) / (h0 + h1); t[i] = Math.sign(s0) * Math.min(Math.abs(s0), Math.abs(s1), 0.5 * Math.abs(p)) * 2; }
    }
    let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
    for (let i = 0; i < n - 1; i++) {
      const h = dx[i];
      d += ` C${(pts[i][0] + h / 3).toFixed(1)},${(pts[i][1] + t[i] * h / 3).toFixed(1)} ${(pts[i + 1][0] - h / 3).toFixed(1)},${(pts[i + 1][1] - t[i + 1] * h / 3).toFixed(1)} ${pts[i + 1][0].toFixed(1)},${pts[i + 1][1].toFixed(1)}`;
    }
    return d;
  }
  function scaleSeries(vals, W, H, pt = 12, pb = 10) {
    let lo = Math.min(...vals), hi = Math.max(...vals);
    const span = hi - lo || Math.max(1, Math.abs(hi) * 0.1);
    lo -= span * 0.12; hi += span * 0.12;
    const step = vals.length > 1 ? W / (vals.length - 1) : W;
    return vals.map((v, i) => [i * step, pt + (1 - (v - lo) / (hi - lo)) * (H - pt - pb)]);
  }
  let gid = 0;
  function areaChart(vals, W, H, color = 'var(--acc)') {
    if (!vals || !vals.length) return '';
    const pts = scaleSeries(vals, W, H);
    const line = monotone(pts);
    const id = 'g' + (++gid);
    const [lx, ly] = pts[pts.length - 1];
    return `<svg viewBox="0 0 ${W} ${H}" height="${H}" aria-hidden="true" preserveAspectRatio="none">
      <defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${color}" stop-opacity="${theme === 'light' ? 0.22 : 0.34}"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs>
      <path d="${line} L${lx},${H} L0,${H} Z" fill="url(#${id})" class="fade"/>
      <path d="${line}" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="draw" vector-effect="non-scaling-stroke" style="filter:drop-shadow(0 0 6px var(--glow))"/>
      <circle cx="${lx}" cy="${ly}" r="4" fill="${color}" class="pulse"/><circle cx="${lx}" cy="${ly}" r="4.5" fill="${color}" stroke="var(--bg)" stroke-width="2"/>
    </svg>`;
  }
  function sparkline(vals, color, W = 64, H = 26) {
    if (!vals || vals.length < 2) return `<svg width="${W}" height="${H}"></svg>`;
    const pts = scaleSeries(vals, W, H, 3, 3);
    const [lx, ly] = pts[pts.length - 1];
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" aria-hidden="true" style="overflow:visible"><path d="${monotone(pts)}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linecap="round" class="draw-s"/><circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="2.4" fill="${color}"/></svg>`;
  }
  function changePill(p, invert) {
    if (p === null || p === undefined) return '<span class="pill flat">новое</span>';
    const good = invert ? p <= 0 : p >= 0;
    if (Math.abs(p) < 0.05) return '<span class="pill flat">0%</span>';
    return `<span class="pill ${good ? 'up' : 'down'}">${icon(p >= 0 ? 'up2' : 'down2', 12, 'currentColor', 2.6)}${fmt(Math.abs(p), 1)}%</span>`;
  }
  function countUp(el, to, ms = 1300) {
    if (!el) return;
    if (reduce) { el.textContent = int(to); return; }
    const t0 = performance.now();
    const step = (t) => {
      const p = Math.min(1, (t - t0) / ms);
      el.textContent = int(to * (1 - Math.pow(1 - p, 4)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // ---------------------------------------------------------------- вход и запросы
  const params = new URLSearchParams(location.search);
  let key = null;
  try { key = new URLSearchParams(location.hash.slice(1)).get('k') || localStorage.getItem('delta_key'); } catch (e) { key = null; }

  function authHeaders() {
    const h = { 'Content-Type': 'application/json' };
    if (tg && tg.initData) h['X-Telegram-Init-Data'] = tg.initData;
    else if (key) h.Authorization = 'Bearer ' + key;
    return h;
  }
  async function api(path, opts = {}) {
    const r = await fetch(path, { ...opts, headers: authHeaders() });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { const e = new Error(j.error || 'Нет связи с сервером'); e.status = r.status; throw e; }
    return j;
  }
  async function login() {
    const token = params.get('login');
    if (!token) return;
    const r = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) });
    const j = await r.json().catch(() => ({}));
    if (j.key) {
      key = j.key;
      try { localStorage.setItem('delta_key', key); } catch (e) { /* приватный режим */ }
      // ключ остаётся в адресе после #, чтобы иконка на экране «Домой» открывалась уже с входом
      history.replaceState(null, '', '/#k=' + encodeURIComponent(key));
    } else {
      throw new Error(j.error || 'Ссылка для входа не подошла');
    }
  }

  // ---------------------------------------------------------------- состояние
  const S = { tab: 'home', home: null, stats: {}, rates: null, settings: null, acc: 0, hover: null, range: '1m', sel: null,
    fx: { code: 'USD', amt: '100', toRub: true }, hidden: false, first: true };
  const screen = $('#screen');

  function applyTheme() {
    let t = tg && tg.colorScheme ? tg.colorScheme : (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    if (params.get('theme') === 'light' || params.get('theme') === 'dark') t = params.get('theme');
    theme = t;
    document.documentElement.dataset.theme = t;
    const bg = t === 'light' ? '#F0EDFB' : '#08061A';
    document.querySelector('meta[name="theme-color"]').setAttribute('content', bg);
    try { tg.setHeaderColor(bg); tg.setBackgroundColor(bg); } catch (e) { /* старый Telegram */ }
  }

  function toast(title, text) {
    const root = $('#toast-root');
    root.innerHTML = `<div class="toast glass" role="status"><span class="tile">${icon('check', 20, 'var(--onacc)', 2.8)}</span><div><b>${esc(title)}</b><span>${esc(text || '')}</span></div></div>`;
    clearTimeout(toast.t);
    toast.t = setTimeout(() => { root.innerHTML = ''; }, 2500);
  }

  function fatal(msg) {
    $('#tabs').innerHTML = '';
    screen.innerHTML = `<div class="top rise"><div class="logo"><span class="logo-mark">Δ</span><span class="logo-word">DELTA</span></div></div>
      <div class="glass empty rise" style="text-align:left"><b style="color:var(--text);font-size:16px">${esc(msg)}</b><br><br>
      Откройте DELTA из Telegram (кнопка «DELTA» в чате с ботом) или отправьте боту команду <b>/web</b> — придёт ссылка для входа без Telegram.</div>`;
  }

  // ---------------------------------------------------------------- нижнее меню
  function renderTabs() {
    const t = (id, ic, label) => `<button class="tab press ${S.tab === id ? 'on' : ''}" data-tab="${id}" aria-current="${S.tab === id ? 'page' : 'false'}">${icon(ic, 22)}<span>${label}</span></button>`;
    $('#tabs').innerHTML = t('home', 'home', 'Главная') + t('stats', 'chart', 'Аналитика') +
      `<button class="fab press" data-add="exp" aria-label="Новая запись">${icon('plus', 26, '#fff', 2.4)}</button>` +
      t('rates', 'globe', 'Курсы') + t('more', 'more', 'Ещё');
  }

  // ---------------------------------------------------------------- главная
  function header() {
    const total = S.home ? S.home.total : 0;
    return `<header class="top rise"><div><div class="logo"><span class="logo-mark">Δ</span><span class="logo-word">DELTA</span></div>
      <div class="top-sub num">Всего на счетах <b class="blur-t ${S.hidden ? 'blurred' : ''}"><span id="total">${int(total)}</span>${NB}₽</b></div></div>
      <div class="row"><button class="icon-btn glass press" data-act="hide" aria-label="${S.hidden ? 'Показать суммы' : 'Скрыть суммы'}">${icon('eye', 20)}</button>
      <button class="icon-btn glass press" data-tab="more" aria-label="Настройки" style="font-weight:800;color:var(--acct)">${esc(((S.home && S.home.user.first_name) || 'Я').slice(0, 1))}</button></div></header>`;
  }

  function cardsHTML() {
    const accs = S.home.accounts, n = accs.length;
    return accs.map((a, i) => {
      const slot = (i - S.acc + n) % n;
      const vis = slot < 3;
      const bal = a.currency === 'RUB' ? rub(a.balance) : money(a.balance, a.currency);
      const sub = { card: 'Карта', cash: 'Кошелёк', crypto: 'Криптовалюта' }[a.kind] + ' · ' + a.currency;
      return `<button class="card press" data-act="next-card" aria-label="${esc(a.name)}: ${esc(bal)}. Следующий счёт"
        style="transform:translateY(${slot * 16}px) scale(${1 - slot * 0.06});opacity:${vis ? 1 - slot * 0.28 : 0};z-index:${n - slot}">
        <span class="holo" style="background:${HOLO[a.style] || HOLO.tb};animation-delay:${-i * 2.5}s"></span><span class="shine"></span>
        <span class="sheen" style="animation-delay:${i * 1.1}s"></span>
        <span class="body"><span class="row" style="justify-content:space-between;align-items:flex-start">
          <span style="display:flex;flex-direction:column;gap:2px"><span class="name">${esc(a.name)}</span><span class="sub">${esc(sub)}</span></span>
          <span style="font-family:Unbounded,sans-serif;font-size:20px;font-weight:700;opacity:.9">Δ</span></span>
          <span class="row" style="justify-content:space-between;align-items:flex-end">
          <span class="bal num blur-t ${S.hidden ? 'blurred' : ''}">${esc(bal)}</span>
          <span class="cur">${a.currency !== 'RUB' ? '≈' + NB + rub(a.balance_rub) : ''}</span></span></span></button>`;
    }).join('');
  }

  function chartCardHTML() {
    const a = S.home.accounts[S.acc];
    const up = a.delta >= 0;
    return `<div class="chart-head"><div style="display:flex;flex-direction:column;gap:4px"><span class="muted" style="font-size:12.5px">Баланс счёта · ${esc(a.name)}</span>
        <span class="big num blur-t ${S.hidden ? 'blurred' : ''}" id="acc-big"><span id="acc-num">${int(a.balance_rub)}</span><small>₽</small></span></div>
        <div style="text-align:right;display:flex;flex-direction:column;gap:2px;padding-bottom:2px">
        <span class="chg ${up ? 'up' : 'down'} num" id="acc-chg"><span class="delta">Δ</span>${up ? '+' : '−'}${rub(Math.abs(a.delta))}</span>
        <span class="muted" style="font-size:12px" id="acc-when">за 30 дней</span></div></div>
      <div class="chart" id="acc-chart" style="height:128px;margin-top:4px">${areaChart(a.series, 354, 128)}
        <div class="hover-line" id="hv-line" hidden></div><div class="hover-dot" id="hv-dot" hidden></div><div class="tip num" id="hv-tip" hidden></div></div>`;
  }

  function renderHome() {
    const h = S.home;
    if (!h) { screen.innerHTML = header() + '<div class="glass empty">Загружаю…</div>'; return; }
    if (S.acc >= h.accounts.length) S.acc = 0;
    const cats = h.categories.length
      ? h.categories.slice(0, 6).map((c) => {
        const col = catColor(c);
        const p = c.change;
        return `<div class="item"><span class="tile" style="background:color-mix(in srgb, ${col} 14%, transparent)">${icon(c.icon, 20, col)}</span>
          <span class="main"><span class="t1">${esc(c.name)}</span><span class="t2 num blur-t ${S.hidden ? 'blurred' : ''}">${rub(c.amount)}</span></span>
          ${sparkline(c.spark, p !== null && p > 0 ? 'var(--down)' : 'var(--up)')}<span style="width:66px;display:flex;justify-content:flex-end">${changePill(p, true)}</span></div>`;
      }).join('')
      : '<div class="empty">Пока нет трат в этом месяце.<br>Нажмите «+» или напишите боту <b>кофе 350</b>.</div>';
    const recent = h.recent.length
      ? h.recent.slice(0, 12).map((t) => {
        const col = catColor({ key: t.key, color: t.color });
        const amount = (t.sign < 0 ? '−' : '+') + money(t.amount, t.currency);
        const todayMsk = new Date(Date.now() + 3 * 3600e3).toISOString().slice(0, 10);
        const when = t.day === todayMsk ? 'сегодня ' + t.time : t.day.slice(8, 10) + '.' + t.day.slice(5, 7) + ' ' + t.time;
        return `<button class="item press" data-tx="${t.id}"><span class="tile" style="background:color-mix(in srgb, ${col} 14%, transparent)">${icon(t.icon, 20, col)}</span>
          <span class="main"><span class="t1">${esc(t.note || t.category)}</span><span class="t2">${esc(t.category)} · ${esc(t.account)} · ${when}</span></span>
          <span class="amt num ${t.sign > 0 ? 'plus' : ''} blur-t ${S.hidden ? 'blurred' : ''}">${esc(amount)}</span></button>`;
      }).join('')
      : '<div class="empty">Записей ещё нет.</div>';
    const fresh = !h.recent.length && h.accounts.every((a) => !a.balance);
    const onboard = fresh
      ? `<section class="onboard rise" style="animation-delay:.1s"><h2>Добро пожаловать в DELTA</h2>
          <p>Три шага — и приложение начнёт считать за вас.</p>
          <div class="steps"><div><b>1</b>Впишите, сколько денег на счетах</div><div><b>2</b>Задайте лимит трат на месяц</div><div><b>3</b>Записывайте траты: «+» здесь или «кофе 350» боту</div></div>
          <button class="cta press" data-act="setup">Указать остатки</button></section>`
      : '';
    screen.innerHTML = header() +
      `<section class="stack rise" style="animation-delay:.07s" id="stack">${cardsHTML()}</section>
       <div class="dots" id="dots">${h.accounts.map((a, i) => `<button class="dot-btn ${i === S.acc ? 'on' : ''}" data-acc="${i}" aria-label="${esc(a.name)}"><span></span></button>`).join('')}</div>
       ${onboard}
       <section class="glass chart-card rise" style="animation-delay:.14s" id="chart-card">${chartCardHTML()}</section>
       <section class="rise" style="animation-delay:.21s;display:flex;flex-direction:column;gap:10px">
         <div class="sec-head"><h2>Категории как активы</h2><span>к прошлому месяцу</span></div><div class="glass list">${cats}</div></section>
       <section class="rise" style="animation-delay:.28s;display:flex;flex-direction:column;gap:10px">
         <div class="sec-head"><h2>Последние записи</h2><span>нажмите, чтобы удалить</span></div><div class="glass list">${recent}</div></section>`;
    if (S.first) { countUp($('#total'), h.total); countUp($('#acc-num'), h.accounts[S.acc].balance_rub); S.first = false; }
    bindScrub();
  }

  function switchCard(i) {
    S.acc = i; S.hover = null;
    $('#stack').innerHTML = cardsHTML();
    document.querySelectorAll('.dot-btn').forEach((b, j) => b.classList.toggle('on', j === i));
    $('#chart-card').innerHTML = chartCardHTML();
    bindScrub();
    haptic('light');
  }

  function bindScrub() {
    const el = $('#acc-chart');
    if (!el) return;
    const a = S.home.accounts[S.acc];
    const move = (e) => {
      const r = el.getBoundingClientRect();
      const x = Math.max(0, Math.min(r.width, e.clientX - r.left));
      const n = a.series.length;
      const i = Math.round(x / r.width * (n - 1));
      if (i === S.hover) return;
      S.hover = i;
      const pts = scaleSeries(a.series, r.width, 128);
      const [px, py] = pts[i];
      const line = $('#hv-line'), dot = $('#hv-dot'), tip = $('#hv-tip');
      line.hidden = dot.hidden = tip.hidden = false;
      line.style.left = px + 'px'; dot.style.left = px + 'px'; dot.style.top = py + 'px';
      tip.textContent = a.labels[i];
      tip.style.left = Math.max(0, Math.min(r.width - 70, px - 30)) + 'px';
      $('#acc-num').textContent = int(a.series[i]);
      const d = a.series[i] - a.series[0];
      $('#acc-chg').className = 'chg num ' + (d >= 0 ? 'up' : 'down');
      $('#acc-chg').innerHTML = '<span class="delta">Δ</span>' + (d >= 0 ? '+' : '−') + rub(Math.abs(d));
      $('#acc-when').textContent = 'на ' + a.labels[i];
      haptic('soft');
    };
    const leave = () => {
      S.hover = null;
      const card = $('#chart-card');
      if (!card || S.tab !== 'home') return;
      card.innerHTML = chartCardHTML();
      bindScrub();
    };
    el.addEventListener('pointermove', move);
    el.addEventListener('pointerdown', move);
    el.addEventListener('pointerleave', () => S.hover !== null && setTimeout(leave, 600));
  }

  // ---------------------------------------------------------------- аналитика
  function renderStats() {
    const s = S.stats[S.range];
    const head = `<header class="top rise"><h1 style="margin:0;font-family:Unbounded,sans-serif;font-size:26px">Аналитика</h1>
      <span class="glass" style="padding:8px 14px;border-radius:18px;font-weight:800;font-size:13.5px">${['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][new Date().getMonth()]}</span></header>`;
    if (!s) { screen.innerHTML = head + '<div class="glass empty">Загружаю…</div>'; return; }
    const lim = s.limit, pct = lim ? Math.min(1, s.spent / lim) : 0, C = 2 * Math.PI * 30;
    const W = 322, H = 160;
    const real = s.bars.filter((b) => !b.ghost).map((b) => b.value);
    const sorted = [...real].sort((a, b) => a - b);
    const maxReal = Math.max(...real, 1);
    // одна крупная трата (аренда) не должна сплющивать остальные дни: такой столбик рисуем «с разрывом»
    let cap = Math.max(s.avg * 2.6, sorted.length > 3 ? sorted[sorted.length - 2] * 1.3 : 0);
    cap = Math.max(1, s.avg * 1.15, Math.min(cap || maxReal * 1.1, maxReal * 1.1));
    const slot = W / s.bars.length, bw = Math.max(4, Math.min(16, slot * 0.6));
    const top = H - 26;
    const cut = [];
    const bars = s.bars.map((b, i) => {
      const h = Math.max(3, Math.min(b.value, cap) / cap * top);
      const x = slot * (i + 0.5) - bw / 2, y = H - h, rx = Math.min(5, bw / 2.5);
      const delay = `animation-delay:${((b.ghost ? 0.5 : 0.1) + i * 0.02).toFixed(2)}s`;
      if (b.ghost) return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" rx="${rx}" fill="var(--acc)" fill-opacity=".22" class="bar" style="${delay}"/>`;
      const attrs = `fill="var(--acc)" fill-opacity="${S.sel === null || S.sel === i ? 1 : 0.4}" data-bar="${i}"`;
      if (b.value <= cap) return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" rx="${rx}" ${attrs} class="bar" style="${delay}"/>`;
      cut.push(i);
      return `<g class="bar" style="${delay}"><rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="9" rx="${rx}" ${attrs}/>
        <rect x="${x.toFixed(1)}" y="${(y + 13).toFixed(1)}" width="${bw.toFixed(1)}" height="${(h - 13).toFixed(1)}" rx="${rx}" ${attrs}/></g>`;
    }).join('');
    const cutTags = cut.length <= 4
      ? cut.map((i) => `<span class="cut-tag num" style="left:${(slot * (i + 0.5) / W * 100).toFixed(2)}%;top:${H - top - 20}px">${short(s.bars[i].value)}</span>`).join('')
      : '';
    const avgY = H - Math.min(s.avg, cap) / cap * top;
    let tip = '';
    if (S.sel !== null && s.bars[S.sel]) {
      const b = s.bars[S.sel];
      const h = Math.max(3, Math.min(b.value, cap) / cap * top);
      const left = Math.max(0, Math.min(W - 110, slot * (S.sel + 0.5) - 50));
      tip = `<div class="tip" style="left:${left}px;top:${Math.max(-8, H - h - 52)}px;display:flex;flex-direction:column;gap:1px;padding:6px 10px;border-radius:11px;animation:pop .4s both">
        <span style="font-size:10.5px;opacity:.7">${esc(b.label)}</span><span style="font-size:13px" class="num">${rub(b.value)}</span></div>`;
    }
    const total = s.shares.reduce((a, b) => a + b.amount, 0) || 1;
    const shares = s.shares.length
      ? `<div class="shares">${s.shares.map((c) => `<div style="width:${(c.amount / total * 100).toFixed(2)}%;background:${catColor(c)}"></div>`).join('')}</div>
         <div class="legend">${s.shares.slice(0, 6).map((c) => `<div><i style="background:${catColor(c)}"></i><span class="muted">${esc(c.name)}</span><b class="num">${Math.round(c.amount / total * 100)}%</b></div>`).join('')}</div>`
      : '<div class="empty" style="padding:8px">Трат в этом месяце пока нет.</div>';
    const fcText = lim
      ? (s.forecast <= lim ? 'в пределах лимита' : `больше лимита на ${rub(s.forecast - lim)}`)
      : 'лимит пока не задан';
    const labels = { '14d': ['14 дней назад', 'сегодня'], '1m': ['1 число', 'конец месяца'], '3m': ['13 недель назад', 'эта неделя'] }[s.range];
    screen.innerHTML = head +
      `<section class="glass ring-card rise" style="animation-delay:.07s"><div class="ring">
        <svg width="76" height="76" viewBox="0 0 76 76"><circle cx="38" cy="38" r="30" fill="none" stroke="var(--grid)" stroke-width="8"/>
        <circle cx="38" cy="38" r="30" fill="none" stroke="var(--acc)" stroke-width="8" stroke-linecap="round" stroke-dasharray="${(pct * C).toFixed(1)} ${C.toFixed(1)}" style="filter:drop-shadow(0 0 6px var(--glow))" class="fade"/></svg>
        <b>${lim ? Math.round(pct * 100) + '%' : '—'}</b></div>
        <div style="display:flex;flex-direction:column;gap:4px"><span class="muted" style="font-size:12.5px">Потрачено в этом месяце</span>
        <span class="big num" style="font-size:26px">${rub(s.spent)}</span>
        <span class="muted" style="font-size:12.5px">${lim ? 'из лимита ' + rub(lim) + ' · ' : ''}≈${NB}${rub(s.avg_day)} в обычный день · доход ${rub(s.income)}</span></div></section>
      <section class="glass bars-card rise" style="animation-delay:.14s"><div class="row" style="justify-content:space-between">
        <h2 style="margin:0;font-size:15px;font-weight:800">Траты по дням</h2>
        <div class="seg">${[['14d', '14Д'], ['1m', '1М'], ['3m', '3М']].map(([k, l]) => `<button class="${S.range === k ? 'on' : ''}" data-range="${k}">${l}</button>`).join('')}</div></div>
        <div class="bars"><svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" preserveAspectRatio="none" style="overflow:visible">
          <line x1="0" x2="${W}" y1="${avgY.toFixed(1)}" y2="${avgY.toFixed(1)}" stroke="var(--text2)" stroke-dasharray="4 5" stroke-opacity=".7" vector-effect="non-scaling-stroke"/>${bars}</svg>
          <span class="avg-tag" style="top:${(avgY - 22).toFixed(0)}px">средний день ${rub(s.avg)}</span>${cutTags}${tip}</div>
        <div class="row muted" style="justify-content:space-between;font-size:11.5px"><span>${labels[0]}</span>
          ${s.range === '1m' ? '<span class="row" style="gap:6px"><span style="width:12px;height:8px;background:var(--acc);opacity:.3;border-radius:2px"></span>прогноз</span>' : ''}<span>${labels[1]}</span></div></section>
      <section class="glass rise" style="animation-delay:.21s;padding:16px;display:flex;flex-direction:column;gap:12px">
        <h2 style="margin:0;font-size:15px;font-weight:800">Куда уходят деньги</h2>${shares}</section>
      ${s.spent > 0
        ? `<section class="insight rise" style="animation-delay:.28s"><span class="tile">${icon('spark', 18, 'var(--onacc)', 2)}</span>
        <div>При таком темпе к концу месяца вы потратите <b>≈${NB}${rub(s.forecast)}</b> — ${fcText}.</div></section>`
        : `<section class="insight rise" style="animation-delay:.28s"><span class="tile">${icon('spark', 18, 'var(--onacc)', 2)}</span>
        <div>Здесь появится прогноз на конец месяца — после первых трат.${lim ? '' : ' А пока задайте лимит, чтобы видеть, сколько можно тратить в день.'}</div></section>`}
      ${lim ? '' : '<button class="cta press rise" style="animation-delay:.32s" data-tab="more">Задать лимит</button>'}`;
  }

  // ---------------------------------------------------------------- курсы
  const fxWidth = (v) => `calc(${Math.max(1, String(v).length)}ch + 6px)`;
  function renderRates() {
    const list = S.rates;
    const head = `<header class="top rise"><div><h1 style="margin:0;font-family:Unbounded,sans-serif;font-size:26px">Курсы</h1>
      <div class="muted" style="font-size:12.5px;margin-top:3px">ЦБ РФ и CoinGecko · обновляется каждый час</div></div></header>`;
    if (!list) { screen.innerHTML = head + '<div class="glass empty">Загружаю…</div>'; return; }
    const cur = list.find((x) => x.code === S.fx.code) || list[0];
    if (!cur || cur.rate === null) { screen.innerHTML = head + '<div class="glass empty">Курсы ещё загружаются с ЦБ и CoinGecko. Загляните через минуту.</div>'; return; }
    const up = cur.change30 >= 0;
    const v = parseFloat(String(S.fx.amt).replace(',', '.')) || 0;
    const res = S.fx.toRub ? v * cur.rate : v / cur.rate;
    const rows = list.filter((x) => x.rate !== null).map((x) => {
      const c = x.change >= 0 ? 'var(--up)' : 'var(--down)';
      return `<button class="item fx-row press ${x.code === cur.code ? 'on' : ''}" data-fx="${x.code}">
        <span class="fx-ic" style="font-size:${x.symbol.length > 1 ? 12 : 17}px">${esc(x.symbol)}</span>
        <span class="main"><span class="t1">${x.code}</span><span class="t2">${esc(x.name)}</span></span>
        ${sparkline(x.series.slice(-14), c, 56, 24)}
        <span style="width:96px;display:flex;flex-direction:column;align-items:flex-end;gap:3px"><span class="amt num">${x.rate >= 1000 ? fmt(Math.round(x.rate)) : fmt2(x.rate)}${NB}₽</span>${changePill(x.change)}</span></button>`;
    }).join('');
    screen.innerHTML = head +
      `<section class="rise" style="animation-delay:.07s;display:flex;flex-direction:column;gap:2px">
        <div class="row" style="justify-content:space-between;align-items:flex-end">
          <div style="display:flex;flex-direction:column;gap:4px"><span class="muted" style="font-size:12.5px;letter-spacing:.06em">${cur.code} / RUB</span>
          <span class="price num">${cur.rate >= 1000 ? fmt(Math.round(cur.rate)) : fmt2(cur.rate)}${NB}₽</span></div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;font-size:12px" class="muted"><span class="chg ${up ? 'up' : 'down'}">${icon(up ? 'up2' : 'down2', 13, 'currentColor', 2.6)}${fmt(Math.abs(cur.change30), 2)}%</span><span>за 30 дней</span></div></div>
        <div class="chart" style="height:136px;margin-top:6px">${areaChart(cur.series, 354, 136)}</div></section>
      <section class="glass conv rise" style="animation-delay:.14s">
        <div class="row"><label class="sr" for="fx-amt">Сумма</label><input id="fx-amt" inputmode="decimal" value="${esc(S.fx.amt)}" class="num" autocomplete="off" style="width:${fxWidth(S.fx.amt)}">
          <b class="muted">${S.fx.toRub ? cur.code : 'RUB'}</b>
          <button class="round-acc press" data-act="fx-swap" aria-label="Поменять направление">${icon('swap', 18, 'currentColor', 2.2)}</button></div>
        <div class="res num"><span id="fx-res">= ${S.fx.toRub ? fmt2(res) : fmt(res, cur.code === 'BTC' ? 8 : 2)}</span><span class="muted" style="font-size:14px;font-weight:800">${S.fx.toRub ? 'RUB' : cur.code}</span></div>
        <div class="row" style="gap:6px">${[['1', '1'], ['100', '100'], ['1000', '1' + NB + '000'], ['10000', '10' + NB + '000']].map(([a, l]) => `<button class="chip press num" data-fxamt="${a}">${l}</button>`).join('')}</div></section>
      <section class="glass list rise" style="animation-delay:.21s">${rows}</section>`;
  }

  // ---------------------------------------------------------------- ещё (настройки)
  function renderMore() {
    const st = S.settings, h = S.home;
    const head = `<header class="top rise"><h1 style="margin:0;font-family:Unbounded,sans-serif;font-size:26px">Ещё</h1></header>`;
    if (!st || !h) { screen.innerHTML = head + '<div class="glass empty">Загружаю…</div>'; return; }
    const accs = h.accounts.map((a) => `<div class="item"><span class="tile" style="background:${HOLO[a.style] || HOLO.tb}">${icon(a.kind === 'cash' ? 'bag' : a.kind === 'crypto' ? 'spark' : 'phone', 18, '#fff')}</span>
      <span class="main"><span class="t1">${esc(a.name)}</span><span class="t2 num">${a.currency === 'RUB' ? rub(a.balance) : money(a.balance, a.currency)}</span></span>
      <button class="btn2 press" data-edit-acc="${a.id}">Изменить</button></div>`).join('');
    screen.innerHTML = head +
      `<section class="glass rise" style="padding:16px;display:flex;flex-direction:column;gap:12px;animation-delay:.07s">
        <h2 style="margin:0;font-size:15px;font-weight:800">Лимит трат на месяц</h2>
        <div class="row"><label class="sr" for="limit">Лимит, ₽</label><input id="limit" class="note num" inputmode="numeric" placeholder="Например, 100 000" value="${st.limit ? Math.round(st.limit) : ''}">
        <button class="btn2 press" data-act="save-limit" style="background:var(--acc);color:var(--onacc)">Сохранить</button></div></section>
      <section class="rise" style="display:flex;flex-direction:column;gap:10px;animation-delay:.14s"><div class="sec-head"><h2>Счета</h2><button class="press" data-act="add-acc" style="color:var(--acct);font-weight:700">+ Добавить</button></div>
        <div class="glass list">${accs}</div></section>
      <section class="glass rise" style="padding:16px;display:flex;flex-direction:column;gap:10px;animation-delay:.21s">
        <h2 style="margin:0;font-size:15px;font-weight:800">Без Telegram: двойное касание крышки iPhone</h2>
        <div class="muted" style="font-size:13px;line-height:1.45">Этот ключ вставляется в команду iPhone. Никому его не показывайте.</div>
        <div class="key-box" id="key-box">${esc(st.key)}</div>
        <div class="key-acts"><button class="btn2 press" data-act="copy-key">${icon('copy', 16)} Скопировать</button>
        <a class="btn2 press" href="/ios#k=${encodeURIComponent(st.key)}" target="_blank" rel="noopener">Инструкция</a>
        <button class="btn2 press wide" data-act="rotate-key">${icon('repeat', 16)} Выпустить новый ключ</button></div></section>
      <section class="glass rise empty" style="animation-delay:.28s;text-align:left;font-size:13px">Чтобы открыть DELTA в Safari и добавить на экран «Домой», отправьте боту <b>/web</b>.</section>`;
  }

  // ---------------------------------------------------------------- окно новой записи
  let A = null; // состояние окна записи
  function rateOf(code) {
    if (code === 'RUB') return 1;
    const r = S.rates && S.rates.find((x) => x.code === code);
    return r && r.rate ? r.rate : null;
  }
  function openAdd(type) {
    if (!S.home) return;
    A = { type, amt: '0', cur: 'RUB', cat: type === 'exp' ? 'food' : 'salary', acc: S.home.accounts[S.acc] ? S.home.accounts[S.acc].id : null, note: '', busy: false };
    $('#sheet-root').innerHTML = `<div class="overlay" data-act="close-sheet"></div><section class="sheet" role="dialog" aria-label="Новая запись" id="sheet"></section>`;
    renderSheet();
    try { tg.BackButton.show(); } catch (e) { /* нет Telegram */ }
    haptic('medium');
  }
  function closeSheet() {
    const sh = $('#sheet');
    if (!sh) return;
    sh.classList.add('closing');
    try { tg.BackButton.hide(); } catch (e) { /* нет Telegram */ }
    setTimeout(() => { $('#sheet-root').innerHTML = ''; A = null; }, reduce ? 0 : 280);
  }
  function sheetNumbers() {
    const [i, f] = A.amt.split('.');
    const num = fmt(parseInt(i || '0', 10)) + (A.amt.includes('.') ? ',' + (f || '') : '');
    const v = parseFloat(A.amt) || 0;
    const r = rateOf(A.cur);
    const rubV = r ? v * r : null;
    return { num, v, rubV };
  }
  function renderSheet() {
    const sh = $('#sheet');
    if (!sh || !A) return;
    const h = S.home, exp = A.type === 'exp';
    const cats = exp ? h.expense_categories : h.income_categories;
    const { num, v, rubV } = sheetNumbers();
    const sub = A.cur === 'RUB'
      ? (rateOf('USD') ? `≈ $${fmt2(v / rateOf('USD'))} · €${fmt2(v / (rateOf('EUR') || 1))} · ¥${fmt2(v / (rateOf('CNY') || 1))}` : '')
      : (rubV !== null ? `≈ ${fmt2(rubV)} ₽ · курс 1 ${SYM[A.cur]} = ${fmt2(rateOf(A.cur))} ₽` : 'курс пока недоступен');
    const lim = h.limit;
    let impact = '';
    if (exp && lim.limit) {
      const spentPct = Math.min(100, lim.spent / lim.limit * 100);
      const addPct = Math.max(0, Math.min(100 - spentPct, (rubV || 0) / lim.limit * 100));
      const left = lim.limit - lim.spent - (rubV || 0);
      impact = `<div class="glass impact"><div class="row muted" style="justify-content:space-between;font-size:12.5px"><span>Лимит месяца</span>
        <b class="num" style="color:var(--text)">${rub(lim.spent + (rubV || 0))} / ${rub(lim.limit)}</b></div>
        <div class="bar-bg"><div class="a" style="width:${spentPct}%"></div><div class="b" style="width:${addPct}%;background-color:${left < 0 ? 'var(--down)' : 'var(--acc)'}"></div></div>
        <div class="muted num" style="font-size:12px">${left < 0 ? 'Лимит будет превышен на ' + rub(-left) : 'Останется ' + rub(left) + ' · ≈' + NB + rub(left / Math.max(1, lim.days_left)) + ' в день'}</div></div>`;
    } else if (!exp) {
      impact = `<div class="glass impact muted num" style="font-size:12.5px">Баланс станет ${rub(h.total + (rubV || 0))}</div>`;
    }
    sh.innerHTML = `<div class="grab"></div>
      <div class="row"><button class="icon-btn press" style="background:var(--key)" data-act="close-sheet" aria-label="Закрыть">${icon('close', 18, 'var(--text2)', 2.2)}</button>
        <div class="seg" style="flex:1"><button style="flex:1" class="${exp ? 'on' : ''}" data-type="exp">Расход</button><button style="flex:1" class="${!exp ? 'on' : ''}" data-type="inc">Доход</button></div></div>
      <div class="amount num ${exp ? '' : 'plus'}">${exp ? '−' : '+'}${num}${NB}${SYM[A.cur]}</div>
      <div class="amount-sub num">${esc(sub)}</div>
      <div class="curs">${CURS.map((c) => `<button class="cur-chip press ${A.cur === c ? 'on' : ''}" data-cur="${c}">${SYM[c]} ${c}</button>`).join('')}</div>
      <div class="hscroll">${cats.map((c) => { const col = catColor(c); return `<button class="cat-btn press ${A.cat === c.key ? 'on' : ''}" data-cat="${c.key}">
        <span class="tile" style="background:color-mix(in srgb, ${col} 14%, transparent);box-shadow:0 0 0 2px ${A.cat === c.key ? col : 'transparent'}">${icon(c.icon, 22, col)}</span>${esc(c.name)}</button>`; }).join('')}</div>
      <div class="hscroll" style="gap:6px">${h.accounts.map((a) => `<button class="acc-chip press ${A.acc === a.id ? 'on' : ''}" data-accid="${a.id}">${esc(a.name)}</button>`).join('')}</div>
      <label class="sr" for="note">Заметка</label><input id="note" class="note" placeholder="Заметка (необязательно)" value="${esc(A.note)}" maxlength="120">
      ${impact}
      <div class="keys">${['1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '0', 'del'].map((k) => `<button class="press num" data-key="${k}" aria-label="${k === 'del' ? 'Стереть' : k}">${k === 'del' ? icon('back', 22) : k}</button>`).join('')}</div>
      <button class="cta press" data-act="save" ${v > 0 && !A.busy ? '' : 'disabled'}>${A.busy ? 'Сохраняю…' : exp ? 'Добавить расход' : 'Добавить доход'}</button>`;
  }
  function press(k) {
    let a = A.amt;
    if (k === 'del') a = a.length > 1 ? a.slice(0, -1) : '0';
    else if (k === ',') { if (!a.includes('.')) a += '.'; }
    else {
      const p = a.split('.');
      if (p.length === 2 && p[1].length >= (A.cur === 'BTC' ? 8 : 2)) return;
      if (p.length === 1 && p[0].length >= 9) return;
      a = a === '0' ? k : a + k;
    }
    A.amt = a;
    haptic('light');
    renderSheet();
  }
  async function save() {
    const v = parseFloat(A.amt);
    if (!(v > 0) || A.busy) return;
    A.busy = true; renderSheet();
    try {
      const r = await api('/api/transactions', { method: 'POST', body: JSON.stringify({ type: A.type, amount: v, currency: A.cur, category: A.cat, account_id: A.acc, note: A.note }) });
      haptic('ok');
      const lines = r.text.split('\n');
      toast(lines[0], lines.slice(1).join('\n'));
      closeSheet();
      S.stats = {};
      await loadHome();
    } catch (e) {
      A.busy = false; renderSheet();
      toast('Не сохранилось', e.message);
    }
  }

  // мини-окно: форма или подтверждение
  function dialog(html) {
    $('#sheet-root').innerHTML = `<div class="overlay" data-act="close-sheet"></div><section class="sheet" role="dialog" id="sheet">${html}</section>`;
    try { tg.BackButton.show(); } catch (e) { /* нет Telegram */ }
  }

  // ---------------------------------------------------------------- загрузка
  async function loadHome() {
    S.home = await api('/api/home');
    if (S.tab === 'home') renderHome(); else render();
  }
  async function loadStats() {
    if (!S.stats[S.range]) S.stats[S.range] = await api('/api/stats?range=' + S.range);
    if (S.tab === 'stats') renderStats();
  }
  async function loadRates() {
    S.rates = (await api('/api/rates')).rates;
    if (S.tab === 'rates') renderRates();
  }
  async function loadSettings() {
    S.settings = await api('/api/settings');
    if (S.tab === 'more') renderMore();
  }
  function render() {
    renderTabs();
    window.scrollTo(0, 0);
    if (S.tab === 'home') renderHome();
    else if (S.tab === 'stats') { renderStats(); loadStats().catch(showErr); }
    else if (S.tab === 'rates') { renderRates(); if (!S.rates) loadRates().catch(showErr); }
    else if (S.tab === 'more') { renderMore(); loadSettings().catch(showErr); }
  }
  function showErr(e) {
    if (e && e.status === 401) fatal(e.message); else toast('Ошибка', e ? e.message : '');
  }

  // ---------------------------------------------------------------- события
  document.addEventListener('click', async (e) => {
    const t = e.target.closest('button, [data-act], rect[data-bar]');
    if (!t) return;
    const d = t.dataset;
    if (d.tab) { S.tab = d.tab; S.sel = null; haptic('light'); render(); return; }
    if (d.add) { openAdd(d.add); return; }
    if (d.acc !== undefined && t.classList.contains('dot-btn')) { switchCard(+d.acc); return; }
    if (d.range) { S.range = d.range; S.sel = null; renderStats(); loadStats().catch(showErr); return; }
    if (d.bar !== undefined) { S.sel = S.sel === +d.bar ? null : +d.bar; haptic('light'); renderStats(); return; }
    if (d.fx) { S.fx.code = d.fx; haptic('light'); renderRates(); return; }
    if (d.fxamt) { S.fx.amt = d.fxamt; renderRates(); return; }
    if (d.key) { press(d.key); return; }
    if (d.type) { A.type = d.type; A.cat = d.type === 'exp' ? 'food' : 'salary'; haptic('light'); renderSheet(); return; }
    if (d.cur) { A.cur = d.cur; haptic('light'); renderSheet(); return; }
    if (d.cat) { A.cat = d.cat; haptic('light'); renderSheet(); return; }
    if (d.accid) { A.acc = +d.accid; haptic('light'); renderSheet(); return; }
    if (d.tx) {
      const tx = S.home.recent.find((x) => x.id === +d.tx);
      dialog(`<div class="grab"></div><h2 style="margin:4px 0 0;font-size:18px">Удалить запись?</h2>
        <div class="muted">${esc(tx.note || tx.category)} · ${esc((tx.sign < 0 ? '−' : '+') + money(tx.amount, tx.currency))}</div>
        <div class="row"><button class="btn2 press" style="flex:1" data-act="close-sheet">Оставить</button>
        <button class="btn2 press" style="flex:1;background:var(--down);color:#fff" data-del="${tx.id}">${icon('trash', 16, '#fff')} Удалить</button></div>`);
      return;
    }
    if (d.del) {
      try { await api('/api/transactions/' + d.del, { method: 'DELETE' }); closeSheet(); toast('Удалено', ''); S.stats = {}; await loadHome(); } catch (err) { showErr(err); }
      return;
    }
    if (d.editAcc) {
      const a = S.home.accounts.find((x) => x.id === +d.editAcc);
      dialog(`<div class="grab"></div><h2 style="margin:4px 0 0;font-size:18px">Счёт «${esc(a.name)}»</h2>
        <label class="field">Название<input id="acc-name" value="${esc(a.name)}" maxlength="40"></label>
        <label class="field">Остаток сейчас, ${a.currency}<input id="acc-bal" inputmode="decimal" value="${String(Math.round(a.balance * 100) / 100).replace('.', ',')}"></label>
        <div class="muted" style="font-size:12.5px">Если остаток не совпадает с банком — впишите настоящий. Разница запишется как корректировка и не попадёт в траты.</div>
        <button class="cta press" data-save-acc="${a.id}">Сохранить</button>`);
      return;
    }
    if (d.saveAcc) {
      const name = $('#acc-name').value, bal = $('#acc-bal').value.replace(/\s/g, '').replace(',', '.');
      try { await api('/api/accounts/' + d.saveAcc, { method: 'PATCH', body: JSON.stringify({ name, balance: parseFloat(bal) }) }); closeSheet(); toast('Сохранено', ''); await loadHome(); renderMore(); } catch (err) { showErr(err); }
      return;
    }
    if (d.act === 'setup') {
      const rows = S.home.accounts.map((a) => `<label class="field">${esc(a.name)}, ${a.currency === 'RUB' ? '₽' : a.currency}
        <input data-setup="${a.id}" inputmode="decimal" placeholder="0"></label>`).join('');
      dialog(`<div class="grab"></div><h2 style="margin:4px 0 0;font-size:18px">Сколько денег сейчас?</h2>
        <div class="muted" style="font-size:13px">Впишите остатки — потом их можно поправить во вкладке «Ещё». Пустое поле — 0.</div>
        ${rows}<button class="cta press" data-act="save-setup">Готово</button>`);
      return;
    }
    if (d.act === 'save-setup') {
      try {
        for (const inp of document.querySelectorAll('[data-setup]')) {
          const v = parseFloat((inp.value || '').replace(/\s/g, '').replace(',', '.'));
          if (v) await api('/api/accounts/' + inp.dataset.setup, { method: 'PATCH', body: JSON.stringify({ balance: v }) });
        }
        closeSheet(); haptic('ok'); toast('Готово', 'Остатки сохранены'); S.stats = {}; S.first = true; await loadHome();
      } catch (err) { showErr(err); }
      return;
    }
    switch (d.act) {
      case 'hide': S.hidden = !S.hidden; document.querySelectorAll('.blur-t').forEach((n) => n.classList.toggle('blurred', S.hidden)); haptic('light'); break;
      case 'next-card': switchCard((S.acc + 1) % S.home.accounts.length); break;
      case 'close-sheet': closeSheet(); break;
      case 'save': save(); break;
      case 'fx-swap': S.fx.toRub = !S.fx.toRub; haptic('light'); renderRates(); break;
      case 'save-limit': {
        const v = parseFloat(($('#limit').value || '0').replace(/\s/g, '').replace(',', '.')) || 0;
        try { await api('/api/settings', { method: 'PATCH', body: JSON.stringify({ limit: v }) }); toast('Лимит сохранён', v ? rub(v) + ' в месяц' : 'без лимита'); S.stats = {}; await loadHome(); renderMore(); } catch (err) { showErr(err); }
        break;
      }
      case 'copy-key':
        try { await navigator.clipboard.writeText(S.settings.key); toast('Скопировано', 'Вставьте ключ в команду iPhone'); } catch (err) { toast('Не получилось скопировать', 'Выделите ключ и скопируйте вручную'); }
        break;
      case 'rotate-key':
        try { const r = await api('/api/settings', { method: 'PATCH', body: JSON.stringify({ rotate_key: true }) }); S.settings.key = r.key; renderMore(); toast('Новый ключ готов', 'Обновите его в команде iPhone'); } catch (err) { showErr(err); }
        break;
      case 'add-acc':
        dialog(`<div class="grab"></div><h2 style="margin:4px 0 0;font-size:18px">Новый счёт</h2>
          <label class="field">Название<input id="new-acc" maxlength="40" placeholder="Например, Сбер"></label>
          <div class="seg" id="new-kind"><button class="on" style="flex:1" data-kind="card">Карта</button><button style="flex:1" data-kind="cash">Наличные</button><button style="flex:1" data-kind="crypto">Крипто</button></div>
          <button class="cta press" data-act="create-acc">Добавить</button>`);
        break;
      case 'create-acc': {
        const kind = ($('#new-kind .on') || {}).dataset ? $('#new-kind .on').dataset.kind : 'card';
        try { await api('/api/accounts', { method: 'POST', body: JSON.stringify({ name: $('#new-acc').value, kind, currency: kind === 'crypto' ? 'USDT' : 'RUB' }) }); closeSheet(); await loadHome(); renderMore(); } catch (err) { toast('Не получилось', err.message); }
        break;
      }
      default: break;
    }
    if (d.kind) { document.querySelectorAll('#new-kind button').forEach((b) => b.classList.toggle('on', b === t)); }
  });
  document.addEventListener('input', (e) => {
    if (e.target.id === 'note' && A) A.note = e.target.value;
    if (e.target.id === 'fx-amt') {
      S.fx.amt = e.target.value.replace(/[^0-9.,]/g, '').slice(0, 12);
      e.target.style.width = fxWidth(S.fx.amt);
      const cur = S.rates.find((x) => x.code === S.fx.code);
      const v = parseFloat(S.fx.amt.replace(',', '.')) || 0;
      const res = S.fx.toRub ? v * cur.rate : v / cur.rate;
      $('#fx-res').textContent = '= ' + (S.fx.toRub ? fmt2(res) : fmt(res, cur.code === 'BTC' ? 8 : 2));
    }
  });

  // ---------------------------------------------------------------- старт
  // ---------------------------------------------------------------- заставка
  const splashStart = Date.now();
  let splashSeen = false;
  try { splashSeen = sessionStorage.getItem('delta_splash') === '1'; sessionStorage.setItem('delta_splash', '1'); } catch (e) { splashSeen = false; }
  if (splashSeen || reduce) { const sp = $('#splash'); if (sp) sp.remove(); }
  function hideSplash() {
    const sp = $('#splash');
    if (!sp) return;
    const wait = Math.max(0, 1700 - (Date.now() - splashStart));
    setTimeout(() => { sp.classList.add('out'); setTimeout(() => sp.remove(), 600); }, wait);
  }

  async function start() {
    if (tg) { tg.ready(); tg.expand(); try { tg.BackButton.onClick(closeSheet); } catch (e) { /* старый клиент */ } try { tg.onEvent('themeChanged', () => { applyTheme(); render(); }); } catch (e) { /* нет */ } }
    applyTheme();
    renderTabs();
    renderHome();
    try { await login(); } catch (e) { hideSplash(); fatal(e.message); return; }
    if (!(tg && tg.initData) && !key) { hideSplash(); fatal('Нужен вход'); return; }
    try {
      await Promise.all([loadHome(), loadRates().catch(() => null)]);
    } catch (e) { hideSplash(); showErr(e); return; }
    hideSplash();
    if (params.get('add') === 'exp' || params.get('add') === 'inc') openAdd(params.get('add'));
    const tab = params.get('tab');
    if (tab && ['stats', 'rates', 'more'].includes(tab)) { S.tab = tab; render(); }
  }
  start();
})();
