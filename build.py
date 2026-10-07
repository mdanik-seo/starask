"""Builds StarAsk's static pages from one template.
Run:  python3 build.py   -> writes index.html and each page folder's index.html, plus sitemap.xml.
Edit page copy in PAGES below; edit shared layout in render()."""
import json, html, datetime, pathlib

SITE = "https://getstarask.com"
ROOT = pathlib.Path(__file__).parent
TODAY = datetime.date.today().isoformat()

NAV = [("/review-link-generator/", "Review link"), ("/review-qr-code/", "QR code"), ("/review-card/", "Review card"),
       ("/review-request-templates/", "Templates"), ("/google-business-profile-audit/", "Audit"),
       ("/get-more-google-reviews/", "Guide")]

# Review request templates. {name} and {link} are filled in the browser from the tool above.
TEMPLATES = [
    ("Text message after a visit", "SMS",
     "Hi {first}, thanks for coming in to {name} today! If you have a minute, a quick Google review would mean a lot to us: {link}"),
    ("Text message after a finished job", "SMS",
     "Hi {first}, it was great working on your project. If you're happy with the result, would you share a quick Google review? {link} Thank you!"),
    ("Follow-up email", "Email",
     "Subject: Thank you from {name}\n\nHi {first},\n\nThank you for choosing {name}. We hope everything went well.\n\nIf you have a minute, we'd be grateful for a quick Google review. It helps other people nearby find us, and we read every one.\n\nLeave a review: {link}\n\nThank you,\nThe {name} team"),
    ("Gentle reminder (send once, 3 to 5 days later)", "Email",
     "Subject: Quick favor?\n\nHi {first},\n\nJust a short note in case our last message got buried. If you have 30 seconds, a Google review would really help {name}:\n\n{link}\n\nNo worries if not. Thanks again for your business!"),
    ("Receipt or invoice footer", "Print",
     "Enjoyed your experience? Leave {name} a Google review: {link}"),
    ("Social media post", "Social",
     "Thank you to everyone who has visited {name} this month! If we made your day a little better, we'd love to hear about it on Google: {link}"),
]

CHECKLIST = [
    ("Basics", [
        "Business name matches your real-world signage, with no extra keywords",
        "Primary category is the most specific one that fits",
        "Up to 9 secondary categories added where they truly apply",
        "Address or service area is correct",
        "Phone number is a local number that rings during open hours",
        "Website link points to the right page (location page for multi-location businesses)",
    ]),
    ("Hours and details", [
        "Regular hours are set",
        "Holiday hours are set before each holiday",
        "Attributes are filled in (accessibility, payments, amenities)",
        "Business description uses all 750 characters and says what you do and where",
        "Opening date is set",
    ]),
    ("Photos", [
        "Logo and cover photo uploaded",
        "At least 10 photos of the interior, exterior, team, and work",
        "New photos added at least once a month",
    ]),
    ("Reviews", [
        "You have a direct review link and a QR code",
        "Every customer is asked for a review, not only the happy ones",
        "Every review gets a reply, including the negative ones",
        "No reviews are bought or offered rewards in exchange",
    ]),
    ("Activity", [
        "A Google post goes up at least once a week",
        "Products or services are listed with short descriptions",
    ]),
]


def templates_html():
    cards = []
    for i, (title, kind, body) in enumerate(TEMPLATES):
        cards.append(
            f'<div class="tpl"><div class="tpl-head"><h3>{html.escape(title)}</h3><span class="tag">{kind}</span></div>'
            f'<div class="msg" id="tpl-{i}" data-tpl="{html.escape(body, quote=True)}"></div>'
            f'<div class="row"><button type="button" class="ghost" data-copy="tpl-{i}">Copy</button></div></div>')
    return '<div class="tpls">' + "".join(cards) + '</div><p class="status" id="tpl-status" role="status"></p>'


TEMPLATES_JS = """<script>
(function(){
  var state={url:'https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID',name:'our business'};
  function fill(){document.querySelectorAll('[data-tpl]').forEach(function(el){
    el.textContent=el.getAttribute('data-tpl').split('{link}').join(state.url).split('{name}').join(state.name).split('{first}').join('[First name]');});}
  document.addEventListener('starask:link',function(e){state.url=e.detail.url;state.name=e.detail.name||'our business';fill();});
  var st=document.getElementById('tpl-status');
  document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){
    var el=document.getElementById(b.getAttribute('data-copy'));
    function sel(){var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);st.textContent='Text selected. Press Ctrl+C to copy.';}
    try{navigator.clipboard.writeText(el.textContent).then(function(){st.textContent='Template copied.';},sel);}catch(e){sel();}
  });});
  fill();
})();
</script>"""


