#Requires -Version 5.1
<#
.SYNOPSIS
  Convert Windows (PowerShell) directory addresses to WSL cd commands (and back).

.DESCRIPTION
  winluxcd wraps `wsl wslpath` so you can convert a path between Windows and WSL
  without pasting it into an AI chat or remembering the syntax.

.PARAMETER Path
  The path to convert.  If omitted (and -Clipboard is not used), the current
  clipboard contents are converted instead.

.PARAMETER Windows
  Reverse direction: convert a WSL path to a Windows path.

.PARAMETER Clipboard
  Read the input path from the Windows clipboard.

.PARAMETER Copy
  Write the result back to the Windows clipboard (and also print it).

.PARAMETER Raw
  Print just the converted path, without the "cd " prefix.

.EXAMPLE
  .\winluxcd.ps1 'C:\Users\you\Documents'
  cd "/mnt/c/Users/you/Documents"

.EXAMPLE
  .\winluxcd.ps1 -Clipboard
  # converts whatever is on the clipboard

.EXAMPLE
  .\winluxcd.ps1 -Windows '/home/you'
  \\wsl.localhost\Ubuntu\home\you

.EXAMPLE
  .\winluxcd.ps1 -Raw 'D:\work\Project X'
  /mnt/d/work/Project X
#>
[CmdletBinding()]
param(
  [string]$Path = '',
  [switch]$Windows,
  [switch]$Clipboard,
  [switch]$Copy,
  [switch]$Raw
)

$ErrorActionPreference = 'Stop'

function Convert-WinPath {
  param([string]$InputPath, [switch]$ToWindows)
  $mode = if ($ToWindows) { '-w' } else { '-u' }
  # wsl.exe drops backslashes from unquoted command-line args, so pass the
  # path with forward slashes instead (wslpath accepts both).
  $clean = $InputPath -replace '\\', '/'
  # UNC paths: wslpath cannot round-trip them, so convert natively.
  if ($clean -match '^//') {
    if ($ToWindows) { return $clean -replace '/', '\' }  # //server/share -> \\server\share
    return $clean                                        # \\server\share -> //server/share
  }
  # wsl.exe can fail to launch with "The filename or extension is too long"
  # when the process environment block is huge (typically a very long PATH).
  # Run it with a minimal environment and restore everything afterwards.
  $saved = @{}
  Get-ChildItem Env: | ForEach-Object { $saved[$_.Name] = $_.Value }
  try {
    $keep = @('PATH', 'SystemRoot', 'SystemDrive', 'TEMP', 'TMP', 'USERNAME',
              'USERPROFILE', 'COMPUTERNAME', 'HOMEDRIVE', 'HOMEPATH',
              'LOGONSERVER', 'SESSIONNAME', 'PROGRAMDATA', 'PROMPT')
    Get-ChildItem Env: | ForEach-Object {
      if ($keep -notcontains $_.Name) {
        Remove-Item "Env:\$($_.Name)" -ErrorAction SilentlyContinue
      }
    }
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    $out = & wsl.exe wslpath $mode $clean 2>$null
  } finally {
    foreach ($k in $saved.Keys) {
      [Environment]::SetEnvironmentVariable($k, $saved[$k])
    }
  }
  if ($LASTEXITCODE -ne 0) { throw "wslpath $mode failed for: $InputPath" }
  return ($out -join ' ').Trim()
}

# 1) pick the input ---------------------------------------------------------
$inputPath = $Path
if ($Clipboard -or [string]::IsNullOrWhiteSpace($inputPath)) {
  $inputPath = Get-Clipboard -Raw
  if ([string]::IsNullOrWhiteSpace($inputPath)) {
    throw 'No path given and the clipboard is empty.'
  }
}
$inputPath = $inputPath.Trim().Trim('"').Trim("'")

# 1b) guard: only convert things that look like paths. Feeding wsl.exe random
#     clipboard content (e.g. a copied shell command) produces confusing errors.
if ($inputPath -notmatch '^([a-zA-Z]:[\\/]|[\\/]{2}|/)') {
  $preview = $inputPath
  if ($preview.Length -gt 60) { $preview = $preview.Substring(0, 60) + '...' }
  throw ("Input does not look like a path: `"$preview`". Copy a Windows path " +
         '(C:\...), a UNC path (\\server\share), or a WSL path (/home/...) first.')
}

# 2) convert ----------------------------------------------------------------
$converted = if ($Windows) {
  Convert-WinPath -InputPath $inputPath -ToWindows
} else {
  Convert-WinPath -InputPath $inputPath
}

# 3) render + emit ----------------------------------------------------------
$text = if ($Raw) { $converted } else { 'cd "{0}"' -f $converted }
if ($Copy) { $text | Set-Clipboard }
$text
