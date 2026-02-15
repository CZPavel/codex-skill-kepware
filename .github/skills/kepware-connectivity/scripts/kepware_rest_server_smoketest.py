#!/usr/bin/env python3
"""Smoke test Kepware IoT Gateway REST Server Agent browse/read/write endpoints.

Safety defaults:
- browse + read only by default
- write requires explicit --enable-write
- retries + exponential backoff
- timeout for all calls
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kepware IoT Gateway REST Server smoke test")
    parser.add_argument("--base-url", default=os.getenv("KEPWARE_REST_SERVER_URL", "https://localhost:39320/iotgateway"))
    parser.add_argument("--username", default=os.getenv("KEPWARE_REST_USER"))
    parser.add_argument("--password", default=os.getenv("KEPWARE_REST_PASS"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("KEPWARE_TIMEOUT", "10")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("KEPWARE_RETRIES", "3")))
    parser.add_argument("--backoff", type=float, default=float(os.getenv("KEPWARE_BACKOFF", "0.5")))
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification (development only)")

    parser.add_argument("--browse", action="store_true", default=True)
    parser.add_argument("--no-browse", dest="browse", action="store_false")
    parser.add_argument("--tag-id", action="append", default=[], help="Tag id to read (repeatable)")

    parser.add_argument("--enable-write", action="store_true")
    parser.add_argument("--write-body-json", help="Path to write payload JSON body")
    parser.add_argument("--write-tag-id", help="Tag id for simple write payload")
    parser.add_argument("--write-value", help="Value for simple write payload")
    return parser.parse_args()


def headers(username: str | None, password: str | None) -> dict[str, str]:
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    if username:
        pwd = password or ""
        token = base64.b64encode(f"{username}:{pwd}".encode("utf-8")).decode("ascii")
        h["Authorization"] = f"Basic {token}"
    return h


def request_with_retry(
    method: str,
    url: str,
    timeout: float,
    retries: int,
    backoff: float,
    insecure: bool,
    req_headers: dict[str, str],
    payload: dict[str, Any] | list[Any] | None = None,
) -> tuple[int, str]:
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    ssl_context = ssl._create_unverified_context() if insecure else None

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url=url, data=body, method=method, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:  # nosec B310
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as err:
            text = err.read().decode("utf-8", errors="replace")
            if err.code >= 500 and attempt < retries:
                wait_s = backoff * (2**attempt)
                print(f"[WARN] HTTP {err.code}, retry in {wait_s:.2f}s")
                time.sleep(wait_s)
                continue
            return err.code, text
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            if attempt < retries:
                wait_s = backoff * (2**attempt)
                print(f"[WARN] Network error: {err}. retry in {wait_s:.2f}s")
                time.sleep(wait_s)
                continue
            break

    raise RuntimeError(f"Request failed after retries: {method} {url}; error={last_err}")


def print_response(label: str, status: int, text: str) -> None:
    print(f"\n=== {label} ===")
    print(f"status: {status}")
    if not text:
        return
    try:
        parsed = json.loads(text)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(text)


def load_write_payload(path: str | None, tag_id: str | None, value: str | None) -> dict[str, Any] | list[Any] | None:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    if tag_id is not None and value is not None:
        return [{"id": tag_id, "v": value}]
    return None


def main() -> int:
    args = parse_args()
    base = args.base_url.rstrip("/")
    req_headers = headers(args.username, args.password)

    if args.browse:
        status, text = request_with_retry(
            "GET",
            f"{base}/browse",
            args.timeout,
            args.retries,
            args.backoff,
            args.insecure,
            req_headers,
        )
        print_response("browse", status, text)

    if args.tag_id:
        ids = ",".join(args.tag_id)
        query = urllib.parse.urlencode({"ids": ids})
        status, text = request_with_retry(
            "GET",
            f"{base}/read?{query}",
            args.timeout,
            args.retries,
            args.backoff,
            args.insecure,
            req_headers,
        )
        print_response("read", status, text)

    if args.enable_write:
        payload = load_write_payload(args.write_body_json, args.write_tag_id, args.write_value)
        if payload is None:
            raise SystemExit("Write enabled, but no payload provided. Use --write-body-json or --write-tag-id + --write-value")

        status, text = request_with_retry(
            "POST",
            f"{base}/write",
            args.timeout,
            args.retries,
            args.backoff,
            args.insecure,
            req_headers,
            payload,
        )
        print_response("write", status, text)
    else:
        print("\nWrite test skipped (use --enable-write to allow).")

    print("\nDone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