def checklist_html():
    out, n = [], 0
    for group, items in CHECKLIST:
        lis = []
        for it in items:
            lis.append(f'<li><input type="checkbox" id="ck-{n}" data-ck><label for="ck-{n}">{html.escape(it)}</label></li>')
            n += 1
        out.append(f'<div class="ckgroup"><h3>{html.escape(group)}</h3><ul class="checklist">{"".join(lis)}</ul></div>')
    return ('<div class="ckbar panel"><strong id="ck-count">0 of %d done</strong>'
            '<div class="meter"><span id="ck-meter"></span></div></div>' % n) + "".join(out)


CHECKLIST_JS = """<script>
(function(){
  var boxes=[].slice.call(document.querySelectorAll('[data-ck]')),key='starask-checklist';
  try{var saved=JSON.parse(localStorage.getItem(key)||'[]');boxes.forEach(function(b,i){b.checked=!!saved[i];});}catch(e){}
  function update(){var d=boxes.filter(function(b){return b.checked;}).length;
    document.getElementById('ck-count').textContent=d+' of '+boxes.length+' done';
    document.getElementById('ck-meter').style.width=(100*d/boxes.length)+'%';
    try{localStorage.setItem(key,JSON.stringify(boxes.map(function(b){return b.checked;})));}catch(e){}}
  boxes.forEach(function(b){b.addEventListener('change',update);});update();
})();
</script>"""

# Hand-drawn style line icons (24px grid, 2px stroke, round joins), colored by currentColor.
ICON_PATHS = {
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "qr": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="M14 14h3v3M21 14v.01M14 21h.01M17.5 17.5V21H21"/>',
    "card": '<rect x="5" y="2.5" width="14" height="19" rx="2.5"/><path d="M12 7.2l1.2 2.4 2.6.4-1.9 1.8.5 2.6-2.4-1.3-2.4 1.3.5-2.6-1.9-1.8 2.6-.4z"/><path d="M9 18h6"/>',
    "audit": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/><circle cx="12" cy="17" r="1.2"/>',
    "templates": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 4v-4H6.5A2.5 2.5 0 0 1 4 13.5z"/><path d="M8 8h8M8 11.5h5"/>',
    "checklist": '<path d="M4 6l1.5 1.5L8 5M4 12l1.5 1.5L8 11M4 18l1.5 1.5L8 17"/><path d="M11 6.5h9M11 12.5h9M11 18.5h9"/>',
    "guide": '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H11v17H5.5A1.5 1.5 0 0 1 4 18.5z"/><path d="M20 4.5A1.5 1.5 0 0 0 18.5 3H13v17h5.5a1.5 1.5 0 0 0 1.5-1.5z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    "print": '<path d="M7 8V3h10v5"/><rect x="3" y="8" width="18" height="9" rx="2"/><path d="M7 14h10v7H7z"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
}
PAGE_ICON = {"review-qr-code/": "qr", "review-link-generator/": "link", "review-card/": "card",
             "review-request-templates/": "templates", "google-business-profile-audit/": "audit",
             "get-more-google-reviews/": "guide", "google-business-profile-checklist/": "checklist"}


def icon(name, cls="ic"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON_PATHS[name]}</svg>')


STAR = "&#9733;"

HOME_HERO = f"""
<div class="hero hero-home">
  <div class="hero-copy">
    <h1>Turn happy customers into Google reviews</h1>
    <p class="lede">Get a direct review link, a QR code, and a printable counter card for your business. Free, and it takes about a minute.</p>
    <form class="try" id="try" autocomplete="off">
      <label for="try-name">Your business name</label>
      <div class="try-row">
        <input type="text" id="try-name" maxlength="60" placeholder="Harbor Street Coffee">
        <button type="submit">Make my card</button>
      </div>
      <p class="try-note">Free. No sign-up. Works for any business on Google Maps.</p>
    </form>
  </div>
  <div class="stage" aria-hidden="true">
    <div class="stand" id="stand">
      <canvas id="hero-card" width="1200" height="1800"></canvas>
      <span class="shine"></span>
    </div>
    <div class="base"></div>
  </div>
</div>"""

HERO_JS = """<script>
(function(){
  var form=document.getElementById('try'), input=document.getElementById('try-name'), c=document.getElementById('hero-card');
  var demoUrl=StarAsk.reviewUrl('ChIJN1t_tDeuEmsRUsoyG83frY4');
  function draw(){StarAsk.drawCard(c,{url:demoUrl,name:input.value.trim()||'Harbor Street Coffee',theme:'sunny'});}
  var t=null; input.addEventListener('input',function(){clearTimeout(t);t=setTimeout(draw,60);});
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(draw);}else{draw();}
  form.addEventListener('submit',function(e){
    e.preventDefault();
    var n=document.getElementById('sa-name'); if(input.value.trim()){n.value=input.value.trim();n.dispatchEvent(new Event('input'));}
    document.getElementById('tool').scrollIntoView({behavior:'smooth',block:'start'});
    setTimeout(function(){(document.getElementById('sa-search').offsetParent?document.getElementById('sa-search'):document.getElementById('sa-placeid')).focus({preventScroll:true});},500);
  });
  var stand=document.getElementById('stand');
  if(window.matchMedia('(pointer:fine)').matches&&!window.matchMedia('(prefers-reduced-motion:reduce)').matches){
    var stage=stand.parentNode.parentNode;
    stage.addEventListener('pointermove',function(e){var r=stage.getBoundingClientRect();
      var x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
      stand.style.setProperty('--ry',(-14+x*16).toFixed(2)+'deg'); stand.style.setProperty('--rx',(6-y*10).toFixed(2)+'deg');});
    stage.addEventListener('pointerleave',function(){stand.style.removeProperty('--ry');stand.style.removeProperty('--rx');});
  }
})();
</script>"""

