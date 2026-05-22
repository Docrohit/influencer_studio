# Prompt 3: Bug Investigation — Root Cause, Not Symptom

**Who uses this:** Junior devs, when given a bug report from QA/ops/testing teams.

**What it does:** Separates investigation from fixing. Forces a trace through the code. Prevents the "just suppress the error" reflex.

**Before using this:** Make sure the bug is reported in your `bug_report_format.md` format.

**Copy-paste into your AI tool:**

```
A bug has been reported. Here is the bug data in our standard bug report format:

[PASTE THE BUG REPORT DATA HERE — from your sheets, DB, or the filled template]

---

## STEP 1 — Understand the Bug

**FIRST — Read the company's bug report format:**
- Search the project for the bug report format file. It could be named: `bug_report_format.md`, `BUG_REPORT_TEMPLATE.md`, `OPS_BUG_REPORT_FORMAT.md`, `bug reporting format for reported bugs .md`, or similar.
- Read it. Understand every header/field/column. This tells you what each piece of bug data means.
- If NO format file exists, tell me: "I can't find a bug report format in this project. Can you share it or describe what fields your team uses?"

**Then** explain the bug back to me:
- What is happening?
- What SHOULD be happening?
- Where in the system is this occurring (which module, which layer)?
- What environment? (dev / qa / prod — the bug report should say)

## STEP 2 — Trace the Code Path

Starting from the entry point (route / API call / component), trace the FULL code path to the failure point.

List every file in the chain. For each file:
- What does it do in this flow?
- Is there a test covering this path?

Format:
```
Route: /api/users/{id}
  → users/urls.py:10 → UserViewSet.get()
  → users/views.py:45 → calls UserService.get_user()
  → users/services.py:23 → calls UserRepository.find_by_id()
  → users/repositories.py:12 → SELECT * FROM users WHERE id = ?
  → FAILS HERE because __________
```

If you need server logs to continue, use commands from server_info.md to SSH in and review logs. NEVER edit the server. NEVER run write commands on the server.

## STEP 3 — Root Cause Analysis

Answer these:

1. What is the ACTUAL root cause? (Not "the error says X" — WHY did X happen?)
2. Is this a one-off bug or could this same pattern exist elsewhere in the codebase? Search for similar code.
3. Could a test have caught this? If yes:
   - Why wasn't there a test?
   - What test should exist to prevent this in the future?

## STEP 4 — Fix Proposal (Do Not Code Yet)

- Which layer should the fix live in? Why? (Check the Layer Map in AGENTS.md)
- Is there an existing pattern in the codebase for this kind of fix?
- List the exact files and changes. Include the test you will write.

Show me:
```
## Fix Proposal: [Bug ID or short description]

### Root cause: [1 sentence]
### Fix in: [file path], [layer name]
### Changes needed:
- file1.py: [what + why]
- file2.py: [what + why]
### New/updated tests:
- test_file.py: [what it covers]
### Risk: [low / medium / high — and why]
```

WAIT FOR MY APPROVAL. Do not implement until I say "go ahead."

---

## STEP 5 — Implement Fix (After Approval)

- Make the fix following existing patterns.
- Write the test FIRST (TDD), see it fail, then apply the fix.
- Run the full test suite. Ensure nothing else broke.
- Create the session .md file documenting the bug, root cause, fix, and test added.

REMEMBER: explain before you edit. Wait for my approval. Never change server directly.
```
