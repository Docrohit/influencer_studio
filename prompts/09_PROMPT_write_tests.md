# Prompt 9: Write Tests — Add Coverage Without Breaking Anything

**Who uses this:** Junior devs, when they need to add tests to untested code, either as a standalone task or before/after a feature change.

**What it does:** Analyzes the existing code, identifies what tests are missing, writes tests that follow project conventions, and runs them to verify.

**Copy-paste into your AI tool:**

```
I need to write tests for: [FILE / MODULE / FEATURE NAME]

This is a TESTING task. DO NOT change the production code. Only add tests. If the code is untestable as written, TELL ME why (e.g., no dependency injection, hardcoded side effects, no interfaces). Don't refactor unless I explicitly ask.

---

## STEP 1 — Understand What Needs Testing

- Read the file(s) I specified.
- Read AGENTS.md to find: which test framework? where tests live? naming conventions?
- Find existing tests in the project that test similar code. Show me 2-3 examples so I can see the pattern.

## STEP 2 — Audit: What Test Coverage Exists?

For each function/method/component in the target file, report:

```
Function: [name]
Existing tests: [Yes/No — test file + test name]
What it does: [1 sentence]
Edge cases to test: [list]
```

## STEP 3 — Identify Gaps (What To Test)

List the specific scenarios that need tests. Prioritize:

1. **Critical path** — the main thing it's supposed to do
2. **Error states** — what happens when things fail
3. **Edge cases** — empty input, max values, null, boundary conditions
4. **Integration points** — does it call a DB, API, or external service? Mock those.
5. **Regression cases** — bugs that were fixed before but might come back

For each scenario, write:
- **Test name:** `test_{function}_{scenario}`
- **Input:** [what goes in]
- **Expected:** [what should come out or happen]

Show me the plan. WAIT for my approval.

## STEP 4 — Write the Tests (After Approval)

- Follow the EXACT testing patterns used in the existing tests you found. Same imports, same setup, same assertion style.
- Use the project's test utilities, fixtures, factories, or mocks — don't invent new ones.
- Name tests following AGENTS.md conventions.
- Test one thing per test function.
- Use descriptive test names that explain the scenario.

## STEP 5 — Run and Verify

- Run the specific tests you wrote: `{test command from AGENTS.md} {test file}`
- Run the full suite to make sure nothing broke: `{test command from AGENTS.md}`
- If tests fail: fix the tests (not the production code). If the production code has a BUG that the test found, STOP and tell me. Don't fix the bug in this task unless I ask.

## STEP 6 — Report

```
## Test Coverage Added
- File: [path]
- Tests written: [N]
- Scenarios covered: [list]
- Previous coverage: [estimate]
- New coverage: [estimate]
- Full suite: [passed/failed — N tests ran]
```

REMEMBER: Write tests, don't change production code. Follow existing patterns. If the code is untestable, flag it — don't hack around it.
```
