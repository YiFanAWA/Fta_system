"""Controlled component vocabulary used by the extraction adapter.

This registry owns stable component-name normalization only. It does not
enumerate fault descriptions or causes; those remain model-extracted semantic
fields and must still be supported by source evidence.
"""

from __future__ import annotations

import re
from typing import Pattern


# A new stable spelling can be added here without adding another semantic
# branch to the extraction adapter.
COMPONENT_ALIASES: dict[str, tuple[str, ...]] = {
    "Control Unit": ("Control Unit", "Control Units"),
    "Power unit": ("Power unit", "Power units"),
    "Encoder": ("Encoder", "Encoders"),
    "Motor": ("Motor", "Motors"),
    "Sensor Module": ("Sensor Module", "Sensor Modules"),
    "Safety Integrated": ("Safety Integrated", "SI"),
    "SI Motion": ("SI Motion",),
    "Control system (internal software)": (
        "Internal software",
        "Software timeout",
    ),
    "Parameter configuration system": ("Parameter error",),
    "DRIVE-CLiQ line": ("DRIVE-CLiQ line",),
    "Encoder 1 (DRIVE-CLiQ)": (
        "Encoder 1 DRIVE-CLiQ",
        "Encoder 1",
    ),
}

COMPONENT_EVIDENCE_ALIASES: dict[str, tuple[str, ...]] = {
    canonical: aliases
    for canonical, aliases in COMPONENT_ALIASES.items()
    if any(alias.casefold() != canonical.casefold() for alias in aliases)
}

_EXACT_ALIAS_TO_CANONICAL = {
    alias.casefold(): canonical
    for canonical, aliases in COMPONENT_ALIASES.items()
    for alias in aliases
}

_ENGLISH_COMPONENT_HEADING_RE = re.compile(
    r"^(?P<component>"
    r"SI\s+Motion(?:\s+P\d+)?|"
    r"SI(?:\s+P\d+)?|"
    r"Function\s+generator|"
    r"Power\s+unit|"
    r"Drive|"
    r"Encoder\s+\d+\s+DRIVE-CLiQ(?:\s+\(CU\))?|"
    r"Encoder(?:\s+\d+)?|"
    r"DRIVE-CLiQ(?:\s+socket\s+X\d+)?|"
    r"PN/COMM\s+BOARD|"
    r"Web\s+server"
    r")\s*:",
    re.IGNORECASE,
)

_EXPLICIT_ENGLISH_COMPONENT_PATTERNS: tuple[
    tuple[Pattern[str], str], ...
] = (
    (re.compile(r"\bcontrol\s+units?\b", re.IGNORECASE), "Control Unit"),
    (re.compile(r"\bpower\s+units?\b", re.IGNORECASE), "Power unit"),
    (re.compile(r"\bencoder(?:s)?\b", re.IGNORECASE), "Encoder"),
    (re.compile(r"\bmotor(?:s)?\b", re.IGNORECASE), "Motor"),
    (re.compile(r"\bsensor\s+modules?\b", re.IGNORECASE), "Sensor Module"),
)


def normalize_component_label(value: str | None) -> str:
    """Return a canonical label for a controlled component spelling."""
    text = re.sub(r"\s+", " ", (value or "")).strip()
    if not text:
        return ""

    exact = _EXACT_ALIAS_TO_CANONICAL.get(text.casefold())
    if exact is not None:
        return exact

    if re.fullmatch(r"SI\s+Motion(?:\s+P\d+)?", text, re.IGNORECASE):
        return "SI Motion"
    if re.fullmatch(r"SI(?:\s+P\d+)?", text, re.IGNORECASE):
        return "Safety Integrated"

    match = re.fullmatch(
        r"Encoder\s+(\d+)\s+DRIVE-CLiQ(?:\s+\(CU\))?",
        text,
        re.IGNORECASE,
    )
    if match:
        return f"Encoder {match.group(1)} (DRIVE-CLiQ)"

    return text


def find_english_component_heading(source_window: str) -> str | None:
    """Read and normalize an explicit component prefix in an English title."""
    first_line = source_window.splitlines()[0].strip() if source_window else ""
    first_line = re.sub(
        r"^(?:[AFNE]\d{5}|E\d+|ERR_[A-Za-z0-9_]+)\s+",
        "",
        first_line,
        flags=re.IGNORECASE,
    )

    title_rules = (
        (r"(?:Internal\s+software|Software\s+timeout)\b", "Control system (internal software)"),
        (r"Parameter\s+error\b", "Parameter configuration system"),
        (r"\bDRIVE-CLiQ\s+line\b", "DRIVE-CLiQ line"),
    )
    for pattern, canonical in title_rules:
        if re.search(pattern, first_line, re.IGNORECASE):
            return canonical

    # A plain ``Encoder 1: ...`` title names the component directly.  Do not
    # promote it to the more specific DRIVE-CLiQ alias unless that qualifier
    # is present in the title itself.
    plain_encoder = re.match(r"(?P<component>Encoder\s+\d+)\s*:", first_line, re.IGNORECASE)
    if plain_encoder:
        return plain_encoder.group("component").strip()

    match = _ENGLISH_COMPONENT_HEADING_RE.match(first_line)
    return normalize_component_label(match.group("component")) if match else None


def explicit_english_component_candidates(
    clause: str,
) -> tuple[tuple[Pattern[str], str], ...]:
    """Return controlled component patterns for an explicit relation clause."""
    return _EXPLICIT_ENGLISH_COMPONENT_PATTERNS
