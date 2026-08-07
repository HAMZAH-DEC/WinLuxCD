# WinLuxCD

WinLuxCD converts Windows paths into WSL paths and copy-ready `cd` commands.
It provides a tested WSL command-line tool, a PowerShell companion, and a
small Windows desktop application.

![winluxcd icon](icons/winluxcd-256.png)

## What it does

```console
$ winluxcd 'C:\Users\you\Documents'
cd "/mnt/c/Users/you/Documents"

$ winluxcd                                    # reads the Windows clipboard
cd "/mnt/c/Users/you/Downloads"

$ winluxcd -p 'D:/work/Project X'             # raw path, no cd prefix
/mnt/d/work/Project X

$ winluxcd -w /home/you                     # reverse: WSL -> Windows
C:\Users\you

$ winluxcd -c 'C:\Users\foo'                  # convert + copy to clipboard
cd "/mnt/c/Users/foo"
```

With the shell function installed, `winluxcd` even **changes directory**:

```console
$ winluxcd 'C:\Users\you\Downloads'
/mnt/c/Users/you/Downloads
```

## Requirements

- WSL2 (Ubuntu/Debian any) — already met if you are reading this from `wsl`
- `wslpath` (ships with every WSL distro; optional, a fallback is built in)
- `powershell.exe` (ships with Windows; used for clipboard support)
- Windows Python 3 and PyInstaller (only required to build the desktop EXE)

The installed desktop EXE is one-file and does not need Python at runtime.

## Windows app

The repository includes a small Windows app with an editable path field. It has
Paste and Convert buttons, displays both the raw WSL path and a copy-ready
`cd "/mnt/..."` command, and provides a separate Copy button for each result.
The Paste button immediately converts the clipboard contents, so a second
click is not required. Invalid clipboard contents such as a web URL are shown
as an error instead of being sent to WSL.

Build the one-file Windows executable from Windows PowerShell:

```powershell
Set-Location 'C:\path\to\WinLuxCD'
python build.py
```

The output is `dist\WinLuxCD.exe`, and `build.py` creates a real
`WinLuxCD.lnk` on the Windows Desktop targeting that EXE. You can also copy
`dist\WinLuxCD.exe` directly to the Desktop; its icon is embedded in the EXE.
From WSL, the equivalent command is:

```console
$ make windows
```

### Clone versus packaged EXE

A Git clone contains the source code, icons, tests, and build instructions.
The generated `dist\WinLuxCD.exe` is intentionally excluded from Git, so a
Windows user must run `python build.py` after cloning. A ready-made EXE can be
distributed separately as a GitHub Release asset.

## Install

```console
$ cd "/path/to/WinLuxCD"
$ ./install.sh
```

The installer:

- puts `winluxcd` and `winluxcd-desktop` into `~/.local/bin/`
- installs the icon (PNG + SVG + Windows `.ico`) under `~/.local/share/icons/`
- installs a `.desktop` launcher and a man page
- adds the `winluxcd()` **cd** function to `~/.bash_aliases` (idempotent)
- repairs/creates a `WinLuxCD.lnk` shortcut targeting `dist\WinLuxCD.exe` when
  the Windows EXE has already been built

The WSL CLI can be installed without the Windows EXE. The normal Windows build
command creates the desktop shortcut itself.

After installation, the shortcut target should be the EXE under `dist`. If it
still opens a PowerShell window mentioning `%LOCALAPPDATA%\WinLuxCD\winluxcd.ps1`,
rerun the installer after building the EXE; that is the legacy shortcut.

Then reload your shell:

```console
$ source ~/.bash_aliases
$ winluxcd
cd "/mnt/c/Users/you/Downloads"            # whatever was on the clipboard
```

> If `~/.local/bin` isn't on your PATH, add it:
> `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc`

## Usage cheat-sheet

| Command                          | Result                                   |
| -------------------------------- | ---------------------------------------- |
| `winluxcd 'C:\Users\you\Docs'`      | `cd "/mnt/c/Users/you/Docs"`             |
| `winluxcd`                          | converts the current Windows clipboard   |
| `winluxcd -p 'D:\work'`             | `/mnt/d/work` (no prefix — pipe it)      |
| `winluxcd -w /home/you`             | Windows form of a WSL path               |
| `winluxcd -c 'C:\path'`             | prints **and** copies to the clipboard   |
| `cd "$(winluxcd -p)"`               | jump, no function needed                 |
| `explorer.exe "$(winluxcd -p)"`     | open the clipboard's folder in Explorer  |
| `winluxcd --help`                   | full help                                |

Accepted input: backslashes, forward slashes, spaces, surrounding quotes,
lowercase drive letters, UNC paths (`\\server\share` → `//server/share`),
and WSL paths (passed through unchanged). Anything that doesn't look like a
path (e.g. a copied shell command) is rejected with a clear message instead of
a cryptic `wsl.exe` error.

## PowerShell side

A command-line PowerShell fallback lives at `powershell/winluxcd.ps1` (also
installed to `~/.local/share/winluxcd/winluxcd.ps1`):

```powershell
.\winluxcd.ps1 'C:\Users\you\Docs'      # cd "/mnt/c/Users/you/Docs"
.\winluxcd.ps1 -Clipboard               # convert clipboard contents
.\winluxcd.ps1 -Windows '/home/you'     # reverse direction
.\winluxcd.ps1 -Raw -Copy 'D:\work'     # raw path, also copied
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

`winluxcd` is just these, wrapped, tested and documented.

## Icon

`icons/` ships the artwork in every format you'd want:

- `winluxcd.svg` — vector source
- `winluxcd-512.png` … `winluxcd-16.png` — raster sizes
- `winluxcd.ico` — multi-resolution Windows icon (16 → 256 px)

Regenerate them anytime with `bash scripts/make-icon.sh` (Pillow only —
no ImageMagick needed). PyInstaller embeds the ICO in `dist\WinLuxCD.exe`.

## Uninstall

```console
$ ./install.sh uninstall
```

Removes the binaries, icons, `.desktop` file, man page, shell function, and
Windows desktop shortcut. It leaves the locally built `dist` directory alone.

## Development

```console
$ make test          # bash tests/run-tests.sh
$ make windows-test  # Python conversion-core tests
$ make windows       # run build.py through Windows Python
$ make install
$ make uninstall
```

Test suite covers: drive letters, forward slashes, spaces, quoting, lowercase
drives, WSL passthrough, UNC, reverse mode, clipboard mode, copy mode, the
no-`wslpath` fallback, meta flags, and Windows app input validation.

## Project layout

```
bin/winluxcd             main CLI (bash, zero deps)
bin/winluxcd-desktop     launcher used by the .desktop entry
powershell/winluxcd.ps1  PowerShell twin
shell/winluxcd.bash      cd() function added to ~/.bash_aliases
winluxcd_app.py          Windows GUI entry point
winluxcd_core.py         shared Windows/WSL conversion logic
desktop/              .desktop entry template
icons/                SVG/PNG/ICO artwork
scripts/make-icon.*   icon generator
man/winluxcd.1        man page
tests/run-tests.sh    Bash test suite
tests/test_winluxcd.py Python conversion tests
build.py              PyInstaller EXE and shortcut builder
install.sh            installer / uninstaller
dist/                 generated Windows EXE (not committed)
```

See [CHANGELOG.md](CHANGELOG.md) for release history and
[BUILD_LOG.md](BUILD_LOG.md) for the verified Windows build record.

## License

MIT — see [LICENSE](LICENSE).
