# Git Init Kit

## One-command setup (PowerShell)
Run from repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\git_init_kit.ps1 -RemoteUrl "https://github.com/<owner>/<repo>.git"
```

This does:
- `git init` (if not already initialized)
- creates/switches to `main`
- stages and commits current files
- configures `origin` and pushes `main` (if `-RemoteUrl` is provided)
- creates/switches to `codex/compliance-engine`
- pushes feature branch (if `-RemoteUrl` is provided)

## Local-only bootstrap (without remote)
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\git_init_kit.ps1
```

## Manual fallback
```powershell
git init
git checkout -b main
git add .
git commit -m "chore: bootstrap sentinel compliance-as-code platform"
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
git checkout -b codex/compliance-engine
git push -u origin codex/compliance-engine
```

## Next step
Open a PR:
- base: `main`
- compare: `codex/compliance-engine`
