param(
  [Parameter(Mandatory=$false)][string]$RemoteUrl = "",
  [Parameter(Mandatory=$false)][string]$DefaultBranch = "main",
  [Parameter(Mandatory=$false)][string]$FeatureBranch = "codex/compliance-engine",
  [Parameter(Mandatory=$false)][string]$InitialCommitMessage = "chore: bootstrap sentinel compliance-as-code platform"
)

$ErrorActionPreference = "Stop"

function Run-Git {
  param([string[]]$Args)
  Write-Host "> git $($Args -join ' ')" -ForegroundColor Cyan
  git @Args
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "git is not installed or not in PATH."
}

$repoRoot = (Get-Location).Path
Write-Host "Repo path: $repoRoot" -ForegroundColor Green

# 1) Initialize repository if needed
$insideRepo = $false
try {
  $null = git rev-parse --is-inside-work-tree 2>$null
  if ($LASTEXITCODE -eq 0) { $insideRepo = $true }
} catch { $insideRepo = $false }

if (-not $insideRepo) {
  Run-Git @("init")
}

# 2) Ensure default branch exists
$currentBranch = ""
try {
  $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
} catch {
  $currentBranch = ""
}

if ($currentBranch -eq "HEAD" -or [string]::IsNullOrWhiteSpace($currentBranch)) {
  Run-Git @("checkout", "-b", $DefaultBranch)
} elseif ($currentBranch -ne $DefaultBranch) {
  # create/switch to default branch
  Run-Git @("checkout", "-B", $DefaultBranch)
}

# 3) Commit current workspace
Run-Git @("add", ".")
$hasChanges = $true
try {
  git diff --cached --quiet
  if ($LASTEXITCODE -eq 0) { $hasChanges = $false }
} catch { $hasChanges = $true }

if ($hasChanges) {
  Run-Git @("commit", "-m", $InitialCommitMessage)
} else {
  Write-Host "No staged changes to commit." -ForegroundColor Yellow
}

# 4) Configure remote if provided
if (-not [string]::IsNullOrWhiteSpace($RemoteUrl)) {
  $existingOrigin = ""
  try { $existingOrigin = (git remote get-url origin 2>$null).Trim() } catch { $existingOrigin = "" }

  if ([string]::IsNullOrWhiteSpace($existingOrigin)) {
    Run-Git @("remote", "add", "origin", $RemoteUrl)
  } elseif ($existingOrigin -ne $RemoteUrl) {
    Run-Git @("remote", "set-url", "origin", $RemoteUrl)
  }

  # push default branch
  Run-Git @("push", "-u", "origin", $DefaultBranch)
}

# 5) Create/switch feature branch
Run-Git @("checkout", "-B", $FeatureBranch)

if (-not [string]::IsNullOrWhiteSpace($RemoteUrl)) {
  Run-Git @("push", "-u", "origin", $FeatureBranch)
  Write-Host "`nNext: open a PR from '$FeatureBranch' into '$DefaultBranch'." -ForegroundColor Green
}

Write-Host "`nGit Init Kit completed." -ForegroundColor Green
