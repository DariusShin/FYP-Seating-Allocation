param(
    [ValidateSet("plan", "plan-sweep", "check", "pilot", "run", "sweep", "report")]
    [string]$Mode = "plan",
    [Parameter(Mandatory = $true)]
    [string]$Out,
    [switch]$NoPlots
)

$ErrorActionPreference = "Stop"
$Repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.."))
$Python = Join-Path $Repo ".venv-study-b/Scripts/python.exe"
if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "Use this wrapper on native Windows 11. Non-Windows development uses the Python check --development command."
}
if (-not (Test-Path $Python)) {
    throw "Install the environment first: py -3.14 research/experiments/setup_production_benchmark.py"
}
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Push-Location $Repo
try {
    $RunArguments = @("research/experiments/production_solver_benchmark.py", $Mode, "--out", $Out)
    if ($NoPlots -and $Mode -notin @("plan", "plan-sweep")) { $RunArguments += "--no-plots" }
    & $Python @RunArguments
    if ($LASTEXITCODE -ne 0) { throw "Study B stopped with exit code $LASTEXITCODE; inspect the output manifest and logs." }
} finally {
    Pop-Location
}
