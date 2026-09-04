#!/usr/bin/env python3
"""Shared setup for the probes in this directory.

page_url() rebuilds test.html from the current index.html, serves the project
over HTTP on a loopback port, and returns the URL. Two reasons for the server
rather than a file:// path:

  * the Content-Security-Policy behaves as it will in production — under
    file:// every origin is opaque, so connect-src 'self' can never match
  * going through one place means no probe can measure a stale build, and
    none of them care what the working directory is
"""
import functools
import http.server
import os
import socketserver
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROMIUM = os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium')

_server = None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _serve():
    global _server
    if _server is None:
        handler = functools.partial(_Quiet, directory=ROOT)
        _server = socketserver.TCPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()
    return _server.server_address[1]


def page_url(name='test.html'):
    subprocess.run([sys.executable, os.path.join(HERE, 'wrap.py'), name],
                   check=True, cwd=HERE, stdout=subprocess.DEVNULL)
    return 'http://127.0.0.1:%d/test/%s' % (_serve(), name)


def launch(pw):
    """Chromium, from the path this container ships it at. Override with
    CHROMIUM=/path/to/chromium when running elsewhere."""
    return pw.chromium.launch(executable_path=CHROMIUM)
