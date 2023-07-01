#!/usr/bin/env python3
"""
From https://stackoverflow.com/a/25810600
"""

from http.server import CGIHTTPRequestHandler, HTTPServer
from io import BytesIO


class BufferedCGIHTTPRequestHandler(CGIHTTPRequestHandler):
    def setup(self):
        """
        Arrange for CGI response to be buffered in a StringIO rather than
        sent directly to the client.
        """
        CGIHTTPRequestHandler.setup(self)
        self.original_wfile = self.wfile
        self.wfile = BytesIO()
        self.have_fork = False

    def run_cgi(self):
        """
        Post-process CGI script response before sending to client.
        Override HTTP status line with value of "Status:" header, if set.
        """
        CGIHTTPRequestHandler.run_cgi(self)
        self.wfile.seek(0)
        headers = []
        body = None

        for line in map(bytes.decode, self.wfile):
            if line.strip() == "":
                body = self.wfile.read()
                break
            elif line.startswith("Status:"):
                status = line.split(":")[1].strip()
                headers[0] = f"{self.protocol_version} {status}\n"
            else:
                headers.append(line)

        self.original_wfile.write("".join(headers).encode())

        if (body):
            self.original_wfile.write(b"\n")
            self.original_wfile.write(body)


with HTTPServer(("localhost", 12321), BufferedCGIHTTPRequestHandler) as httpd:
    print("serving at", "http://localhost:12321")
    httpd.serve_forever()
