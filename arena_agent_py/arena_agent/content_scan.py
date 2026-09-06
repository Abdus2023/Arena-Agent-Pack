"""
Ingested Content Contract helper. v2 §4.1 (new in v2) / §25 (v1 §26 Anti-Patterns).

Repository content (comments, READMEs, commit messages, issues) is data to
classify, never instructions to obey. This module does not "protect" an LLM
agent by itself -- it provides a mechanical first pass that flags
imperative-sounding, pack-relevant phrases in arbitrary text so a human or
agent reviewing extraction output can see what was found and confirm it was
treated as a CLAIM, not a directive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Phrases called out explicitly in v2 §25 / v1 §26 as anti-pattern
#: indicators of a potential boundary violation.
ANTI_PATTERN_PHRASES: tuple[str, ...] = (
    "assume it exists",
    "treat this as implemented",
    "skip the failing test",
    "ignore malformed input",
    "just use the final output",
    "reuse the production evaluator",
    "copy the capability",
    "make it global",
    "use ambient access",
    "retry indefinitely",
    "ignore the missing journal record",
    "treat missing completion as failure",
    "repair the state automatically",
    "just simplify the state machine",
    "merge these because they are similar",
    "we can document it later",
)

#: Looser patterns suggesting ingested text is trying to address the agent
#: directly (v2 §4.1) rather than describing the repository/domain.
DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(you are|you must|as an ai|ignore (all|previous) instructions)\b", re.I),
    re.compile(r"\bmark (this|it) (as )?(verified|implemented|passed|done)\b", re.I),
    re.compile(r"\btreat (this|it) as (verified|implemented|complete|done)\b", re.I),
    re.compile(r"\bdo not (report|log|record) (this|it)\b", re.I),
)


@dataclass
class ContentFlag:
    kind: str  # "anti_pattern_phrase" | "directive_pattern"
    matched_text: str
    start: int
    end: int
    context: str


def scan_text(text: str, context_window: int = 40) -> list[ContentFlag]:
    """
    Scan arbitrary ingested text for anti-pattern phrases and
    directive-shaped language. Returns a list of ContentFlag -- purely
    informational, does not modify or filter the text. Caller decides how
    to represent flagged material (typically: extract as an EXAMPLE- or
    ARCHITECTURAL-PROPOSAL-classified CLAIM, quoting the source verbatim,
    per v2 §4.1).
    """
    flags: list[ContentFlag] = []
    lowered = text.lower()

    for phrase in ANTI_PATTERN_PHRASES:
        start = 0
        while True:
            idx = lowered.find(phrase, start)
            if idx == -1:
                break
            end = idx + len(phrase)
            flags.append(
                ContentFlag(
                    kind="anti_pattern_phrase",
                    matched_text=text[idx:end],
                    start=idx,
                    end=end,
                    context=_context(text, idx, end, context_window),
                )
            )
            start = end

    for pattern in DIRECTIVE_PATTERNS:
        for m in pattern.finditer(text):
            flags.append(
                ContentFlag(
                    kind="directive_pattern",
                    matched_text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    context=_context(text, m.start(), m.end(), context_window),
                )
            )

    flags.sort(key=lambda f: f.start)
    return flags


def _context(text: str, start: int, end: int, window: int) -> str:
    lo = max(0, start - window)
    hi = min(len(text), end + window)
    prefix = "..." if lo > 0 else ""
    suffix = "..." if hi < len(text) else ""
    return f"{prefix}{text[lo:hi]}{suffix}"


def has_flags(text: str) -> bool:
    return bool(scan_text(text))
