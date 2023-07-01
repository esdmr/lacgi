#!/usr/bin/env python3
import http.server
import json
import os
import socketserver
import sqlite3


def to_bytes(s: str):
    return (s + "\n").encode("UTF-8")


class DbRequestHandler(http.server.BaseHTTPRequestHandler):
    def _operational_error(self, e: sqlite3.OperationalError):
        msg = to_bytes(str(e))
        self.send_response_only(400)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

    def _unknown_error(self):
        msg = b"Unknown error\n"
        self.send_response_only(500)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

    def do_POST(self):
        try:
            content = self.rfile.read(
                int(self.headers.get("Content-Length") or 0)
            ).decode("UTF-8")

            if self.path.startswith("/script"):
                with con:
                    con.cursor().executescript(content)

                result = b"OK\n"
            else:
                with con:
                    l = json.loads(content)
                    assert isinstance(l, list)
                    for i in l:
                        assert isinstance(i, str)
                    cur = con.cursor().execute(l[0], l[1::])
                    result = to_bytes(json.dumps([i for i in cur]))

            self.send_response_only(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", str(len(result)))
            self.end_headers()
            self.wfile.write(result)
        except sqlite3.OperationalError as e:
            self._operational_error(e)
        except:
            self._unknown_error()
            raise


class UnixHTTPServer(socketserver.UnixStreamServer):
    def get_request(self):
        request, client_address = self.socket.accept()

        if len(client_address) == 0:
            client_address = (self.server_address,)

        return (request, client_address)


DB_PATH = "index.db"
SOCKET_PATH = "db.socket"

con = sqlite3.connect(DB_PATH)

try:
    os.chmod(DB_PATH, 0o600)

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    with UnixHTTPServer(SOCKET_PATH, DbRequestHandler) as httpd:
        os.chmod(SOCKET_PATH, 0o600)
        print("serving at", SOCKET_PATH)
        httpd.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    con.close()

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
