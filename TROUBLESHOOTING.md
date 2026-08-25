# Troubleshooting Log

A record of every real issue hit while setting up this pipeline on Windows,
and how each was diagnosed and fixed. Kept here because these are exactly
the kinds of problems you'll hit again on any real CI/CD setup — the fixes
are more useful documented than forgotten.

---

## 1. Actions tab showed "Get started with GitHub Actions" instead of a run

**Symptom:** After pushing, the Actions tab showed GitHub's default template
gallery instead of picking up `ci.yml`.

**Cause:** The `.github/workflows/ci.yml` file wasn't actually at that path —
files had been uploaded individually and landed flat in the repo root
instead of inside their folders. GitHub Actions *only* recognizes workflow
files at the exact path `.github/workflows/*.yml`; a `ci.yml` sitting at
the repo root is invisible to it.

**Fix:** Recreate the proper folder structure locally
(`app/`, `tests/`, `.github/workflows/`) and move each file into place
before committing, e.g. with `git mv`.

---

## 2. `mkdir -p app tests .github/workflows` failed in PowerShell

**Symptom:**

**Cause:** `mkdir -p` with multiple space-separated paths is bash syntax.
Windows PowerShell's `mkdir` (an alias for `New-Item`) doesn't parse
arguments the same way.

**Fix:** Use PowerShell syntax instead:
```powershell
New-Item -ItemType Directory -Path app, tests, .github\workflows -Force
```

---

## 3. `git remote add origin ...` failed with "remote origin already exists"

**Symptom:**

**Cause:** A remote named `origin` was already registered locally from an
earlier attempt, even after deleting and recreating the local project
folder — `git remote` state doesn't get cleared just by removing files.

**Fix:** Either update the existing remote's URL, or remove and re-add it:
```powershell
git remote set-url origin https://github.com/<user>/<repo>.git
# or
git remote remove origin
git remote add origin https://github.com/<user>/<repo>.git
```

---

## 4. `pyproject.toml: Invalid statement (at line 1, column 1)`

**Symptom:** The `test` job failed immediately with a TOML parse error,
even though the file looked completely normal when opened.

**Cause:** PowerShell's `Out-File -Encoding utf8` writes a **UTF-8 BOM**
(Byte Order Mark) — a few invisible bytes at the very start of the file
that signal "this is UTF-8" to some Windows programs. It's invisible on
screen, but pytest's TOML parser (which is strict) trips over those extra
bytes before `[build-system]` and treats the whole file as invalid.

**Diagnosis:** Read the file's raw first bytes and check for the BOM
signature (`EF BB BF`):
```powershell
$bytes = [System.IO.File]::ReadAllBytes("pyproject.toml")
"{0:X2} {1:X2} {2:X2}" -f $bytes[0], $bytes[1], $bytes[2]
```

**Fix:** Rewrite the file using .NET's UTF8Encoding with the BOM flag
explicitly set to `false`:
```powershell
$content = Get-Content pyproject.toml -Raw
[System.IO.File]::WriteAllText("$PWD\pyproject.toml", $content, [System.Text.UTF8Encoding]::new($false))
```

---

## 5. `ModuleNotFoundError: No module named 'app'`

**Symptom:** Tests passed locally (`python -m pytest`) but failed in CI
with this error on every Python version.

**Cause:** `python -m pytest` automatically adds the current directory to
Python's import path — but plain `pytest` (what the CI workflow ran) does
not. So `app/` was never actually importable in the CI environment, since
it was just a folder sitting next to `tests/`, not an installed package.

**Fix:** Install the project itself as an editable package before running
tests, so `app` becomes a real importable package regardless of working
directory:
```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -e .
```

---

## 6. Fix from #5 didn't work — same error persisted

**Symptom:** After adding `pip install -e .`, the exact same
`ModuleNotFoundError` still showed up in the next run.

**Cause:** The new install step was accidentally added *after* the
`Run tests with coverage` step instead of replacing the *existing*
"Install dependencies" step that ran *before* it. So the execution order
became: install (old, incomplete) -> run tests (still fails) -> install
(new, correct, but too late to matter).

**Diagnosis:** Reading the full `ci.yml` end-to-end (not just grepping for
one line) showed two separate `Install dependencies` steps, with the test
step sandwiched between them.

**Fix:** Delete the duplicate, keeping exactly one `Install dependencies`
step — with both install commands — positioned immediately before
`Run tests with coverage`:
```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -e .
- name: Run tests with coverage
  run: pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Key takeaway

Every one of these came down to the gap between **"works on my machine"**
and **"works in a clean environment"** — which is the entire reason CI/CD
exists. Local testing used `python -m pytest` (path bonus), an
already-correct local folder structure, and an editor that doesn't add a
BOM by default. CI has none of those unless you make them explicit.
