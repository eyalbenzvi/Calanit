# Editing the content

Everything a visitor reads lives in `index.html`. There is no CMS and no build
step: edit the file, run one check, deploy. Aimed at whoever makes the
occasional wording change — the deployment and security side is in
[HANDOVER.md](HANDOVER.md).

**After every edit, run:**

```bash
python3 tools/preflight.py --content
```

It takes a second and catches the mistakes that are invisible in a browser —
most importantly a string changed in one place but not the other, which leaves
English on screen for Arabic and Greek visitors with no error anywhere.

---

## How a string reaches the screen

Every piece of text exists in **two** places, and both have to change
together:

1. **the markup**, as the element's own text — this is what a visitor sees on
   first paint, and all they ever see with scripting off;
2. **the translation table** for each language — `T.en`, `T.ar`, `T.el`, near
   the bottom of the file — keyed by the same name.

```html
<h2 data-i18n="svc.h2">Personalization services</h2>
```

```js
T.en = { …, "svc.h2":"Personalization services", … };
T.ar = { …, "svc.h2":"خدمات تخصيص البطاقات", … };
T.el = { …, "svc.h2":"Υπηρεσίες εξατομίκευσης", … };
```

So changing that heading means four edits: the markup, `T.en`, `T.ar`, `T.el`.
Miss the markup and English visitors briefly see the old wording. Miss `T.ar`
and Arabic visitors see the English. `preflight.py` reports both.

Three variants exist for text that is not an element's content:

| Attribute | Sets | Also needs |
|---|---|---|
| `data-i18n` | the element's text | the literal text inside the element |
| `data-i18n-ph` | a `placeholder` | the literal `placeholder="…"` |
| `data-i18n-aria` | an `aria-label` | the literal `aria-label="…"` |

`data-i18n-html` does not exist any more, on purpose — see
[Things not to do](#things-not-to-do).

---

## Common changes

### Reword something

Find the key. If you can see the English text on the page, search for it — it
appears in the markup and in `T.en`. Change all four places (markup, `T.en`,
`T.ar`, `T.el`), then run preflight.

If you have no Arabic or Greek translation to hand, still change all three
tables: leaving the old wording in `T.ar` is worse than a rough translation,
because it silently contradicts the English. Mark it for a translator.

### Add or remove a service card

The cards are a plain grid — copy an existing `<div class="svc-card">`, give
the new one fresh keys (`s12.t`, `s12.p`), and add those keys to all three
tables. To remove one, delete the block and its keys; preflight will warn
about keys left behind with nothing referencing them.

**Keep the checkbox list in step.** The "Services required" checkboxes in the
form (`chk1`–`chk8`) mirror the service cards, and a checkbox has to be worded
exactly like the card it refers to — a language reviewer will flag it
otherwise. If you add a card that customers should be able to tick, add the
checkbox too, with a stable `value` (see below).

### Change a select option

Options carry a **stable machine value** and a translated label:

```html
<option value="payment" data-i18n="ct1">Payment card (credit / debit)</option>
```

The `value` is what the form submits, so it must not change once the endpoint
is live — reports and CRM records would split in two. The label can change
freely. Never remove the `value` attribute: without it the browser submits the
label, and a submission then means something different in each language.

### Change the three counter figures

`30+`, `50M+`, `60+` in the About section, and their labels
(`about.c1`–`about.c3`). The page currently says "figures are indicative"
(`counter.note`); if you replace them with audited numbers, that note can go —
delete the element and its key from all three tables.

### The copyright year

Leave it alone. The strings contain a `{year}` token that the page replaces
with the current year at load. The literal `2026` in the markup is only the
fallback for visitors with scripting off; it is not worth updating.

---

## Adding a fourth language

1. Add the code to `LANGS` near the i18n engine, with its writing direction:
   `fr:{short:'FR', dir:'ltr'}`.
2. Add a `<button data-lang="fr">` to `#langMenu`, matching the others.
3. Copy the whole `T.en` block to `T.fr` and translate every value. All keys
   must be present — a missing key falls back to English silently.
4. If the language needs different fonts or heading sizes, add a
   `:root[lang="fr"]` token block next to the Arabic and Greek ones. Check
   that the fonts in `assets/fonts/` cover the script; if not, add the family
   to `tools/build_fonts.py` and rerun it.
5. For a right-to-left language, set `dir:'rtl'` and check the layout: the CSS
   uses logical properties and mirrors automatically, but verify the nav,
   the form grid and the process timeline.
6. Add the code to `LANGS` in `test/test_suite.py` and to `docs/`, and add
   `<meta property="og:locale:alternate" content="fr">` in `<head>`.
7. Run `python3 test/run_all.py` — the layout probes will catch text that is
   too long for its box in the new language, which is the usual problem.

---

## Things not to do

**Do not put HTML in a translation string.** No `<br>`, `<em>` or `<strong>`
in a table value. Every string is written to the page as plain text, so tags
would appear literally — and re-introducing an HTML path would mean any string
in the tables could inject markup. Text that needs two styles gets two keys
and two elements; the hero headline (`hero.h1a`, `hero.h1b`) is the pattern.

**Do not use `left`, `right`, `margin-left` or `padding-right` in new CSS.**
Arabic renders right-to-left, and the layout mirrors only because it is
written with logical properties: `inset-inline-start`, `margin-inline-start`,
`border-inline-end`, `text-align: start`. A physical property looks fine in
English and breaks Arabic.

**Do not define a colour only inside a dark-mode block.** Colours come from
tokens on `:root`; the dark blocks redefine the tokens, not the components. A
colour whose only definition sits inside `@media (prefers-color-scheme: dark)`
disappears in light mode.

**Do not add a certification, standard, statistic, client name or SLA figure
that has not been confirmed by the company.** The page is deliberately hedged
in several places for this reason — the open items are listed in
[HANDOVER.md](HANDOVER.md#facts-only-the-client-can-supply).

**Do not delete the non-breaking spaces.** Several strings contain U+00A0 —
around `&`, before the `·` separators, and inside standards codes like
`ISO/IEC 7810`. They stop a line breaking in an ugly place. They look like
ordinary spaces in an editor; if you retype such a string, the glue is gone,
and `widows.py` will start reporting the heading.

---

## Checking your work

```bash
python3 tools/preflight.py --content     # after every edit, one second
python3 test/run_all.py                  # before deploying, a few minutes
python3 tools/build_standalone.py        # refresh the one-file review copy
```

`run_all.py` needs Playwright and Chromium (`pip install playwright &&
playwright install chromium`). It drives a real browser at 28 viewport widths
in all three languages and reports text that overflows, headings whose longest
word cannot fit, colour combinations below WCAG AA, and short last lines.
