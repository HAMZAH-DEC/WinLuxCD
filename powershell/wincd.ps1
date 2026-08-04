#Requires -Version 5.1
<#
.SYNOPSIS
  Convert Windows (PowerShell) directory addresses to WSL cd commands (and back).

.DESCRIPTION
  wincd wraps `wsl wslpath` so you can convert a path between Windows and WSL
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
  .\wincd.ps1 'C:\Users\you\Documents'
  cd "/mnt/c/Users/you/Documents"

.EXAMPLE
  .\wincd.ps1 -Clipboard
  # converts whatever is on the clipboard

.EXAMPLE
  .\wincd.ps1 -Windows '/home/you'
  \\wsl.localhost\Ubuntu\home\you

.EXAMPLE
  .\wincd.ps1 -Raw 'D:\work\Project X'
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
  $out = & wsl wslpath $mode $InputPath 2>$null
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
