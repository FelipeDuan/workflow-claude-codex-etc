---
name: ai-os-orchestration
description: Orchestrate work across native specialists and Paseo providers. Use when the user wants to delegate, split tasks, parallelize, use Codex or OpenCode, save Claude quota, obtain review from another model family, or execute an approved plan with several agents. Trigger by semantic intent, including requests in Portuguese.
---

# AI OS orchestration

## 1. Choose the delegation level

- Work directly for trivial tasks when coordination would cost more than the work, subject to AGENTS.md's implementation delegation rule.
- Use a native harness subagent for a specialist working with the same context and checkout, without a separate worktree.
- Use Paseo for independent or parallel tasks, another provider, saving quota, or review by another model family.
- Split only independent tasks with verifiable acceptance criteria. Assign one writer per worktree; keep dependent work sequential.
- State the distribution before dispatch: task → executor → reason. Choosing not to delegate is valid.

## 2. Check availability and select the executor

1. Run `paseo daemon status`. If unavailable, fall back to native subagents and tell Felipe which provider or isolation requirements cannot be met.
2. Check whether the project matches `[restricted].paths` in `~/Workspace/tools/workflow-ai/config/ai-os-memory.toml` (including its main checkout for worktrees), or has a SessionStart restriction warning. File presence alone does not make a project restricted. Such projects permit only `allowed_models`, including fallback and reviewers. Match Paseo's `opencode/opencode/<model>` against policy ID `opencode/<model>`. Claude/Codex mean subscription harnesses, not gateway APIs.
3. Read `~/.local/state/ai-os/quota/claude.json` and run `python3 ~/Workspace/tools/workflow-ai/scripts/quota_codex.py`. Missing, stale, or failed readings mean `unknown`; never invent percentages. If the sandbox blocks the sensor, request a real reading from the orchestrator (I-06).
4. Apply ADR-0002's quality floor, then choose the lowest effective coordination and quota cost:

| Risk | Executor | Verification |
|---|---|---|
| High: security, auth, data, architecture | Frontier: Claude Opus or GPT-6 Astra | Reviewer from another model family |
| Medium | Codex Luna/Sol or Claude Sonnet | Add a reviewer for a large diff |
| Low, test-verifiable | OpenCode free | Orchestrator checks tests and diff |

5. At 5h usage ≥85% or weekly usage ≥75%, prefer another provider for new low/medium-risk tasks. Consider reset time; ADR-0002 allows a short task within 20 minutes of reset. Never lower the high-risk quality floor: wait or ask Felipe if no eligible executor/reviewer is available.
6. Verify available model IDs on the host. `docs/ai-os/roteamento.json` is advisory, not native Paseo configuration. In this repo, consult ADR-0002/0003 and `docs/ai-os/USO-DIARIO.md` for operational details.

## 3. Launch with explicit ownership

From a terminal, substitute the current branch, confirmed provider/model, and a provider-valid mode:

```sh
paseo run --no-wait --title <t> --provider <provider/model> --mode <mode> --new-workspace worktree --worktree-slug <slug> --base <current-branch> "<objective; owned files; limits; acceptance criteria; end with a state note>"
```

- Always specify `provider/model` (I-19) and `--base` (I-17); a new worktree otherwise starts from the default branch.
- Codex modes: `auto`, `auto-review`, `full-access`. Default to `auto-review`; never use `full-access`.
- Claude mode IDs: `plan`, `default`, `acceptEdits`, `auto`. Never use `bypassPermissions`.
- OpenCode mode IDs: `build`, `plan`. Pass mode IDs, not UI labels (`Build` is rejected).
- Inside Paseo, use injected MCP tools `create_workspace` then `create_agent`. Explicitly set the base branch, provider/model and `settings.modeId`; children do not inherit model or mode (I-19). Apply the same ownership and permission limits.
- Record each agent ID and worktree/branch. Await completion notifications inside Paseo without polling.

## 4. Handle waiting and approvals

- In a terminal, use `paseo wait <id>` and `paseo permit ls`. `paseo ls` can report `running` while the agent waits for permission (I-16).
- Approve only safe, task-scoped requests inside the assigned worktree, when the harness permits you to approve. Send everything else to Felipe; never bypass a parent approval gate.
- Check concrete progress when diagnosing a stall: created session, changed artifacts, test output. A live process does not prove progress (I-01).

## 5. Verify, integrate, and clean up

1. Inspect actual artifacts, diff, relevant test results and commit contents against every acceptance criterion. The agent's final message alone is insufficient evidence.
2. If sandbox protection blocks a commit, the verifying orchestrator commits the checked result (I-05); preserve the sandbox.
3. Integrate the verified result with merge/cherry-pick into the intended branch, then run the relevant checks there. Preserve unrelated changes.
4. After successful integration, clean up with `paseo delete <id>`, `git worktree remove <path>`, then `git branch -D <branch>`. Confirm the exact targets are integrated and disposable; follow AGENTS.md's confirmation requirements for destructive actions.
5. In the workflow-ai repo, append one JSON line per task to `docs/ai-os/telemetria.jsonl` using ADR-0002's schema; elsewhere, include the same record in the final summary. Record observed values only, using `null` for unavailable measurements:

```json
{"date":"YYYY-MM-DD","task":"<task>","category":"<category>","risk":"low","complexity":"low","divisible":false,"harness":"<harness>","model":"<model>","duration_s":null,"tests_passed":null,"human_corrections":0,"handoff":false,"outcome":"<outcome>","notes":"<evidence or unavailable measurements>"}
```

## Output contract

- Distribution plan: task → executor → reason, including any fallback or decision to work directly.
- Agent IDs with provider/model and worktree/branch, or explicitly no agents launched.
- Verified results: artifacts/diff, tests actually run, commits and integration status.
- Pending approvals, failed checks, limitations and cleanup still required.
- End with a state note: completed and verified work, decisions in force, open questions, exact next step.
