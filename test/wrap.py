#!/usr/bin/env python3
"""Produce test.html from ../index.html.

index.html is a complete standalone document, so nothing is wrapped: the only
change is that asset paths climb one directory, because the copy under test
sits in test/. The fonts, icons and images are the ones the site serves, so
layout assertions measure exactly the metrics production uses.
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSET = '="assets/'

src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
out = next((a for a in sys.argv[1:] if not a.startswith('--')), 'test.html')

if ASSET not in src:
    sys.exit('index.html no longer references anything under assets/ — '
             'update this script')
src = src.replace(ASSET, '="../assets/')

open(os.path.join(HERE, out), 'w', encoding='utf-8').write(src)
print('wrote', out)
