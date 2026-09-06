#!/usr/bin/env python3
"""Build build/beeri-landing-standalone.html — one file, zero dependencies.

    python3 tools/build_standalone.py

Everything is inlined: the fonts as data: URIs, the favicon as a data: URI.
The result opens from a desktop, a USB stick or an email attachment, works
with no network at all, and makes no request to anything. Meant for review and
sign-off, where the reader should not have to unzip a folder or run a server.

FOR REVIEW, NOT FOR DEPLOYMENT. Deploy index.html + assets/ (see
docs/HANDOVER.md): the split version lets the browser cache the fonts and
download only the subsets a visitor's language needs, while this one carries
every subset in the HTML and re-downloads them on every page load.
"""
import base64
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, 'assets', 'fonts')

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
css = open(os.path.join(FONT_DIR, 'fonts.css'), encoding='utf-8').read()


def data_uri(path, mime):
    with open(path, 'rb') as fh:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(fh.read()).decode())


# ── fonts: rewrite each src url() to a data: URI, then inline the sheet ──
def inline_font(m):
    rel = m.group(1)
    path = os.path.join(FONT_DIR, rel)
    if not os.path.exists(path):
        sys.exit('assets/fonts/fonts.css references missing file %s' % rel)
    return 'url(%s)' % data_uri(path, 'font/woff2')


# Google's stylesheet declares one @font-face per weight even where a family
# ships as a single variable font, so the same file is named several times.
# Inlining each one separately would triple the file. Collapse blocks that are
# identical apart from font-weight into one block with a weight range, which
# is how a variable font should be declared anyway.
def collapse(sheet):
    groups, order = {}, []
    for m in re.finditer(r'(/\*[^*]*\*/\s*)?(@font-face\s*\{[^}]*\})', sheet):
        blk = m.group(2)
        wt = re.search(r'font-weight:\s*([^;]+);', blk)
        key = re.sub(r'font-weight:\s*[^;]+;', 'font-weight:@;', blk)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(wt.group(1).strip() if wt else '400')
    out = []
    for key in order:
        weights = groups[key]
        nums = []
        for w in weights:
            nums.extend(int(x) for x in re.findall(r'\d+', w))
        span = str(nums[0]) if len(set(nums)) == 1 else '%d %d' % (min(nums), max(nums))
        out.append(key.replace('font-weight:@;', 'font-weight: %s;' % span))
    return '\n'.join(out) + '\n'


css = collapse(css)
css = re.sub(r'url\(([^)]+)\)', inline_font, css)

link = '<link rel="stylesheet" href="assets/fonts/fonts.css">'
if link not in src:
    sys.exit('index.html no longer links %s — update this script' % link)
src = src.replace(link, '<style>\n%s</style>' % css, 1)

# ── icon ────────────────────────────────────────────────────────────────
src = src.replace(
    '<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">',
    '<link rel="icon" type="image/svg+xml" href="%s">'
    % data_uri(os.path.join(ROOT, 'assets', 'favicon.svg'), 'image/svg+xml'), 1)

# ── things that cannot travel in a single file ──────────────────────────
# The touch icon, social preview, canonical, hreflang, structured data and
# font preload need real URLs or a server; a reviewer opening a local file
# needs none of them, and leaving broken references would be worse.
src = re.sub(r'\n?\s*<link rel="apple-touch-icon"[^>]*>', '', src, count=1)
src = re.sub(r'\n?\s*<meta property="og:image[^"]*"[^>]*>', '', src)
src = re.sub(r'\n?\s*<link rel="canonical"[^>]*>', '', src, count=1)
src = re.sub(r'\n?\s*<link rel="alternate"[^>]*>', '', src)
src = re.sub(r'\n?\s*<meta property="og:url"[^>]*>', '', src, count=1)
src = re.sub(r'\n?\s*<meta name="twitter:image[^"]*"[^>]*>', '', src)
src = re.sub(r'\n?\s*<meta name="twitter:title"[^>]*>', '', src, count=1)
src = re.sub(r'\n?\s*<meta name="twitter:description"[^>]*>', '', src, count=1)
src = re.sub(r'\n?\s*<meta name="robots"[^>]*>', '', src, count=1)
src = re.sub(r'\n?\s*<link rel="preload"[^>]*>', '', src)
src = re.sub(r'\n?\s*<script type="application/ld\+json">.*?</script>',
             '', src, count=1, flags=re.S)

# data: fonts have to be allowed, and file:// treats every document as its own
# opaque origin, so 'self' matches nothing — hence the explicit data:.
src = src.replace("font-src 'self';", "font-src data:;", 1)

# ── say what this file is, at the top ───────────────────────────────────
src = src.replace('''  Editing content, adding a language, the launch checklist and the
  recommended HTTP response headers are all in docs/HANDOVER.md.
  Run tools/preflight.py before every deploy — it fails on unset
  configuration and on translation tables that have drifted apart.
-->''',
'''  ┌──────────────────────────────────────────────────────────────────┐
  │  REVIEW COPY — generated by tools/build_standalone.py            │
  │                                                                  │
  │  Self-contained: fonts and icon are inlined, so this file opens  │
  │  anywhere, offline, and requests nothing from the network.       │
  │                                                                  │
  │  Do not deploy this file. The site to publish is index.html      │
  │  plus assets/ — see docs/HANDOVER.md. Editing content here has   │
  │  no effect on the source; edit index.html and rebuild.           │
  └──────────────────────────────────────────────────────────────────┘
-->''', 1)

out = os.path.join(ROOT, 'build')
os.makedirs(out, exist_ok=True)
dest = os.path.join(out, 'beeri-landing-standalone.html')
open(dest, 'w', encoding='utf-8').write(src)

remote = re.findall(r'(?:href|src)="(https?://[^"]+)"',
                    re.sub(r'<!--.*?-->', '', src, flags=re.S))
if remote:
    sys.exit('the standalone file still references %s' % remote[0])

print('wrote build/beeri-landing-standalone.html (%.1f MB, 0 external references)'
      % (len(src.encode('utf-8')) / 1048576))
