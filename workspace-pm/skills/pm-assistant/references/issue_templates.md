# Issue Template Examples

## Good Feature Request Example

**Title:** feat: Add dark mode support for dashboard

## Summary
Add a dark/light mode toggle to the dashboard that persists across sessions.

## Motivation
Users working at night report eye strain. Dark mode is the #1 feature request
(23 requests in the last month from feedback channel).

## Requirements
- [ ] Dark/light toggle button in top navigation
- [ ] Dark palette following WCAG AA contrast ratios
- [ ] Persist preference in localStorage
- [ ] Respect OS-level dark mode as default
- [ ] All components render correctly in both modes

## Technical Notes
- React + Tailwind CSS, `dark:` variant configured but unused
- Color tokens: `src/styles/tokens.ts`
- Key components: Dashboard, Sidebar, DataTable, Charts

## Acceptance Criteria
- [ ] Toggle works instantly (no page reload)
- [ ] Preference survives browser restart
- [ ] All text meets 4.5:1 contrast ratio
- [ ] Charts readable in both modes

## Out of Scope
- Custom theme colors beyond light/dark
- Marketing site dark mode (separate repo)

## Claude Code Implementation Prompt
```
Read issue #42 in myorg/myapp.
Branch: feat/dark-mode
Key files: src/styles/tokens.ts, src/components/Dashboard/, tailwind.config.ts
Use Tailwind dark: variant. Persist in localStorage. Test all components.
```

---

## Good Bug Report Example

**Title:** fix: Silent failure when session expires during form submission

## Summary
Form submission fails silently when session token expires mid-fill.
No error, no redirect — spinner appears briefly then disappears.

## Steps to Reproduce
1. Log in
2. Open "Create Project" form
3. Wait 30+ min (session timeout)
4. Fill form, click "Create"
5. Observe: spinner → nothing. No project created.

## Expected: Error message + redirect to login
## Actual: Silent failure

## Technical Notes
- Auth middleware returns 401 but axios interceptor swallows it
- Files: `src/api/interceptors.ts`, `src/hooks/useAuth.ts`

## Acceptance Criteria
- [ ] Expired session shows visible error notification
- [ ] User redirected to login after acknowledgment
- [ ] Form data preserved in sessionStorage for recovery

## Out of Scope
- Changing session timeout duration
- Token refresh mechanism (separate issue)

---

## Anti-Patterns (BAD Issues)

**BAD — Too vague:**
> Title: Fix login
> Body: Login broken, please fix.

**BAD — Too broad:**
> Title: Redesign the entire frontend

**BAD — No acceptance criteria:**
> Title: Add search
> Body: We need search. Add it.
