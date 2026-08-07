# >>> WinLuxCD >>>  (managed by install.sh — do not edit by hand)
# Jump to a Windows directory from WSL:
#   winluxcd                   -> cd to whatever is on the Windows clipboard
#   winluxcd 'C:\Users\you\X'  -> cd to the converted path
#   winluxcd -p 'D:\work'      -> print the converted path only
#   winluxcd -w /home/you      -> print the Windows form of a WSL path
if [ -x "$HOME/.local/bin/winluxcd" ]; then
  winluxcd() {
    case "${1:-}" in
      -h|--help|--version|-p|-w|-c|--*)
        "$HOME/.local/bin/winluxcd" "$@" ;;
      *)
        local target
        if [ "$#" -eq 0 ]; then
          target="$("$HOME/.local/bin/winluxcd" -p)"
        else
          target="$("$HOME/.local/bin/winluxcd" -p "$*")"
        fi
        if [ "$?" -eq 0 ] && [ -n "$target" ]; then
          cd -- "$target" && pwd
        fi
        ;;
    esac
  }
fi
# <<< WinLuxCD <<<
