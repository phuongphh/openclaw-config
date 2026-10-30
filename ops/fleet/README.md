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
