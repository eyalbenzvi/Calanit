# Handover — Be’eri Printers landing page

Everything a development team needs to publish this page and keep it running.
Read [Launch checklist](#launch-checklist) first: two configuration values are
still unset, and until they are, the contact form cannot deliver a lead.

For editing the wording on the page, see [CONTENT-EDITING.md](CONTENT-EDITING.md).

---

## What this is

One static HTML page in three languages (English by default, Arabic, Greek),
marketing card-personalization services to banks, financial institutions,
fintechs, government bodies and card issuers.

```
index.html                 the whole page: markup, CSS, JS, translations
assets/
  fonts/                   self-hosted webfonts + licences
  favicon.svg              browser tab icon
  apple-touch-icon.png     iOS home-screen icon
  og-image.png             1200×630 social preview
docs/                      this file and the content guide
tools/
  preflight.py             pre-deploy gate — run before every publish
  build_fonts.py           regenerates assets/fonts/ (needs network)
  build_images.py          regenerates the icon and social image
  csp_hash.py              prints a stricter, hash-based CSP
  build_standalone.py      one-file review copy for sign-off
test/
  run_all.py               runs every check
  test_suite.py            151 behaviour / a11y / layout assertions
  contrast.py              WCAG AA contrast, light and dark
  wordfit.py               headings whose longest word cannot fit its box
  widows.py                short last lines (report)
  consistency.py           components that render differently (report)
```

No build step, no package manager, no server-side code, no database. There is
nothing to compile and nothing to install in order to deploy.

### The review copy

`python3 tools/build_standalone.py` writes `build/beeri-landing-standalone.html`
— the same page as one file, with the fonts and icon inlined, so it opens
offline from a desktop or an email attachment and requests nothing from
anywhere. Use it to circulate the page for approval.

Do not deploy it. Split across `index.html` + `assets/` the browser caches the
fonts and downloads only the subsets a visitor's language needs; the one-file
copy carries every subset inline and re-downloads roughly 1 MB on every page
load. It is also generated output — edits made to it are lost on the next
rebuild.

## Deploying

Copy `index.html` and `assets/` to a web root. That is the entire deployment.
`docs/`, `tools/` and `test/` are for maintainers and should not be published —
they contain no secrets, but they are not part of the site.

Works unchanged on Nginx, Apache, IIS, S3 + CloudFront, Netlify, Vercel,
Cloudflare Pages, GitHub Pages, or any static host. Serve over HTTPS.

Nothing is fetched from a third party at runtime — no CDN, no Google Fonts,
no analytics, no trackers. `test/test_suite.py` asserts this, so a request to
any other origin will fail the build.

### Recommended response headers

The page carries a `Content-Security-Policy` meta tag, which covers hosts that
cannot set headers. Where you can set headers, set these — `frame-ancestors`
and `Strict-Transport-Security` only work as headers, not as a meta tag.

```
Content-Security-Policy: default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'
Strict-Transport-Security: max-age=63072000; includeSubDomains
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Cross-Origin-Opener-Policy: same-origin
```

`'unsafe-inline'` is there only because the CSS and JS live inside
`index.html`. To drop it, run `python3 tools/csp_hash.py`, which prints the
same policy with `sha256` hashes of the exact inline blocks. That is strictly
better — the trade-off is that the header has to be updated after every edit
to the page, and nothing can check that for you.

<details>
<summary>Nginx</summary>

```nginx
location / {
    root /var/www/beeri;
    add_header Content-Security-Policy "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
}

# fonts and images are content-addressed by name and never change in place
location /assets/fonts/ { expires 1y; add_header Cache-Control "public, immutable"; }
location = /index.html   { expires -1;  add_header Cache-Control "no-cache"; }
```
</details>

<details>
<summary>Netlify / Cloudflare Pages (_headers)</summary>

```
/*
  Content-Security-Policy: default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'
  Strict-Transport-Security: max-age=63072000; includeSubDomains
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()

/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable
```
</details>

### Caching

`index.html` should not be cached hard, or a content edit will not reach
visitors: `Cache-Control: no-cache` (revalidate every time) is right for it.
Everything under `assets/fonts/` can be cached for a year — the filenames come
from content hashes, so a rebuild produces new names rather than changing a
file in place.

---

## Launch checklist

Run `python3 tools/preflight.py`. It fails while any of the first three items
below is outstanding, so it is the gate, not this list.

### Blocking — the page must not go live without these

1. **`CONFIG.MAILTO`** (top of the `<script>` in `index.html`).
   Currently `headoffice@beeriprint.co.il`. The contact form builds a
   `mailto:` URI from the filled fields and opens the visitor's email client.
   Change this value if the receiving inbox moves.

2. **`CONFIG.PRIVACY_URL`.** Currently empty, which keeps the footer privacy
   link hidden. The form collects a name, company, country, email, phone and
   free text behind a consent checkbox, and the page is marketed to Greek and
   other EU institutions, so GDPR Art. 13 applies: the notice has to be
   reachable at the point of collection. Point this at the company's real
   privacy notice.

3. **`REPLACE-WITH-LIVE-ORIGIN`** in the `<link rel="canonical">` and
   `og:image` tags in `<head>`. Replace with the live origin, e.g.
   `https://www.beeriprint.co.il`. Social scrapers need an absolute URL for
   the preview image; a relative one produces no card at all.

### Facts only the client can supply

None of the following was invented, and none of it should be. Each item is
either absent from the page or deliberately hedged, and needs the company to
confirm the real value before it is stated.

| # | What | Where it lands | Why it is not there yet |
|---|------|----------------|--------------------------|
| 1 | Certification status — whether the facility holds **PCI Card Production and Provisioning** (Physical / Logical), which is a different assessment from PCI DSS; plus ISO certificate numbers, issuing bodies and validity dates | Security section badges and the note under them | The page currently says scope and status are "provided on request" rather than claiming a certification. A wrong claim here is a compliance problem, not a copy problem. There is a `CLIENT SIGN-OFF REQUIRED BEFORE LAUNCH` comment in `index.html` above the badges. |
| 2 | Scheme vendor certification (Mastercard / Visa card personalization vendor status) | Would be a badge row in the Security section | Claiming scheme certification without holding it is actionable. Not added. |
| 3 | The three headline figures — 30+ years, 50M+ cards, 60+ organizations | About section counters | Marked "figures are indicative" on the page. Replace with audited numbers or remove the counters. |
| 4 | Contact details — legal entity name, registered address, phone, and the inbox that receives form submissions | Footer, and the no-script notice in the form | **The page has no contact details at all.** For an EU-facing site this is also an imprint/transparency gap. |
| 5 | Reference case studies — real volumes, SLA figures and programme durations | References section | The four cases are described qualitatively, with no numbers. |
| 6 | Services deliberately not listed: EMV data preparation, HSM key management, secure destruction of rejects, BCP/DR arrangements | Would be additional service cards | An industry reviewer recommended these. They were left out because we cannot confirm the company performs them. Add the ones it actually does. |
| 7 | Whether "worldwide distribution" and "cross-border dispatch" are accurate for the markets targeted | Footer strip, capabilities | Stated on the page; confirm before launch. |

### Worth doing, not blocking

- **`Organization` JSON-LD** in `<head>` — improves how the company appears in
  search results. Needs items 4 and 1 above, so it is not there yet. Template:

  ```html
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Organization",
   "name":"Be’eri Printers","url":"https://REPLACE",
   "logo":"https://REPLACE/assets/apple-touch-icon.png",
   "address":{"@type":"PostalAddress","streetAddress":"…","addressCountry":"IL"},
   "contactPoint":{"@type":"ContactPoint","telephone":"…","contactType":"sales"}}
  </script>
  ```
- **`hreflang`.** The three languages share one URL, so there is nothing for
  `hreflang` to point at. `?lang=ar` and `?lang=el` are shareable deep links
  and can be declared as alternates if search visibility in Arabic or Greek
  matters:
  `<link rel="alternate" hreflang="el" href="https://…/?lang=el">`
- **Analytics.** Nothing is installed. Anything you add becomes the page's
  first third-party request: it needs a `connect-src`/`script-src` entry in
  the CSP, a mention in the privacy notice, and — for EU visitors — a lawful
  basis, which for most analytics means consent.

---

## The contact form

The form validates in the browser, then builds a `mailto:` URI from the
filled fields and opens the visitor's email client via
`window.location.href`. The email is addressed to `CONFIG.MAILTO`
(`headoffice@beeriprint.co.il`), with a localized subject line and the
form data formatted as a readable text body.

Field labels in the email body use the visitor's current language (the
same labels shown in the UI). Select fields send their visible text (the
translated option label), not machine values, so the email is
human-readable in every language.

