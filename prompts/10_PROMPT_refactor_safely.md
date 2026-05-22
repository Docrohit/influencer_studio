# Prompt 10: Refactor Safely — Clean Up Without Breaking

**Who uses this:** Junior devs, when they inherit messy code and need to improve it without changing behavior.

**What it does:** Characterizes the current behavior, writes tests to lock it in, refactors, and verifies nothing broke. Behavior is preserved.

**Copy-paste into your AI tool:**

```
I need to refactor: [FILE / MODULE / FUNCTION NAME]

REASON: [Why — too long, duplicated, hard to read, wrong layer, etc.]

CRITICAL RULE: ZERO BEHAVIOR CHANGES. The refactored code must produce IDENTICAL results for ALL inputs. If you think behavior should change, note it separately — don't do it here.

---

## STEP 1 — Characterize Current Behavior

- Read the code. Trace all callers (search the codebase: who calls this?).
- List every input→output pair or every state transition.
- What external dependencies does it have? (DB calls, API calls, file I/O, global state)
- Read AGENTS.md: what LAYER should this code be in? Is it in the right layer?

## STEP 2 — Safety Net (Tests First)

Before touching the code:

- Do tests already exist for this code? If yes, verify they pass.
- If no tests exist, write characterization tests that capture the CURRENT behavior — even if the behavior seems wrong. These are the safety net.
- Run the tests. They MUST pass before any refactoring.

## STEP 3 — Propose the Refactor

Show me your plan:

```
## Refactor Plan: [file/function name]

### Current problems:
- [Problem 1]
- [Problem 2]
- [Problem 3]

### What I will change:
- [Change 1 — e.g., "Extract validation into separate function"]
- [Change 2 — e.g., "Replace nested if-else with lookup table"]
- [Change 3]

### What I will NOT change:
- [Behavior: identical input → identical output]
- [Public API / function signatures — unless approved]
- [Database schema]
- [Any other unchanged areas]

### Layer check (from AGENTS.md):
This code is currently in [layer]. It should be in [layer].
[If wrong layer: "I recommend moving it, but I won't without your approval."]
```

WAIT FOR MY APPROVAL.

## STEP 4 — Refactor (After Approval)

Refactor step by step. After EACH step:
- Run the tests.
- If tests fail, UNDO the last step and tell me.

Refactoring techniques allowed:
- Extract function/method
- Rename for clarity (consistent with AGENTS.md naming)
- Replace magic numbers with named constants
- Flatten nested conditionals (guard clauses)
- Deduplicate repeated code
- Split large functions into smaller ones

NOT allowed (without explicit discussion):
- Introducing new libraries
- Changing function signatures or public APIs
- Changing database queries or data structures
- Adding or removing features
- "While I'm here" changes to unrelated code

## STEP 5 — Verify

- Run the FULL test suite. All tests must pass.
- Confirm: every caller still works. The same inputs produce the same outputs.
- Run linter/formatter.

## STEP 6 — Report

```
## Refactor Summary
- File: [path]
- Lines before: [N] / after: [N]
- What changed: [summary in 2-3 bullets]
- Tests: [all passing / N tests]
- Behavior: 100% preserved / [exceptions with reason]
- Risks: [none / what to watch]
```

REMEMBER: Behavior is sacred. Tests are the safety net. No scope creep. If you see a bug in the existing code, note it — don't fix it here unless I say "fix that too."
```
