# Fleet configuration development

This repository is a versioned snapshot, not authority to overwrite the active
Gateway. PM manages requirements and PRs through the shared private
`phuongphh/fleet-engineering` platform. The local DevOps agent owns Dev and
Production activation on the owner's Mac; coding workers stop at a PR.

Configuration CI checks tracked JSON syntax, agent/binding/cron references and
common credential-shaped values, with regression cases for invalid configurations.
It does not certify complete OpenClaw schema compatibility or plugin behavior.
An isolated runtime compatibility check and a recovery path are mandatory before
activating changes. Never apply an old snapshot wholesale to the live fleet.

Do not commit credentials or host runtime state. Keep the reviewed project policy
in the shared registry; product-specific validation stays in this repository.
Claude is the shared default, with explicit owner choices for Codex per task or
for future defaults. Merge does not authorize a Gateway restart or deployment.
