# Prompt 5: Session End — Review, Document & Handoff (MANDATORY)

**Who uses this:** Junior devs, at the end of EVERY AI coding session, before closing.

**What it does:** Quality-gates the code, creates institutional memory, enforces secrets hygiene. The next person (or the same person next session) knows exactly what happened and why.

**Copy-paste into your AI tool:**

```
We are done with this session. Do the following in order:

---

## STEP 1 — Quality Review (DO THIS FIRST, BEFORE documenting)

Review every file changed or added in this session for these common junior mistakes.
Read the actual diff — do NOT rely on memory.

### 1.1 Silent Failure Patterns (MOST IMPORTANT)

Look at every `except` block. For each one, ask:

| Check | Red Flag |
|---|---|
| Does the except catch `Exception` or bare `except:`? | Should be specific (`except ValueError`, `except requests.Timeout`) |
| Does the except silently return a default or `pass`? | If an error is swallowed, the feature silently breaks instead of failing loudly |
| Does the except log anything? | If not, the bug will be invisible for weeks |

**Real bug this catches:** A variable `content_length` was checked in an `if` but never assigned from `response.headers`. A broad `except` caught the `NameError` and returned `10.0 MB` silently. The feature was broken for 4 weeks — it only surfaced when larger inputs overloaded the fallback path.

**Rule:** If an except block returns a default value, it MUST also log a warning. If it catches a broad exception, it MUST be intentional with a comment explaining why.

### 1.2 Variable Definition Check

For every variable used in a conditional or comparison:
- Is it assigned in ALL code paths before it's read?
- Could a `try` block fail before the assignment, leaving the variable undefined?
- Are there any variables that exist only inside a `try` block but are referenced outside it?

### 1.3 Scope & Side Effects

- Are any new functions or variables modifying state they shouldn't? (global variables, module-level mutation, unintended DB writes)
- If a function was modified, does the change affect ALL its callers? Trace at least one caller to confirm.
- Was any existing function signature changed? If yes — did you update every caller?

### 1.4 Regression Check — Did This Break Anything?

For EVERY changed file, ask:

| Question | How to verify |
|---|---|
| Is there an existing test for the code I touched? | Run it. Does it still pass? |
| Does my change alter the return type or structure of any function? | Check callers — do they expect the old format? |
| Did I remove or rename any function, class, import, or config key? | Grep the codebase for all references |
| Did I change a shared utility, base class, or middleware? | These affect EVERYTHING. List every downstream impact. |
| If I changed error handling, does the new behavior match what callers expect? | Check if callers have try/except around the changed code |

### 1.5 Edge Case Check

- What happens if the input is empty? Null? Extremely large? Malformed?
- What happens if an external API call fails? Timeout? Returns unexpected format?
- What happens if the database has no matching rows? Too many rows?

**If ANY quality issue is found, fix it NOW.** Do not document and move on — this is the last gate before the code is committed.

---

## STEP 2 — Create Session Document

Create a file: `sessions/[YourName]_[YYYY-MM-DD]_[HHMM].md`

Use this exact template:

```markdown
# Session: [Brief title — e.g., "Fix login timeout bug #452"]

**Developer:** [Your name]
**Date:** [YYYY-MM-DD]
**Time:** [HH:MM]
**Quality Review:** ✅ Passed / ⚠️ Issues found and fixed (list below)

---

## What We Worked On
- [Bullet 1 — feature or bug]
- [Bullet 2]
- [Bullet 3]

## What Changed

| File | Change | Why | Layer |
|---|---|---|---|
| path/to/file.py | [What was changed] | [Architectural reason] | [Controller/Service/Repo/Util] |
| path/to/file2.py | [What was changed] | [Architectural reason] | [Controller/Service/Repo/Util] |

## Architecture Notes
[Any design decisions made and WHY. If you followed an existing pattern, name it. If you had to choose between two approaches, explain the choice.]

## Tests Added / Updated
| Test File | What It Covers |
|---|---|
| path/to/test.py | [what scenario] |

## Risks / Follow-ups
- [Thing to watch after deploy]
- [Thing not done yet — needs separate task]
- [Any manual verification needed]

## Environment
- Branch: [branch name]
- Environment: [dev-env / qa-env / prod-env]
```

---

## STEP 3 — Security Check

Before committing, verify ALL changed files + the session .md have NO:
- Passwords
- API keys
- Tokens or secrets
- Server IP addresses or hostnames
- Internal URLs
- PII (emails, names of real users, phone numbers)
- Database connection strings

If any doubt — ASK ME before committing.

---

## STEP 4 — Commit and Push

- Add the session .md file + all code changes.
- Commit with a message that says WHAT and WHY: `fix: [brief description] — [root cause in one line]`
- Push to the appropriate environment branch following deploy_rules.md.
- Tell me: "Pushed to [branch]. Session doc: [filename]. Watch for: [things to monitor]."

---

## STEP 5 — Handoff Checklist

Confirm:
□ Quality review completed (Step 1), issues fixed
□ Session .md file created
□ No secrets in any file (verified)
□ All tests passing
□ Code pushed to correct branch
□ I know what to monitor post-deploy

REMEMBER: This .md file is how the NEXT session picks up context. Make it good.
```
