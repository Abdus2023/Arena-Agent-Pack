---
name: arena-workspace-publication
description: Validate and publish Arena workspaces through knowledge graphs, canonical wiki pages, Markdown export, and HTML projections.
---

# Arena Workspace Publication

## Purpose
Produce consistent, derived documentation from the Arena JSON workspace without creating a second source of truth or inventing missing records.

## Activation
Use when maintaining canonical wiki pages, building knowledge-graph views, validating an export plan, exporting Markdown, or rendering HTML.

Do not use this skill to fabricate missing wiki pages, repair invalid records silently, or implement new validation rules in the presentation layer.

## Inputs
- Arena workspace root and pinned package revision.
- Validated source records and references.
- Canonical wiki page number (00–17) and page content/scope.
- Export destination and output policy.
- Existing ExportPlan and findings, where applicable.

## Procedure
1. Validate the workspace records and cross-record references before publication.
2. Create/update only canonical wiki pages 00–17. Derive headers from current referenced records; do not store independently asserted status fields in page headers.
3. Validate wiki page structure separately from cross-record reference resolution.
4. Build the export plan through the existing export pipeline. Use `export validate` as a non-writing validation operation.
5. Preserve missing, invalid, blocked and not-applicable as distinct states. Do not synthesize missing canonical wiki pages.
6. Materialize Markdown with the export command only after reviewing the plan and findings.
7. Render HTML from the same ExportPlan. The HTML layer is presentation only; it must not reopen the workspace, revalidate records or derive a second status model.
8. Confirm output paths and counts match records actually present. Preserve ERROR findings in rendered output.
9. Record export timestamp, workspace root, pack version and source record identities.
10. Review the final artifact tree and retain the underlying JSON workspace as source of truth.

## Outputs
- Validated canonical wiki records.
- ExportPlan validation result.
- Markdown artifact tree.
- HTML projection.
- Publication report with missing/invalid items and findings.

## Failure handling
Do not publish when the export plan has unresolved integrity errors without explicit disclosure. Stop if HTML rendering attempts to reopen workspace state or invent new validation logic. Do not write files during `export validate`.

## Acceptance criteria
- Source JSON workspace remains authoritative.
- Wiki index is closed to page numbers 00–17.
- Headers are derived from current referenced records.
- Missing pages are reported, not fabricated.
- Markdown and HTML share the same ExportPlan.
- HTML performs presentation only.
- Findings remain visible in exported artifacts.

## Source references
- `arena_agent_py/arena_agent/export.py`
- `arena_agent_py/arena_agent/html.py`
- `arena_agent_py/arena_agent/cli.py`, `models.py`, `validation.py`, and `reporting.py` for the maintained wiki command/model/validation/rendering implementation
- `templates/arena-wiki-page-template.md`

## Validation status
The package README documents a 241-test suite for its recorded revision; this skill does not claim that the suite was executed in this increment.