HOW = f"""
<section class="how">
  <h2>How it works</h2>
  <ol class="how-steps">
    <li><span class="how-ic">{icon('search')}</span><h3>Find your business</h3><p>Type your business name, or paste your Google Place ID.</p></li>
    <li><span class="how-ic">{icon('link')}</span><h3>Get your link and QR code</h3><p>One link that opens your review box, and a sharp QR code for print.</p></li>
    <li><span class="how-ic">{icon('print')}</span><h3>Share it and print it</h3><p>Text the link after each visit and put the card by the register.</p></li>
  </ol>
</section>"""

TOOL_ROWS = [("review-link-generator/", "link", "Review link generator", "One tap opens your review box."),
             ("review-qr-code/", "qr", "QR code generator", "High-resolution and print-ready."),
             ("review-card/", "card", "Printable review card", "A 4×6 in card in three colors."),
             ("review-request-templates/", "templates", "Request templates", "Texts and emails with your link in them."),
             ("google-business-profile-checklist/", "checklist", "Profile checklist", "20 checks for a complete profile."),
             ("get-more-google-reviews/", "guide", "Review guide", "9 ways to get more reviews, within Google’s rules.")]

TOOLS = (f"""
<section class="toolset">
  <h2>Everything for more reviews, in one place</h2>
  <div class="toolset-grid">
    <a class="feature" href="google-business-profile-audit/">
      <span class="score warn" style="--pct:72"><strong>72</strong><span>out of 100</span></span>
      <span class="feature-copy"><h3>Profile audit</h3><p>Score any Google Business Profile out of 100 and see which fixes matter most. Works for your own business, a competitor, or a client.</p><span class="btn">Audit a profile</span></span>
    </a>
    <ul class="tool-list">"""
    + "".join(f'<li><a href="{h}"><span class="tl-ic">{icon(i)}</span><span><strong>{t}</strong><span>{d}</span></span></a></li>' for h, i, t, d in TOOL_ROWS)
    + "</ul></div></section>")


def plan(name, price, per, note, feats, cta, featured=False):
    lis = "".join(f"<li>{icon('check')}{f}</li>" for f in feats)
    badge = '<span class="soon-tag">Coming soon</span>' if per else ""
    return (f'<div class="plan{" featured" if featured else ""}"><div class="plan-top"><h3>{name}</h3>{badge}</div>'
            f'<p class="price"><strong>{price}</strong><span>{per or "forever"}</span></p><p class="muted">{note}</p>'
            f'<ul>{lis}</ul>{cta}</div>')


PRICING = ('<section class="pricing"><h2>Pricing</h2>'
           '<p class="muted">Every tool on this site is free. Paid plans that ask for reviews automatically are coming soon.</p>'
           '<div class="plans">'
           + plan("Free", "$0", "", "For any business getting started.",
                  ["Review link and QR code", "Printable review cards", "Profile audit", "Request templates and checklist"],
                  '<a class="btn ghost" href="#tool">Start free</a>')
           + plan("Business", "$19", "/month", "For a business that wants reviews on autopilot.",
                  ["Everything in Free", "Automatic review request emails", "Alerts when a new review comes in",
                   "Your logo on review cards", "Monthly profile score report"],
                  '<span class="btn soon" aria-disabled="true">Coming soon</span>', featured=True)
           + plan("Agency", "$49", "/month", "For marketers who manage clients.",
                  ["Everything in Business", "Up to 10 client businesses", "White-label cards and reports",
                   "Audit reports to share with clients"],
                  '<span class="btn ghost soon" aria-disabled="true">Coming soon</span>')
           + '</div></section>')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800'
         '&family=Geist+Mono:wght@400;500&display=swap">')

