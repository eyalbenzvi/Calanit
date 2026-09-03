#!/usr/bin/env python3
"""Find components whose instances render inconsistently.

For every class used more than once, compare the computed style of each
instance across a set of visual properties. A class with more than one
distinct signature is either an intentional variant or a cascade collision
(a generic descendant rule out-specifying the component class). This is the
check that would have caught the eyebrow rendering at four different sizes.
"""
import os, sys, json
from playwright.sync_api import sync_playwright

PROPS = ['fontSize','fontWeight','fontFamily','lineHeight','letterSpacing','color',
         'textTransform','marginTop','marginBottom','paddingTop','paddingBottom',
         'paddingLeft','paddingRight','borderRadius','borderTopWidth','backgroundColor',
         'textAlign','opacity']

JS = """
(props) => {
  const byClass = {};
  document.querySelectorAll('[class]').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    if (!el.offsetParent && cs.position !== 'fixed') return;
    const sig = {};
    props.forEach(p => sig[p] = cs[p]);
    el.className.split(/\\s+/).filter(Boolean).forEach(cls => {
      if (/^(reveal|visible|full|open|err|js|mir|s-\\w+|sh-tight)$/.test(cls)) return;
      (byClass[cls] = byClass[cls] || []).push({
        sig: JSON.stringify(sig),
        where: (el.closest('section') || el.closest('footer') || el.closest('header') || {}).id
               || (el.closest('.cta-band') ? 'cta-band' : 'other'),
        text: (el.textContent || '').trim().slice(0, 22)
      });
    });
  });
  const out = [];
  Object.entries(byClass).forEach(([cls, items]) => {
    if (items.length < 2) return;
    const groups = {};
    items.forEach(it => (groups[it.sig] = groups[it.sig] || []).push(it));
    const sigs = Object.keys(groups);
    if (sigs.length < 2) return;
    // report which properties actually differ
    const parsed = sigs.map(s => JSON.parse(s));
    const diff = props.filter(p => new Set(parsed.map(o => o[p])).size > 1);
    out.push({
      cls, instances: items.length, variants: sigs.length, diff,
      detail: sigs.map(s => ({
        n: groups[s].length,
        where: [...new Set(groups[s].map(i => i.where))].slice(0, 4),
        vals: Object.fromEntries(diff.map(p => [p, JSON.parse(s)[p]]))
      }))
    });
  });
  return out.sort((a, b) => b.instances - a.instances);
}
"""

def run(width=1440, lang='en', scheme='light'):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = b.new_page(viewport={'width': width, 'height': 1000})
        pg.emulate_media(color_scheme=scheme)
        pg.goto('file:///home/user/Calanit/test/test.html')
        if lang != 'en':
            pg.evaluate("l=>localStorage.setItem('beeri-lang',l)", lang); pg.reload()
        pg.wait_for_timeout(600)
        pg.evaluate("()=>document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
        pg.wait_for_timeout(150)
        res = pg.evaluate(JS, PROPS)
        pg.close(); b.close()
    return res

if __name__ == '__main__':
    res = run()
    print(f'classes rendering inconsistently: {len(res)}\n')
    for r in res:
        print(f"  .{r['cls']}  ({r['instances']} instances, {r['variants']} variants)")
        print(f"      differs in: {', '.join(r['diff'])}")
        for d in r['detail']:
            print(f"        x{d['n']:2d} {str(d['where']):38s} {json.dumps(d['vals'], ensure_ascii=False)[:110]}")
        print()
    sys.exit(1 if res else 0)
