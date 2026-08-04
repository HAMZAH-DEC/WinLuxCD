# >>> wsl-cd >>>  (managed by install.sh — do not edit by hand)
# Jump to a Windows directory from WSL:
#   wincd                   -> cd to whatever is on the Windows clipboard
#   wincd 'C:\Users\you\X'  -> cd to the converted path
#   wincd -p 'D:\work'      -> print the converted path only
#   wincd -w /home/you      -> print the Windows form of a WSL path
if [ -x "$HOME/.local/bin/wincd" ]; then
  wincd() {
    case "${1:-}" in
      -h|--help|--version|-p|-w|-c|--*)
        "$HOME/.local/bin/wincd" "$@" ;;
      *)
        local target
        if [ "$#" -eq 0 ]; then
          target="$("$HOME/.local/bin/wincd" -p)"
        else
          target="$("$HOME/.local/bin/wincd" -p "$*")"
        fi
        if [ "$?" -eq 0 ] && [ -n "$target" ]; then
          cd -- "$target" && pwd
        fi
        ;;
    esac
  }
fi
# <<< wsl-cd <<<
