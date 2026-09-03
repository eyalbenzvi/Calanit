# Test harness

Checks for `index.html`. The page is an artifact *body fragment* (no
`<html>`/`<head>`/`<body>` of its own — the host supplies them), so the harness
first wraps it into a standalone page.

## Setup

```sh
pip install playwright
playwright install chromium     # or point at an existing Chromium, see below
```

If Chromium already exists (e.g. `/opt/pw-browsers/chromium`), the scripts pick
it up via `executable_path`; edit that constant if your path differs.

## Running

```sh
cd test
python3 fetch_fonts.py   # once: cache the webfonts into ./fonts (needs network)
python3 wrap.py          # regenerate test.html from ../index.html — rerun after any edit
python3 test_suite.py    # 155 functional cases
python3 contrast.py      # WCAG AA audit, both themes (exit 1 on failure)
```

`fetch_fonts.py` mirrors the eight font families the page requests into
`./fonts` (about 1.8 MB, gitignored) and rewrites the stylesheet to point at
them. `wrap.py` then uses that cache, so layout assertions measure real font
metrics offline and fast.

Skipping the fetch is supported but slower, and the run then needs network
access — without either the cache or the network, text is measured in fallback
fonts and every layout assertion becomes meaningless. Re-run `fetch_fonts.py`
if you change the font request in `index.html`.

## What `test_suite.py` covers

| Area | Checks |
|---|---|
| Static integrity | duplicate IDs, `label[for]` targets, `#anchor` targets, single `h1`, no skipped heading levels, no unlabelled controls |
| Per language (en/he/ar/el) | `lang` and `dir`, localized `<title>` and meta description, no empty i18n nodes, no untranslated leakage, no JS errors |
| Language switcher | open/close by click, Escape, outside click, `aria-expanded`, `aria-current`, localStorage persistence, survives reload |
| Keyboard | Arrow/Home/End navigation, Enter to open and select, focus return on Escape |
| Mobile | hamburger visibility, drawer open/close, sticky CTA bar, 44px minimum tap targets |
| Form | required-field flagging, email validation, error clearing on input, focus to first invalid, unconfigured submit reports failure rather than false success, stubbed endpoint shows success, stable `<option>` values, `aria-required`/`aria-describedby`, live-region success panel |
| Reveal animations | all content visible after scrolling, nothing hidden under `prefers-reduced-motion` |
| No JavaScript | hero, services and form still present and visible |
| Responsive | zero horizontal overflow at 10 widths × 4 languages |
| Dark mode | no transparent text, explicit body background |
| Clipping | no element clipping its own text at 6 widths × 4 languages |

## Note on the contact form

`FORM_ENDPOINT` in `index.html` is `null`. Until it points at a real endpoint
the form deliberately reports a send failure instead of showing a success
message, so an enquiry is never silently discarded. `test_suite.py` asserts
both behaviours (unconfigured → failure; stubbed endpoint → success).
