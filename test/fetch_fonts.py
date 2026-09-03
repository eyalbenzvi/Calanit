#!/usr/bin/env python3
"""Populate ./fonts with the webfonts index.html requests, and rewrite the
stylesheet to point at the local copies.

wrap.py uses this cache when present so layout assertions measure real font
metrics offline. Run once; re-run if the font request in index.html changes.
"""
import re, os, hashlib, urllib.request, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120 Safari/537.36')

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
m = re.search(r'(https://fonts\.googleapis\.com/css2\?[^"]+)', src)
if not m:
    raise SystemExit('no Google Fonts request found in index.html')

op = urllib.request.build_opener(); op.addheaders = [('User-Agent', UA)]
os.makedirs(os.path.join(HERE, 'fonts', 'f'), exist_ok=True)
with op.open(m.group(1), timeout=60) as r:
    css = r.read().decode('utf-8')

urls = sorted(set(re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css)))
def get(u):
    name = hashlib.md5(u.encode()).hexdigest()[:16] + '.woff2'
    path = os.path.join(HERE, 'fonts', 'f', name)
    if not os.path.exists(path) or not os.path.getsize(path):
        for _ in range(3):
            try:
                with op.open(u, timeout=30) as r, open(path, 'wb') as f:
                    f.write(r.read())
                break
            except Exception:
                pass
    return u, name, os.path.getsize(path) if os.path.exists(path) else 0

ok = 0
with cf.ThreadPoolExecutor(12) as ex:
    for u, name, size in ex.map(get, urls):
        if size:
            css = css.replace(u, 'f/' + name); ok += 1
        else:
            print('  could not fetch', u[:80])
open(os.path.join(HERE, 'fonts', 'local.css'), 'w', encoding='utf-8').write(css)
print('cached %d/%d font files' % (ok, len(urls)))
