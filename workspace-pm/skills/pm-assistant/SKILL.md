---
name: pm-assistant
description: "GitHub Issue creator and Claude Code prompt generator for software projects. Use when the user wants to: (1) create a GitHub issue or ticket, (2) write a feature request or bug report, (3) break down an idea into tasks, (4) generate Claude Code implementation prompts, (5) list or check status of existing issues. Triggers: 'tạo ticket', 'viết issue', 'create issue', 'feature request', 'bug report', 'tạo task', 'implement this', 'break this down', 'list issues'."
metadata:
  openclaw:
    requires:
      bins:
        - gh
    emoji: "📋"
---

# PM Assistant — GitHub Issue & Claude Code Prompt Skill

## Core Workflow

### Step 1: Understand the Request
Parse the user's idea. Identify:
- Type: feature | bug | improvement | refactor | documentation
- Scope: Is this one issue or should it be broken down?
- Repo: Which repository? If not specified, ask or use the remembered default.

### Step 2: Clarify (if needed)
If the idea is too vague, ask **max 2-3 questions**. Examples:
- "Repo nào?" (if not specified and no default remembered)
- "User nào sẽ dùng tính năng này?" (for features)
- "Có thể reproduce lỗi không? Steps?" (for bugs)

Do NOT over-ask. If you have enough info, proceed to draft.

### Step 3: Draft the Issue
Write the issue body following this exact structure:

```
## Summary
[1-2 sentences: what needs to be built or fixed]

## Motivation
[Why this matters. What problem it solves. Who benefits.]

## Requirements
- [ ] [Specific, testable requirement 1]
- [ ] [Specific, testable requirement 2]
- [ ] [Specific, testable requirement 3]

## Technical Notes
[Affected files, modules, APIs, constraints. Skip if unknown.]

## Acceptance Criteria
- [ ] [AC1: verifiable condition that must be true when done]
- [ ] [AC2: verifiable condition]

## Out of Scope
[What this issue explicitly does NOT cover]

## Claude Code Implementation Prompt
\`\`\`
[Ready-to-paste prompt for Claude Code — see template below]
\`\`\`
```

### Step 4: Get Approval
Show the full draft to the user. Ask:
"Draft đã sẵn sàng. Tạo issue luôn hay cần chỉnh sửa gì không?"

### Step 5: Create the Issue
Only after explicit approval:

```bash
# Write body to temp file (handles special characters safely)
cat > /tmp/issue-body.md << 'ISSUE_EOF'
[full issue body here]
ISSUE_EOF

# Create the issue
gh issue create \
  --repo "OWNER/REPO" \
  --title "[type]: Brief descriptive title" \
  --body-file /tmp/issue-body.md \
  --label "enhancement"

# Clean up
rm /tmp/issue-body.md
```

### Step 6: Send Claude Code Prompt
After issue creation, send the user a separate message with just the Claude Code prompt, easy to copy-paste:

## Claude Code Prompt Template

```
Read GitHub issue #[NUMBER] in [OWNER/REPO].

Implement all requirements from the issue. Guidelines:
- Branch: [type]/[short-kebab-description]
- Write clean, documented code with tests
- Follow existing code style and patterns
- Conventional commits (feat:, fix:, docs:, refactor:)
- Create draft PR linking to issue #[NUMBER]

Context: [paste Technical Notes if any]
```

## Label Mapping
| Request Type | Labels | Title Prefix |
|-------------|--------|--------------|
| New feature | `enhancement` | `feat:` |
| Bug fix | `bug` | `fix:` |
| Improvement | `enhancement` | `improve:` |
| Refactor | `refactor` | `refactor:` |
| Documentation | `documentation` | `docs:` |

## Handling Large Ideas
When the user's idea is too big for one issue:
1. Acknowledge: "Ý tưởng này khá lớn, nên break thành nhiều issues nhỏ."
2. Propose breakdown: List 3-5 sub-issues with titles
3. Ask user to confirm the breakdown
4. Create each sub-issue one by one (ask approval for each)
5. Optionally create a parent "epic" issue linking to all sub-issues

## Listing / Checking Issues
When user asks about existing issues:
```bash
# List open issues
gh issue list --repo OWNER/REPO --state open --limit 20

# View specific issue
gh issue view NUMBER --repo OWNER/REPO

# Search issues
gh issue list --repo OWNER/REPO --search "keyword"
```

## Additional Resources
- See `references/issue-templates.md` for detailed examples of good issues
```

