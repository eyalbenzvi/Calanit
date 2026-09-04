#!/usr/bin/env python3
"""Render assets/apple-touch-icon.png and assets/og-image.png.

Both are generated from the page's own logo paths and palette, so re-running
this after a brand change keeps them in step. Requires Playwright + Chromium
(executable path below matches this container; change it elsewhere).
"""
import os
import re
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMIUM = os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium')

page = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
mark = re.search(r'<svg class="logo-mark".*?</svg>', page, re.S).group(0)
PATHS = '\n'.join('<path d="%s"/>' % d
                  for d in re.findall(r'<path fill="#00AEEF" d="([^"]+)"/>', mark))
assert PATHS.count('<path') == 2, 'expected the two logo paths'

SC = 1.45
W, H = 25.06 * SC, 27.52 * SC
ICON = """<!doctype html><meta charset="utf-8"><style>html,body{{margin:0}}</style>
<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="11" fill="#071E38"/>
  <g fill="#00AEEF" transform="translate({tx:.2f} {ty:.2f}) scale({sc})">{p}</g>
</svg>""".format(tx=(64 - W) / 2, ty=(64 - H) / 2, sc=SC, p=PATHS)

OG = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="../assets/fonts/fonts.css">
<style>
  html,body{margin:0}
  .card{width:1200px;height:630px;box-sizing:border-box;overflow:hidden;position:relative;
        background:radial-gradient(120% 120% at 100% 0%, #14406E 0%, #071E38 55%);
        color:#fff;display:flex;flex-direction:column;justify-content:center;
        padding:0 96px;font-family:'Barlow',sans-serif}
  .rule{position:absolute;top:0;left:0;right:0;height:8px;background:#C4882A}
  .brand{display:flex;align-items:center;gap:14px;margin-bottom:44px}
  .brand svg{width:44px;height:48px;fill:#00AEEF}
  .brand span{font-family:'Montserrat',sans-serif;font-weight:700;font-size:34px;letter-spacing:-.01em}
  h1{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:98px;
     line-height:.97;margin:0 0 26px}
  h1 em{color:#D4A240;font-style:normal;display:block}
  p{font-size:27px;color:#B9CBDE;margin:0;max-width:34ch;line-height:1.4}
  .eyebrow{position:absolute;bottom:52px;left:96px;font-size:19px;letter-spacing:.16em;
     text-transform:uppercase;color:#00AEEF;font-weight:600}
</style>
<div class="card">
  <div class="rule"></div>
  <div class="brand">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 25.06 27.52">__PATHS__</svg>
    <span>be&rsquo;eri printers</span>
  </div>
  <h1>Secure card <em>personalization</em></h1>
  <p>For banks, financial institutions and card issuers worldwide.</p>
  <div class="eyebrow">Encoding &middot; embossing &middot; mailing &middot; fulfillment</div>
</div>""".replace('__PATHS__', PATHS)

tmp = os.path.join(ROOT, 'tools', '.og.html')
open(tmp, 'w', encoding='utf-8').write(OG)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM)

        pg = b.new_page(viewport={'width': 180, 'height': 180})
        pg.set_content(ICON)
        pg.wait_for_timeout(200)
        pg.screenshot(path=os.path.join(ROOT, 'assets', 'apple-touch-icon.png'))
        pg.close()

        pg = b.new_page(viewport={'width': 1200, 'height': 630})
        pg.goto('file://' + tmp)
        pg.wait_for_timeout(1200)
        pg.screenshot(path=os.path.join(ROOT, 'assets', 'og-image.png'))
        pg.close()
        b.close()
finally:
    os.remove(tmp)

print('wrote assets/apple-touch-icon.png and assets/og-image.png')