No server-side endpoint is needed. The browser's `mailto:` handler
(Outlook, Gmail, Apple Mail, etc.) composes the message, and the visitor
sends it themselves.

The page includes a hidden bot-trap field (`_ref2`). A submission that
fills it is refused locally and the mailto never opens.

### Without JavaScript

The whole page renders and reads correctly with scripting off: all content is
in the markup, and the language switcher, mobile drawer and reveal animations
degrade to a static English page. The form is the exception — it needs
JavaScript to build the mailto URI, and shows a `<noscript>` notice saying
so and giving the email address for direct contact.

---

## How the page is put together

Single file, top to bottom: `<head>` metadata → `<style>` (CSS custom-property
tokens, then components, then media queries) → markup → `<script>` (config,
three translation tables, i18n engine, then the UI behaviours).

**Theming.** Colours come from tokens on `:root`. Dark mode redefines only the
tokens, in two places: `@media (prefers-color-scheme: dark)` guarded by
`:root:not([data-theme="light"])`, and `:root[data-theme="dark"]`. Never put a
colour's only definition inside one of those blocks.

**Right-to-left.** Arabic is RTL. The layout uses logical properties
(`inset-inline-start`, `border-inline-start`, `text-align: start`) so it mirrors
without a separate stylesheet. Letter-spacing is zeroed for Arabic, which is a
connected script. Adding CSS with `left`, `right`, `margin-left` or
`padding-right` will break the Arabic layout — use the logical equivalents.

