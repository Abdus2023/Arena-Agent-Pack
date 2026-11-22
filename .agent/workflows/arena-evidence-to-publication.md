# Arena Evidence-to-Publication Workflow

**Status:** operator-run workflow  
**Computational implementation:** `arena_agent_py/arena_agent/`

## 1. Initialize and audit
1. Pin Arena package version and repository commit.
2. Initialize a workspace with `arena --workspace .arena init`.
3. Create a Repository Audit record and run `audit scan-fs` with explicit root and depth.
4. Record scan limits and local-observation authority.

## 2. Model knowledge and work
1. Create Knowledge Units with evidence class and confidence.
2. Create bounded Work Items with owner, responsibility and acceptance criteria.
3. Claim work and advance only through legal lifecycle transitions.
4. Attach gates and evidence; validate each record.

## 3. Decisions and counterexamples
1. Create attributed Decision Records with alternatives, selected choice and scope.
2. Record stop-condition overrides explicitly.
3. Stage Counterexamples and promote only with required reproduction evidence.
4. Create Change-Impact records and obtain explicit approval.

## 4. Verify and report
1. Validate every referenced record and graph relationship.
2. Build a Final Report and complete the completion checklist.
3. Derive the maximum status from evidence; reject status-masquerading.
4. Distinguish COMPLETE, COMPLETE-WITH-WARNINGS, BLOCKED and INCOMPLETE according to implementation rules.

## 5. Publish
1. Maintain canonical wiki pages 00–17; do not synthesize missing pages.
2. Run `export validate` first; it must not write.
3. Review findings, then materialize Markdown.
4. Render HTML from the same ExportPlan; presentation must not re-open or re-validate workspace state.
5. Verify artifact paths, referenced record identities and report scope.

## Stop conditions
Stop on illegal lifecycle transitions, unsubstantiated decision overrides, unsupported counterexample promotion, missing cross-record references, or a final status above the evidence ceiling. The package records and validates; external side effects remain outside its authority.
