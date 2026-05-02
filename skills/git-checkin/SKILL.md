---
name: git-checkin
description: Pre-commit and check-in review for Git repositories with emphasis on preventing leaked secrets, API keys, credentials, tokens, private certificates, environment files, and accidental sensitive data. Use when Codex is asked to review changes before committing, prepare a commit, inspect a diff for security issues, or verify that code and config are safe to check in.
---

# Git Check-In

## Core Rule

Treat secret leaks as blockers. Do not commit, summarize, or reproduce secret values. Report only the file, line, key name or token type, and the remediation needed.

Review the actual Git state before giving advice. Prefer checking staged changes first, then unstaged changes, then suspicious untracked files.

## Workflow

1. Run `git status --short` to understand staged, unstaged, and untracked files.
2. Inspect staged changes with `git diff --cached --stat` and `git diff --cached`.
3. Inspect unstaged changes with `git diff --stat` and `git diff`.
4. Inspect untracked text files that look commit-worthy or risky.
5. Search for secret patterns across changed files and obvious config files.
6. Check whether generated artifacts, logs, binaries, local recordings, caches, or environment files should be ignored.
7. Report blockers first, then warnings, then clean findings.
8. If making a commit, proceed only after blockers are resolved or the user explicitly accepts non-secret residual risks.

## Secret Patterns

Search changed files for likely secrets and credentials:

- API keys: `api_key`, `apikey`, `api-key`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- Tokens: `token`, `access_token`, `refresh_token`, `bearer`, `jwt`, `session`
- Passwords: `password`, `passwd`, `pwd`, `secret`
- Cloud credentials: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AZURE_CLIENT_SECRET`, `GOOGLE_APPLICATION_CREDENTIALS`
- Private keys: `BEGIN PRIVATE KEY`, `BEGIN RSA PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`
- Certificates and key files: `.pem`, `.key`, `.p12`, `.pfx`, `.crt`
- Database URLs: `postgres://`, `postgresql://`, `mysql://`, `mongodb://`, `redis://`
- Webhooks: Slack, Discord, GitHub, Stripe, Twilio, SendGrid, Firebase, Supabase, Vercel, Netlify URLs or tokens
- Encoded blobs: long base64-like values assigned to suspicious names
- Local paths that reveal private user or machine info when not needed

Use `rg` first. Useful searches:

```powershell
rg -n --hidden -S "(api[_-]?key|secret|token|password|passwd|pwd|bearer|BEGIN .*PRIVATE KEY|postgres(ql)?://|mysql://|mongodb://|redis://|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)" .
```

For staged-only review, prefer inspecting `git diff --cached` and searching the diff text. If a command emits a suspected secret, do not paste the value back to the user.

## Files That Need Extra Suspicion

Treat these as risky unless clearly sanitized:

- `.env`, `.env.*`, `.flaskenv`, `.npmrc`, `.pypirc`
- `config.*`, `settings.*`, `secrets.*`, `credentials.*`
- service account JSON files
- exported Postman or Insomnia collections
- deployment files with inline env vars
- logs, traces, crash dumps, request/response captures
- notebooks with outputs
- generated audio/video/images containing private user data
- local database files, SQLite files, backups, dumps
- SSH keys, certificates, keystores

If such files are untracked, recommend adding them to `.gitignore` unless they are intended sanitized templates.

## Safe Examples

Do not flag obvious placeholders as blockers:

- `YOUR_API_KEY_HERE`
- `example-token`
- `changeme`
- `sk-...`
- `<API_KEY>`
- `${OPENAI_API_KEY}`
- `process.env.OPENAI_API_KEY`
- documented variable names without values

Still warn if placeholders appear in production config where runtime resolution is unclear.

## Remediation

When a secret is found:

1. Stop the check-in.
2. Tell the user the file and line or diff hunk without revealing the secret.
3. Recommend moving the value to an environment variable, local secret store, or deployment secret manager.
4. Add or update `.gitignore` for local secret files.
5. Replace committed examples with `.env.example` or documented placeholder values.
6. If the secret may already be committed in history, tell the user to rotate it and remove it from history with an appropriate secret-cleaning process.

Do not run destructive Git history rewrite commands unless the user explicitly asks.

## Beyond Secrets

Also check for accidental check-in issues:

- Debug-only code, temporary bypasses, or hardcoded test accounts
- Broad CORS settings or disabled auth in non-local code
- Excessive logging of credentials, prompts, user content, tokens, or headers
- Client-side exposure of server-only keys
- Large generated files that should be storage artifacts, not source
- Platform-specific absolute paths
- Dependency lock or requirements changes that look unrelated
- Missing `.gitignore` entries for new local artifacts

## Reporting Format

Lead with findings:

- **Blocker**: likely secret, private key, credential, or sensitive data leak.
- **Warning**: risky pattern that may be safe but needs confirmation.
- **Clean**: no obvious secret leaks found in reviewed scope.

For each finding, include:

- File and line if available
- What kind of secret or risk it appears to be
- Why it matters
- Exact remediation

End with reviewed scope:

- staged changes reviewed
- unstaged changes reviewed
- untracked files reviewed
- repo-wide search performed or skipped
- any limits, such as binary files not inspected

## Commit Guidance

Only help create the commit after blockers are resolved. If no blockers remain, summarize the intended commit contents and use a concise commit message.

Never include secret values in commit messages, PR descriptions, summaries, or final responses.