TOOL = """
<div class="tool" id="tool">
  <div class="panel toolform">
    <div class="field search" data-sa="search" hidden>
      <label for="sa-search">Find your business</label>
      <div class="combo">
        <input type="text" id="sa-search" data-sa="search-input" placeholder="Business name and city, e.g. Joe's Pizza Austin"
               autocomplete="off" spellcheck="false" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="sa-results">
        <ul class="results" id="sa-results" data-sa="results" role="listbox" hidden></ul>
      </div>
      <p class="hint" data-sa="picked" hidden></p>
    </div>
    <div class="field">
      <label for="sa-name">Business name</label>
      <input type="text" id="sa-name" data-sa="name" value="Harbor Street Coffee" autocomplete="organization">
    </div>
    <div class="field" data-sa="manual">
      <label for="sa-placeid">Google Place ID</label>
      <input type="text" id="sa-placeid" class="mono" data-sa="placeid" value="ChIJN1t_tDeuEmsRUsoyG83frY4" autocomplete="off" spellcheck="false">
      <details class="howto">
        <summary>How do I find my Place ID?</summary>
        <ol>
          <li>Open Google&rsquo;s free <a href="https://developers.google.com/maps/documentation/javascript/examples/places-placeid-finder" target="_blank" rel="noopener">Place ID Finder</a>.</li>
          <li>Type your business name and pick it from the list.</li>
          <li>Copy the ID that appears on the map (it starts with &ldquo;ChIJ&rdquo;) and paste it here.</li>
        </ol>
      </details>
    </div>
    <div class="row"><button type="button" data-sa="go">Create my review link</button></div>
    <p class="err" data-sa="error" hidden></p>
    <div class="out" data-sa="output">
      <div class="linkbox" data-sa="link"></div>
      <div class="row">
        <button type="button" class="ghost" data-sa="copy-link">Copy link</button>
        <button type="button" class="ghost" data-sa="copy-msg">Copy text message</button>
        <button type="button" class="ghost" data-sa="dl-qr">Download QR code</button>
      </div>
      <p class="status" data-sa="status" role="status"></p>
      <div>
        <label>Ready-to-send message</label>
        <div class="msg" data-sa="message"></div>
      </div>
    </div>
  </div>
  <div class="panel cardside">
    <h3 class="no-print">Your printable review card</h3>
    <canvas data-sa="card" width="1200" height="1800" aria-label="Printable review card with QR code"></canvas>
    <div class="tabs no-print" role="group" aria-label="Card color">
      <button type="button" data-sa-theme="sunny" aria-pressed="true">Sunny</button>
      <button type="button" data-sa-theme="ink" aria-pressed="false">Ink</button>
      <button type="button" data-sa-theme="paper" aria-pressed="false">Paper</button>
    </div>
    <div class="row no-print" style="justify-content:center">
      <button type="button" data-sa="dl-card">Download card</button>
      <button type="button" class="ghost" data-sa="print">Print</button>
    </div>
    <p class="hint no-print">Prints well at 4&times;6 in. Put it by the register, on tables, or in the bag.</p>
  </div>
</div>"""

AUDIT = """
<div class="audit" id="audit" data-rel="{rel}">
  <div class="panel">
    <p class="demo-note" data-au="demo" hidden><strong>Sample mode.</strong> Search shows made-up businesses so you can see how the audit works.</p>
    <div class="field search" data-au="search" hidden>
      <label for="au-input">Find your business</label>
      <div class="combo">
        <input type="text" id="au-input" data-au="input" placeholder="Business name and city, e.g. Joe's Pizza Austin"
               autocomplete="off" spellcheck="false" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="au-results">
        <ul class="results" id="au-results" data-au="results" role="listbox" hidden></ul>
      </div>
      <p class="hint">Pick your business from the list. The audit runs right away.</p>
    </div>
    <div data-au="off" hidden>
      <h3>The live audit opens soon</h3>
      <p class="muted" style="margin-top:6px">Until then, try it on a sample business, or work through the free checklist.</p>
      <div class="row" style="margin-top:14px"><a class="btn" href="?demo=1">See a sample audit</a><a class="btn ghost" href="{rel}google-business-profile-checklist/">Open the checklist</a></div>
    </div>
    <p class="status" data-au="status" role="status"></p>
  </div>
  <div class="audit-out" data-au="out" aria-live="polite" hidden></div>
</div>"""

