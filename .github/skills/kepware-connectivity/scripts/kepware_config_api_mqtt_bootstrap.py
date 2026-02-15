#!/usr/bin/env python3
"""Bootstrap Kepware IoT Gateway MQTT client and one iot_item via Configuration API.

Safety defaults:
- dry-run enabled by default
- retries + exponential backoff
- timeout for all HTTP calls
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
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ClientConfig:
    base_url: str
    username: str | None
    password: str | None
    timeout: float
    retries: int
    backoff: float
    insecure: bool
    dry_run: bool


class HttpClient:
    def __init__(self, cfg: ClientConfig) -> None:
        self.cfg = cfg

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.cfg.username:
            pwd = self.cfg.password or ""
            token = base64.b64encode(f"{self.cfg.username}:{pwd}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, str]:
        url = self.cfg.base_url.rstrip("/") + path
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        ssl_context = ssl._create_unverified_context() if self.cfg.insecure else None

        if self.cfg.dry_run and method in {"POST", "PUT", "DELETE", "PATCH"}:
            print(f"[DRY-RUN] {method} {url}")
            if payload is not None:
                print(json.dumps(payload, indent=2))
            return 0, "dry-run"

        last_err: Exception | None = None
        for attempt in range(self.cfg.retries + 1):
            req = urllib.request.Request(url=url, data=body, method=method, headers=self._headers())
            try:
                with urllib.request.urlopen(req, timeout=self.cfg.timeout, context=ssl_context) as resp:  # nosec B310
                    text = resp.read().decode("utf-8", errors="replace")
                    return resp.status, text
            except urllib.error.HTTPError as err:
                text = err.read().decode("utf-8", errors="replace")
                if err.code >= 500 and attempt < self.cfg.retries:
                    wait_s = self.cfg.backoff * (2**attempt)
                    print(f"[WARN] HTTP {err.code}, retry in {wait_s:.2f}s")
                    time.sleep(wait_s)
                    continue
                return err.code, text
            except (urllib.error.URLError, TimeoutError) as err:
                last_err = err
                if attempt < self.cfg.retries:
                    wait_s = self.cfg.backoff * (2**attempt)
                    print(f"[WARN] Network error: {err}. retry in {wait_s:.2f}s")
                    time.sleep(wait_s)
                    continue
                break

        raise RuntimeError(f"Request failed after retries: {method} {url}; error={last_err}")


def load_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    data = Path(path).read_text(encoding="utf-8")
    return json.loads(data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kepware Configuration API bootstrap for MQTT client + iot_item")
    parser.add_argument("--base-url", default=os.getenv("KEPWARE_CONFIG_API_URL", "https://localhost:57513"))
    parser.add_argument("--username", default=os.getenv("KEPWARE_CONFIG_API_USER"))
    parser.add_argument("--password", default=os.getenv("KEPWARE_CONFIG_API_PASS"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("KEPWARE_TIMEOUT", "10")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("KEPWARE_RETRIES", "3")))
    parser.add_argument("--backoff", type=float, default=float(os.getenv("KEPWARE_BACKOFF", "0.5")))
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification (development only)")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false")

    parser.add_argument("--mqtt-client-name", default="mqtt_agent_1")
    parser.add_argument("--mqtt-client-json", help="Path to full JSON payload for mqtt client create")

    parser.add_argument("--iot-item-name", default="iot_item_1")
    parser.add_argument("--tag-id", default="Channel1.Device1.Tag1", help="Kepware tag path / item id")
    parser.add_argument("--iot-item-json", help="Path to full JSON payload for iot_item create")

    parser.add_argument("--cleanup", action="store_true", help="Delete mqtt client at end (honors dry-run)")
    return parser.parse_args()


def default_mqtt_client_payload(name: str) -> dict[str, Any]:
    return {
        "common": {
            "name": name,
            "description": "Created by kepware_config_api_mqtt_bootstrap.py",
        }
    }


def default_iot_item_payload(name: str, tag_id: str) -> dict[str, Any]:
    return {
        "common": {
            "name": name,
            "description": "Created by kepware_config_api_mqtt_bootstrap.py",
        },
        "server_tag": tag_id,
    }


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


def main() -> int:
    args = parse_args()
    cfg = ClientConfig(
        base_url=args.base_url,
        username=args.username,
        password=args.password,
        timeout=args.timeout,
        retries=args.retries,
        backoff=args.backoff,
        insecure=args.insecure,
        dry_run=args.dry_run,
    )
    client = HttpClient(cfg)

    agent_name = args.mqtt_client_name

    status, text = client.request("GET", "/config/v1/project/_iot_gateway/mqtt_clients")
    print_response("list mqtt_clients", status, text)

    mqtt_payload = load_json(args.mqtt_client_json) or default_mqtt_client_payload(agent_name)
    status, text = client.request("POST", "/config/v1/project/_iot_gateway/mqtt_clients", mqtt_payload)
    print_response("create mqtt_client", status, text)

    item_payload = load_json(args.iot_item_json) or default_iot_item_payload(args.iot_item_name, args.tag_id)
    path = f"/config/v1/project/_iot_gateway/mqtt_clients/{agent_name}/iot_items"
    status, text = client.request("POST", path, item_payload)
    print_response("create iot_item", status, text)

    status, text = client.request("GET", f"/config/v1/project/_iot_gateway/mqtt_clients/{agent_name}/iot_items")
    print_response("list iot_items", status, text)

    if args.cleanup:
        status, text = client.request("DELETE", f"/config/v1/project/_iot_gateway/mqtt_clients/{agent_name}")
        print_response("cleanup mqtt_client", status, text)

    print("\nDone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
