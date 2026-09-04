"""Detect a heading whose longest word cannot fit its content box -- the
condition that forces an ugly mid-word break. Clipping probes miss this
because overflow-wrap:break-word 'solves' the overflow by breaking the word."""
import os, sys
from _harness import page_url, launch
from playwright.sync_api import sync_playwright
JS = """()=>{const out=[];
 document.querySelectorAll('h1,h2,h3,.btn-primary,.btn-ghost,.btn-nav,.cta-band h2').forEach(el=>{
   const cs=getComputedStyle(el);
   if(cs.display==='none'||!el.offsetParent)return;
   const box=el.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
   const probe=document.createElement('span');
   probe.style.cssText='position:absolute;visibility:hidden;white-space:pre;'+
     'font-family:'+cs.fontFamily+';font-size:'+cs.fontSize+';font-weight:'+cs.fontWeight+
     ';font-style:'+cs.fontStyle+';letter-spacing:'+cs.letterSpacing+';text-transform:'+cs.textTransform;
   document.body.appendChild(probe);
   let worst=null;
   (el.innerText||el.textContent||'').split(/[ \\t\\n\\r]+/).filter(Boolean).forEach(w=>{
     probe.textContent=w;
     const ww=probe.getBoundingClientRect().width;
     if(ww>box+0.5&&(!worst||ww>worst.w))worst={word:w,w:Math.round(ww),box:Math.round(box)};});
   probe.remove();
   if(worst)out.push({sel:el.className||el.tagName,...worst});});
 return out;}"""
if __name__=='__main__':
    D=os.path.dirname(os.path.abspath(__file__)); bad=0
    with sync_playwright() as p:
        b = launch(p)
        for lang in ('en','ar','el'):
            for w in (1440,1120,980,768,620,500,430,414,390,375,360,320):
                pg=b.new_page(viewport={'width':w,'height':900})
                pg.goto(page_url())
                pg.evaluate("l=>localStorage.setItem('beeri-lang',l)",lang); pg.reload()
                pg.wait_for_timeout(420)
                pg.evaluate("()=>document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
                pg.wait_for_timeout(120)
                for r in pg.evaluate(JS):
                    bad+=1
                    print(f"  [{lang} @{w}] {r['sel']}: '{r['word']}' needs {r['w']}px, box is {r['box']}px")
                pg.close()
        b.close()
    print('headings whose longest word cannot fit:', bad)
    sys.exit(1 if bad else 0)
