# Using Arena-Agent-Pack with Arena's Agent Mode

*A practical integration guide, including applying it across other projects' repositories. Several of these mechanics are reasoned inference rather than officially documented — flagged as such throughout.*

## The Core Relationship

There's no native bridge between these two products. They come from unrelated parties, so integration means wiring them together deliberately rather than flipping a setting.

- **[Arena-Agent-Pack](https://github.com/Abdus2023/Arena-Agent-Pack)** doesn't take actions in the world on its own. Its own README states plainly that it isn't built to invoke external effects on an agent's behalf — instead it's a record-keeping and validation layer: work items, evidence classes, verification gates, decisions, counterexamples, change-impact analyses, and an 18-page wiki, each moved through explicit lifecycle states rather than free-text status updates.
- **[Arena's Agent Mode](https://arena.ai/agent)** is the thing with hands. It's a prompt-driven mode (alongside Battle/Direct/Side-by-Side) that plans autonomously and reaches for tools including web search, image generation, and bash access to a sandbox environment for testing and iteration. It also has a GitHub connector: OAuth-authenticate, pick a repo and branch, and the agent reads the codebase, edits files, and runs commands against your prompt, with every change tracked live in a diff panel you can push upstream as a PR.

So "using them together" means getting Agent Mode's own LLM to invoke the `arena` CLI as a side-channel discipline while it does its actual work. Nobody has built this integration for you — you're prompting it into existence each time.

## Setup: One Repo (developing the Pack itself, or governing a single project)

1. Turn on the GitHub connector, pointed at either your target repo (with the pack cloned in) or the pack's own repo if you're extending it.
2. Have the agent bootstrap the tool:
   ```bash
   pip install -e ./arena_agent_py
   arena --workspace .arena init
   ```
3. Feed it `arena-agent-instructions-pack-v2.md` in your opening prompt (or tell it to read that file from the repo) as its operating discipline for the session — the CLI is quite literally that document turned into tooling.
4. Instruct it to interleave real actions with matching CLI calls, rather than doing the task and self-certifying done:
   ```bash
   arena work claim <id> --owner agent-1
   arena work gate <id> --gate <name> --method <method> --result PASS --evidence "<what was actually checked>"
   arena work validate <id>
   ```
5. Close the session with:
   ```bash
   arena report finalize <id> --status COMPLETE
   arena export --to export
   ```
   pushed back alongside the code diff.

## Setup: Other Projects' Repos

This is where the mechanics change. Arena's own architecture write-up confirms that connecting a repo triggers a brand-new sandbox for that session alone, with the repository copied in fresh each time — an isolated environment, not a persistent one. That means Arena-Agent-Pack doesn't travel with you automatically. For "other projects," you're repeating the bootstrap once per repo, per session — there's no evidence of a shared environment spanning multiple connected repos at once.

Two ways to make that repeatable:

| Approach | How | Trade-off |
|---|---|---|
| **Vendor it in** | Add Arena-Agent-Pack as a git submodule (or a copied subfolder) inside each target repo | Available the instant the connector clones the repo, no dependency on outbound network access at runtime — but you're maintaining a copy/reference in every repo you govern |
| **Re-fetch each session** | Open your prompt with: `pip install git+https://github.com/Abdus2023/Arena-Agent-Pack.git#subdirectory=arena_agent_py && arena --workspace .arena init` | Nothing extra committed to target repos, one canonical source — but it depends on the sandbox actually reaching GitHub/PyPI at runtime, which I haven't seen independently confirmed |

On that last point: the sandbox is described as letting you preview and interact with a running build inside the same session where the agent edits code, which implies dependency installation is a normal thing to do there. That's suggestive, not conclusive — Arena's own showcased examples (storefronts, games, a "Fullstack Code Arena" feature) read distinctly webdev/Node-flavored, so I can't be fully confident Python/pip is equally well-trodden ground.

**A consequence of "fresh sandbox per session":** your `.arena/` workspace is ephemeral by default too. The full git lifecycle — clone, commit, push, PR — is one of the connector's own built-in jobs, which is convenient, but it also means step 5 above (export, then push) isn't just a tidy close. It's the *only* way the audit trail outlives the session. Skip it, move to the next repo, and the records disappear with the sandbox.

## Open Questions I'd Treat as Unverified

- **Network egress from the sandbox** — whether `pip install` (vs. `npm install`) works reliably at runtime is untested by me; worth a small trial before trusting a long unattended run.
- **Data use** — coverage of the Agent Mode launch describes session data feeding Arena's own leaderboard for ranking agents. Worth checking Arena's terms before connecting anything private.
- **The deeper, structural issue** — and this one seems squarely in the Pack's own stated spirit: it enforces internal *consistency* of a record (you can't skip lifecycle states) but not the *truth* of what's written into it. Nothing stops the same LLM from writing a gate result of `PASS` without having earned it. The discipline only bites if the evidence fields carry something independently checkable — real command output, an actual diff — rather than just the agent's own narration of what it did.

## Sources

- Arena-Agent-Pack README — https://github.com/Abdus2023/Arena-Agent-Pack
- Arena Help Center, "How to use Agent Mode" — https://help.arena.ai/articles/5432423882-how-to-use-agent-mode
- Arena Blog, "Coding in Agent Mode: From Idea to Shipping with GitHub" — https://arena.ai/blog/coding-in-agent-mode
- Arena Agent Mode landing page — https://arena.ai/agent
