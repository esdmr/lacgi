#!/usr/bin/env python3
import http.client
import json
import requests
import requests.adapters
import socket
import sys
import urllib3

type = sys.argv[1]
query = sys.argv[2::]

if type == "script":
    body = "\n".join(query).encode("UTF-8")
    path = "script"
else:
    body = json.dumps(query).encode("UTF-8")
    path = ""


class DbConnection(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("db.socket")


class DbConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
    def __init__(self):
        super().__init__("localhost")

    def _new_conn(self):
        return DbConnection()


class DbAdapter(requests.adapters.HTTPAdapter):
    def get_connection(self, url, proxies=None):
        return DbConnectionPool()


session = requests.Session()
session.mount("http://db/", DbAdapter())
response = session.post(f"http://db/{path}", body)


if type == "script" or response.status_code != 200:
    print(response.text, end="")
else:
    print(
        *["\t".join([str(j).replace("\t", "  ") for j in i]) for i in response.json()],
        sep="\n",
        end="",
    )

exit(int(response.status_code != 200))
