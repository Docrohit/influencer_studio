# Prompt 12: Performance Debug — Find and Fix Bottlenecks

**Who uses this:** Junior devs, when an endpoint, page, or query is slow and needs investigation.

**What it does:** Profiles the slow code, identifies the bottleneck, proposes a fix, verifies the improvement.

**Copy-paste into your AI tool:**

```
Something is slow. Help me find and fix it.

Slow thing: [API endpoint URL / page route / database query / background job]
How slow: [takes 5 seconds / times out / users complaining]
When: [always / under load / with specific data / started after deploy on {date}]

This is a PERFORMANCE task. DO NOT change behavior. DO NOT refactor unrelated code. Make it faster without breaking anything.

---

## STEP 1 — Measure Baseline

Establish the current performance:

- How do I reproduce the slowness? (Specific request, data set, user action)
- What's the current time? (Measure it — use browser devtools, curl with `-w "@curl-format.txt"`, or server timing headers)
- If it's a DB query: get the EXPLAIN plan. `EXPLAIN ANALYZE SELECT ...`

## STEP 2 — Profile and Find the Bottleneck

Trace the code path (read AGENTS.md Layer Map first). For each step, identify:

```
Step: [file:line — what happens]
Time: [estimate or actual ms]
Calls: [how many DB queries? how many external API calls?]
Problem? [Yes/No — what's suspicious]
```

Check for common performance killers:

- **N+1 queries:** Looping over results and making a DB query per item. Use `select_related`/`prefetch_related`/`includes`/eager loading.
- **Missing indexes:** Check EXPLAIN output for sequential scans. Does the query use indexes?
- **Unindexed foreign keys:** Every ForeignKey should have an index (Django auto-creates; raw SQL may not).
- **Loading too much data:** `SELECT *` when only 3 columns needed. Pagination missing.
- **Synchronous external calls:** Waiting for external API in request thread. Should be async/background.
- **N+1 API calls:** Calling an API inside a loop.
- **Large serialization:** Serializing huge nested objects. Use sparse fields / pagination.
- **No caching:** Repeated expensive computation. Can Redis/Memcached help?
- **Inefficient algorithm:** O(n²) when O(n log n) is possible. Sorting in a loop.
- **Blocking I/O:** File reads, large payloads in request thread.

## STEP 3 — Propose Fix (Top 1-2 Changes That Matter Most)

Prioritize the fix with the biggest impact, lowest risk. Show me:

```
## Performance Fix Plan

### Root cause: [1 sentence — what's making it slow]
### Fix: [what to change — be specific: file, line, change]
### Before: [N] ms / [N] queries
### Expected after: [N] ms / [N] queries
### Risk: [Low/Medium/High — why]
### Test needed: [what to test to verify correctness]
```

WAIT FOR MY APPROVAL.

## STEP 4 — Implement Fix (After Approval)

- Make the change. Keep it minimal.
- Add the test you proposed.
- Run existing tests to verify nothing broke.

## STEP 5 — Measure Again

- Reproduce the same scenario. Compare before and after.
- Show me the improvement:

```
## Performance Result
- Metric: [response time / query count / memory]
- Before: [N]
- After: [N]
- Improvement: [X% faster / Y fewer queries]
- Trade-off: [e.g., "uses 50MB more cache", "adds an index that slows writes by 2%"]
- All tests: [passing / N tests]
```

REMEMBER: Measure before and after. Fix the biggest bottleneck first. Don't micro-optimize. Don't change behavior. Document the trade-off.
```
