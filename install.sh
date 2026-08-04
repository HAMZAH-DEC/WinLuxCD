#!/usr/bin/env bash
# wsl-cd installer / uninstaller.
#   ./install.sh [install|uninstall]   (default: install)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
ALIASES="$HOME/.bash_aliases"

info() { printf '\033[1;32m[wsl-cd]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[wsl-cd]\033[0m %s\n' "$*" >&2; }

cmd="${1:-install}"
case "$cmd" in
  install|uninstall) ;;
  -h|--help|help) echo "usage: $0 [install|uninstall]"; exit 0 ;;
  *) warn "unknown command: $cmd"; exit 2 ;;
esac

ensure_dirs() {
  mkdir -p "$BIN_DIR" \
    "$DATA_DIR/wsl-cd" \
    "$DATA_DIR/applications" \
    "$DATA_DIR/man/man1" \
    "$DATA_DIR/icons/hicolor/scalable/apps"
  for s in 512 256 128 64 32 16; do
    mkdir -p "$DATA_DIR/icons/hicolor/${s}x${s}/apps"
  done
}

copy_to_windows_desktop() {
  local desk
  desk="$(powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Desktop')" 2>/dev/null | tr -d '\r' || true)"
  [ -n "$desk" ] || return 0
  desk="$(wslpath -u "$desk" 2>/dev/null || true)"
  [ -n "$desk" ] && [ -d "$desk" ] || return 0
  if cp "$ROOT/icons/wincd.ico" "$desk/wincd.ico" 2>/dev/null; then
    info "copied wincd.ico to your Windows Desktop: $desk/wincd.ico"
  else
    warn "could not copy icon to Windows Desktop"
  fi
}

add_shell_function() {
  [ -f "$ALIASES" ] || touch "$ALIASES"
  if grep -qs '^# >>> wsl-cd >>>' "$ALIASES"; then
    info "shell function already present in $ALIASES"
    return 0
  fi
  {
    printf '\n'
    cat "$ROOT/shell/wincd.bash"
  } >> "$ALIASES"
  info "added wincd() function to $ALIASES"
}

remove_shell_function() {
  [ -f "$ALIASES" ] || return 0
  if grep -qs '^# >>> wsl-cd >>>' "$ALIASES"; then
    sed -i '/^# >>> wsl-cd >>>/,/^# <<< wsl-cd <<</d' "$ALIASES"
    info "removed wincd() function from $ALIASES"
  fi
}

do_install() {
  ensure_dirs
  # executables
  install -m 0755 "$ROOT/bin/wincd"           "$BIN_DIR/wincd"
  install -m 0755 "$ROOT/bin/wincd-desktop"   "$BIN_DIR/wincd-desktop"
  install -m 0644 "$ROOT/powershell/wincd.ps1" "$DATA_DIR/wsl-cd/wincd.ps1"
  # icons
  for s in 512 256 128 64 32 16; do
    install -m 0644 "$ROOT/icons/wincd-$s.png" \
      "$DATA_DIR/icons/hicolor/${s}x${s}/apps/wincd.png"
  done
  install -m 0644 "$ROOT/icons/wincd.svg" "$DATA_DIR/icons/hicolor/scalable/apps/wincd.svg"
  install -m 0644 "$ROOT/icons/wincd.ico" "$DATA_DIR/icons/wincd.ico"
  # desktop entry
  sed "s|__EXEC__|$BIN_DIR/wincd-desktop|g" \
    "$ROOT/desktop/wincd.desktop.in" > "$DATA_DIR/applications/wincd.desktop"
  chmod 0644 "$DATA_DIR/applications/wincd.desktop"
  # man page
  install -m 0644 "$ROOT/man/wincd.1" "$DATA_DIR/man/man1/wincd.1"
  # shell integration
  add_shell_function
  # caches (best effort)
  update-desktop-database "$DATA_DIR/applications" >/dev/null 2>&1 || true
  gtk-update-icon-cache -f -t "$DATA_DIR/icons/hicolor" >/dev/null 2>&1 || true
  # Windows side
  copy_to_windows_desktop
  info "installed wincd $VERSION -> $BIN_DIR/wincd"
  if ! printf '%s' "$PATH" | grep -q "$BIN_DIR"; then
    warn "$BIN_DIR is not on PATH. Add it with: export PATH=\"$BIN_DIR:\$PATH\""
  fi
  info "run: source ~/.bash_aliases   (or open a new terminal), then try: wincd"
}

do_uninstall() {
  rm -f "$BIN_DIR/wincd" "$BIN_DIR/wincd-desktop"
  rm -rf "$DATA_DIR/wsl-cd"
  for s in 512 256 128 64 32 16; do
    rm -f "$DATA_DIR/icons/hicolor/${s}x${s}/apps/wincd.png"
  done
  rm -f "$DATA_DIR/icons/hicolor/scalable/apps/wincd.svg"
  rm -f "$DATA_DIR/icons/wincd.ico"
  rm -f "$DATA_DIR/applications/wincd.desktop"
  rm -f "$DATA_DIR/man/man1/wincd.1"
  remove_shell_function
  info "wincd $VERSION uninstalled"
}

case "$cmd" in
  install)   do_install ;;
  uninstall) do_uninstall ;;
esac
