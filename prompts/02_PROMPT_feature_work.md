# Prompt 2: Feature Work — Architecture-First Development

**Who uses this:** Junior devs, when building a new feature or making any non-trivial change.

**What it does:** Forces the AI to plan architecturally before coding. Prevents "just make it work" thinking. The approval gate stops runaway changes.

**Copy-paste into your AI tool:**

```
I need to build: [DESCRIBE THE FEATURE HERE — be specific] (ask me if left empty.)

This is a feature task. Follow these steps IN ORDER. Do not skip.

---

## STEP 1 — Architecture Fit (Analyze First)

Answer these questions:

- Which layer(s) does this feature touch? Refer to the Layer Map in AGENTS.md.
- Find 2+ features in our codebase that are SIMILAR to this one. List the files they touch. Explain the pattern they follow.
- Does this feature align with product_theory.md's future plans? If it conflicts with upcoming changes, warn me.

## STEP 2 — Impact Analysis

- List every file you think you will CREATE or MODIFY.
- For EACH file, explain WHY (the architectural reason, not just "it works").
- What tests, types, migrations, or docs will need updating?

## STEP 3 — Propose (Do Not Code Yet)

Show me your plan in this format:

```
## Plan: [Feature Name]

### Files to create:
- path/to/file.py — [what + why]

### Files to modify:
- path/to/file.py — [what + why]

### Pattern I'm following:
[Link to or describe existing similar feature]

### Risks:
- [thing that could go wrong]
- [thing that could break]

### Are you sure this is the right layer?
[Yes/No, with reasoning]
```

WAIT FOR MY APPROVAL. Say "ready for your go-ahead" and stop.

---

## STEP 4 — Implement (Only After I Approve)

- Follow the existing patterns exactly. Do not invent new ones.
- No new libraries. No new abstractions. No "while you're at it" refactors.
- Write tests alongside the code.

## STEP 5 — Verify

- Run the full test suite: follow the command in AGENTS.md.
- Fix any failures before declaring "done."
- Run the linter/formatter if one exists.
- Create the session .md file documenting what was done and why.

REMEMBER: explain before you edit. Wait for my approval. Never change server directly.
```
