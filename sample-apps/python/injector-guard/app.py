# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Test app for the ADOT start-up guard (Injector mode).

It imports urllib3 at start-up. Built on Python 3.9 with urllib3 1.26.20 it reproduces the
case where the urllib3 bundled with ADOT Python v0.21.0 shadows the app's own copy and the
app crashes at start-up; built on Python 3.11 it is a healthy app.
"""
import http.server

import urllib3


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok urllib3=" + urllib3.__version__.encode())


print("serving, urllib3", urllib3.__version__, flush=True)
http.server.ThreadingHTTPServer(("", 8080), Handler).serve_forever()
