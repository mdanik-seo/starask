/* StarAsk review tool: builds a Google review link, QR code, and a printable review card.
   Needs assets/qrcode.js (qrcode-generator, MIT, global `qrcode`) loaded first. Mount with StarAsk.mount(rootElement, {focus:'link'|'qr'|'card'}). */
(function () {
  'use strict';

  var CARD_W = 1200, CARD_H = 1800; // 4x6 in at 300 dpi
  var THEMES = {
    sunny: { bg: '#ffc531', ink: '#1d1b3a', sub: '#4a3f1c', panel: '#ffffff', star: '#1d1b3a' },
    ink:   { bg: '#1d1b3a', ink: '#fffaf0', sub: '#c9c5e0', panel: '#ffffff', star: '#ffc531' },
    paper: { bg: '#fffaf0', ink: '#1d1b3a', sub: '#5b5875', panel: '#ffffff', star: '#ff6b4a' }
  };

  function reviewUrl(placeId) {
    return 'https://search.google.com/local/writereview?placeid=' + encodeURIComponent(placeId);
  }

  function validPlaceId(id) {
    return typeof id === 'string' && id.length >= 10 && !/\s/.test(id) && /^[A-Za-z0-9_-]+$/.test(id);
  }

  function messageText(name, url) {
    var who = name ? name : 'us';
    return 'Hi! Thanks for choosing ' + who + '. If you have a minute, a quick Google review helps a small business like ours a lot: ' + url;
  }

  // Draws a QR code onto a new canvas using qrcode-generator (assets/qrcode.js, global `qrcode`).
  function makeQrCanvas(text, size) {
    if (typeof window.qrcode !== 'function') return null;
    var qr = window.qrcode(0, 'M');
    qr.addData(text);
    qr.make();
    var n = qr.getModuleCount(), quiet = 4, cells = n + quiet * 2;
    var scale = Math.max(1, Math.floor(size / cells));
    var c = document.createElement('canvas');
    c.width = c.height = cells * scale;
    var ctx = c.getContext('2d');
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, c.width, c.height);
    ctx.fillStyle = '#000000';
    for (var r = 0; r < n; r++) {
      for (var col = 0; col < n; col++) {
        if (qr.isDark(r, col)) ctx.fillRect((col + quiet) * scale, (r + quiet) * scale, scale, scale);
      }
    }
    return c;
  }

  function drawStars(ctx, cx, cy, r, color, count) {
    var gap = r * 2.5;
    var startX = cx - gap * (count - 1) / 2;
    ctx.fillStyle = color;
    for (var s = 0; s < count; s++) {
      var x = startX + s * gap;
      ctx.beginPath();
      for (var i = 0; i < 10; i++) {
        var rad = i % 2 === 0 ? r : r * 0.45;
        var a = -Math.PI / 2 + i * Math.PI / 5;
        ctx.lineTo(x + rad * Math.cos(a), cy + rad * Math.sin(a));
      }
      ctx.closePath();
      ctx.fill();
    }
  }

  function wrapText(ctx, text, maxW) {
    var words = text.split(' '), lines = [], line = '';
    for (var i = 0; i < words.length; i++) {
      var test = line ? line + ' ' + words[i] : words[i];
      if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = words[i]; }
      else { line = test; }
    }
    if (line) lines.push(line);
    return lines;
  }

  function drawCard(canvas, opts) {
    var t = THEMES[opts.theme] || THEMES.sunny;
    canvas.width = CARD_W; canvas.height = CARD_H;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = t.bg; ctx.fillRect(0, 0, CARD_W, CARD_H);
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';

    // business name
    var name = (opts.name || 'Your Business').trim();
    var size = 92;
    ctx.font = '700 ' + size + 'px "Unbounded", "Arial Black", sans-serif';
    while (ctx.measureText(name).width > CARD_W - 160 && size > 52) {
      size -= 4;
      ctx.font = '700 ' + size + 'px "Unbounded", "Arial Black", sans-serif';
    }
    var lines = wrapText(ctx, name, CARD_W - 160).slice(0, 2);

    // vertical layout: measure the whole block, then center it on the card
    var qrSize = 700, pad = 40, panel = qrSize + pad * 2;
    var nameH = lines.length * size * 1.1;
    var blockH = nameH + 70 + 130 + 70 + 60 + panel + 90;
    var y = (CARD_H - blockH) / 2 + size * 0.85;

    ctx.fillStyle = t.ink;
    lines.forEach(function (l) { ctx.fillText(l, CARD_W / 2, y); y += size * 1.1; });
    y += 70 - size * 0.85 * 0.4;

    drawStars(ctx, CARD_W / 2, y, 40, t.star, 5);
    y += 130;

    ctx.fillStyle = t.ink;
    ctx.font = '600 68px "Unbounded", "Arial Black", sans-serif';
    ctx.fillText(opts.headline || 'Loved your visit?', CARD_W / 2, y);
    y += 70;
    ctx.fillStyle = t.sub;
    ctx.font = '400 46px "Figtree", "Segoe UI", sans-serif';
    ctx.fillText('Scan to leave us a Google review', CARD_W / 2, y);
    y += 60;

    var px = (CARD_W - panel) / 2;
    ctx.fillStyle = t.panel;
    roundRect(ctx, px, y, panel, panel, 36); ctx.fill();
    var qr = makeQrCanvas(opts.url, qrSize);
    if (qr) ctx.drawImage(qr, px + pad, y + pad, qrSize, qrSize);
    y += panel + 80;

    ctx.fillStyle = t.sub;
    ctx.font = '400 40px "Figtree", "Segoe UI", sans-serif';
    ctx.fillText('Point your phone camera at the code', CARD_W / 2, y);
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function copyText(text, fallbackEl, statusEl, label) {
    function fallback() {
      var r = document.createRange(); r.selectNodeContents(fallbackEl);
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      statusEl.textContent = 'Text selected. Press Ctrl+C (or ⌘+C) to copy.';
    }
    try {
      navigator.clipboard.writeText(text).then(function () { statusEl.textContent = label + ' copied.'; }, fallback);
    } catch (e) { fallback(); }
  }

  function download(href, filename) {
    var a = document.createElement('a');
    a.href = href; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
  }

  // ---- Business name search (Google Places Autocomplete) ----
  // Turns on only when assets/config.js sets a Maps API key. Without a key the Place ID box is used.
  // Cost note: each lookup is one Autocomplete Request (10,000 free per month on Google's pricing);
  // typing is debounced and needs 3+ characters, so a typical search uses a handful of requests.
  var mapsPromise = null;
  function loadPlaces(key) {
    if (mapsPromise) return mapsPromise;
    mapsPromise = new Promise(function (resolve, reject) {
      if (window.google && window.google.maps && window.google.maps.importLibrary) {
        window.google.maps.importLibrary('places').then(resolve, reject); return;
      }
      var cb = '__staraskMapsReady';
      window[cb] = function () { window.google.maps.importLibrary('places').then(resolve, reject); };
      var s = document.createElement('script');
      s.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(key) +
              '&v=weekly&loading=async&libraries=places&callback=' + cb;
      s.async = true;
      s.onerror = function () { reject(new Error('Maps could not load')); };
      document.head.appendChild(s);
    });
    return mapsPromise;
  }

  function setupSearch(root, onPick) {
    var cfg = window.STARASK_CONFIG || {};
    if (!cfg.mapsApiKey) return;
    var box = root.querySelector('[data-sa="search"]');
    var input = root.querySelector('[data-sa="search-input"]');
    var list = root.querySelector('[data-sa="results"]');
    var picked = root.querySelector('[data-sa="picked"]');
    var manual = root.querySelector('[data-sa="manual"]');

    loadPlaces(cfg.mapsApiKey).then(function (places) {
      box.hidden = false;
      manual.hidden = true;
      var toggle = document.createElement('button');
      toggle.type = 'button'; toggle.className = 'linkish';
      toggle.textContent = 'Can’t find it? Enter a Place ID instead';
      toggle.addEventListener('click', function () { manual.hidden = false; toggle.hidden = true; });
      box.appendChild(toggle);

      var token = new places.AutocompleteSessionToken();
      var timer = null, seq = 0, items = [], active = -1;

      function close() { list.hidden = true; input.setAttribute('aria-expanded', 'false'); active = -1; }
      function show(sugs) {
        list.innerHTML = ''; items = sugs;
        if (!sugs.length) {
          var li = document.createElement('li'); li.className = 'empty';
          li.textContent = 'No matches. Try adding the city.'; list.appendChild(li);
        }
        sugs.forEach(function (s, i) {
          var li = document.createElement('li');
          li.setAttribute('role', 'option'); li.id = 'sa-opt-' + i;
          var main = document.createElement('strong'); main.textContent = s.main;
          var sub = document.createElement('span'); sub.textContent = s.sub;
          li.appendChild(main); li.appendChild(sub);
          li.addEventListener('mousedown', function (e) { e.preventDefault(); choose(i); });
          list.appendChild(li);
        });
        list.hidden = false; input.setAttribute('aria-expanded', 'true');
      }
      function highlight(i) {
        var lis = list.querySelectorAll('[role=option]');
        lis.forEach(function (li, j) { li.setAttribute('aria-selected', String(j === i)); });
        active = i;
        if (lis[i]) input.setAttribute('aria-activedescendant', lis[i].id);
      }
      function choose(i) {
        var s = items[i]; if (!s) return;
        close();
        input.value = s.main + (s.sub ? ', ' + s.sub : '');
        picked.hidden = false; picked.textContent = 'Selected: ' + s.main;
        token = new places.AutocompleteSessionToken(); // a pick ends the session
        onPick(s.placeId, s.main);
      }
      function query(text) {
        var my = ++seq;
        places.AutocompleteSuggestion.fetchAutocompleteSuggestions({ input: text, sessionToken: token, language: 'en-US' })
          .then(function (res) {
            if (my !== seq) return; // a newer search is running
            var out = [];
            (res.suggestions || []).forEach(function (sg) {
              var p = sg.placePrediction; if (!p) return;
              out.push({
                placeId: p.placeId,
                main: p.mainText ? p.mainText.text : String(p.text),
                sub: p.secondaryText ? p.secondaryText.text : ''
              });
            });
            show(out.slice(0, 6));
          })
          .catch(function () { if (my === seq) { close(); manual.hidden = false; } });
      }
      input.addEventListener('input', function () {
        clearTimeout(timer);
        var v = input.value.trim();
        if (v.length < 3) { close(); return; }
        timer = setTimeout(function () { query(v); }, 300);
      });
      input.addEventListener('keydown', function (e) {
        if (list.hidden) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); highlight(Math.min(active + 1, items.length - 1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); highlight(Math.max(active - 1, 0)); }
        else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); choose(active); }
        else if (e.key === 'Escape') { close(); }
      });
      input.addEventListener('blur', function () { setTimeout(close, 120); });
    }).catch(function () { /* keep the Place ID box */ });
  }

  function mount(root, options) {
    options = options || {};
    var $ = function (sel) { return root.querySelector(sel); };
    var nameIn = $('[data-sa="name"]'), idIn = $('[data-sa="placeid"]');
    var err = $('[data-sa="error"]'), out = $('[data-sa="output"]');
    var linkEl = $('[data-sa="link"]'), msgEl = $('[data-sa="message"]'), status = $('[data-sa="status"]');
    var canvas = $('[data-sa="card"]');
    var theme = 'sunny', current = '';

    function render() {
      var id = (idIn.value || '').trim();
      if (!validPlaceId(id)) {
        err.textContent = 'That doesn’t look like a Place ID. It’s one word with no spaces, and usually starts with “ChIJ”.';
        err.hidden = false; out.hidden = true; return;
      }
      err.hidden = true; out.hidden = false; status.textContent = '';
      current = reviewUrl(id);
      linkEl.textContent = current;
      msgEl.textContent = messageText((nameIn.value || '').trim(), current);
      drawCard(canvas, { url: current, name: nameIn.value, theme: theme });
      document.dispatchEvent(new CustomEvent('starask:link', { detail: { url: current, name: (nameIn.value || '').trim() } }));
    }

    $('[data-sa="go"]').addEventListener('click', render);
    [nameIn, idIn].forEach(function (el) {
      el.addEventListener('keydown', function (e) { if (e.key === 'Enter') render(); });
    });
    nameIn.addEventListener('input', function () { if (current) render(); });

    $('[data-sa="copy-link"]').addEventListener('click', function () { copyText(current, linkEl, status, 'Link'); });
    $('[data-sa="copy-msg"]').addEventListener('click', function () { copyText(msgEl.textContent, msgEl, status, 'Message'); });
    $('[data-sa="dl-card"]').addEventListener('click', function () {
      download(canvas.toDataURL('image/png'), 'review-card.png');
      status.textContent = 'Card downloaded.';
    });
    $('[data-sa="dl-qr"]').addEventListener('click', function () {
      var qr = makeQrCanvas(current, 1000);
      if (qr) { download(qr.toDataURL('image/png'), 'google-review-qr-code.png'); status.textContent = 'QR code downloaded.'; }
    });
    $('[data-sa="print"]').addEventListener('click', function () { window.print(); });

    root.querySelectorAll('[data-sa-theme]').forEach(function (b) {
      b.addEventListener('click', function () {
        theme = b.getAttribute('data-sa-theme');
        root.querySelectorAll('[data-sa-theme]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        if (current) render();
      });
    });

    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(render); } else { render(); }
    setupSearch(root, function (placeId, name) {
      idIn.value = placeId;
      nameIn.value = name;
      render();
    });
    if (options.focus === 'card') canvas.scrollIntoView({ block: 'nearest' });
  }

  window.StarAsk = { mount: mount, reviewUrl: reviewUrl, validPlaceId: validPlaceId };
})();
