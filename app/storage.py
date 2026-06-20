from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep Supabase rows useful without requiring a huge table schema."""
    return json.loads(json.dumps(payload, ensure_ascii=False, default=str))


async def save_analysis_result(kind: str, input_text: str, result: dict[str, Any]) -> dict[str, Any]:
    """Persist an analysis result to Supabase when env vars are configured.

    The app must remain fully usable without Supabase credentials, so storage
    failures are returned as metadata instead of breaking the analyzer.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return {"enabled": False, "saved": False, "reason": "supabase env vars are not configured"}

    row = {
        "kind": kind,
        "input_hash": _stable_hash(input_text),
        "input_preview": input_text[:800],
        "result_json": _compact_payload(result),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    url = f"{settings.supabase_url.rstrip('/')}/rest/v1/{settings.supabase_table}"
    body = json.dumps(row, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            saved_rows = json.loads(raw) if raw else []
            saved = saved_rows[0] if saved_rows else {}
            return {"enabled": True, "saved": True, "row": saved}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        return {"enabled": True, "saved": False, "error": f"Supabase HTTP {exc.code}: {detail}"}
    except Exception as exc:  # pragma: no cover - network/environment dependent
        return {"enabled": True, "saved": False, "error": str(exc)}
