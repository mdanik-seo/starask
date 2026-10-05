/* StarAsk Google Business Profile audit.
   Needs assets/places.js. Scores a profile out of 100 from public Google data and suggests fixes.
   Mount with StarAskAudit.mount(rootElement). */
(function () {
  'use strict';

  var DAY = 864e5;

  // weight = points when the check passes; a warning earns half.
  function runChecks(p) {
    var days = p.latestReview ? Math.floor((Date.now() - p.latestReview.getTime()) / DAY) : null;
    var rl = { href: 'review-link-generator/', text: 'Get your review link' };
    var card = { href: 'review-card/', text: 'Print a QR card' };
    var tpl = { href: 'review-request-templates/', text: 'Use a request template' };
    var ck = { href: 'google-business-profile-checklist/', text: 'Open the checklist' };
    var c = [];

    c.push({ label: 'Profile is marked open', weight: 10,
      state: p.status === 'OPERATIONAL' ? 'good' : (p.status === 'CLOSED_TEMPORARILY' || p.status === 'CLOSED_PERMANENTLY') ? 'bad' : 'warn',
      found: p.status === 'OPERATIONAL' ? 'Open' : p.status === 'CLOSED_TEMPORARILY' ? 'Temporarily closed' : p.status === 'CLOSED_PERMANENTLY' ? 'Permanently closed' : 'Not shown',
      fix: 'If you are open, update the status in your Business Profile right away. A closed label stops most customers from calling.' });

    var n = p.reviewCount || 0;
    c.push({ label: 'Number of reviews', weight: 20,
      state: n >= 100 ? 'good' : n >= 25 ? 'warn' : 'bad', found: n + (n === 1 ? ' review' : ' reviews'),
      fix: 'Ask every customer with a direct link. Aim to match the review count of the top three businesses near you.', action: rl });

    c.push({ label: 'Star rating', weight: 15,
      state: p.rating == null ? 'bad' : p.rating >= 4.5 ? 'good' : p.rating >= 4.0 ? 'warn' : 'bad',
      found: p.rating == null ? 'No rating yet' : p.rating.toFixed(1) + ' ★',
      fix: 'More reviews from ordinary happy customers lift an average quickly. Reply politely to low reviews and say how you fixed the problem.', action: tpl });

    c.push({ label: 'Recent reviews', weight: 15,
      state: days == null ? 'bad' : days <= 30 ? 'good' : days <= 90 ? 'warn' : 'bad',
      found: days == null ? 'None found' : days === 0 ? 'Newest is from today' : 'Newest is ' + days + (days === 1 ? ' day' : ' days') + ' old',
      fix: 'New reviews every month show people and Google that you are active. A QR card at the counter keeps them coming without extra work.', action: card });

    c.push({ label: 'Photos', weight: 10,
      state: p.photoCount >= 10 ? 'good' : p.photoCount >= 5 ? 'warn' : 'bad',
      found: p.photoCount >= 10 ? '10 or more' : p.photoCount + (p.photoCount === 1 ? ' photo' : ' photos'),
      fix: 'Add at least 10 photos: outside, inside, team, and your work or products. Add new ones every month.', action: ck });

    c.push({ label: 'Opening hours', weight: 10, state: p.hours.length ? 'good' : 'bad',
      found: p.hours.length ? 'Set' : 'Missing', fix: 'Add regular hours, and set holiday hours before each holiday.', action: ck });

    c.push({ label: 'Phone number', weight: 7, state: p.phone ? 'good' : 'bad',
      found: p.phone || 'Missing', fix: 'Add a local number that is answered during open hours.', action: ck });

    c.push({ label: 'Website link', weight: 8, state: p.website ? 'good' : 'bad',
      found: p.website ? shortUrl(p.website) : 'Missing', fix: 'Link your website, or the page for this location if you have several.', action: ck });

    c.push({ label: 'Categories', weight: 5, state: p.typeCount >= 3 ? 'good' : 'warn',
      found: p.category ? p.category + (p.typeCount > 1 ? ' + ' + (p.typeCount - 1) + ' more' : '') : 'Not shown',
      fix: 'Pick the most specific primary category, then add secondary categories that truly apply.', action: ck });

    var score = 0;
    c.forEach(function (x) { score += x.state === 'good' ? x.weight : x.state === 'warn' ? x.weight / 2 : 0; });
    return { checks: c, score: Math.round(score) };
  }

  function shortUrl(u) { return u.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '').slice(0, 40); }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  var STATE_TEXT = { good: 'Good', warn: 'Improve', bad: 'Fix' };

  function render(out, p, rel) {
    var r = runChecks(p);
    var grade = r.score >= 80 ? 'Strong profile' : r.score >= 50 ? 'Needs work' : 'Weak profile';
    var gradeCls = r.score >= 80 ? 'good' : r.score >= 50 ? 'warn' : 'bad';
    out.innerHTML = '';

    var head = el('div', 'panel audit-head');
    var ring = el('div', 'score ' + gradeCls);
    ring.style.setProperty('--pct', r.score);
    ring.appendChild(el('strong', null, String(r.score)));
    ring.appendChild(el('span', null, 'out of 100'));
    var info = el('div', 'audit-info');
    info.appendChild(el('span', 'pill ' + gradeCls, grade));
    info.appendChild(el('h3', null, p.name));
    if (p.address) info.appendChild(el('p', 'muted', p.address));
    var fixes = r.checks.filter(function (x) { return x.state !== 'good'; }).length;
    info.appendChild(el('p', null, fixes ? fixes + (fixes === 1 ? ' thing' : ' things') + ' to improve, biggest wins first.' : 'Everything we can check looks good. Keep the reviews coming.'));
    head.appendChild(ring); head.appendChild(info);
    out.appendChild(head);

    // biggest point losses first
    var order = r.checks.slice().sort(function (a, b) {
      var la = a.state === 'good' ? 0 : a.state === 'warn' ? a.weight / 2 : a.weight;
      var lb = b.state === 'good' ? 0 : b.state === 'warn' ? b.weight / 2 : b.weight;
      return lb - la;
    });
    var list = el('ul', 'checks');
    order.forEach(function (x) {
      var li = el('li', 'check ' + x.state);
      var top = el('div', 'check-top');
      top.appendChild(el('span', 'pill ' + x.state, STATE_TEXT[x.state]));
      top.appendChild(el('strong', null, x.label));
      top.appendChild(el('span', 'found', x.found));
      li.appendChild(top);
      if (x.state !== 'good') {
        li.appendChild(el('p', 'muted', x.fix));
        if (x.action) {
          var a = el('a', null, x.action.text);
          a.href = rel + x.action.href + (x.action.href === 'review-link-generator/' || x.action.href === 'review-card/' ? linkParams(p) : '');
          li.appendChild(a);
        }
      }
      list.appendChild(li);
    });
    out.appendChild(list);

    var cta = el('div', 'panel audit-cta');
    cta.appendChild(el('h3', null, 'Start with more reviews'));
    cta.appendChild(el('p', null, 'Reviews carry the most points. Make a free review link, QR code, and printable card for ' + p.name + ' in one click.'));
    var btn = el('a', 'btn', 'Make my review link');
    btn.href = rel + 'review-link-generator/' + linkParams(p);
    cta.appendChild(btn);
    out.appendChild(cta);

    out.appendChild(el('p', 'hint', p.demo
      ? 'Sample data: this business is made up to show how the audit works.'
      : 'Business data from Google. Checked ' + new Date().toLocaleDateString() + '. Description, posts, and replies to reviews are not public, so check those in your Business Profile.'));
    out.hidden = false;
  }

  function linkParams(p) {
    if (p.demo) return '?placeid=' + encodeURIComponent(p.placeId) + '&name=' + encodeURIComponent(p.name) + '&demo=1';
    return '?placeid=' + encodeURIComponent(p.placeId) + '&name=' + encodeURIComponent(p.name);
  }

  function mount(root) {
    var P = window.StarAskPlaces;
    var rel = root.getAttribute('data-rel') || '';
    var out = root.querySelector('[data-au="out"]');
    var status = root.querySelector('[data-au="status"]');
    var off = root.querySelector('[data-au="off"]');
    var demoNote = root.querySelector('[data-au="demo"]');
    var cache = {};

    if (!P || P.mode() === 'off') { off.hidden = false; return; }
    if (P.mode() === 'demo') demoNote.hidden = false;

    function audit(placeId) {
      status.textContent = 'Checking the profile…';
      out.hidden = true;
      var job = cache[placeId] || (cache[placeId] = P.ready().then(function (prov) { return prov.details(placeId); }));
      job.then(function (p) { status.textContent = ''; render(out, p, rel); out.scrollIntoView({ behavior: 'smooth', block: 'start' }); })
        .catch(function () { delete cache[placeId]; status.textContent = 'We couldn’t load that profile. Please try again in a moment.'; });
    }

    P.attachSearch({
      box: root.querySelector('[data-au="search"]'),
      input: root.querySelector('[data-au="input"]'),
      list: root.querySelector('[data-au="results"]'),
      picked: null,
      onPick: function (placeId) { audit(placeId); },
      onFail: function () { status.textContent = 'Search isn’t available right now. Please try again later.'; }
    }).catch(function () { off.hidden = false; });
  }

  window.StarAskAudit = { mount: mount, runChecks: runChecks };
})();
