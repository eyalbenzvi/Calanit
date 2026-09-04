# Be’eri Printers — card personalization landing page

A static, single-page site in three languages (English by default, Arabic,
Greek), marketing card-personalization services to banks, financial
institutions, fintechs, government bodies and card issuers.

No build step, no dependencies, no server-side code. To publish, copy
`index.html` and `assets/` to a web root.

```
index.html    the whole page — markup, CSS, JS, translations
assets/       self-hosted fonts, icons, social preview image
docs/         handover and content-editing guides
tools/        pre-deploy checks and asset generators
test/         automated browser checks
build/        generated review copy (not committed, not for deployment)
```

## A copy to send round for approval

```bash
python3 tools/build_standalone.py
```

Writes `build/beeri-landing-standalone.html`: one file, ~1 MB, with the fonts
and icon inlined. It opens from a desktop or an email attachment, works with
no network, and requests nothing from anywhere — so it can go to business
stakeholders for sign-off without a server. It is a review copy; the site to
publish is `index.html` plus `assets/`.

## Before it goes live

Two configuration values are still unset, and the contact form cannot deliver
a lead until the first one is:

```bash
python3 tools/preflight.py     # tells you exactly what is outstanding
```

There is also a short list of facts only the company can confirm —
certifications, contact details, the three headline figures. See
[docs/HANDOVER.md](docs/HANDOVER.md#launch-checklist).

## Documentation

- **[docs/HANDOVER.md](docs/HANDOVER.md)** — deploying, response headers, the
  form endpoint, the launch checklist, how the page is built.
- **[docs/CONTENT-EDITING.md](docs/CONTENT-EDITING.md)** — changing wording,
  adding a service card, adding a language.
- **[test/README.md](test/README.md)** — what the automated checks cover.

## Checks

```bash
python3 tools/preflight.py --content   # after every content edit — one second
python3 test/run_all.py                # before every deploy — needs Playwright
```
