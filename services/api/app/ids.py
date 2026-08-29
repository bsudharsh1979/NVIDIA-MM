"""Deterministic content ids — Modal SQLite is ephemeral; uuid4 breaks every cold start."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha1_hex(value: str, n: int = 16) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:n]


def artifact_uid(path: str) -> str:
    return sha1_hex(str(path).replace("\\", "/"))


def span_uid(art_uid: str, locator: dict[str, Any], kind: str, seq: int) -> str:
    loc = json.dumps(locator, sort_keys=True, default=str)
    return sha1_hex(f"{art_uid}:{loc}:{kind}:{seq}")


def notebook_uid(filename: str) -> str:
    return artifact_uid(filename)