**Per-language typography.** Each language gets its own font stack, heading
sizes and line-height multiplier, via `:root[lang="ar"]` and
`:root[lang="el"]` token overrides. Greek is set in Roboto Condensed because
Barlow Condensed has no Greek coverage.

**Language selection.** English is the default and browser language is
deliberately not sniffed. Precedence: `?lang=` in the URL, then the visitor's
previous choice in `localStorage`, then English. Both sources are validated
against the translation tables, so an unknown or hostile value falls back to
English rather than reaching the `lang`/`dir` attributes.

**No innerHTML.** Every translated string is written with `textContent` or
`setAttribute`, so no value in the translation tables can inject markup. The
hero headline needs two type styles, and gets two keys and two elements rather
than one string containing tags. `tools/preflight.py` fails if a
`data-i18n-html` attribute reappears.

**Copyright year** comes from the clock: the strings contain a `{year}` token
that the i18n engine replaces. The literal year in the markup is only the
no-script fallback.

---

## Testing

```bash
pip install playwright && playwright install chromium   # once
python3 test/run_all.py
```

The probes drive real Chromium over a loopback HTTP server, so the CSP behaves
as it will in production. `CHROMIUM=/path/to/chromium` overrides the browser
path. `test.html` is generated on each run and can be deleted at any time.

`run_all.py` exits non-zero if a gate fails, which makes it usable as a CI
step. The four gates are: preflight, `test_suite.py`, `contrast.py`,
`wordfit.py`. `widows.py` and `consistency.py` print reports and never fail —
they are for a human to glance at.

Run at minimum `python3 tools/preflight.py` before every deploy. It catches
the failure modes that are invisible in a browser: a translation key missing
from one language (that string silently stays English), fallback text in the
markup that has drifted from the English table (that text is what the visitor
sees on first paint, and all they see with scripting off), a referenced asset
that is not there, and unset launch configuration.
