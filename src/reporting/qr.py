"""QR code payload + rendering for inspection reports.

The QR encodes a compact *verification payload* (report id + hash + a
verification URL/path) — never the whole report.

`qrcode` may be absent in a minimal environment: in that case the payload is
still produced (and printed as text), and `render_png` raises a clear
`QrUnavailable` instead of silently writing a broken file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:  # optional dependency
    import qrcode  # type: ignore
    _QRCODE_OK = True
except Exception:  # pragma: no cover
    _QRCODE_OK = False


class QrUnavailable(RuntimeError):
    """Raised when QR rendering is requested but `qrcode` is not installed."""


@dataclass
class QrPayload:
    report_id: str
    report_hash: str
    verify_path: str = "/report/verify"

    def encode(self) -> str:
        """Compact, stable text payload (scannable and human-readable)."""
        return json.dumps({
            "t": "ONIONQ-REPORT",
            "id": self.report_id,
            "h": self.report_hash,
            "v": self.verify_path,
        }, separators=(",", ":"))

    def verify_url(self, base_url: str = "") -> str:
        base = base_url.rstrip("/")
        return f"{base}{self.verify_path}/{self.report_id}"


def render_png(payload: QrPayload, out_path: str | Path,
               box_size: int = 8, border: int = 2) -> Path:
    if not _QRCODE_OK:
        raise QrUnavailable(
            "The `qrcode` package is not installed. Install it with "
            "`pip install qrcode` (declared in requirements.txt) to render QR "
            "images; the text payload is still available via "
            "QrPayload.encode().")
    img = qrcode.make(payload.encode(), box_size=box_size, border=border)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out))
    return out


def decode_verify_payload(text: str) -> Optional[dict]:
    """Parse a scanned QR payload; returns None when it is not one of ours."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if data.get("t") != "ONIONQ-REPORT":
        return None
    return data
