#!/usr/bin/env python3
"""Run every check in one go.

    python3 test/run_all.py

Order matters: preflight is cheap and catches the kind of mistake that would
make the browser probes meaningless (a translation key gone missing, an asset
that is not there). Exit status is non-zero if any hard check fails, so this
is the one command to put in CI.

widows.py and consistency.py are reports, not pass/fail gates — they print
what a typographer or designer should glance at, and never fail the run.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

GATES = [
    ('preflight  (config, i18n, assets)', [os.path.join(ROOT, 'tools', 'preflight.py'), '--content']),
    ('test_suite (behaviour, a11y, layout)', [os.path.join(HERE, 'test_suite.py')]),
    ('contrast   (WCAG AA, light and dark)', [os.path.join(HERE, 'contrast.py')]),
    ('wordfit    (headings that cannot fit)', [os.path.join(HERE, 'wordfit.py')]),
]
REPORTS = [
    ('widows      (short last lines)', [os.path.join(HERE, 'widows.py')]),
    ('consistency (components that drift)', [os.path.join(HERE, 'consistency.py')]),
]

failed = []
for label, cmd in GATES:
    print('\n' + '=' * 72)
    print('== %s' % label)
    print('=' * 72)
    if subprocess.run([sys.executable] + cmd).returncode != 0:
        failed.append(label)

for label, cmd in REPORTS:
    print('\n' + '-' * 72)
    print('-- %s   (report only)' % label)
    print('-' * 72)
    subprocess.run([sys.executable] + cmd)

print('\n' + '=' * 72)
if failed:
    print('FAILED: ' + ', '.join(failed))
else:
    print('All gates passed.')
print('=' * 72)
sys.exit(1 if failed else 0)
