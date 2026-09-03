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
python3 wordfit.py       # headings whose longest word cannot fit (exit 1 on failure)
python3 widows.py        # widows / conspicuously short final lines
python3 consistency.py   # components whose instances render differently
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

`wordfit.py` exists because clipping probes cannot catch this class of bug:
`overflow-wrap:break-word` "solves" an overflowing heading by splitting the
word across lines, so nothing overflows and nothing is clipped -- but the
heading reads as "Personalizatio / n". It measures each heading's longest word
against its content box instead, across 4 languages x 12 widths.

`widows.py` measures real line boxes (a Range per word, grouped by line top)
and reports blocks whose final line holds one short word or is under a fifth of
the measure. Like `wordfit.py` this is invisible to overflow probes -- nothing
overflows, the text simply reads as unbalanced. Some residue is expected and
acceptable: a short last line inside a narrow two-column card is ordinary
typography, not a defect.

`consistency.py` compares the computed style of every instance of each
repeated component class. More than one signature means either an intentional
variant or a cascade collision -- a generic descendant rule out-specifying the
component class. This is the check that would have caught `.eyebrow` rendering
at four different sizes because `.section-hdr p` (0,1,1) beat `.eyebrow`
(0,1,0). Expect some intentional variants in its output (light vs dark
grounds, centred sections); read it as a list to triage, not a pass/fail.

`index.html` is a complete standalone document: it opens correctly from disk,
can be hosted as-is, and still renders when the artifact host wraps it in its
own skeleton. Both paths are verified.

## Note on the contact form

`FORM_ENDPOINT` in `index.html` is `null`. Until it points at a real endpoint
the form deliberately reports a send failure instead of showing a success
message, so an enquiry is never silently discarded. `test_suite.py` asserts
both behaviours (unconfigured → failure; stubbed endpoint → success).
