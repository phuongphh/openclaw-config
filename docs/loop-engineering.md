# Fleet configuration development

This repository is a versioned snapshot, not authority to overwrite the active
Gateway. PM manages requirements and PRs through the shared private
`phuongphh/fleet-engineering` platform. The local DevOps agent owns Dev and
Production activation on the owner's Mac; coding workers stop at a PR.

Shared operations: https://github.com/phuongphh/fleet-engineering/blob/main/docs/OPERATIONS-VI.md
Project profile: https://github.com/phuongphh/fleet-engineering/blob/main/projects/openclaw-config.json

## CI scope

The `config` CI job checks JSON syntax, agent/binding/cron references and
common credential-shaped values, including regression cases for invalid
configurations. It does not certify complete OpenClaw schema/plugin
compatibility or live operation. CI passing is not Dev acceptance or
Production approval.

## Required before DevOps activates any change

1. **Scope and version confirmation** – verify the PR head matches the reviewed
   scope and that the `projects/openclaw-config.json` profile version is
   current (see the shared operations guide in `phuongphh/fleet-engineering`).
2. **Isolated compatibility check** – validate OpenClaw schema and plugin
   behavior in an isolated environment, separate from the offline CI JSON
   checks. Document the outcome.
3. **Recovery path** – include a verified rollback procedure in the version-bound
   activation plan presented for the owner’s approval.

Profile policy (CI, environment, protected-path restrictions) is defined in
`projects/openclaw-config.json`; `dev_paths` describes deployment impact, not
coding write scope. Task write and context paths come from the approved
prepared task, not the profile. Multi-task queue and Pro transport limitations
remain in effect.

## Project acceptance checklist

PM reports the following evidence; one clear owner next action follows each item:

- [ ] `config` CI job passes on the exact PR head commit
- [ ] Independent maintainer text review of the PR diff is complete
- [ ] OpenClaw schema and plugin compatibility confirmed in isolated environment
- [ ] Scope, version, and profile reviewed against `projects/openclaw-config.json`
- [ ] Recovery path documented and owner-acknowledged

**Owner next action:** PM coordinates with DevOps and proactively requests the
required approval. The owner reviews and merges the coding PR; DevOps must not
merge automatically. A passing or merged PR does not authorize Gateway restart,
live ingest, real user publication, or production-data changes.

Do not commit credentials or host runtime state. Never apply an old snapshot
wholesale to the live fleet. Claude is the shared default; explicit owner
choices govern Codex per task or future defaults.
