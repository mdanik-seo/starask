/* ReviewTent places: business search and profile lookup.
   Live mode: uses Google Maps Platform when assets/config.js has mapsApiKey.
   Demo mode: add ?demo=1 to any page URL to try search and the audit with made-up sample businesses (no key, no cost).
   API: StarAskPlaces.mode() -> 'live' | 'demo' | 'off'
        StarAskPlaces.ready() -> Promise<provider> with suggest(text), details(placeId), newSession()
        StarAskPlaces.attachSearch({box, input, list, picked, onPick, onFail}) wires a search combobox. */
(function () {
  'use strict';

  var DEMO = /[?&]demo=1\b/.test(location.search);

  function mode() {
    if (DEMO) return 'demo';
    var cfg = window.STARASK_CONFIG || {};
    return cfg.mapsApiKey ? 'live' : 'off';
  }

  // ---------- demo data (fictional businesses) ----------
  var DAY = 864e5;
  var SAMPLES = [
    { placeId: 'ChIJDemo_HarborStreetCoffee01', name: 'Harbor Street Coffee', address: '214 Harbor St, Baltimore, MD 21230',
      phone: '(410) 555-0142', website: 'https://example.com/harbor-street-coffee', status: 'OPERATIONAL',
      hours: ['Monday: 7:00 AM – 5:00 PM', 'Tuesday: 7:00 AM – 5:00 PM', 'Wednesday: 7:00 AM – 5:00 PM', 'Thursday: 7:00 AM – 5:00 PM', 'Friday: 7:00 AM – 6:00 PM', 'Saturday: 8:00 AM – 6:00 PM', 'Sunday: 8:00 AM – 3:00 PM'],
      rating: 4.4, reviewCount: 38, photoCount: 6, category: 'Coffee shop', typeCount: 4, latestReviewDaysAgo: 52 },
    { placeId: 'ChIJDemo_MapleLaneDental0002', name: 'Maple Lane Dental', address: '88 Maple Ln, Austin, TX 78704',
      phone: '(512) 555-0199', website: 'https://example.com/maple-lane-dental', status: 'OPERATIONAL',
      hours: ['Monday: 8:00 AM – 5:00 PM', 'Tuesday: 8:00 AM – 5:00 PM', 'Wednesday: 8:00 AM – 5:00 PM', 'Thursday: 8:00 AM – 5:00 PM', 'Friday: 8:00 AM – 2:00 PM', 'Saturday: Closed', 'Sunday: Closed'],
      rating: 4.8, reviewCount: 212, photoCount: 10, category: 'Dentist', typeCount: 5, latestReviewDaysAgo: 4 },
    { placeId: 'ChIJDemo_QuickFixPlumbing003', name: 'Quick Fix Plumbing', address: 'Serves Denver, CO',
      phone: '', website: '', status: 'OPERATIONAL', hours: [],
      rating: 3.9, reviewCount: 9, photoCount: 2, category: 'Plumber', typeCount: 2, latestReviewDaysAgo: 160 }
  ];

  function demoProvider() {
    return {
      newSession: function () {},
      suggest: function (text) {
        var q = text.toLowerCase();
        var hits = SAMPLES.filter(function (s) { return s.name.toLowerCase().indexOf(q) !== -1; });
        if (!hits.length) hits = SAMPLES; // demo: always show something to pick
        return Promise.resolve(hits.map(function (s) {
          return { placeId: s.placeId, main: s.name, sub: s.address + ' · sample' };
        }));
      },
      details: function (placeId) {
        var s = SAMPLES.filter(function (x) { return x.placeId === placeId; })[0];
        if (!s) return Promise.reject(new Error('Not found'));
        return new Promise(function (res) {
          setTimeout(function () {
            res({
              placeId: s.placeId, name: s.name, address: s.address, phone: s.phone, website: s.website,
              status: s.status, hours: s.hours.slice(), rating: s.rating, reviewCount: s.reviewCount,
              photoCount: s.photoCount, category: s.category, typeCount: s.typeCount,
              latestReview: new Date(Date.now() - s.latestReviewDaysAgo * DAY), mapsUrl: '', demo: true
            });
          }, 450);
        });
      }
    };
  }

  // ---------- live (Google Maps Platform) ----------
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

  // Fields for the audit. Rating, phone, website and hours are billed as Place Details Enterprise;
  // reviews adds the Atmosphere tier. Each audit is one Place Details call.
  var AUDIT_FIELDS = ['id', 'displayName', 'formattedAddress', 'nationalPhoneNumber', 'websiteURI', 'businessStatus',
    'regularOpeningHours', 'rating', 'userRatingCount', 'photos', 'primaryTypeDisplayName', 'types', 'reviews', 'googleMapsURI'];

  function liveProvider(places) {
    var token = new places.AutocompleteSessionToken();
    return {
      newSession: function () { token = new places.AutocompleteSessionToken(); },
      suggest: function (text) {
        return places.AutocompleteSuggestion.fetchAutocompleteSuggestions({ input: text, sessionToken: token, language: 'en-US' })
          .then(function (res) {
            var out = [];
            (res.suggestions || []).forEach(function (sg) {
              var p = sg.placePrediction; if (!p) return;
              out.push({ placeId: p.placeId, main: p.mainText ? p.mainText.text : String(p.text), sub: p.secondaryText ? p.secondaryText.text : '' });
            });
            return out;
          });
      },
      details: function (placeId) {
        var place = new places.Place({ id: placeId, requestedLanguage: 'en' });
        return place.fetchFields({ fields: AUDIT_FIELDS }).then(function () {
          var latest = null;
          (place.reviews || []).forEach(function (r) {
            var t = r.publishTime ? new Date(r.publishTime) : null;
            if (t && !isNaN(t) && (!latest || t > latest)) latest = t;
          });
          return {
            placeId: place.id, name: place.displayName || '', address: place.formattedAddress || '',
            phone: place.nationalPhoneNumber || '', website: place.websiteURI || '', status: place.businessStatus || '',
            hours: (place.regularOpeningHours && place.regularOpeningHours.weekdayDescriptions) || [],
            rating: place.rating == null ? null : place.rating, reviewCount: place.userRatingCount || 0,
            photoCount: (place.photos || []).length, category: place.primaryTypeDisplayName || '',
            typeCount: (place.types || []).filter(function (t) { return t !== 'point_of_interest' && t !== 'establishment'; }).length,
            latestReview: latest, mapsUrl: place.googleMapsURI || '', demo: false
          };
        });
      }
    };
  }

  var providerPromise = null;
  function ready() {
    if (providerPromise) return providerPromise;
    var m = mode();
    if (m === 'demo') providerPromise = Promise.resolve(demoProvider());
    else if (m === 'live') providerPromise = loadPlaces(window.STARASK_CONFIG.mapsApiKey).then(liveProvider);
    else providerPromise = Promise.reject(new Error('No Maps key'));
    return providerPromise;
  }

  // ---------- search combobox ----------
  function attachSearch(o) {
    return ready().then(function (prov) {
      var input = o.input, list = o.list, picked = o.picked;
      o.box.hidden = false;
      var timer = null, seq = 0, items = [], active = -1;

      function close() { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1; }
      function show(sugs) {
        list.innerHTML = ''; items = sugs;
        if (!sugs.length) {
          var li = document.createElement('li'); li.className = 'empty';
          li.textContent = 'No matches. Try adding the city.'; list.appendChild(li);
        }
        sugs.forEach(function (s, i) {
          var li = document.createElement('li');
          li.setAttribute('role', 'option'); li.id = list.id + '-opt-' + i;
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
        input.value = s.main + (s.sub ? ', ' + s.sub.replace(/ · sample$/, '') : '');
        if (picked) { picked.hidden = false; picked.textContent = 'Selected: ' + s.main; }
        prov.newSession(); // a pick ends the billing session
        o.onPick(s.placeId, s.main);
      }
      function query(text) {
        var my = ++seq;
        prov.suggest(text).then(function (out) { if (my === seq) show(out.slice(0, 6)); })
          .catch(function () { if (my === seq) { close(); if (o.onFail) o.onFail(); } });
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
      return prov;
    });
  }

  window.StarAskPlaces = { mode: mode, ready: ready, attachSearch: attachSearch, samples: SAMPLES };
})();
