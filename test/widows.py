#!/usr/bin/env python3
"""Detect widows and short final lines by measuring REAL line boxes.

For every text block it splits the text into word ranges, gets each word's
client rect, groups words by line top, and then reports blocks whose final
line holds a single word or is very short relative to the widest line.
Nothing overflows or clips in these cases, which is why overflow probes
cannot see them.
"""
import os, sys, json
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const SEL = 'p,h1,h2,h3,h4,li,label,a.btn-nav,.btn-primary,.btn-ghost,'
            + '.btn-dark,.btn-submit,.cert-badge,.counter-label,.ref-type,.svc-checks-label,'
            + '.mobile-cta-bar a,.chk span,.step h3,.eyebrow,.hero-tagline,'
            + '.footer-bottom span,.footer-col a,.ref-row span,.logo-sub';
  const out = [];
  document.querySelectorAll(SEL).forEach(el => {
    // only leaf text blocks
    if (el.children.length) return;
    const txt = (el.textContent || '').trim();
    if (!txt || txt.length < 12) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    if (!el.offsetParent && cs.position !== 'fixed') return;
    const node = el.firstChild;
    if (!node || node.nodeType !== 3) return;

    // map every word to its line box via Range rects
    const raw = node.data;
    const lines = new Map();          // rounded top -> {words, left, right}
    let i = 0;
    while (i < raw.length) {
      while (i < raw.length && /\s/.test(raw[i])) i++;
      const start = i;
      while (i < raw.length && !/\s/.test(raw[i])) i++;
      if (i === start) break;
      const r = document.createRange();
      r.setStart(node, start); r.setEnd(node, i);
      const rect = r.getBoundingClientRect();
      r.detach && r.detach();
      if (!rect.width) continue;
      const key = Math.round(rect.top);
      const rec = lines.get(key) || {words: 0, left: Infinity, right: -Infinity, text: []};
      rec.words++;
      rec.left = Math.min(rec.left, rect.left);
      rec.right = Math.max(rec.right, rect.right);
      rec.text.push(raw.slice(start, i));
      lines.set(key, rec);
    }
    const ls = [...lines.entries()].sort((a, b) => a[0] - b[0]).map(e => e[1]);
    if (ls.length < 2) return;
    const widths = ls.map(l => l.right - l.left);
    const maxW = Math.max(...widths);
    const last = ls[ls.length - 1];
    const lastW = last.right - last.left;
    const ratio = lastW / maxW;
    const single = last.words === 1;
    if ((single && ratio < 0.34) || ratio < 0.20) {
      out.push({
        sel: el.className || el.tagName,
        key: el.getAttribute('data-i18n') || '',
        lines: ls.length,
        lastWords: last.words,
        ratio: +ratio.toFixed(2),
        lastText: last.text.join(' ').slice(0, 34),
        full: txt.slice(0, 52),
        fs: Math.round(parseFloat(cs.fontSize)),
        boxW: Math.round(maxW)
      });
    }
  });
  return out;
}
"""

WIDTHS = [1440,1366,1280,1200,1120,1080,1024,980,940,900,860,820,768,720,700,
          660,620,580,540,500,460,430,414,390,375,360,340,320]
LANGS = ['en','ar','el']

def run(widths=WIDTHS, langs=LANGS, verbose=True):
    url = 'file:///home/user/Calanit/test/test.html'
    found = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        for lang in langs:
            for w in widths:
                pg = b.new_page(viewport={'width': w, 'height': 1000})
                pg.goto(url)
                pg.evaluate("l=>localStorage.setItem('beeri-lang',l)", lang)
                pg.reload(); pg.wait_for_timeout(430)
                pg.evaluate("()=>document.querySelectorAll('.reveal')"
                            ".forEach(e=>e.classList.add('visible'))")
                pg.wait_for_timeout(120)
                for r in pg.evaluate(JS):
                    sig = (r['sel'], r['key'] or r['full'][:24], lang)
                    found.setdefault(sig, []).append(w)
                pg.close()
        b.close()
    if verbose:
        for sig, ws in sorted(found.items(), key=lambda kv: -len(kv[1])):
            sel, key, lang = sig
            print(f'  [{lang}] {sel:26s} {key:16s} at {len(ws)} widths: {sorted(ws, reverse=True)[:9]}')
    total = sum(len(v) for v in found.values())
    print(f'\ndistinct blocks with a widow/short last line: {len(found)}   (occurrences: {total})')
    return found

if __name__ == '__main__':
    f = run()
    sys.exit(1 if f else 0)