PAGES = [
    {
        "path": "",
        "title": "Free Google Review Link, QR Code & Card Generator | StarAsk",
        "desc": "Create a direct Google review link, a QR code, and a printable review card for your business in under a minute. Free, no sign-up.",
        "eyebrow": "Free review tools for local businesses",
        "h1": "Get more Google reviews with one link, one QR code, one card",
        "intro": "Customers who are happy rarely leave a review on their own. Give them a link that opens the review box directly, a QR code for your counter, and a card that does the asking for you.",
        "sections": [
            ("Why a direct review link works", "<p>Most customers give up if they have to search for your business, scroll to reviews, and find the button. A direct link skips all of that. One tap opens the review box with your business already selected, so the effort drops to a few seconds.</p>"),
            ("Three ways to use it", "<ol class=\"steps\"><li><span><strong>Text or email it</strong> right after a job or visit, while the experience is fresh.</span></li><li><span><strong>Print the QR card</strong> and put it where people wait: the register, tables, or the checkout bag.</span></li><li><span><strong>Add the link</strong> to your receipts, email signature, and thank-you pages.</span></li></ol>"),
        ],
        "faq": [
            ("Is StarAsk free?", "Yes. The review link, QR code, and printable card are free with no sign-up."),
            ("Does the link work on phones?", "Yes. It opens the Google review box on iPhone, Android, and desktop. People need to be signed in to a Google account to post a review."),
            ("Can I ask only happy customers for reviews?", "No. Google's rules don't allow filtering who you ask. Send the same link to every customer and let them review honestly."),
        ],
    },
    {
        "path": "review-qr-code/",
        "title": "Free Google Review QR Code Generator (Print-Ready) | StarAsk",
        "desc": "Make a Google review QR code that opens your review box in one scan. Download a high-resolution PNG or a print-ready review card. Free.",
        "eyebrow": "Google review QR code",
        "h1": "Free Google review QR code generator",
        "intro": "Make a QR code that opens your Google review box with one scan. Download it as a high-resolution image, or print it on a ready-made card.",
        "sections": [
            ("How to make your Google review QR code", "<ol class=\"steps\"><li><span>Find your Place ID with Google's Place ID Finder (steps are in the form above).</span></li><li><span>Paste it in and press <em>Create my review link</em>.</span></li><li><span>Press <em>Download QR code</em> for a 1000&times;1000 image, or download the full card.</span></li><li><span>Scan it with your own phone before you print, to make sure it opens your business.</span></li></ol>"),
            ("Where to put the QR code", "<ul><li>On the counter or register, at eye level</li><li>On table tents and menus</li><li>On receipts and invoices</li><li>On the bag, box, or packing slip</li><li>On your business card and van</li></ul>"),
            ("Tips for more scans", "<p>Keep the code at least 1 inch (2.5 cm) wide on paper, print it in black on white, and add one short line that says why, such as &ldquo;Loved your visit? Scan to leave us a review.&rdquo; Codes with a clear reason get far more scans than a bare square.</p>"),
        ],
        "faq": [
            ("Does a Google review QR code expire?", "No. The code holds a fixed link to your review box, so it keeps working as long as your Google Business Profile exists."),
            ("What size should I print it?", "At least 1 inch (2.5 cm) wide. For a counter sign, 2 to 3 inches is easier to scan from a distance."),
            ("Can customers scan it with any phone?", "Yes. The built-in camera on modern iPhones and Android phones reads QR codes without an extra app."),
        ],
    },
    {
        "path": "review-link-generator/",
        "title": "Google Review Link Generator: Direct Link to Your Review Box | StarAsk",
        "desc": "Generate a direct Google review link that opens the review box for your business. Copy it into texts, emails, and receipts. Free, no sign-up.",
        "eyebrow": "Google review link generator",
        "h1": "Google review link generator",
        "intro": "Create a direct link that opens the Google review box for your business. Paste it into texts, emails, receipts, and your website.",
        "sections": [
            ("What a Google review link looks like", "<p>A direct review link follows this pattern:</p><div class=\"linkbox\">https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID</div><p>Your Place ID is the unique code Google gives every business. Paste yours into the tool above and the full link is built for you.</p>"),
            ("Best times to send it", "<ol class=\"steps\"><li><span>Within a few hours of the visit or finished job.</span></li><li><span>After a customer thanks you or says something kind.</span></li><li><span>In the follow-up email that includes the invoice or receipt.</span></li></ol>"),
            ("A short message that works", "<p>Keep it personal and brief. Use the ready-to-send message above, or adapt it: name the customer, thank them for something specific, and include the link on its own line.</p>"),
        ],
        "faq": [
            ("Where do I find my Google review link?", "Google shows a share link inside your Business Profile, but you can also build it from your Place ID with this tool. Both open the same review box."),
            ("Why does the link ask people to sign in?", "Google requires a Google account to post a review. Most people are already signed in on their phone."),
            ("Can I shorten the link?", "Yes. Any link shortener works, but the full link is safer because people can see it goes to Google."),
        ],
    },
    {
        "path": "review-card/",
        "title": "Free Printable Google Review Card with QR Code | StarAsk",
        "desc": "Design a printable Google review card with your business name and QR code. Choose a color, download a print-ready PNG, and put it by the register.",
        "eyebrow": "Printable review card",
        "h1": "Free printable Google review card",
        "intro": "A ready-to-print card with your business name and a QR code that opens your Google review box. No design skills and no NFC hardware needed.",
        "sections": [
            ("How to print your review card", "<ol class=\"steps\"><li><span>Add your business name and Place ID, then pick a color.</span></li><li><span>Press <em>Download card</em> for a 1200&times;1800 PNG (4&times;6 in).</span></li><li><span>Print it at 4&times;6 in on card stock, or send the file to any print shop.</span></li><li><span>Slide it into a clear acrylic stand by the register or on tables.</span></li></ol>"),
            ("Printed card or NFC tap card?", "<p>NFC cards let people tap their phone instead of scanning, but they cost money per card and some phones need NFC turned on. A printed QR card is free, works on every camera phone, and you can print as many as you like. Many businesses start with printed cards and add NFC later.</p>"),
        ],
        "faq": [
            ("What paper should I use?", "Matte card stock around 300 gsm (110 lb cover) holds up well and avoids glare when people scan."),
            ("Can I add my logo?", "Logo upload is coming in the Business plan. For now the card uses your business name."),
            ("Does the card work outside the US?", "Yes. Google review links work in every country where Google Business Profiles exist."),
        ],
    },
    {
        "path": "review-request-templates/",
        "title": "Google Review Request Templates (Text & Email) | StarAsk",
        "desc": "Copy-ready Google review request templates for text messages, emails, receipts, and social posts. Your review link is added automatically.",
        "eyebrow": "Review request templates",
        "h1": "Google review request templates you can copy",
        "intro": "Short, friendly messages for texts, emails, receipts, and social posts. Add your Place ID above and every template fills in your own review link.",
        "sections": [
            ("Templates", templates_html()),
            ("How to ask without being pushy", "<ol class=\"steps\"><li><span><strong>Ask soon.</strong> The same day or the next morning works best.</span></li><li><span><strong>Keep it short.</strong> Thank them, ask once, and put the link on its own.</span></li><li><span><strong>Make it personal.</strong> Use their first name and mention what you did for them.</span></li><li><span><strong>Follow up once.</strong> One reminder a few days later is fine. More than that annoys people.</span></li></ol>"),
        ],
        "faq": [
            ("Should I text or email review requests?", "Text messages are usually opened faster, so they work well right after a visit. Email suits longer jobs, invoices, and customers who prefer it. Always have the customer's permission to message them."),
            ("Can I offer a discount for a review?", "No. Google's policies don't allow offering rewards or discounts in exchange for reviews. Ask every customer the same way and let them decide."),
            ("How many reminders should I send?", "One reminder, three to five days after the first message, is plenty."),
        ],
        "extra_js": TEMPLATES_JS,
    },
    {
        "path": "google-business-profile-audit/",
        "tool": "audit",
        "title": "Free Google Business Profile Audit Tool (Instant Score) | StarAsk",
        "desc": "Audit any Google Business Profile in seconds. Get a score out of 100 for reviews, rating, photos, hours, and contact details, with the fixes that matter most.",
        "eyebrow": "Free profile audit",
        "h1": "Free Google Business Profile audit",
        "intro": "Search for a business and get an instant score out of 100, with the fixes that will make the biggest difference listed first. Works for your own profile or a client's.",
        "sections": [
            ("What the audit checks", "<ul>"
                "<li><strong>Reviews:</strong> how many, the star rating, and how recent the newest one is</li>"
                "<li><strong>Photos:</strong> whether there are enough to show what you do</li>"
                "<li><strong>Basics:</strong> open status, hours, phone number, website, and categories</li></ul>"
                "<p>Reviews carry the most weight because they affect both where you rank in Maps and whether people choose you once they find you.</p>"),
            ("How the score works", "<p>Each check earns full points when it meets the bar, half when it is close, and none when it is missing. Reviews count for half the score (number 20, rating 15, recency 15); photos, hours, phone, website, open status, and categories make up the rest.</p>"
                "<ol class=\"steps\"><li><span><strong>80 to 100:</strong> a strong profile. Keep reviews and photos coming.</span></li>"
                "<li><span><strong>50 to 79:</strong> the basics are there, but you are leaving customers on the table.</span></li>"
                "<li><span><strong>Under 50:</strong> fix the red items first. They are usually quick.</span></li></ol>"),
            ("What the audit can't see", "<p>Some parts of a profile are not public: your business description, Google posts, replies to reviews, and Q&amp;A. Check those inside your Business Profile with the <a href=\"../google-business-profile-checklist/\">free checklist</a>.</p>"),
        ],
        "faq": [
            ("Is the Google Business Profile audit free?", "Yes. Search for any business and see its score and fixes for free, with no sign-up."),
            ("Can I audit a competitor or a client?", "Yes. The audit uses public profile information, so it works for any business on Google Maps."),
            ("How many reviews should a business have?", "There is no fixed number. The audit gives full points at 100 reviews, but the real target is to match or beat the businesses that rank near you."),
            ("Why is my score different from what I see in my dashboard?", "The audit only reads what Google shows the public. Private items like your description and posts are not included in the score."),
        ],
    },
    {
        "path": "get-more-google-reviews/",
        "tool": False,
        "title": "How to Get More Google Reviews: 9 Methods That Work | StarAsk",
        "desc": "A practical guide to getting more Google reviews for a local business: when to ask, where to ask, what to say, and what Google doesn't allow.",
        "eyebrow": "Guide",
        "h1": "How to get more Google reviews",
        "intro": "Most happy customers will leave a review if you ask at the right moment and make it take seconds. Here is what works for local businesses, and what to avoid.",
        "sections": [
            ("Why reviews matter", "<p>Reviews are one of the signals Google uses to rank local businesses in Maps and the local results. They also decide whether people pick you once they find you: more recent, detailed reviews make a business look active and trusted.</p>"),
            ("9 ways to get more reviews", "<ol class=\"steps\">"
                "<li><span><strong>Get your direct review link.</strong> One tap should open the review box. <a href=\"../review-link-generator/\">Create yours free</a>.</span></li>"
                "<li><span><strong>Ask at the happy moment.</strong> Right after a compliment, a finished job, or a smooth checkout.</span></li>"
                "<li><span><strong>Send a short text the same day.</strong> <a href=\"../review-request-templates/\">Use a template</a> with your link already in it.</span></li>"
                "<li><span><strong>Put a QR card where people wait.</strong> The register, tables, waiting room, or bag. <a href=\"../review-card/\">Print one free</a>.</span></li>"
                "<li><span><strong>Add the link to receipts and invoices.</strong> People read these at the end of the job.</span></li>"
                "<li><span><strong>Train your team to ask.</strong> A sentence like &ldquo;It would really help us if you left a review&rdquo; works when it is said warmly.</span></li>"
                "<li><span><strong>Reply to every review.</strong> Customers notice, and it shows new reviewers their words will be read.</span></li>"
                "<li><span><strong>Follow up once.</strong> A single reminder a few days later picks up people who meant to and forgot.</span></li>"
                "<li><span><strong>Make it routine.</strong> Ask every customer, every time. Consistent asking beats occasional pushes.</span></li>"
                "</ol>"),
            ("What Google doesn't allow", "<ul><li>Offering money, discounts, or gifts in exchange for reviews</li><li>Asking only happy customers and steering unhappy ones elsewhere (review gating)</li><li>Writing reviews for your own business, or having staff do it</li><li>Buying reviews or using review exchange groups</li></ul><p>Breaking these rules can get reviews removed or the profile restricted. Asking every customer honestly is both allowed and effective.</p>"),
            ("Let StarAsk do the asking", "<p>The StarAsk Business plan, coming soon, sends review requests by email automatically after each visit or job and alerts you when a new review needs a reply. Until then, every tool on this site is free.</p><p><a class=\"btn\" href=\"../\">Try the free tools</a></p>"),
        ],
        "faq": [
            ("How many Google reviews do I need?", "There is no fixed number. Aim to match or beat the review count of the top three businesses that rank near you, and keep new reviews coming every month."),
            ("Can I remove a bad review?", "Only reviews that break Google's policies, such as spam or off-topic posts, can be reported for removal. For honest negative reviews, reply politely and explain how you fixed the problem."),
            ("How long does it take for a review to appear?", "Most reviews show up within minutes. Some are held for a check and appear later."),
        ],
    },
    {
        "path": "google-business-profile-checklist/",
        "tool": False,
        "title": "Google Business Profile Checklist (Free, Interactive) | StarAsk",
        "desc": "A free interactive Google Business Profile checklist. Tick off basics, hours, photos, reviews, and activity to make your profile complete.",
        "eyebrow": "Checklist",
        "h1": "Google Business Profile checklist",
        "intro": "Work through this list to make sure your profile is complete. Your ticks are saved in this browser, so you can come back later.",
        "sections": [
            ("The checklist", checklist_html()),
            ("What to do next", "<p>Want a score instead of ticking boxes? Run the <a href=\"../google-business-profile-audit/\">free profile audit</a>. Once the basics are done, the biggest ongoing lever is a steady stream of new reviews. <a href=\"../review-link-generator/\">Get your review link</a> and <a href=\"../review-card/\">print a QR card</a> to start.</p>"),
        ],
        "faq": [
            ("How often should I update my profile?", "Check hours before every holiday, add photos monthly, and post at least weekly."),
            ("Does a complete profile rank higher?", "Google says complete, accurate information helps it match your business to the right searches. Relevance, distance, and prominence all play a part."),
        ],
        "extra_js": CHECKLIST_JS,
    },
    {
        "path": "privacy/",
        "tool": False,
        "utility": True,
        "title": "Privacy Policy | StarAsk",
        "desc": "How StarAsk handles your information. The free tools run in your browser and do not send us the details you type.",
        "eyebrow": "Privacy",
        "h1": "Privacy policy",
        "intro": "Short version: the free tools run in your browser, and we don't collect the business details you type into them.",
        "sections": [
            ("The free tools", "<p>The review link, QR code, review card, templates, and checklist are built in your browser. The business name and Place ID you enter are not sent to StarAsk. Checklist ticks are saved only in your own browser and you can clear them by clearing your browser data.</p>"),
            ("Business search", "<p>When you search for a business by name or run the profile audit, your search text and the chosen business are sent to Google Maps Platform to find matching places. Google handles that request under the <a href=\"https://policies.google.com/privacy\" target=\"_blank\" rel=\"noopener\">Google Privacy Policy</a>.</p>"),
            ("Cookies and analytics", "<p>StarAsk does not set advertising cookies. If we add visit analytics, this page will say which service we use and what it records.</p>"),
            ("Paid plans", "<p>Paid plans are not available yet. When they launch, this page will explain what account and customer data we store, how long we keep it, and how to delete it.</p>"),
            ("Changes", "<p>We will update this page when anything here changes, and show the date of the latest update below.</p><p class=\"hint\">Last updated: " + TODAY + "</p>"),
        ],
        "faq": [],
    },
]


