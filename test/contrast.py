"""WCAG contrast audit that composites the full semi-transparent background
chain down to an opaque base before comparing."""
import os, sys
from _harness import page_url, launch
from playwright.sync_api import sync_playwright

def lin(c):
    c/=255.0
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def lum(p): return 0.2126*lin(p[0])+0.7152*lin(p[1])+0.0722*lin(p[2])
def ratio(f,b):
    a,c=lum(f),lum(b)
    if a<c: a,c=c,a
    return (a+0.05)/(c+0.05)
def parse(s):
    v=[float(x) for x in s[s.index('(')+1:s.index(')')].replace('/',',').split(',')]
    return v[:3],(v[3] if len(v)>3 else 1.0)
def blend(fg,fa,bg): return tuple(fa*f+(1-fa)*b for f,b in zip(fg,bg))

# collect the whole ancestor background stack, so alpha layers composite correctly
JS = """()=>{const out=[];const seen=new Set();
 document.querySelectorAll('p,li,label,span,a,h1,h2,h3,h4,div,button').forEach(el=>{
  const t=(el.textContent||'').trim(); if(!t||el.children.length)return;
  // clipped-but-present text: the skip link only shows on focus, the bot
  // trap never shows at all. Neither is read by a sighted visitor.
  if(el.closest('.skip-link,.bot-trap,[aria-hidden="true"]'))return;
  const cs=getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden')return;
  if(!el.offsetParent&&cs.position!=='fixed')return;
  let bgk='';{let n=el;while(n&&n!==document.documentElement){const c=getComputedStyle(n).backgroundColor;if(c&&c!=='rgba(0, 0, 0, 0)'&&c!=='transparent')bgk+=c+';';n=n.parentElement;}}
  const key=(el.className||el.tagName)+'|'+cs.color+'|'+cs.fontSize+'|'+cs.fontWeight+'|'+bgk;
  if(seen.has(key))return; seen.add(key);
  const stack=[];let n=el;
  while(n&&n!==document.documentElement){
    const c=getComputedStyle(n).backgroundColor;
    if(c&&c!=='rgba(0, 0, 0, 0)'&&c!=='transparent')stack.push(c);
    n=n.parentElement;}
  const rc=getComputedStyle(document.documentElement).backgroundColor;
  if(rc&&rc!=='rgba(0, 0, 0, 0)')stack.push(rc);
  out.push({sel:el.className||el.tagName,fg:cs.color,stack,px:parseFloat(cs.fontSize),
            w:cs.fontWeight,t:t.slice(0,26)});});
 return out;}"""

def audit(pg, base):
    rows = pg.evaluate(JS); fails=[]
    for r in rows:
        bg = base
        for c in reversed(r['stack']):          # outermost first
            col, a = parse(c); bg = blend(col, a, bg)
        fg, fa = parse(r['fg']); eff = blend(fg, fa, bg)
        cr = ratio(eff, bg)
        large = r['px'] >= 24 or (r['px'] >= 18.66 and int(r['w']) >= 700)
        need = 3.0 if large else 4.5
        if cr < need - 0.01:
            fails.append((round(cr,2), need, r['sel'][:32], round(r['px']), r['t']))
    return rows, fails

if __name__ == '__main__':
    URL = page_url()
    with sync_playwright() as p:
        b = launch(p)
        bad=0
        for scheme, base in (('light',(255,255,255)), ('dark',(10,10,10))):
            pg=b.new_page(viewport={'width':1440,'height':900})
            pg.emulate_media(color_scheme=scheme)
            pg.goto(URL); pg.wait_for_timeout(500)
            pg.evaluate("()=>document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
            pg.wait_for_timeout(150)
            rows, fails = audit(pg, base)
            bad += len(fails)
            print(f'--- {scheme}: {len(rows)} text styles, {len(fails)} below AA')
            for f in sorted(fails):
                print('   %.2f:1 (need %.1f)  %-32s %2dpx  %s' % f)
            pg.close()
        b.close()
        sys.exit(1 if bad else 0)
