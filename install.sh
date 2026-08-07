#!/usr/bin/env bash
# WinLuxCD installer / uninstaller.
#   ./install.sh [install|uninstall]   (default: install)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.1.0"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
ALIASES="$HOME/.bash_aliases"

info() { printf '\033[1;32m[WinLuxCD]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WinLuxCD]\033[0m %s\n' "$*" >&2; }

cmd="${1:-install}"
case "$cmd" in
  install|uninstall) ;;
  -h|--help|help) echo "usage: $0 [install|uninstall]"; exit 0 ;;
  *) warn "unknown command: $cmd"; exit 2 ;;
esac

ensure_dirs() {
  mkdir -p "$BIN_DIR" \
    "$DATA_DIR/winluxcd" \
    "$DATA_DIR/applications" \
    "$DATA_DIR/man/man1" \
    "$DATA_DIR/icons/hicolor/scalable/apps"
  for s in 512 256 128 64 32 16; do
    mkdir -p "$DATA_DIR/icons/hicolor/${s}x${s}/apps"
  done
}

# Creates a Windows-native .lnk shortcut (WinLuxCD) on the Windows desktop that
# launches the published EXE from the repository's dist/ directory.
make_windows_shortcut() {
  if ! command -v powershell.exe >/dev/null 2>&1; then
    return 0
  fi
  local tmpdir tmpfile win_tmp exe_src out
  if [ ! -f "$ROOT/dist/WinLuxCD.exe" ]; then
    warn "Windows app not found at $ROOT/dist/WinLuxCD.exe; run python build.py before installing the desktop shortcut"
    return 0
  fi
  exe_src="$(wslpath -w "$ROOT/dist/WinLuxCD.exe" 2>/dev/null || true)"
  [ -n "$exe_src" ] || return 0
  tmpdir="$(mktemp -d)" || return 0
  trap 'rm -rf "$tmpdir"' EXIT
  tmpfile="$tmpdir/make-shortcut.ps1"
  cat > "$tmpfile" <<'PS1EOF'
param(
  [string]$ExePath
)
$ErrorActionPreference = 'Stop'
try {
  $desktop = [Environment]::GetFolderPath('Desktop')
  $ws = New-Object -ComObject WScript.Shell
  $lnk = $ws.CreateShortcut((Join-Path $desktop 'WinLuxCD.lnk'))
  $lnk.TargetPath = $ExePath
  $lnk.Arguments  = ''
  $lnk.IconLocation = "$ExePath,0"
  $lnk.Description  = 'WinLuxCD - Convert a Windows path to a WSL path'
  $lnk.WorkingDirectory = Split-Path -Parent $ExePath
  $lnk.Save()
  Write-Output "LNK_OK: $desktop\WinLuxCD.lnk"
} catch {
  Write-Output "LNK_ERR: $($_.Exception.Message)"
  exit 1
}
PS1EOF
  win_tmp="$(wslpath -w "$tmpfile" 2>/dev/null || true)"
  if [ -n "$win_tmp" ] && out="$(powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$win_tmp" -ExePath "$exe_src" 2>&1)" && printf '%s\n' "$out" | grep -q '^LNK_OK:'; then
    info "created Windows shortcut: $(printf '%s\n' "$out" | sed -n 's/^LNK_OK: //p')"
  else
    warn "could not create Windows shortcut${out:+: $out}"
  fi
  rm -rf "$tmpdir"
  trap - EXIT
}

remove_windows_shortcut() {
  command -v powershell.exe >/dev/null 2>&1 || return 0
  local tmpdir tmpfile win_tmp
  tmpdir="$(mktemp -d)" || return 0
  trap 'rm -rf "$tmpdir"' EXIT
  tmpfile="$tmpdir/remove-shortcut.ps1"
  cat > "$tmpfile" <<'PS1EOF'
$ErrorActionPreference = 'Continue'
$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path $desktop 'WinLuxCD.lnk'
if (Test-Path -LiteralPath $lnkPath) { Remove-Item -LiteralPath $lnkPath -Force }
$appDir = Join-Path $env:LOCALAPPDATA 'WinLuxCD'
if (Test-Path -LiteralPath $appDir) { Remove-Item -LiteralPath $appDir -Recurse -Force }
Write-Output 'LNK_REMOVED'
PS1EOF
  win_tmp="$(wslpath -w "$tmpfile" 2>/dev/null || true)"
  [ -n "$win_tmp" ] || return 0
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$win_tmp" >/dev/null 2>&1 \
    && info "removed Windows desktop shortcut" \
    || true
  rm -rf "$tmpdir"
  trap - EXIT
}

