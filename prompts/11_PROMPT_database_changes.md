# Prompt 11: Database Changes — Models, Migrations, No Data Loss

**Who uses this:** Junior devs, when they need to add/modify a database model, create migrations, or run a data migration.

**What it does:** Ensures the model change is architecturally sound, migration is reversible and safe, and no data is lost.

**Copy-paste into your AI tool:**

```
I need to make a database change: [ADD COLUMN / NEW MODEL / MODIFY FIELD / DATA MIGRATION]

Describe what I want: [e.g., "Add a 'status' field to the Order model with values pending/processing/done/failed"]

---

## STEP 1 — Understand Current State

- Read AGENTS.md: how are models organized? Which app/folder? What naming conventions?
- Read product_theory.md: any DB-related decisions? (e.g., "no raw SQL in services", "use Django ORM only")
- Read the relevant models file. Show me the current schema.
- Check API_info.md (if it exists): will this change affect any existing API response?

## STEP 2 — Design Check (Before Writing Code)

Answer:

1. **Model Design:**
   - What fields? Types? Nullable? Default values?
   - Any relationships (ForeignKey, ManyToMany)? Index needed?
   - Does this duplicate data that exists elsewhere? If yes, why is denormalization justified?

2. **Layer Check (from AGENTS.md):**
   - Is this purely a DB change, or does business logic change too?
   - If business logic changes: should that be a SEPARATE task? (Because service layer changes need different testing.)

3. **Migration Safety:**
   - Will this lock the table? (Adding a column with default on a large table locks it.)
   - Is the migration REVERSIBLE? Can we rollback? Write the reverse migration.
   - If adding a NOT NULL column to an existing table: what's the default for existing rows?
   - If removing a column: is anything still reading it? Check ALL consumers.

4. **Data Migration (if applicable):**
   - If transforming existing data: write a data migration that runs in the migration file.
   - Can the data migration be paused/resumed? What happens if it fails halfway?
   - How many rows will be affected? Estimate time.

Show me the plan. Format:
```
## DB Change Plan
- Model: [model name]
- Change: [what]
- Migration operations: [add field / create table / alter column / data migration]
- Reversible: [Yes/No — if yes, show reverse operation]
- Affected rows: [estimate]
- Lock risk: [Low / Medium / High — explain]
- API impact: [which endpoints / none]
```

WAIT FOR MY APPROVAL.

## STEP 4 — Implement (After Approval)

- Write the model change. Follow naming conventions from AGENTS.md.
- Generate migration: `{migration command from AGENTS.md or deploy_rules.md}`.
- Review the auto-generated migration. Does it look right?
- If data migration needed: write it in the same migration file using `RunPython`.
- Add a test that verifies the new model/field works.

## STEP 5 — Test Locally

- Run the migration locally: `{migration command}`.
- Verify: can I create/update records with the new field?
- Reverse the migration: `{reverse migration command}`. Did it work cleanly?
- Re-apply the migration. Run tests.

## STEP 6 — Report

```
## DB Change Summary
- Model: [name]
- Migration file: [path]
- Fields added/changed: [list]
- Data migration: [Yes/No — what it does]
- Reversible: [Yes/No]
- Tests: [N passing]
- Production risk: [Low/Medium/High]
- Pre-deploy step needed: [backup prod DB / run on staging first / manual approval]
```

REMEMBER: Never run `migrate` on prod without backup + lead approval. Never write raw SQL that bypasses the ORM unless explicitly approved. Always write a reversible migration.
```
