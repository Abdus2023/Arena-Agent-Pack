# Arena Decision Record

> Template derived from: **Arena Agent Prompt Instructions Pack**, §24 (Ambiguity Contract), §25 (Stop Conditions).
> Create one of these whenever evidence conflicts, a specification is ambiguous, or a STOP condition is triggered. Never resolve ambiguity silently — this file is the required alternative to guessing.

---

## ARENA-DECISION-<ID>

| Field | Value |
|---|---|
| Decision ID | `ARENA-DECISION-<yyyymmdd>-<seq>` |
| Raised by | |
| Timestamp | |
| Status | OPEN / RESOLVED / SUPERSEDED |
| Related Knowledge Unit(s) | |
| Related Work Item(s) | |
| Triggering Stop Condition (if any, ref. pack §25 items 1-13) | |

### Question
<The precise question that cannot be answered from current evidence alone.>

### Conflicting Statements
| # | Statement | Source | Classification |
|---|---|---|---|
| 1 | | | |
| 2 | | | |

### Sources
- <full citations: doc, path, commit, section>

### Affected Components
- <list>

### Possible Interpretations
| Option | Description | Consequences if chosen |
|---|---|---|
| A | | |
| B | | |

### Consequences
<What happens downstream depending on which interpretation is chosen — invariants, authority, resources, persistence, tests affected.>

### Required Authority
<Who/what has the authority to resolve this — human governance, supervisor, spec owner, etc. The Arena Agent does not self-authorize resolution of ambiguity.>

### Current Decision
- Decision: `UNRESOLVED` (default) | `<chosen option>`
- Decided by:
- Timestamp:
- Rationale:

### Decision Provenance
- How resolution was obtained (meeting, ticket, explicit human instruction, governing spec update, etc.)
- Link/reference to authoritative confirmation

---

## Usage Notes

- While `Status = OPEN`, any dependent Knowledge Unit or Work Item must reference this ID and remain marked `AMBIGUOUS` / `BLOCKED` rather than proceeding on an assumed interpretation.
- Do not delete resolved decision records — mark `RESOLVED` or `SUPERSEDED` and keep history intact (see pack §14: never silently rewrite history).
- If a later decision reverses this one, create a new record and set this one's status to `SUPERSEDED`, linking forward to the new ID.
