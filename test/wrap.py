#!/usr/bin/env python3
"""Wrap /home/user/Calanit/index.html (an artifact body fragment) into a standalone
test.html mimicking the artifact host skeleton.
Uses locally-cached webfonts (fonts/local.css) so layout tests are fast+deterministic.
Pass --remote to keep the real Google Fonts link instead."""
import sys, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
out = 'test.html'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
if args: out = args[0]
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'fonts', 'local.css')
if '--remote' not in sys.argv and os.path.exists(CACHE):
    src = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*">',
                 '<link rel="stylesheet" href="fonts/local.css">', src)
open(out, 'w', encoding='utf-8').write(
 '<!doctype html><html><head><meta charset="utf8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1">'
 '<style>:root{color-scheme:light}body{margin:0;padding:0;'
 'font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#faf9f5;color:#141413}'
 'img{max-width:100%}[hidden]:not([hidden=until-found]){display:none!important}</style>'
 '</head><body>\n' + src + '\n</body></html>')
print('wrote', out, '(local fonts)' if '--remote' not in sys.argv else '(remote fonts)')
