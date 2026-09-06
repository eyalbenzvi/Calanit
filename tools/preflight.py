#!/usr/bin/env python3
"""Pre-deploy check for index.html. Run it before every publish:

    python3 tools/preflight.py            # full check
    python3 tools/preflight.py --content  # skip the launch-config gate

Exit status is 0 only when there are no errors, so it can go straight into
CI. Errors block a deploy; warnings are worth a look but do not.

What it protects:
  * the three translation tables cannot drift apart, and no key can go
    missing in one language (a missing key silently leaves English on screen)
  * the fallback text in the markup cannot drift from the English table
    (that text is what a visitor sees for the first paint, and with
    scripting off it is all they ever see)
  * no translated string is ever written through innerHTML
  * every asset the page references exists, and none of them is remote
  * the two launch-blocking config values are actually set
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'index.html')
LANGS = ('en', 'ar', 'el')

errors, warnings = [], []
def err(msg):  errors.append(msg)
def warn(msg): warnings.append(msg)

src = open(PATH, encoding='utf-8').read()


# ── translation tables ──────────────────────────────────────────────────
def table(lang):
    m = re.search(r'\bT\.' + lang + r'\s*=\s*\{', src)
    if not m:
        err('no T.%s translation table found' % lang)
        return {}
    i, depth = m.end() - 1, 0
    for j in range(i, len(src)):
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0:
                body = src[i:j + 1]
                break
    else:
        err('T.%s table is not closed' % lang)
        return {}
    pairs = re.findall(r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"', body)
    out = {}
    for k, v in pairs:
        if k in out:
            err('T.%s has a duplicate key: %s (the later one silently wins)' % (lang, k))
        out[k] = v
    return out


T = {lang: table(lang) for lang in LANGS}
base = set(T['en'])
for lang in LANGS[1:]:
    missing = sorted(base - set(T[lang]))
    extra = sorted(set(T[lang]) - base)
    for k in missing:
        err('T.%s is missing key %r — that string would stay English' % (lang, k))
    for k in extra:
        err('T.%s has key %r, which does not exist in T.en' % (lang, k))
for lang in LANGS:
    for k, v in T[lang].items():
        if not v.strip():
            err('T.%s[%r] is empty' % (lang, k))


# ── markup attributes must line up with the tables ──────────────────────
def fallback_ok(markup_text, en_value):
    """The markup default is what a visitor sees before the script runs, so it
    has to match T.en. {year} is the one token the script fills in: any
    four-digit year is a valid no-script fallback for it."""
    if '{year}' not in en_value:
        return markup_text == en_value
    pat = '^' + re.escape(en_value).replace(re.escape('{year}'), r'\d{4}') + '$'
    return re.match(pat, markup_text) is not None


def unescape(t):
    return (t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
             .replace('&nbsp;', ' ').replace('&copy;', '©')
             .replace('&rsquo;', '’').replace('&quot;', '"'))

if 'data-i18n-html' in src:
    err('data-i18n-html is back in the markup: translated strings must never '
        'be written through innerHTML (see the note in applyLang)')

used = set()
# inline text defaults: <tag ... data-i18n="key" ...>text</tag>
for m in re.finditer(r'<([a-zA-Z0-9]+)(?=[\s>])([^>]*?)data-i18n="([^"]+)"([^>]*?)>([^<]*)</\1>', src):
    key, txt = m.group(3), unescape(m.group(5))
    used.add(key)
    if key not in T['en']:
        err('markup uses data-i18n=%r but T.en has no such key' % key)
    elif not fallback_ok(txt, T['en'][key]):
        err('the fallback text for %r has drifted from T.en\n'
            '        markup: %r\n'
            '        T.en:   %r' % (key, txt, T['en'][key]))
for m in re.finditer(r'data-i18n="([^"]+)"', src):
    used.add(m.group(1))

for kind, attr in (('ph', 'placeholder'), ('aria', 'aria-label')):
    for m in re.finditer(r'data-i18n-%s="([^"]+)"' % kind, src):
        key = m.group(1)
        used.add(key)
        if key not in T['en']:
            err('markup uses data-i18n-%s=%r but T.en has no such key' % (kind, key))
    # the literal attribute value must match T.en for the same reason
    for m in re.finditer(r'<[^>]*data-i18n-%s="([^"]+)"[^>]*>' % kind, src):
        tag, key = m.group(0), m.group(1)
        lit = re.search(attr + r'="([^"]*)"', tag)
        if not lit:
            err('%s element for %r carries no %s attribute, so there is no '
                'fallback before the script runs' % (kind, key, attr))
        elif key in T['en'] and unescape(lit.group(1)) != T['en'][key]:
            err('the %s fallback for %r has drifted from T.en\n'
                '        markup: %r\n'
                '        T.en:   %r' % (attr, key, unescape(lit.group(1)), T['en'][key]))

# keys the script reads directly rather than through an attribute
SCRIPTED = {'meta.title', 'meta.desc', 'f.sending'}
for k in sorted(base - used - SCRIPTED):
    warn('T.*[%r] is not referenced by any element — dead string?' % k)


# ── assets: all present, none remote ───────────────────────────────────
for ref in sorted(set(re.findall(r'(?:href|src)="((?!https?:|mailto:|#|data:)[^"]+)"', src))):
    if not os.path.exists(os.path.join(ROOT, ref)):
        err('index.html references %s, which does not exist' % ref)

fonts_css = os.path.join(ROOT, 'assets', 'fonts', 'fonts.css')
if os.path.exists(fonts_css):
    css = open(fonts_css, encoding='utf-8').read()
    for u in sorted(set(re.findall(r'url\(([^)]+)\)', css))):
        if u.startswith('http'):
            err('assets/fonts/fonts.css still points at a remote font: %s' % u)
        elif not os.path.exists(os.path.join(ROOT, 'assets', 'fonts', u)):
            err('assets/fonts/fonts.css references missing file %s' % u)
else:
    err('assets/fonts/fonts.css is missing — the page would fall back to system fonts')

# anything remote outside an HTML comment would break "no third-party requests"
stripped = re.sub(r'<!--.*?-->', '', src, flags=re.S)
stripped = re.sub(r'/\*.*?\*/', '', stripped, flags=re.S)
# rel="canonical", rel="alternate" and the og:* tags are metadata, never fetched
fetched = re.sub(r'<link[^>]+rel="canonical"[^>]*>', '', stripped)
fetched = re.sub(r'<link[^>]+rel="alternate"[^>]*>', '', fetched)
for u in sorted(set(re.findall(r'(?:href|src)="(https?://[^"]+)"', fetched))):
    err('the page loads a third-party resource: %s' % u)

if 'Content-Security-Policy' not in src:
    err('the Content-Security-Policy meta tag is gone')


# ── content invariants ─────────────────────────────────────────────────
for lang in LANGS:
    if '{year}' not in T[lang].get('foot.copy', ''):
        err('T.%s["foot.copy"] lost its {year} token — the copyright year '
            'would be frozen' % lang)
if re.search(r"be'eri", stripped, re.I):
    err("a straight apostrophe appears in \"be'eri\" — the brand uses U+2019 (’)")
for lang in LANGS:
    for k, v in T[lang].items():
        if k == 'brand.name':
            continue
        if 'be’eri' in v:
            err('T.%s[%r] uses the lowercase logotype form inside text; running '
                'text takes "Be’eri Printers"' % (lang, k))


# ── launch configuration ───────────────────────────────────────────────
if '--content' not in sys.argv:
    cfg = re.search(r'var CONFIG = \{(.*?)\n\};', src, re.S)
    if not cfg:
        err('the CONFIG block is missing')
    else:
        body = cfg.group(1)
        if re.search(r"MAILTO:\s*''", body):
            err('CONFIG.MAILTO is still empty — the contact form cannot '
                'open the visitor\'s email client')
        if re.search(r"PRIVACY_URL:\s*''", body):
            err('CONFIG.PRIVACY_URL is still empty — the footer privacy link '
                'stays hidden, and the form collects personal data')
    if 'REPLACE-WITH-LIVE-ORIGIN' in src:
        err('canonical and og:image still contain REPLACE-WITH-LIVE-ORIGIN')


# ── report ─────────────────────────────────────────────────────────────
for w in warnings:
    print('WARN   %s' % w)
for e in errors:
    print('ERROR  %s' % e)
print('\n%d error(s), %d warning(s)' % (len(errors), len(warnings)))
if errors:
    print('Not ready to deploy.')
sys.exit(1 if errors else 0)
