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

## 2. Select an executor and run preflight

1. Run `paseo daemon status`. If unavailable, use an eligible native specialist and report any unmet provider or isolation requirement.
2. Classify risk and choose the cheapest executor that meets the quality floor. Policy lives in `docs/ai-os/roteamento.json`; project restrictions and allowed model IDs live in `config/ai-os-memory.toml`. Read these files before choosing an executor, fallback, or reviewer. Confirm model IDs on the host.
3. Before every `paseo run`, run `python3 scripts/preflight.py ...` from the workflow-ai checkout with the intended launch arguments and `--risk`. Use Python 3.11 or newer. The preflight reads metered-provider quota snapshots and the global `paseo ls --json -a -g --background` snapshot; it never launches agents or changes state.
4. Proceed only on `allow`. For `ask_human`, present the reason codes and eligible alternatives to Felipe. For `deny`, correct the parameters or select an eligible executor and rerun. Quota does not lower the high-risk quality floor. Astra also requires the explicit human assessment `--no-cheaper-eligible` when no cheaper executor meets that floor.

| Risk | Executor | Verification |
|---|---|---|
| High: security, auth, data, architecture | Claude Opus; Codex Astra subject to the JSON conditions | Reviewer from another model family |
| Medium | Codex gpt-6.1-sol / gpt-6-luna or Claude Sonnet | For a large diff: another eligible harness, then gpt-6.1-sol with thinking low/medium, gpt-6-luna if mechanical |
| Low, test-verifiable | OpenCode free or Codex gpt-6-luna | Orchestrator checks tests and diff |

OpenCode has no official quota meter; missing quota is expected and does not block it. Claude/Codex mean subscription harnesses, not gateway APIs. Reviewer family, medium-risk review order, data classes and fallback limits remain orchestration duties documented in the JSON, beyond the preflight's checks.

## 3. Launch with explicit ownership

Run preflight against the destination project (`--cwd`) and the exact base reference. Example from the workflow-ai checkout:

```sh
python3 scripts/ai_os_task.py open "<short objective>" --risk medium --cwd <project>
python3 scripts/preflight.py --provider codex/gpt-6.1-sol --mode auto-review --thinking medium --new-workspace worktree --base <current-branch> --cwd <project> --risk medium
# After allow, use the same provider/model, mode, thinking, base and cwd:
paseo run --no-wait --title "[<task_id>] <title>" --provider codex/gpt-6.1-sol --mode auto-review --thinking medium --new-workspace worktree --worktree-slug <slug> --base <current-branch> --cwd <project> "<objective; owned files; limits; acceptance criteria; end with a state note>"
python3 scripts/ai_os_task.py link <task_id> <agent_id> --role exec
```

- Keep the literal title prefix, e.g. `[T-20261109-01] <title>`, and the explicit task link; Paseo does not expose labels. Reuse the task ID for reviewers and fixes, with the corresponding `--role`.
- Specify provider/model, mode and provider-required parameters explicitly. A new worktree requires an explicit base; any supplied base must exist. Child agents do not inherit these settings (I-17, I-19).
- Inside Paseo, apply the same preflight before `create_workspace` and `create_agent`. Carry the checked base, provider/model and `settings.modeId` into those calls.
- Run one heavy Codex task at a time, as defined by `concurrency` in the JSON. Launch sequentially: preflight, run, preflight, run. `--planned-heavy N` adds heavy launches already planned but not yet visible in the snapshot; default is zero.
- With `--short-task`, the JSON reset exception can allow a short task within 20 minutes of the five-hour reset; it never bypasses the weekly limit or concurrency.
- Assign one writer per worktree. Record each agent ID and branch; await completion notifications inside Paseo without polling.

## 4. Handle waiting and approvals

- In a terminal, use `paseo wait <id>` and `paseo permit ls`. `paseo ls` can report `running` while the agent waits for permission (I-16).
- Approve only safe, task-scoped requests inside the assigned worktree, when the harness permits you to approve. Send everything else to Felipe; never bypass a parent approval gate.
- Check concrete progress: session, files, tests and commits. Treat `idle` without a new commit or changed files as suspicious (I-01, I-25).
- A `question` request needs a human answer; notify immediately.
- Keep the OpenCode service running while agents are active; restarting loses permission handlers and creates phantom requests (I-26).
- Prefer `paseo schedule` to resume after a usage limit; tested on 25/10/2026.
- Recheck preflight immediately before launch; its concurrency check is a snapshot, not a reservation (I-23).

## 5. Verify, integrate, and clean up

1. Inspect actual artifacts, diff, relevant test results and commit contents against every acceptance criterion. The agent's final message alone is insufficient evidence.
2. If sandbox protection blocks a commit, the verifying orchestrator commits the checked result (I-05); preserve the sandbox.
3. Integrate the verified result with merge/cherry-pick into the intended branch, then run the relevant checks there. Preserve unrelated changes.
4. After successful integration, clean up with `paseo delete <id>`, `git worktree remove <path>`, then `git branch -D <branch>`. Confirm the exact targets are integrated and disposable; follow AGENTS.md's confirmation requirements for destructive actions.
5. Record the human/orchestrator verdict with the task CLI after verification. Agent `idle` or `closed` is not acceptance. `docs/ai-os/telemetria.jsonl` is legacy history; new verdicts go to the task ledger outside Git:

```sh
python3 ~/Workspace/tools/workflow-ai/scripts/ai_os_task.py close <task_id> <aceito|retrabalho|rejeitado> --nota "<verification evidence>"
```

Reopen a closed task before relaunching or linking another agent to it:

```sh
python3 ~/Workspace/tools/workflow-ai/scripts/ai_os_task.py reopen <task_id> --motivo "<reason for another attempt>"
```

## Antigravity (Gemini)

Uso direto pelo Felipe no app ou CLI oficial. Nenhum agente, Paseo, Claude ou script do AI OS invoca `agy`. A FAQ do Google diz que acessar o Antigravity por software de terceiros viola os Termos de Serviço e pode levar à suspensão ou encerramento da conta; envolver `agy` em agentes de terceiros não é suportado nos planos de consumidor. Ver [ADR-0006](../../docs/ai-os/decisions/0006-antigravity-fora-da-automacao.md). A tabela de modelos e as medições históricas ficam em `docs/ai-os/MODELOS_2026.md` como referência para uso direto.

## Output contract

- Distribution plan: task → executor → reason, including any fallback or decision to work directly.
- Agent IDs with provider/model and worktree/branch, or explicitly no agents launched.
- Verified results: artifacts/diff, tests actually run, commits and integration status.
- Pending approvals, failed checks, limitations and cleanup still required.
- End with a state note: completed and verified work, decisions in force, open questions, exact next step.
