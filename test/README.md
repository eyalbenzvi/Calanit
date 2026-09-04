# Test harness

Automated checks for `index.html`. Nothing here ships with the site.

## Setup

```sh
pip install playwright
playwright install chromium
```

If Chromium is already on the machine, point at it instead:
`CHROMIUM=/opt/pw-browsers/chromium python3 test/run_all.py`.

## Running

```sh
python3 test/run_all.py     # everything, in the right order; exits non-zero on failure
```

Run from anywhere — the probes resolve paths from their own location. Each one
rebuilds `test.html` from the current `index.html` first, so there is no way to
measure a stale build, and serves the project over a loopback HTTP server, so
the Content-Security-Policy behaves as it will in production.

Individually:

| Script | Checks | Fails the build |
|---|---|---|
| `../tools/preflight.py` | config, translation-table drift, assets | yes |
| `test_suite.py` | 151 cases: behaviour, a11y wiring, overflow at 6 widths × 3 languages, dark mode, no-JS, form paths, CSP and handover guarantees | yes |
| `contrast.py` | every text style against WCAG AA, light and dark, compositing the full background stack | yes |
| `wordfit.py` | headings whose longest unbreakable word cannot fit its box | yes |
| `widows.py` | blocks ending in a widow or conspicuously short last line, at 28 widths | no — report |
| `consistency.py` | components whose instances render with different styles | no — report |

`widows.py` and `consistency.py` are reports for a human to glance at. A
handful of widows in narrow card columns is ordinary typography, and the two
`consistency.py` entries that remain are deliberate: `.btn-primary` has a
light-ground variant, and `.cert-note` drops its bottom margin as the last
child.

## Notes

- `test.html` is generated and gitignored; delete it whenever.
- The probes measure the fonts the site actually serves (`assets/fonts/`), so
  layout numbers match production rather than a system-font fallback.
- `test_suite.py` asserts that the page makes **no third-party requests**. If
  you add an analytics script or a CDN reference, that test will fail — which
  is the point; see `docs/HANDOVER.md` before adding one.
