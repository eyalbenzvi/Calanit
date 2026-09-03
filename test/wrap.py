#!/usr/bin/env python3
"""Produce test.html from ../index.html.

index.html is a complete standalone document, so nothing is wrapped: this only
swaps the Google Fonts request for the local cache (see fetch_fonts.py) so
layout assertions measure real font metrics offline. Pass --remote to keep the
network font request.
"""
import sys, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'fonts', 'local.css')

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
out = next((a for a in sys.argv[1:] if not a.startswith('--')), 'test.html')

if '--remote' not in sys.argv and os.path.exists(CACHE):
    src = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*">',
                 '<link rel="stylesheet" href="fonts/local.css">', src)
    note = '(local fonts)'
else:
    note = '(remote fonts)'

open(os.path.join(HERE, out), 'w', encoding='utf-8').write(src)
print('wrote', out, note)
