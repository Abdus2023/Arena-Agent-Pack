"""
Project-wide architectural conformance check (v2 §14 dependency direction).

Conformance audit follow-up (R9, Phase 5A -- Evidence Hardening):

`test_html.py::test_html_module_does_not_import_storage_or_validate_or_derive`
already protects one instance of this property (``html.py`` must not import
``storage``). This module generalizes that pattern to *every* module in
``arena_agent/`` so the whole layering is protected, not just one edge of it.

Guiding rule under test: static analysis only. This test parses each module
with ``ast`` and inspects only its import statements -- it never imports or
executes ``arena_agent`` code itself. That is deliberate: a test that
protects against import-direction/circular-import violations must not do so
by *importing* the modules under test, since that would let Python's own
import machinery (and its willingness to tolerate cycles at runtime in some
orderings) silently paper over exactly the violation this test exists to
catch. Reading source text with ``ast.parse`` cannot be fooled that way.

Layering under test (v2 §14, "no downstream layer may be depended on by an
upstream one"):

    models
      -> validation
           -> storage
           -> reporting
                -> export
                     -> html
                     -> cli (presentation)
    output
      -> validation                      (does not participate in export/html)
    cli
      -> everything                      (presentation layer, top of the graph)

Shared, cross-cutting modules that every layer may depend on without that
being an architectural violation: ``vocab`` (controlled vocabularies) and
``ids`` (stable ID helpers). ``graph`` (the Knowledge Graph value type) is
also treated as a shared low-level dependency: ``validation``, ``storage``,
and ``reporting`` all legitimately hold/manipulate a ``KnowledgeGraph``
value without that implying any of them is "above" the others -- it is data,
not a policy-bearing layer, exactly like ``vocab``/``ids``. ``content_scan``
is a leaf module (Ingested Content Contract helper, §4.1) used only by
``cli`` and has no local imports of its own.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent.parent / "arena_agent"

# ---------------------------------------------------------------------------
# 1. Authoritative dependency rules.
#
# For each module, the set of *other* local modules it is allowed to import.
# Anything not listed here is a forbidden edge. Modules not present as a key
# default to "no local imports allowed" (currently only true of vocab/ids,
# which are listed explicitly below with an empty set for clarity).
# ---------------------------------------------------------------------------

ALLOWED_IMPORTS: dict[str, set[str]] = {
    "vocab": set(),
    "ids": set(),
    "content_scan": set(),
    "models": {"vocab"},
    "graph": {"vocab"},
    "validation": {"graph", "ids", "models", "vocab"},
    "storage": {"graph", "ids", "models", "vocab"},
    "reporting": {"graph", "models", "validation", "vocab"},
    "output": {"validation"},
    "export": {"models", "reporting", "storage", "validation", "vocab"},
    "html": {"export", "validation", "vocab"},
    "cli": {
        "content_scan",
        "export",
        "graph",
        "html",
        "ids",
        "models",
        "output",
        "reporting",
        "storage",
        "validation",
        "vocab",
    },
}

# The package's own top-level package-init module (re-exports __pack_version__
# etc.) is not part of the layering -- every module may import from it
# (``from . import __pack_version__``) without that being an architectural
# statement about layering. It is excluded from the ALLOWED_IMPORTS keys
# above and handled separately below.
PACKAGE_INIT_SENTINEL = "__init__"


def _local_imports(py_file: Path, known_modules: set[str]) -> set[str]:
    """Return the set of arena_agent-local module names imported by py_file.

    Only local imports are returned. ``PACKAGE_INIT_SENTINEL`` is included
    when the file does ``from . import <name-defined-in-__init__>`` (e.g.
    ``from . import __pack_version__``), since that is an import of a name
    the package __init__ module defines/re-exports, not of a sibling
    module -- disambiguated from a genuine ``from . import <sibling-module>``
    by checking the imported name against ``known_modules`` (the real
    ``arena_agent/*.py`` filenames).

    Deliberately conservative: this only needs to recognize the import forms
    actually used in this codebase (confirmed by a full-repo scan before
    writing this test): ``from . import x``, ``from .x import y``, and
    ``from arena_agent[.x] import y``. It does not need to handle multi-level
    relative imports (``from ..x import y``) or absolute
    ``import arena_agent.x`` forms because neither occurs anywhere in
    ``arena_agent/`` -- if one is introduced later, the fallback path below
    still records *something* local rather than silently ignoring it, so a
    newly introduced forbidden edge cannot slip past this test as a false
    negative.
    """
    tree = ast.parse(py_file.read_text(), filename=str(py_file))
    found: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.level >= 1:
                # `from . import a, b`  -> node.module is None, each name
                #   is either a sibling module (`from . import storage`) or
                #   a name re-exported by __init__ (`from . import
                #   __pack_version__`) -- disambiguate against the real
                #   module filenames.
                # `from .x import y`    -> node.module == "x", a direct
                #   import of sibling module x.
                if node.module:
                    found.add(node.module.split(".")[0])
                else:
                    for alias in node.names:
                        found.add(alias.name if alias.name in known_modules else PACKAGE_INIT_SENTINEL)
            elif node.module == "arena_agent":
                # `from arena_agent import x` -- x is either a sibling
                # module or a name re-exported by __init__; disambiguate
                # the same way as the relative-import case above.
                for alias in node.names:
                    found.add(alias.name if alias.name in known_modules else PACKAGE_INIT_SENTINEL)
            elif node.module and node.module.startswith("arena_agent."):
                found.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "arena_agent" or alias.name.startswith("arena_agent."):
                    parts = alias.name.split(".")
                    found.add(parts[1] if len(parts) > 1 else PACKAGE_INIT_SENTINEL)

    return found


def _module_names() -> list[str]:
    return sorted(
        f.stem
        for f in PKG_DIR.glob("*.py")
        if f.stem != "__init__"
    )



def test_allowed_imports_table_covers_every_module():
    """Guard against the rule table silently going stale as modules are added."""
    modules = set(_module_names())
    assert modules == set(ALLOWED_IMPORTS), (
        "ALLOWED_IMPORTS must have exactly one entry per arena_agent/*.py module "
        f"(missing: {modules - set(ALLOWED_IMPORTS)}, "
        f"extra: {set(ALLOWED_IMPORTS) - modules})"
    )


def test_project_wide_import_direction_matches_v2_section_14():
    """v2 §14: no module may import a module that sits above it in the
    layering (models -> validation -> storage/reporting -> export -> html
    -> cli), except for the explicitly shared cross-cutting dependencies
    (vocab, ids) and the shared low-level value type (graph).

    This is the AST-only generalization of
    ``test_html.py::test_html_module_does_not_import_storage_or_validate_or_derive``
    to every module in the package, per conformance audit recommendation R9.
    """
    violations: list[str] = []
    known_modules = set(_module_names())

    for module_name in known_modules:
        py_file = PKG_DIR / f"{module_name}.py"
        local_names = _local_imports(py_file, known_modules)

        # Every module may reference the package __init__ (e.g. for
        # __pack_version__) without that being a layering violation --
        # it carries no policy, only a version constant.
        local_names.discard(PACKAGE_INIT_SENTINEL)

        allowed = ALLOWED_IMPORTS.get(module_name, set())
        forbidden = local_names - allowed

        for target in sorted(forbidden):
            rule = (
                f"'{module_name}' is only permitted to import "
                f"{sorted(allowed) or '(nothing -- it is a leaf module)'}"
            )
            violations.append(
                f"{module_name}.py imports '{target}', which is not in its allowed "
                f"set. Violated rule: {rule}. (v2 section 14 dependency-direction "
                f"invariant: downstream layers must not be depended on by "
                f"upstream/sibling layers outside the declared shared "
                f"dependencies vocab/ids/graph.)"
            )

    assert not violations, "\n".join(violations)


def test_no_module_imports_cli():
    """cli.py is the top of the layering (presentation). No other module may
    import it -- this would be the most severe possible inversion, since it
    would make every other layer depend on the CLI's own dependency closure.
    """
    violations = []
    known_modules = set(_module_names())
    for module_name in known_modules:
        if module_name == "cli":
            continue
        py_file = PKG_DIR / f"{module_name}.py"
        if "cli" in _local_imports(py_file, known_modules):
            violations.append(f"{module_name}.py imports cli.py -- forbidden inversion.")
    assert not violations, "\n".join(violations)


def test_no_circular_imports_among_local_modules():
    """A lightweight structural cycle check independent of the layered-rule
    table above: build the local-import graph from source text alone (no
    execution) and confirm it is a DAG. This is a second, independent proof
    of acyclicity, deliberately not derived from ALLOWED_IMPORTS, so a
    mistake in that table can't simultaneously hide a real cycle.
    """
    graph: dict[str, set[str]] = {}
    known_modules = set(_module_names())
    for module_name in known_modules:
        py_file = PKG_DIR / f"{module_name}.py"
        local_names = _local_imports(py_file, known_modules)
        local_names.discard(PACKAGE_INIT_SENTINEL)
        graph[module_name] = local_names

    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_path: list[str] = []

    def _visit(node: str, path: list[str]) -> bool:
        if node in visiting:
            cycle_path[:] = path + [node]
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in graph.get(node, set()):
            if _visit(neighbor, path + [node]):
                return True
        visiting.discard(node)
        visited.add(node)
        return False

    has_cycle = any(_visit(m, []) for m in graph if m not in visited)
    assert not has_cycle, f"Circular local import detected: {' -> '.join(cycle_path)}"
