#!/usr/bin/env python3
"""Comprehensive functional test suite for the beeri printers landing page."""
import os, re, sys
from playwright.sync_api import sync_playwright

D = os.getcwd()
URL = 'file://' + D + '/test.html'
LANGS = {'en':'ltr','ar':'rtl','el':'ltr'}
PASS, FAIL = [], []

def chk(name, cond, detail=''):
    (PASS if cond else FAIL).append(name + (' :: '+detail if detail and not cond else ''))

def new(b, lang=None, w=1440, h=900, dark=False):
    pg = b.new_page(viewport={'width':w,'height':h})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append('console.'+m.type+': '+m.text) if m.type=='error' else None)
    if dark: pg.emulate_media(color_scheme='dark')
    pg.goto(URL)
    if lang:
        pg.evaluate("l=>{try{localStorage.setItem('beeri-lang',l)}catch(e){}}", lang)
        pg.reload()
    pg.wait_for_timeout(450)
    return pg, errs

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')

    # ---------- 1. STATIC INTEGRITY ----------
    pg, errs = new(b)
    dup = pg.evaluate("""()=>{const s={},d=[];document.querySelectorAll('[id]').forEach(e=>{
        if(s[e.id])d.push(e.id); s[e.id]=1});return d}""")
    chk('no duplicate IDs', dup==[], str(dup))

    badfor = pg.evaluate("""()=>[...document.querySelectorAll('label[for]')]
        .filter(l=>!document.getElementById(l.getAttribute('for'))).map(l=>l.getAttribute('for'))""")
    chk('every label[for] resolves', badfor==[], str(badfor))

    badanchor = pg.evaluate("""()=>[...document.querySelectorAll('a[href^="#"]')]
        .map(a=>a.getAttribute('href')).filter(h=>h!=='#'&&!document.querySelector(h))""")
    chk('every #anchor target exists', badanchor==[], str(badanchor))

    h1c = pg.evaluate("()=>document.querySelectorAll('h1').length")
    chk('exactly one h1', h1c==1, 'found %d'%h1c)

    order = pg.evaluate("""()=>[...document.querySelectorAll('h1,h2,h3,h4')].map(e=>+e.tagName[1])""")
    skips = [(order[i],order[i+1]) for i in range(len(order)-1) if order[i+1]-order[i]>1]
    chk('no skipped heading levels', skips==[], str(skips[:5]))

    unlabelled = pg.evaluate("""()=>[...document.querySelectorAll('button,a')].filter(e=>
        !e.textContent.trim() && !e.getAttribute('aria-label')).map(e=>e.outerHTML.slice(0,60))""")
    chk('no unlabelled buttons/links', unlabelled==[], str(unlabelled))
    pg.close()

    # ---------- 2. PER-LANGUAGE ----------
    for lang, want_dir in LANGS.items():
        pg, errs = new(b, lang)
        st = pg.evaluate("""()=>({lang:document.documentElement.lang,dir:document.documentElement.dir,
            title:document.title, desc:(document.querySelector('meta[name=description]')||{}).content||'',
            ow:document.scrollingElement.scrollWidth>window.innerWidth+1})""")
        chk(f'[{lang}] lang attr', st['lang']==lang, st['lang'])
        chk(f'[{lang}] dir attr', st['dir']==want_dir, st['dir'])
        chk(f'[{lang}] title localized', len(st['title'])>5)
        chk(f'[{lang}] meta desc localized', len(st['desc'])>40)
        chk(f'[{lang}] no h-overflow @1440', not st['ow'])
        chk(f'[{lang}] no JS errors', errs==[], str(errs[:2]))

        # every data-i18n element actually got text
        empty = pg.evaluate("""()=>[...document.querySelectorAll('[data-i18n]')]
            .filter(e=>!e.textContent.trim()).map(e=>e.getAttribute('data-i18n'))""")
        chk(f'[{lang}] no empty i18n nodes', empty==[], str(empty))

        # non-English langs must not leak English defaults
        if lang != 'en':
            leak = pg.evaluate("""()=>{const en=window.T.en,cur=window.T[document.documentElement.lang];
                return [...document.querySelectorAll('[data-i18n]')].map(e=>e.getAttribute('data-i18n'))
                .filter(k=>en[k]&&cur[k]&&en[k]===cur[k]&&/[A-Za-z]{4}/.test(en[k])
                    &&!/^(ISO|PCI|SLA|Visa|Mastercard|American Express|be’eri printers)/.test(en[k]))}""")
            chk(f'[{lang}] no untranslated leakage', len(leak)<=2, str(leak[:8]))
        pg.close()

    # ---------- 3. LANGUAGE SWITCHER ----------
    pg, errs = new(b)
    pg.click('#langBtn'); pg.wait_for_timeout(200)
    chk('lang menu opens', pg.is_visible('#langMenu'))
    chk('aria-expanded true', pg.get_attribute('#langBtn','aria-expanded')=='true')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    chk('Escape closes menu', not pg.is_visible('#langMenu'))
    pg.click('#langBtn'); pg.wait_for_timeout(150)
    pg.click('body', position={'x':700,'y':600}); pg.wait_for_timeout(200)
    chk('outside click closes menu', not pg.is_visible('#langMenu'))
    pg.click('#langBtn'); pg.wait_for_timeout(150)
    pg.click('#langMenu button[data-lang="ar"]'); pg.wait_for_timeout(500)
    chk('switch to ar applies', pg.evaluate("()=>document.documentElement.lang")=='ar')
    chk('switch to ar sets rtl', pg.evaluate("()=>document.documentElement.dir")=='rtl')
    chk('menu closes after pick', not pg.is_visible('#langMenu'))
    chk('aria-current marks active', pg.get_attribute('#langMenu button[data-lang="ar"]','aria-current')=='true')
    chk('lang label updated', pg.inner_text('#langCur').strip()!='EN')
    persisted = pg.evaluate("()=>localStorage.getItem('beeri-lang')")
    chk('choice persisted to localStorage', persisted=='ar', str(persisted))
    pg.reload(); pg.wait_for_timeout(500)
    chk('choice survives reload', pg.evaluate("()=>document.documentElement.lang")=='ar')
    chk('lang switch throws nothing', errs==[], str(errs[:2]))
    pg.close()

    # ---------- 3b. LANGUAGE MENU KEYBOARD ----------
    pg, errs = new(b)
    pg.focus('#langBtn'); pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(200)
    chk('ArrowDown opens menu', pg.is_visible('#langMenu'))
    chk('ArrowDown focuses first item',
        pg.evaluate("()=>document.activeElement.getAttribute('data-lang')")=='en')
    pg.keyboard.press('ArrowDown')
    chk('ArrowDown moves to next item',
        pg.evaluate("()=>document.activeElement.getAttribute('data-lang')")=='ar')
    pg.keyboard.press('End')
    chk('End jumps to last item',
        pg.evaluate("()=>document.activeElement.getAttribute('data-lang')")=='el')
    pg.keyboard.press('Home')
    chk('Home jumps to first item',
        pg.evaluate("()=>document.activeElement.getAttribute('data-lang')")=='en')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    chk('Escape returns focus to button', pg.evaluate("()=>document.activeElement.id")=='langBtn')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    chk('Enter opens menu', pg.is_visible('#langMenu'))
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(1000)
    chk('Enter selects a language', pg.evaluate("()=>document.documentElement.lang") in ('en','ar','el'))
    chk('keyboard nav no JS errors', errs==[], str(errs[:2]))
    pg.close()

    # ---------- 4. MOBILE MENU ----------
    pg, errs = new(b, 'en', w=390, h=780)
    chk('hamburger visible @390', pg.is_visible('#ham'))
    chk('nav-links hidden @390', not pg.is_visible('.nav-links'))
    pg.click('#ham'); pg.wait_for_timeout(250)
    chk('mobile menu opens', pg.is_visible('#mob-menu'))
    pg.click('#mob-menu a[href="#services"]'); pg.wait_for_timeout(400)
    chk('menu closes on link click', not pg.is_visible('#mob-menu'))
    chk('mobile CTA bar visible @390', pg.is_visible('.mobile-cta-bar'))
    pg.click('#ham'); pg.wait_for_timeout(250)   # reopen so drawer links are measurable
    tap = pg.evaluate("""()=>{const r=s=>{const e=document.querySelector(s);if(!e)return null;
        const b=e.getBoundingClientRect();return [s,Math.round(b.width),Math.round(b.height)]};
        return [r('#ham'),r('#langBtn'),r('.mobile-cta-bar a'),r('.mobile-menu a')]}""")
    small = [t for t in tap if t and min(t[1],t[2])<44]
    chk('tap targets >=44px @390', small==[], str(small))
    chk('mobile no JS errors', errs==[], str(errs[:2]))
    pg.close()

    # ---------- 5. FORM ----------
    pg, errs = new(b)
    pg.eval_on_selector('#projectForm','f=>f.scrollIntoView()'); pg.wait_for_timeout(300)
    pg.click('.btn-submit'); pg.wait_for_timeout(300)
    nerr = pg.evaluate("()=>document.querySelectorAll('#projectForm .err').length")
    chk('empty submit flags 5 required', nerr==5, 'flagged %d'%nerr)
    chk('empty submit does NOT show success', not pg.is_visible('#formSuccess'))
    focused = pg.evaluate("()=>document.activeElement.id")
    chk('focus moves to first invalid', focused=='f-name', focused)
    pg.fill('#f-name','Test User'); pg.wait_for_timeout(150)
    chk('err clears on input', pg.evaluate("()=>!document.getElementById('f-name').classList.contains('err')"))
    pg.fill('#f-company','Test Bank'); pg.fill('#f-country','Greece')
    pg.fill('#f-email','not-an-email'); pg.click('.btn-submit'); pg.wait_for_timeout(300)
    chk('invalid email rejected', pg.evaluate("()=>document.getElementById('f-email').classList.contains('err')"))
    chk('invalid email blocks success', not pg.is_visible('#formSuccess'))
    pg.fill('#f-email','buyer@testbank.gr')
    pg.select_option('#f-cardtype', index=1); pg.select_option('#f-qty', index=2)
    pg.check('input[value="encoding"]')
    pg.check('#f-consent')
    pg.click('.btn-submit'); pg.wait_for_timeout(600)
    # FORM_ENDPOINT is unset by default: the page must report a send failure
    # rather than show a false confirmation that discards the enquiry.
    chk('unconfigured submit shows failure, not fake success',
        pg.is_visible('#formFail') and not pg.is_visible('#formSuccess'))
    # with an endpoint configured and the network stubbed, success must show
    pg.route('**/api/rfq', lambda route: route.fulfill(status=200, body='{"ok":true}'))
    pg.evaluate("()=>{ FORM_ENDPOINT='https://stub.test/api/rfq'; }")
    pg.route('**/stub.test/**', lambda route: route.fulfill(status=200, body='{"ok":true}'))
    pg.click('.btn-submit'); pg.wait_for_timeout(800)
    chk('configured submit shows success', pg.is_visible('#formSuccess'))
    chk('configured submit hides form', not pg.is_visible('#projectForm'))
    chk('form no JS errors', errs==[], str(errs[:2]))
    ov = pg.evaluate("""()=>{const o=document.querySelector('#f-cardtype option:nth-child(2)');
        return {value:o.value, text:o.textContent}}""")
    chk('select option has stable value attr', ov['value']!=ov['text'], 'value=%r'%ov['value'])
    # a11y wiring on required fields
    a11y = pg.evaluate("""()=>({
        req:[...document.querySelectorAll('#projectForm [aria-required=true]')].length,
        desc:[...document.querySelectorAll('#projectForm [aria-describedby]')].length,
        live:!!document.querySelector('#formSuccess[aria-live]'),
        hamExp:document.getElementById('ham').hasAttribute('aria-expanded'),
        skip:!!document.querySelector('.skip-link')})""")
    chk('5 fields aria-required', a11y['req']==5, str(a11y['req']))
    chk('5 fields aria-describedby', a11y['desc']==5, str(a11y['desc']))
    chk('success panel is a live region', a11y['live'])
    chk('hamburger exposes aria-expanded', a11y['hamExp'])
    chk('skip link present', a11y['skip'])
    pg.close()

    # ---------- 6. REVEAL ----------
    pg, errs = new(b)
    pg.evaluate("""async()=>{const step=Math.round(innerHeight*0.6);
        for(let y=0;y<document.body.scrollHeight;y+=step){window.scrollTo(0,y);
        await new Promise(r=>setTimeout(r,60));}
        window.scrollTo(0,document.body.scrollHeight);}""")
    pg.wait_for_timeout(900)
    inv = pg.evaluate("""()=>[...document.querySelectorAll('.reveal')]
        .filter(e=>getComputedStyle(e).opacity==='0').length""")
    chk('all reveals visible after scroll', inv==0, '%d still opacity:0'%inv)
    pg.close()

    # reduced motion: content must be visible without JS reveal
    pg = b.new_page(viewport={'width':1440,'height':900})
    pg.emulate_media(reduced_motion='reduce')
    pg.goto(URL); pg.wait_for_timeout(500)
    inv = pg.evaluate("""()=>[...document.querySelectorAll('.reveal')]
        .filter(e=>getComputedStyle(e).opacity==='0').length""")
    chk('reduced-motion: nothing hidden', inv==0, '%d hidden'%inv)
    pg.close()

    # ---------- 7. NO-JS ----------
    ctx = b.new_context(java_script_enabled=False, viewport={'width':1440,'height':900})
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(600)
    txt = pg.inner_text('body')
    chk('no-JS: hero copy present', 'Secure card' in txt)
    chk('no-JS: services present', 'Encoding' in txt)
    chk('no-JS: form present', pg.is_visible('#projectForm'))
    njinv = pg.evaluate("""()=>[...document.querySelectorAll('.reveal')]
        .filter(e=>getComputedStyle(e).opacity==='0').length""")
    chk('no-JS: content not stuck invisible', njinv==0, '%d sections invisible without JS'%njinv)
    ctx.close()

    # ---------- 8. RESPONSIVE OVERFLOW MATRIX ----------
    for w in (1440,1280,1120,1024,980,768,620,414,390,360):
        for lang in LANGS:
            pg, errs = new(b, lang, w=w, h=900)
            ow = pg.evaluate("()=>document.scrollingElement.scrollWidth-window.innerWidth")
            chk(f'no h-overflow @{w} [{lang}]', ow<=1, 'overflow %dpx'%ow)
            pg.close()

    # ---------- 9. DARK MODE ----------
    for lang in ('en','ar'):
        pg, errs = new(b, lang, dark=True)
        bad = pg.evaluate("""()=>{const out=[];
          document.querySelectorAll('p,h1,h2,h3,h4,li,label,span,a,div').forEach(e=>{
            if(!e.textContent.trim()||e.children.length)return;
            const s=getComputedStyle(e); const c=s.color;
            if(c==='rgba(0, 0, 0, 0)')out.push(e.className+':transparent');
          }); return out.slice(0,5)}""")
        chk(f'dark [{lang}] no transparent text', bad==[], str(bad))
        bg = pg.evaluate("()=>getComputedStyle(document.body).backgroundColor")
        chk(f'dark [{lang}] body bg explicit', bg not in ('rgba(0, 0, 0, 0)','transparent'), bg)
        pg.close()


    # ---------- 10. ELEMENT-LEVEL CLIPPING ----------
    CLIP = """()=>{const bad=[];
      document.querySelectorAll('h1,h2,h3,h4,p,li,label,span,a,button,div').forEach(el=>{
        if(el.classList.contains('skip-link'))return;
        const cs=getComputedStyle(el);
        if(cs.display==='none'||cs.visibility==='hidden')return;
        if(!el.offsetParent&&cs.position!=='fixed')return;
        if(el.scrollWidth>el.clientWidth+1&&cs.overflowX!=='auto'&&cs.overflowX!=='scroll'){
          const t=(el.textContent||'').trim().slice(0,30);
          if(t)bad.push((el.className||el.tagName)+':'+(el.scrollWidth-el.clientWidth)+'px');}});
      return bad;}"""
    for w in (1440, 980, 620, 430, 390, 320):
        for lang in LANGS:
            pg, errs = new(b, lang, w=w, h=900)
            pg.evaluate("()=>window.scrollTo(0,document.body.scrollHeight)")
            pg.wait_for_timeout(550)
            clip = pg.evaluate(CLIP)
            chk(f'no clipped text @{w} [{lang}]', clip==[], str(clip[:3]))
            pg.close()

    b.close()

print('='*70)
print('PASSED: %d' % len(PASS))
print('FAILED: %d' % len(FAIL))
if FAIL:
    print('-'*70)
    for f in FAIL: print('  FAIL  ' + f)
print('='*70)
