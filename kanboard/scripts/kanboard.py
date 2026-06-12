#!/usr/bin/env python3
"""Minimal Kanboard JSON-RPC client.

Usage:
    python kanboard.py <method> ['<json-params>']

Reads credentials from the environment:
    KANBOARD_URL    base URL, e.g. https://kanboard.example.com (/jsonrpc.php is appended)
    KANBOARD_USER   "jsonrpc" for the Application API, or a username for the User API
    KANBOARD_TOKEN  API token, password, or personal access token

Prints the JSON-RPC `result` on success. Exits non-zero and prints the `error`
object on failure. Uses only the Python standard library.
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2

    method = argv[1]
    if len(argv) >= 3 and argv[2].strip():
        try:
            params = json.loads(argv[2])
        except json.JSONDecodeError as exc:
            print(f"error: params is not valid JSON: {exc}", file=sys.stderr)
            return 2
    else:
        params = {}

    base = os.environ.get("KANBOARD_URL", "").rstrip("/")
    user = os.environ.get("KANBOARD_USER")
    token = os.environ.get("KANBOARD_TOKEN")
    missing = [n for n, v in
               (("KANBOARD_URL", base), ("KANBOARD_USER", user), ("KANBOARD_TOKEN", token))
               if not v]
    if missing:
        print(f"error: missing env var(s): {', '.join(missing)}", file=sys.stderr)
        return 2

    endpoint = base if base.endswith("jsonrpc.php") else base + "/jsonrpc.php"
    payload = json.dumps(
        {"jsonrpc": "2.0", "method": method, "id": 1, "params": params}
    ).encode("utf-8")

    creds = base64.b64encode(f"{user}:{token}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {creds}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        detail = exc.read().decode("utf-8", "replace")
        if detail:
            print(detail, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"error: could not reach {endpoint}: {exc.reason}", file=sys.stderr)
        return 1

    if "error" in body:
        print(json.dumps(body["error"], indent=2), file=sys.stderr)
        return 1

    print(json.dumps(body.get("result"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
