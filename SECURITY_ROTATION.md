# Security Rotation Guide

## URGENT: credentials.json was committed to git history

`credentials.json` (Google OAuth client secret) was included in commits up to and
including `cfae166`. The secret `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` is now
**compromised** and must be rotated **before** doing anything else.

---

## Step 1 — Rotate the Google OAuth client secret (do this first)

1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Find the OAuth 2.0 Client: **manhwa-engine** (`48189806448-biqa9g6v2mn2d8pkanuq7v97ffka1v45`)
3. Click **Edit** → **Reset secret** (or delete and recreate the OAuth client)
4. Download the new `credentials.json` and place it in the project root
5. Delete the existing `token.pickle` and `youtube_token.pickle` (they are bound to the old secret):
   ```bash
   rm token.pickle youtube_token.pickle
   ```
6. On next run, you will be prompted to re-authenticate via browser

## Step 2 — Purge the secret from git history

> ⚠️ This rewrites history. Coordinate with anyone else using this repo.
> Force-push ONLY after everyone has been notified.

### Install git-filter-repo (one-time):
```bash
pip install git-filter-repo
```

### Remove the tracked files from ALL history:
```bash
git filter-repo --path credentials.json --invert-paths --force
git filter-repo --path youtube_credentials.json --invert-paths --force
```

### Verify they are gone:
```bash
git log --all --full-history -- credentials.json
# Should show no output
```

### Force-push all branches:
```bash
git push origin --force --all
git push origin --force --tags
```

### Tell all collaborators to re-clone:
```bash
# Everyone with a local clone must:
git clone <repo-url>   # fresh clone
# OR
git fetch --all
git reset --hard origin/main
```

---

## Where to store secrets

| File | Location |
|---|---|
| `credentials.json` | Project root (git-ignored). Never commit. |
| `service_account.json` | Project root (git-ignored). Never commit. |
| `token.pickle` | Project root (git-ignored). Auto-generated on first OAuth run. |
| `*.cookies.txt` | Project root (git-ignored). Export from browser manually. |
| `.env` | Project root (git-ignored). Copy from `.env.example`. |

All of the above are covered by `.gitignore`. Run `./secure.sh` after any fresh
checkout to set restrictive file permissions (`chmod 600`).

---

## What NOT to do

- Never run `git add .` without checking `git status` first
- Never use `--no-verify` to skip pre-commit hooks
- Never commit any file matching: `*.json` without checking its contents first
- Do not share this project directory via Dropbox/iCloud sync without encrypting credentials

---

## Verifying nothing sensitive is staged

```bash
# Before every commit, run:
git diff --cached --name-only
# Then manually inspect any .json, .pickle, or .txt files listed
```

---

## Gemini API key (.env)

The `.env` file contains `GEMINI_API_KEY`. It is git-ignored and was NOT committed.
However, if you suspect it was exposed (e.g., via screen share), rotate it at:
[Google AI Studio → API Keys](https://aistudio.google.com/app/apikey)