add_shell_function() {
  [ -f "$ALIASES" ] || touch "$ALIASES"
  if grep -qs '^# >>> WinLuxCD >>>' "$ALIASES"; then
    info "shell function already present in $ALIASES"
    return 0
  fi
  {
    printf '\n'
    cat "$ROOT/shell/winluxcd.bash"
  } >> "$ALIASES"
  info "added winluxcd() function to $ALIASES"
}

remove_shell_function() {
  [ -f "$ALIASES" ] || return 0
  if grep -qs '^# >>> WinLuxCD >>>' "$ALIASES"; then
    sed -i '/^# >>> WinLuxCD >>>/,/^# <<< WinLuxCD <<</d' "$ALIASES"
    info "removed winluxcd() function from $ALIASES"
  fi
}

do_install() {
  ensure_dirs
  # executables
  install -m 0755 "$ROOT/bin/winluxcd"           "$BIN_DIR/winluxcd"
  install -m 0755 "$ROOT/bin/winluxcd-desktop"   "$BIN_DIR/winluxcd-desktop"
  install -m 0644 "$ROOT/powershell/winluxcd.ps1" "$DATA_DIR/winluxcd/winluxcd.ps1"
  # icons
  for s in 512 256 128 64 32 16; do
    install -m 0644 "$ROOT/icons/winluxcd-$s.png" \
      "$DATA_DIR/icons/hicolor/${s}x${s}/apps/winluxcd.png"
  done
  install -m 0644 "$ROOT/icons/winluxcd.svg" "$DATA_DIR/icons/hicolor/scalable/apps/winluxcd.svg"
  install -m 0644 "$ROOT/icons/winluxcd.ico" "$DATA_DIR/icons/winluxcd.ico"
  # desktop entry
  sed "s|__EXEC__|$BIN_DIR/winluxcd-desktop|g" \
    "$ROOT/desktop/winluxcd.desktop.in" > "$DATA_DIR/applications/winluxcd.desktop"
  chmod 0644 "$DATA_DIR/applications/winluxcd.desktop"
  # man page
  install -m 0644 "$ROOT/man/winluxcd.1" "$DATA_DIR/man/man1/winluxcd.1"
  # shell integration
  add_shell_function
  # caches (best effort)
  update-desktop-database "$DATA_DIR/applications" >/dev/null 2>&1 || true
  gtk-update-icon-cache -f -t "$DATA_DIR/icons/hicolor" >/dev/null 2>&1 || true
  # Windows side
  make_windows_shortcut
  info "installed winluxcd $VERSION -> $BIN_DIR/winluxcd"
  if ! printf '%s' "$PATH" | grep -q "$BIN_DIR"; then
    warn "$BIN_DIR is not on PATH. Add it with: export PATH=\"$BIN_DIR:\$PATH\""
  fi
  info "run: source ~/.bash_aliases   (or open a new terminal), then try: winluxcd"
}

do_uninstall() {
  rm -f "$BIN_DIR/winluxcd" "$BIN_DIR/winluxcd-desktop"
  rm -rf "$DATA_DIR/winluxcd"
  for s in 512 256 128 64 32 16; do
    rm -f "$DATA_DIR/icons/hicolor/${s}x${s}/apps/winluxcd.png"
  done
  rm -f "$DATA_DIR/icons/hicolor/scalable/apps/winluxcd.svg"
  rm -f "$DATA_DIR/icons/winluxcd.ico"
  rm -f "$DATA_DIR/applications/winluxcd.desktop"
  rm -f "$DATA_DIR/man/man1/winluxcd.1"
  remove_shell_function
  remove_windows_shortcut
  info "winluxcd $VERSION uninstalled"
}

case "$cmd" in
  install)   do_install ;;
  uninstall) do_uninstall ;;
esac
