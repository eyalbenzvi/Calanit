#!/usr/bin/env python3
"""Print a hash-based Content-Security-Policy for index.html.

    python3 tools/csp_hash.py

The policy shipped in the page uses 'unsafe-inline' for script-src and
style-src, because the CSS and JS are inline in the file. If you would rather
not allow inline code at all, this prints the same policy with sha256 hashes
of the exact inline blocks instead — strictly better, at the cost of having to
rerun this and update the header after every edit to the page.

Serve the result as a Content-Security-Policy response header (the meta tag in
<head> can stay; the header wins where both apply, and the header is also the
only place frame-ancestors works).
"""
import base64
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()


def hashes(tag):
    out = []
    for m in re.finditer(r'<%s(?![^>]*\bsrc=)[^>]*>(.*?)</%s>' % (tag, tag), src, re.S):
        body = m.group(1)
        digest = hashlib.sha256(body.encode('utf-8')).digest()
        out.append("'sha256-%s'" % base64.b64encode(digest).decode())
    return out


scripts, styles = hashes('script'), hashes('style')
if not scripts or not styles:
    sys.exit('found %d inline script(s) and %d inline style(s) — expected at '
             'least one of each; has the page structure changed?'
             % (len(scripts), len(styles)))

policy = ' '.join([
    "default-src 'none';",
    "script-src %s;" % ' '.join(scripts),
    "style-src 'self' %s;" % ' '.join(styles),
    "font-src 'self';",
    "img-src 'self' data:;",
    "connect-src 'self';",
    "form-action 'none';",
    "base-uri 'none';",
    "frame-ancestors 'none'",
])

print('%d inline script(s), %d inline style(s)\n' % (len(scripts), len(styles)))
print('Content-Security-Policy: %s' % policy)
print("""
Notes
  * style-src keeps 'self' because assets/fonts/fonts.css is a real file.
  * connect-src has to name the form endpoint's origin if it is not
    same-origin. A same-origin path such as /api/rfq needs no change.
  * Re-run this after any edit to the inline <style> or <script>, or the
    browser will block the page's own code. tools/preflight.py cannot catch
    a stale hash, because the hash lives in your server config.""")
