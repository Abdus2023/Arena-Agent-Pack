"""
Output layer for the `arena` CLI: Rich-formatted human output, or a
`--json` machine-readable mode for scripting.

Design goals
------------
- In JSON mode, every command prints **exactly one** JSON document to
  stdout and nothing else -- no color codes, no decorative text, no log
  lines interleaved -- so `arena ... --json | jq ...` is always safe.
  Diagnostics that must not pollute stdout (there are none needed today)
  would go to stderr; as it stands, JSON mode is silent on stderr.
- In text mode, output goes through Rich: tables for lists, panels/tables
  for single-record views, and a colored table for validation findings
  (ERROR=red, WARNING=yellow, INFO=cyan).
- All dynamic string content is passed through ``rich.markup.escape``
  before reaching a Rich renderable. Rich's markup parser treats a literal
  ``[x]`` or ``['a', 'b']`` as a style tag and silently drops it -- this
  bit us during development (a Completion Contract checklist rendered as
  "checklist:  done" instead of "checklist: [x] done") so every text-mode
  render here escapes first, matching the pack's own "never silently drop
  information" principle applied to the tool itself.
- Exit codes are unaffected by output mode: JSON mode still exits non-zero
  on ERROR-severity findings or command failure, same as text mode; only
  the *representation* changes, never the *result*.
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Optional

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

#: Rich's Console defaults to an 80-column width when stdout is not a real
#: terminal (piped, redirected, or under a test runner like Click's
#: CliRunner). At that width, Table silently ellipsizes long cell content
#: (e.g. a full ARENA-... id gets cut to "ARENA-REPO-C…") -- which is
#: exactly the kind of silent information loss this pack forbids. When
#: stdout *is* a real terminal we still want to fit it, but the fallback
#: for non-terminal output should be generous rather than 80.
_FALLBACK_WIDTH = 200


def _detect_width() -> int:
    return shutil.get_terminal_size(fallback=(_FALLBACK_WIDTH, 24)).columns

from .validation import Finding, Severity, has_errors

_SEVERITY_STYLE = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


def finding_to_dict(f: Finding) -> dict[str, str]:
    return {
        "severity": f.severity.value,
        "code": f.code,
        "message": f.message,
        "ref": f.ref,
    }


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False, default=_json_default)


@dataclass
class Output:
    """
    Bound to one CLI invocation. Every command handler gets one of these
    (via the click context) and routes all output through it instead of
    calling click.echo/click.secho directly, so text-vs-JSON is decided in
    exactly one place.
    """

    fmt: OutputFormat = OutputFormat.TEXT
    console: Console = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.console is None:
            # no_color left to Rich's own auto-detection (NO_COLOR env,
            # non-tty stdout) unless explicitly forced off by the CLI flag,
            # which is passed in via the `console` argument by the caller.
            self.console = Console(width=_detect_width())
        elif self.console.width < _FALLBACK_WIDTH and not self.console.is_terminal:
            # A real terminal's own width should be respected; only widen
            # when Rich fell back to its default because stdout isn't a
            # terminal at all (piped/redirected/tests), where silent
            # ellipsis-truncation would otherwise drop information.
            self.console.width = _FALLBACK_WIDTH

    @property
    def is_json(self) -> bool:
        return self.fmt is OutputFormat.JSON

    # -- low-level -----------------------------------------------------------

    def json(self, data: Any) -> None:
        """Print exactly one JSON document. Only valid call in JSON mode."""
        print(dump_json(data))

    def text(self, renderable: Any) -> None:
        """Print a Rich renderable (or a plain string, which is escaped)."""
        if isinstance(renderable, str):
            self.console.print(escape(renderable))
        else:
            self.console.print(renderable)

    # -- structured helpers, dispatching on self.fmt -------------------------

    def success(self, message: str, **data: Any) -> None:
        if self.is_json:
            self.json({"status": "ok", "message": message, **data})
        else:
            self.console.print(f"[bold green]{escape(message)}[/bold green]")

    def error(self, message: str, **data: Any) -> None:
        """Report an error without exiting (caller decides exit behavior)."""
        if self.is_json:
            self.json({"status": "error", "message": message, **data})
        else:
            self.console.print(f"[bold red]Error:[/bold red] {escape(message)}")

    def findings(
        self,
        findings: list[Finding],
        *,
        title: str = "Validation Findings",
        record_id: Optional[str] = None,
        also: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Render a list of Finding objects. In JSON mode, emits a structured
        object with severity counts so scripts can check `has_errors`
        without re-deriving it. In text mode, renders a colored Rich table
        (or a plain green "No findings" line when the list is empty).
        """
        if self.is_json:
            payload: dict[str, Any] = {
                "record_id": record_id,
                "findings": [finding_to_dict(f) for f in findings],
                "has_errors": has_errors(findings),
                "error_count": sum(1 for f in findings if f.severity == Severity.ERROR),
                "warning_count": sum(1 for f in findings if f.severity == Severity.WARNING),
            }
            if also:
                payload.update(also)
            self.json(payload)
            return

        if not findings:
            if title:
                self.console.print(f"[bold]{escape(title)}[/bold]")
            self.console.print("[bold green]No findings.[/bold green]")
            return

        table = Table(title=escape(title), show_lines=False)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Code", overflow="fold")
        table.add_column("Message", overflow="fold")
        table.add_column("Ref", overflow="fold", style="dim")
        for f in findings:
            style = _SEVERITY_STYLE.get(f.severity, "")
            table.add_row(
                f"[{style}]{f.severity.value}[/{style}]",
                escape(f.code),
                escape(f.message),
                escape(f.ref),
            )
        self.console.print(table)
        errors = sum(1 for f in findings if f.severity == Severity.ERROR)
        if errors:
            self.console.print(f"[bold red]{errors} error(s) found.[/bold red]")

    def table(
        self,
        rows: list[dict[str, Any]],
        *,
        columns: Optional[list[str]] = None,
        title: Optional[str] = None,
        column_styles: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Render a list of flat dicts. JSON mode: the raw list. Text mode: a
        Rich table, with an optional per-column value->style mapping (e.g.
        coloring a status column by its value).
        """
        if self.is_json:
            self.json(rows)
            return

        if not rows:
            self.console.print("[dim]No records.[/dim]")
            return

        cols = columns or list(rows[0].keys())
        t = Table(title=escape(title) if title else None)
        for c in cols:
            # overflow="fold" wraps long content onto extra lines instead of
            # Rich's default ellipsis truncation, which would otherwise
            # silently drop characters from long values like full ARENA-...
            # ids -- unacceptable for a tool whose whole point is never to
            # silently drop information (v2 Core Contract, §2).
            t.add_column(escape(c), overflow="fold")
        for row in rows:
            cells = []
            for c in cols:
                value = str(row.get(c, ""))
                style = None
                if column_styles and c in column_styles:
                    style = column_styles[c].get(value)
                cells.append(f"[{style}]{escape(value)}[/{style}]" if style else escape(value))
            t.add_row(*cells)
        self.console.print(t)

    def record(
        self,
        data: dict[str, Any],
        *,
        title: str,
        sections: Optional[list[tuple[str, dict[str, Any]]]] = None,
    ) -> None:
        """
        Render a single record. JSON mode: the raw dict. Text mode: a Rich
        panel with the top-level fields, plus optional named sub-tables for
        nested structures (e.g. a Work Item's gates or lifecycle log).
        """
        if self.is_json:
            self.json(data)
            return

        lines = "\n".join(f"[bold]{escape(str(k))}:[/bold] {escape(str(v))}" for k, v in data.items())
        self.console.print(Panel(lines, title=escape(title), expand=False))
        for section_title, rows in sections or []:
            if isinstance(rows, list):
                self.table(rows, title=section_title)
            elif isinstance(rows, dict):
                sub_lines = "\n".join(f"[bold]{escape(str(k))}:[/bold] {escape(str(v))}" for k, v in rows.items())
                self.console.print(Panel(sub_lines, title=escape(section_title), expand=False))


def severity_ok_exit(findings: Iterable[Finding]) -> bool:
    """True if there are no ERROR-severity findings."""
    return not has_errors(list(findings))
