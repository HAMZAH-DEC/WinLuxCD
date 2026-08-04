# wsl-cd

> **wincd** — stop pasting `C:\Users\...` into GPT. Convert Windows (PowerShell)
> directory addresses into WSL `cd` commands in one command.

![wincd icon](icons/wincd-256.png)

## What it does

```console
$ wincd 'C:\Users\hamzah_dec\Documents'
cd "/mnt/c/Users/hamzah_dec/Documents"

$ wincd                                    # reads the Windows clipboard
cd "/mnt/c/Users/hamzah_dec/Downloads"

$ wincd -p 'D:/work/Project X'             # raw path, no cd prefix
/mnt/d/work/Project X

$ wincd -w /home/hamzah_dec                # reverse: WSL -> Windows
C:\Users\hamzah_dec

$ wincd -c 'C:\Users\foo'                  # convert + copy to clipboard
cd "/mnt/c/Users/foo"
```

With the shell function installed, `wincd` even **changes directory**:

```console
$ wincd 'C:\Users\hamzah_dec\Downloads'
/mnt/c/Users/hamzah_dec/Downloads
```

## Requirements

- WSL2 (Ubuntu/Debian any) — already met if you are reading this from `wsl`
- `wslpath` (ships with every WSL distro; optional, a fallback is built in)
- `powershell.exe` (ships with Windows; used for clipboard support)

Nothing else. No Node, no Python runtime at install time.

## Install

```console
$ cd ~/projects/wsl-cd
$ ./install.sh
```

The installer:

- puts `wincd` and `wincd-desktop` into `~/.local/bin/`
- installs the icon (PNG + SVG + Windows `.ico`) under `~/.local/share/icons/`
- installs a `.desktop` launcher and a man page
- adds the `wincd()` **cd** function to `~/.bash_aliases` (idempotent)
- copies `wincd.ico` onto your Windows Desktop so you can pin/taskbar it

Then reload your shell:

```console
$ source ~/.bash_aliases
$ wincd
cd "/mnt/c/Users/hamzah_dec/Downloads"     # whatever was on the clipboard
```

> If `~/.local/bin` isn't on your PATH, add it:
> `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc`

## Usage cheat-sheet

| Command                          | Result                                   |
| -------------------------------- | ---------------------------------------- |
| `wincd 'C:\Users\you\Docs'`      | `cd "/mnt/c/Users/you/Docs"`             |
| `wincd`                          | converts the current Windows clipboard   |
| `wincd -p 'D:\work'`             | `/mnt/d/work` (no prefix — pipe it)      |
| `wincd -w /home/you`             | Windows form of a WSL path               |
| `wincd -c 'C:\path'`             | prints **and** copies to the clipboard   |
| `cd "$(wincd -p)"`               | jump, no function needed                 |
| `explorer.exe "$(wincd -p)"`     | open the clipboard's folder in Explorer  |
| `wincd --help`                   | full help                                |

Accepted input: backslashes, forward slashes, spaces, surrounding quotes,
lowercase drive letters, UNC paths (`\\server\share` → `//server/share`),
and WSL paths (passed through unchanged).

## PowerShell side

A twin script lives at `powershell/wincd.ps1` (also installed to
`~/.local/share/wsl-cd/wincd.ps1`):

```powershell
.\wincd.ps1 'C:\Users\you\Docs'      # cd "/mnt/c/Users/you/Docs"
.\wincd.ps1 -Clipboard               # convert clipboard contents
.\wincd.ps1 -Windows '/home/you'     # reverse direction
.\wincd.ps1 -Raw -Copy 'D:\work'     # raw path, also copied
```

## The "other way" (built into WSL, no tool needed)

If you ever want the raw one-liners:

```console
# WSL shell
cd "$(wslpath "$(powershell.exe Get-Clipboard)")"
wslpath 'C:\Users\you\Docs'                    # -> /mnt/c/Users/you/Docs
wslpath -w /home/you                           # -> C:\Users\you

# PowerShell
wsl wslpath -u 'C:\Users\you\Docs'             # -> /mnt/c/Users/you/Docs
```

`wincd` is just these, wrapped, tested and documented.

## Icon

`icons/` ships the artwork in every format you'd want:

- `wincd.svg` — vector source
- `wincd-512.png` … `wincd-16.png` — raster sizes
- `wincd.ico` — multi-resolution Windows icon (16 → 256 px)

Regenerate them anytime with `bash scripts/make-icon.sh` (Pillow only —
no ImageMagick needed). The installer drops `wincd.ico` onto your Windows
Desktop automatically; you can also paste it into your taskbar via
*Right-click taskbar → Taskbar settings →* or pin it from the desktop.

## Uninstall

```console
$ ./install.sh uninstall
```

Removes the binaries, icons, `.desktop` file, man page and the shell function.

## Development

```console
$ make test          # bash tests/run-tests.sh
$ make install
$ make uninstall
```

Test suite covers: drive letters, forward slashes, spaces, quoting, lowercase
drives, WSL passthrough, UNC, reverse mode, clipboard mode, copy mode, the
no-`wslpath` fallback, and meta flags.

## Project layout

```
bin/wincd             main CLI (bash, zero deps)
bin/wincd-desktop     launcher used by the .desktop entry
powershell/wincd.ps1  PowerShell twin
shell/wincd.bash      cd() function added to ~/.bash_aliases
desktop/              .desktop entry template
icons/                SVG/PNG/ICO artwork
scripts/make-icon.*   icon generator
man/wincd.1           man page
tests/run-tests.sh    test suite
install.sh            installer / uninstaller
```

## License

MIT — see [LICENSE](LICENSE).