def esc(s):
    return html.escape(s, quote=True)


def render(p):
    url = f"{SITE}/{p['path']}"
    depth = p["path"].count("/")
    rel = "../" * depth
    nav = "".join(
        f'<a href="{rel}{h.strip("/")}/"' + (' aria-current="page"' if h.strip("/") + "/" == p["path"] else "") + f">{esc(t)}</a>"
        for h, t in NAV)
    sections = "".join(f'<section><h2>{esc(h)}</h2>{body}</section>' for h, body in p["sections"])
    is_home = p["path"] == ""
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in p["faq"])
    related = "".join(
        f'<a href="{rel}{x["path"]}">{icon(PAGE_ICON.get(x["path"], "link"), "ic rel-ic")}<strong>{esc(x["h1"])}</strong><span>{esc(x["desc"][:90])}&hellip;</span></a>'
        for x in PAGES if x["path"] and x["path"] != p["path"] and not x.get("utility"))
    related_block = "" if is_home else f'<section><h2>More free tools and guides</h2><div class="related">{related}</div></section>'
    hero = HOME_HERO if is_home else ((f'<div class="hero">'
                                      f'<h1>{esc(p["h1"])}</h1><p class="lede">{esc(p["intro"])}</p></div>'))
    kind = p.get("tool", True)
    has_tool = kind is True
    is_app = kind is True or kind == "audit"
    faq_block = f'<section><h2>Questions</h2><div class="faq">{faq_html}</div></section>' if p["faq"] else ""
    main_schema = ({"@context": "https://schema.org", "@type": "WebApplication", "name": "StarAsk", "url": url,
                    "applicationCategory": "BusinessApplication", "operatingSystem": "Any",
                    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": p["desc"]}
                   if is_app else
                   {"@context": "https://schema.org", "@type": "Article", "headline": p["h1"], "description": p["desc"],
                    "url": url, "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "StarAsk"}})
    tool_html = TOOL if has_tool else AUDIT.replace("{rel}", rel) if kind == "audit" else ""
    base_js = f'<script src="{rel}assets/config.js"></script>\n<script src="{rel}assets/places.js"></script>\n'
    if has_tool:
        scripts = (base_js + f'<script src="{rel}assets/qrcode.js"></script>\n<script src="{rel}assets/tool.js"></script>\n'
                   "<script>StarAsk.mount(document.getElementById('tool'));</script>" + (HERO_JS if is_home else ""))
    elif kind == "audit":
        scripts = base_js + f'<script src="{rel}assets/audit.js"></script>\n<script>StarAskAudit.mount(document.getElementById(\'audit\'));</script>'
    else:
        scripts = ""
    scripts += p.get("extra_js", "")
    schema = [
        main_schema,
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]},
    ]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(p['title'])}</title>
