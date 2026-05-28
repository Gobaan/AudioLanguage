---
name: commit
description: Use when the user types /commit or asks for a quick git commit workflow. Performs a concise pre-commit check, avoids obvious local junk, stages intended changes, commits with a clear message, and reports the hash.
---

# Commit

Use this skill for `/commit`, `commit this`, or similar requests where the user wants a fast safe check-in.

## Workflow

1. Run `git status --short`.
2. Inspect changes with `git diff --stat` and, when useful, focused `git diff` for changed source files.
3. Keep known local scratch files out of the commit unless the user explicitly asks. For this repo, do not stage `analysis.txt`.
4. Search changed/staged text for obvious secrets before committing:

```powershell
rg -n --hidden -S "(api[_-]?key|secret|token|password|passwd|pwd|bearer|BEGIN .*PRIVATE KEY|postgres(ql)?://|mysql://|mongodb://|redis://|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)" <changed paths>
```

5. Run the smallest relevant verification that is already known for the changed area. If nothing is obvious, skip tests and say so.
6. Stage only files that belong to the requested change.
7. Commit with a concise imperative message. If the user provides text after `/commit`, prefer it as the commit message unless it is too vague.
8. Report the commit hash, what was left untracked, and the verification result.

## Blockers

Do not commit if a likely secret, credential, private key, local environment file, or unrelated destructive change is found. Report the file and risk without repeating secret values.

Do not run destructive git commands such as `git reset --hard` or `git checkout --` unless explicitly requested.
