# Prompt 8: Understand Code — Walk Through a Module

**Who uses this:** Junior devs, when onboarding or trying to understand how an existing module/feature works end-to-end.

**What it does:** Forces the AI to trace the full code path, explain every file's role, and connect it to the architecture. No code changes allowed — understanding only.

**Copy-paste into your AI tool:**

```
I need to understand how this works: [MODULE / FEATURE / ENDPOINT / COMPONENT NAME]

This is an UNDERSTANDING task. DO NOT propose any code changes. DO NOT suggest improvements. I just need to learn what exists and WHY it is built this way.

---

## STEP 1 — Find the Entry Point

Read AGENTS.md to understand the layer architecture. Then find where this feature starts:

- Traced from: [route / URL / component / button click / cron job] 
- Entry file: [path]

## STEP 2 — Trace the Full Path (End to End)

Walk me through EVERY step from entry to completion. For each file:

```
File: path/to/file.py (or .tsx, .js, etc.)
Layer: [Controller / Service / Repository / Component / Hook — from AGENTS.md]
What it does: [1-2 sentences]
Input: [what comes in]
Output: [what goes out]
Calls: [next file in chain]
Why it's in this layer: [architectural reason from product_theory.md]
```

Draw the flow as a diagram:
```
[Entry] → [File A] → [File B] → [File C] → [DB/API] → [File D] → [Response/UI]
```

## STEP 3 — Key Decisions Along the Path

At each step where a design decision was made (e.g., "why cache here?", "why Celery task not direct call?"), explain:
- What was the alternative?
- Why was this approach chosen? (Reference product_theory.md if it explains it.)

## STEP 4 — Dependencies & Side Effects

- What external services does this flow depend on? (APIs, databases, caches, queues)
- What would break if any of these dependencies failed?
- Are there any background tasks triggered? (Celery, cron, webhooks)
- Are there any events/logs/metrics emitted?

## STEP 5 — Connected Code

Show me what else is connected to this flow:
- What OTHER features or modules call into this code?
- What tests exist for this flow? List the test files.
- What API endpoints touch this flow? (Check API_info.md if it exists.)

## STEP 6 — Summary

End with a plain-English summary (3-5 sentences) a new team member could read to understand this feature.

Format: "When a user does [X], the system [Y] by going through [Z]. The key decision was [W] because [reason]. The riskiest part is [V]."

REMEMBER: Understanding only. No edits. No "you should refactor this." Just help me learn.
```