<meta name="description" content="{esc(p['desc'])}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(p['title'])}">
<meta property="og:description" content="{esc(p['desc'])}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
{FONTS}
<link rel="stylesheet" href="{rel}assets/style.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body class="{'has-app' if is_app else 'no-app'}{' home' if is_home else ''}">
<div class="band">
<div class="wrap">
<header class="top">
  <a class="brand" href="{rel or './'}"><span class="pin"><span>&#9733;</span></span>StarAsk</a>
  <nav aria-label="Tools">{nav}</nav>
</header>
{hero}
</div>
</div>
<main class="wrap">
{tool_html}
<div class="content">
{HOW + TOOLS if is_home else ""}
{sections}
{PRICING if is_home else ""}
{faq_block}
{related_block}
</div>
</main>
<footer class="wrap">
<div class="foot">
  <div class="foot-brand">
    <a class="brand" href="{rel or './'}"><span class="pin"><span>&#9733;</span></span>StarAsk</a>
    <p>Free Google review tools for local businesses.</p>
  </div>
  <div class="foot-cols">
    <div><h4>Tools</h4><a href="{rel}review-link-generator/">Review link</a><a href="{rel}review-qr-code/">QR code</a><a href="{rel}review-card/">Review card</a><a href="{rel}google-business-profile-audit/">Profile audit</a></div>
    <div><h4>Guides</h4><a href="{rel}get-more-google-reviews/">Get more reviews</a><a href="{rel}review-request-templates/">Request templates</a><a href="{rel}google-business-profile-checklist/">Profile checklist</a></div>
    <div><h4>StarAsk</h4><a href="{rel}privacy/">Privacy</a></div>
  </div>
  <p class="foot-bottom"><span>&copy; {datetime.date.today().year} StarAsk</span><span>StarAsk is not affiliated with or endorsed by Google.</span></p>
</div>
</footer>
{scripts}
</body>
</html>
"""


def main():
    for p in PAGES:
        out = ROOT / p["path"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(p), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))
    urls = "".join(f"<url><loc>{SITE}/{p['path']}</loc><lastmod>{TODAY}</lastmod></url>" for p in PAGES)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print("wrote sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
