# Prompt 4: Code Review — Quality Gate

**Who uses this:** Junior devs, before pushing code. Senior devs, during PR review with AI assistance.

**What it does:** A checklist-driven review that catches architecture violations, patchy fixes, and security issues. Forces the AI to check consistency, not just correctness.

**Copy-paste into your AI tool:**

```
Review the following changes. Be thorough — these are NOT approved yet.

[PASTE A GIT DIFF, OR DESCRIBE THE FILES CHANGED, OR SAY "review all uncommitted changes"]

---

## Check each category below. Flag EVERY issue.

### 1. ARCHITECTURE (most important)

- Is the change in the RIGHT layer? (Check AGENTS.md Layer Map)
- Does it follow an EXISTING pattern? (Name the pattern it follows. If you can't name one, flag it.)
- Does it introduce a NEW abstraction, library, or pattern? (If yes, flag it — needs discussion.)
- Does it conflict with anything in product_theory.md? (Future plans, forbidden patterns, tech debt)

### 2. QUALITY

- Are ALL error paths handled? Not just the happy path.
- Is anything hardcoded that should be in config or constants?
- Are there magic numbers or unexplained values?
- Is there dead code, commented-out blocks, or debug logs (console.log, print, etc.)?
- Are functions too long or doing too many things?

### 3. CONSISTENCY

- Does naming match the rest of the codebase? (Check AGENTS.md naming conventions)
- Are imports organized correctly? (Order, absolute vs relative, barrel exports)
- Does it use the project's existing utilities instead of reimplementing them?
- Does the code LOOK like it was written by the same person as the rest of the codebase?

### 4. SAFETY & SECURITY

- Could this break something else? Check all callers, consumers, and upstream code.
- Are secrets, tokens, passwords, or PII exposed anywhere?
- Are DB queries protected against injection?
- Is user input validated at the boundary?
- Is the change behind proper auth/authz checks?

### 5. TESTS

- Are there tests for the new code or the fix?
- Do existing tests still pass?
- Are edge cases tested? (null, empty, boundary values, error states)
- If there's no test, flag it and say what test is missing.

---

## Output Format

Use this exact format for each finding:

```
🔴 FAIL — [file:line] — [what's wrong] — [suggested fix]
🟡 WARN — [file:line] — [what's questionable] — [suggestion]
🟢 PASS — [category] — [what was checked]
```

After listing all findings, give a summary:

```
## Summary
- 🔴 FAIL: [N]
- 🟡 WARN: [N]
- 🟢 PASS: [N]

### Verdict: APPROVED / NEEDS FIXES (N issues) / REJECTED
```

If VERDICT is NOT "APPROVED", list the MUST-FIX items before the SHOULD-FIX items.

REMEMBER: Your job is to protect the architecture. Flagging something is NOT being pedantic — it's preventing future rot.
```
