"""Load auditable domain evidence without embedding policy in Router code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from domain_router import DomainScopeProfile


DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "config" / "domain_evidence_registry_v1.json"


def load_domain_evidence_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or DEFAULT_REGISTRY_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("domain evidence registry must be an object")
    scopes = payload.get("scopes")
    if not isinstance(scopes, dict) or not scopes:
        raise ValueError("domain evidence registry must contain non-empty scopes")
    return payload


def _signal_terms(scope: Mapping[str, Any], group: str, *, include_pending: bool) -> tuple[str, ...]:
    values = scope.get(group, {})
    if isinstance(values, list):
        return tuple(str(value).strip() for value in values if str(value).strip())
    if not isinstance(values, Mapping):
        raise ValueError(f"{group} must be a list or status map")
    statuses = ("confirmed", "pending_manual_confirmation") if include_pending else ("confirmed",)
    result: list[str] = []
    for status in statuses:
        items = values.get(status, [])
        if not isinstance(items, list):
            raise ValueError(f"{group}.{status} must be a list")
        result.extend(str(item).strip() for item in items if str(item).strip())
    return tuple(dict.fromkeys(result))


def build_domain_scope_profiles(
    path: Path | None = None, *, include_pending: bool = False
) -> tuple[DomainScopeProfile, ...]:
    """Build Router profiles from confirmed registry evidence.

    ``include_pending`` exists only for offline review tooling. Production and
    shadow callers must use the default, which excludes unconfirmed signals.
    """

    payload = load_domain_evidence_registry(path)
    profiles: list[DomainScopeProfile] = []
    for scope_id, raw_scope in payload["scopes"].items():
        if not isinstance(raw_scope, Mapping):
            raise ValueError(f"scope {scope_id} must be an object")
        patterns = raw_scope.get("identifier_patterns", [])
        if not isinstance(patterns, list):
            raise ValueError(f"scope {scope_id}.identifier_patterns must be a list")
        profiles.append(
            DomainScopeProfile(
                scope_id=str(scope_id),
                domain=str(raw_scope.get("domain", "")),
                manufacturer=str(raw_scope.get("manufacturer", "")),
                system=str(raw_scope.get("system", "")),
                strong_terms=_signal_terms(raw_scope, "high_signal", include_pending=include_pending),
                weak_terms=_signal_terms(raw_scope, "medium_signal", include_pending=include_pending),
                identifier_patterns=tuple(str(pattern) for pattern in patterns),
            )
        )
    return tuple(profiles)
