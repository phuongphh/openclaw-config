# OpenClaw — minimal configuration deployment

The `openclaw-config` repo is a historical snapshot, not authority to replace the live `~/.openclaw` tree. Never copy its `openclaw.json`, credentials, devices, sessions, auth profiles, identities or cron database wholesale into the running Gateway. The platform excludes snapshot openclaw.json from deploy artifacts and protects it from ordinary coding workers.

## Isolated Dev

`python ops/fleet/verify_dev.py --openclaw <installed-cli>` creates a temporary state/config, validates it with the installed OpenClaw schema, then removes it. It has loopback port 28789, a fresh workspace, no channels/providers and plugins disabled. It does not start a Gateway or restart the live service. Success reports schema/isolation only; channels/user_path remain unverified.

Register a persistent, separate Dev state/workspace/port before testing runtime changes. Review a minimal patch against current live settings with secrets redacted. The patch must enumerate allowed config keys and specific agent/workspace/skill files; unchanged live values stay in place. Credentials/channels/account permissions/tool privileges/cron settings cannot be adopted from a snapshot or expanded implicitly. A real test channel requires separately approved credentials and cannot compete with Production polling/webhooks.

## Production activation

After Dev validation and separate version/patch approval, record the live config fingerprint and exact installed OpenClaw version. Back up current config + selected agent files privately. Apply only the approved patch/managed files while preserving current accounts, sessions, bindings, auth and enabled jobs. Run current-version config validation before any restart. If a restart is required, restart only the registered Gateway service, verify readiness, agent bindings/exec restrictions, intended channel routes and the actual user command/reply. Schema or HTTP health alone is not a successful deployment.

On failure restore the exact pre-change config/files after drift checks, validate, and restart/recheck only if required. Preserve sessions/auth/cron history; do not reinstall/upgrade OpenClaw as a side effect of deploying a fleet config change. Keep capability flags off until isolated runtime + channel/user-path evidence is recorded.

## Delivery contract

PM owns requirements/issues and PO communication; the coding worker proposes code and stops at a PR. The PO merges. DevOps operates deployments only after a separate version-bound approval. A merge, passing CI, generated plan or health-only check is not deployment or owner acceptance.

The shared controller stages reviewed code from Git objects by full SHA, with a manifest digest; it never pulls/reset the live checkout. Host paths, service identifiers, baseline observations and credentials stay in private host bindings outside Git. `ops/fleet/**` is a maintenance path: normal coding workers cannot modify this adapter to grant themselves execution.

Before activation, DevOps must record the observed runtime files, review uncommitted/local changes, verify candidate CI, obtain exact scope/version/environment approval, establish quiescence and create a recoverable backup. Apply selected code only, restart only registered affected services, check the exact running version and all project readiness checks, then persist a deployment receipt. PM can invite PO acceptance only after those checks pass. Preserve unknown/failed states and never replay a deployment intent blindly.

Code rollback uses the private file journal and verifies no newer owner edits would be overwritten. Database rollback is a separate data decision: never restore an older DB after new writes without reconciliation. Keep deployment history, signing keys, approval references and recovery evidence.

## Running a separate Dev Gateway

`dev_gateway.py prepare --root <new-private-root> --candidate <SHA-pinned-artifact> [--brain-workspace <synthetic-SecondBrain-workspace>]` creates a fresh state/config/HOME. It does not read the live config, accounts, sessions or scheduler. Validate the new config, then run `provider` and `gateway` with that same root using separate service identities. The Dev Control UI is on `http://127.0.0.1:28789`; provider port 28790 is loopback only. Access uses a newly generated private Dev token stored in the new config, never the Production token.

This runtime uses a deterministic local fixture provider. It requests a real `read` tool call and derives the answer from the returned file content. A unique generated marker proves the round trip. It is a transport/filesystem-policy test, **not a real-model quality evaluation**. No paid model, Telegram account, channel delivery or Production agent-to-agent delegation is involved. Ốp Dev remains the Telegram operations contact; there is no extra Telegram bot to create.

Only read is allowed, filesystem access is workspace-scoped, exec/write/edit/elevation/network messaging tools are disabled, plugins and channels are empty. Test the normal read and an outside-workspace read denial through the actual Gateway. Health/schema validation alone does not establish readiness. The synthetic `brain-dev` agent can share this separate Gateway; its workspace and heartbeat remain separate from the live curator.

On update, preserve private Dev config/state and credentials, stage the exact approved SHA into a new candidate directory, stop only the registered Dev processes, update the allowlisted candidate/workspace links, restart only those Dev processes and verify fresh user-path and policy results. Do not restore the tracked `openclaw.json` snapshot over any live config. Production keeps the separate `gateway-patch` procedure and requires its own approval.

Operational limitation: this first Dev runtime previews staged agent instructions as candidate files and verifies read-only transport. It does not execute arbitrary candidate instructions or validate real-model behavior, external channels or Production scheduling. Changes requiring those paths need an additional scoped test before acceptance.
