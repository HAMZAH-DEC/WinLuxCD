#!/usr/bin/env bash
# WinLuxCD test suite — run with:  bash tests/run-tests.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WINC="$ROOT/bin/winluxcd"

pass=0
fail=0

# t <desc> <expected> <cmd...> — exact match, must exit 0
t() {
  local desc="$1" expected="$2"; shift 2
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ] && [ "$out" = "$expected" ]; then
    printf 'ok   %s\n' "$desc"; pass=$((pass + 1))
  else
    printf 'FAIL %s (rc=%s)\n' "$desc" "$rc"
    printf '  want: %s\n  got:  %s\n' "$expected" "$out"
    fail=$((fail + 1))
  fi
}

# t_err <desc> <cmd...> — must exit non-zero
t_err() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf 'FAIL %s (expected non-zero exit)\n' "$desc"; fail=$((fail + 1))
  else
    printf 'ok   %s\n' "$desc"; pass=$((pass + 1))
  fi
}

# t_contains <desc> <needle> <cmd...>
t_contains() {
  local desc="$1" needle="$2"; shift 2
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -qF -- "$needle"; then
    printf 'ok   %s\n' "$desc"; pass=$((pass + 1))
  else
    printf 'FAIL %s (rc=%s)\n' "$desc" "$rc"
    printf '  want substring: %s\n  got: %s\n' "$needle" "$out"
    fail=$((fail + 1))
  fi
}

[ -x "$WINC" ] || { echo "missing $WINC (chmod +x?)"; exit 1; }

echo "== conversion =="
t "backslash path"        'cd "/mnt/c/Users/foo/Documents"' "$WINC" 'C:\Users\foo\Documents'
t "forward slashes"       'cd "/mnt/c/Users/foo"'          "$WINC" 'C:/Users/foo'
t "path with spaces"      'cd "/mnt/c/Users/foo/My Docs"'  "$WINC" 'C:\Users\foo\My Docs'
t "lowercase drive"       'cd "/mnt/c/users/foo"'           "$WINC" 'c:\users\foo'
t "double-quoted input"   'cd "/mnt/c/Users/foo"'           "$WINC" '"C:\Users\foo"'
t "single-quoted input"   'cd "/mnt/c/Users/foo"'           "$WINC" "'C:\Users\foo'"
t "wsl path passthrough"  'cd "/home/user"'                 "$WINC" '/home/user'
t "-p raw path"           '/mnt/d/work'                     "$WINC" -p 'D:\work'
t "UNC path"              'cd "//server/share/dir"'         "$WINC" '\\server\share\dir'

echo "== reverse (-w) =="
t "-w mnt path"           'C:\Users\foo'                    "$WINC" -w '/mnt/c/Users/foo'
EXPECT_HOME="$(wslpath -w "$HOME" 2>/dev/null || printf '\\\\wsl.localhost\\Ubuntu%s' "$HOME")"
t "-w home path"          "$EXPECT_HOME"                    "$WINC" -w "$HOME"
t "-w UNC"                '\\server\share\dir'              "$WINC" -w '//server/share/dir'

echo "== fallback (wslpath unavailable) =="
t "fallback backslash"    'cd "/mnt/c/Users/foo"'           env WSLPATH=/nonexistent "$WINC" 'C:\Users\foo'
t "fallback spaces"       'cd "/mnt/d/work/My Docs"'        env WSLPATH=/nonexistent "$WINC" 'D:\work\My Docs'
t "fallback UNC"          'cd "//server/share/dir"'         env WSLPATH=/nonexistent "$WINC" '\\server\share\dir'
t "fallback -w"           'C:\Users\foo'                    env WSLPATH=/nonexistent "$WINC" -w '/mnt/c/Users/foo'
t "fallback -w UNC"       '\\server\share\dir'              env WSLPATH=/nonexistent "$WINC" -w '//server/share/dir'

echo "== clipboard & copy =="
MOCK="$(mktemp -d)"
trap 'rm -rf "$MOCK"' EXIT
cat > "$MOCK/powershell.exe" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *Get-Clipboard* ]]; then
  if [ "${MOCK_CLIP+x}" = x ]; then
    printf '%s' "$MOCK_CLIP"
  else
    printf '%s' 'C:\Users\clip\My Folder'
  fi
else
  cat > /dev/null
fi
EOF
chmod +x "$MOCK/powershell.exe"

t "clipboard mode" 'cd "/mnt/c/Users/clip/My Folder"' env PATH="$MOCK:$PATH" MOCK_CLIP='C:\Users\clip\My Folder' "$WINC"
t "copy mode -c"   'cd "/mnt/c/Users/foo"'            env PATH="$MOCK:$PATH" "$WINC" -c 'C:\Users\foo'
MOCK_CLIP='' t_err "empty clipboard errors" env PATH="$MOCK:$PATH" "$WINC"
t_err "garbage arg rejected"      "$WINC" 'verify_roads.py >/dev/null; do sleep 10; done'
t_err "garbage clipboard rejected" env PATH="$MOCK:$PATH" MOCK_CLIP='verify_roads.py >/dev/null; do sleep 10; done' "$WINC"

echo "== meta =="
t_contains "--help shows usage" "USAGE"        "$WINC" --help
t_contains "--version"          "1.1.0"        "$WINC" --version

echo
echo "== results: $pass passed, $fail failed =="
[ "$fail" -eq 0 ]
