# Prompt 7: Deploy — Ship Changes Safely

**Who uses this:** Junior devs, when code is ready to push to dev-env / qa-env.

**What it does:** Runs through the deploy_rules.md checklist, verifies everything, deploys, verifies post-deploy, and documents.

**Copy-paste into your AI tool:**

```
I have changes ready to deploy. I want to deploy to: [dev-env / qa-env].

---

## STEP 1 — Pre-Deploy Verification

- Read deploy_rules.md and server_info.md. Confirm what environment I'm deploying to and what the process is.
- Run the full test suite: follow the command in AGENTS.md. Show me the results.
- Run linter/formatter if one exists in the project.
- Check: are there any uncommitted changes? `git status`
- Check: is my branch up to date with remote? `git fetch && git status`
- Check: do I need a DB migration? Are there unapplied migrations? List them.

## STEP 2 — Pre-Deploy Checklist

Answer these before we proceed:

```
□ Tests passing: [Yes/No — paste summary]
□ Build succeeds (if frontend): [Yes/No]
□ No uncommitted changes: [Yes/No]
□ Branch matches deploy target (see deploy_rules.md): [Yes/No]
□ No secrets in code: [Yes/No — verified]
□ DB migrations needed: [Yes/No — list them if yes]
□ Session .md file created for this work: [Yes/No]
□ I know the rollback procedure if this goes wrong: [Yes/No]
```

WAIT FOR MY APPROVAL. Do not deploy until I say "go ahead."

## STEP 3 — Deploy (After Approval)

Follow deploy_rules.md EXACTLY. The deploy process is:

1. {Step from deploy_rules.md}
2. {Step from deploy_rules.md}
3. {Step from deploy_rules.md}

For each step:
- Run the command.
- Show me the output.
- If anything fails, STOP. Tell me what failed.

If a deploy script exists (deploy_dev.sh etc.), use it.

## STEP 4 — Post-Deploy Verification

- Check services are running: run the health check commands from server_info.md.
- Check recent logs for errors: `journalctl -u {service} --since "2 min ago" | grep -i error`
- Run the health endpoint: `curl {health_url}` — should return 200.
- Run a smoke test: {1-2 key user flows to verify}.

## STEP 5 — Create Deploy Document

Create a deploy tracking entry (append to SCP_DEPLOY_TRACKING.md or similar if it exists, or note in the session .md file):

```
## Deploy: [date] [time]
- Environment: [env]
- Branch: [branch]
- What was deployed: [summary]
- Verification: [passed/failed]
- Deployed by: [name]
```

Tell me: "Deploy complete. Verified. Monitoring for [N] minutes."

REMEMBER: Never deploy to prod without lead approval. Never skip verification. Never make direct server changes.
```
