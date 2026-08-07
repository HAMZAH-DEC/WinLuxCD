# WinLuxCD Build Log

This file records the last verified Windows desktop build. It is documentation
for reproducibility, not generated build output.

## Verified Build

- Date: 2026-08-07
- Host: Windows 11, build 26200
- Python: 3.14.2
- PyInstaller: 6.21.0
- Architecture: Windows x86-64
- Build mode: one-file, windowed GUI
- Result: successful

## Build Command

Run from Windows PowerShell in the repository root:

```powershell
Set-Location 'C:\path\to\WinLuxCD'
python build.py
```

The script installs PyInstaller if it is not available, packages
`winluxcd_app.py`, includes the ICO and PNG assets, and creates the Windows
shortcut after the EXE is built.

## Outputs

```text
dist/WinLuxCD.exe
%USERPROFILE%/Desktop/WinLuxCD.lnk
```

The verified EXE was a PE32+ Windows GUI executable approximately 11 MB in
size. The shortcut target was:

```text
<repository>\dist\WinLuxCD.exe
```

The shortcut uses the icon embedded in the EXE and sets the EXE directory as
its working directory.

## Verification

The following checks passed after the build:

```console
python3 -m py_compile winluxcd_core.py winluxcd_app.py build.py tests/test_winluxcd.py
python3 -m unittest discover -s tests -p test_winluxcd.py -v
bash tests/run-tests.sh
git diff --check
```

Test results:

- Python conversion tests: 4 passed.
- Bash CLI tests: 24 passed.
- EXE startup smoke test: passed; the GUI remained running after launch.
- Desktop shortcut target and icon metadata: verified.

## Rebuild Notes

- Close all running `WinLuxCD.exe` instances before rebuilding. Windows can
  otherwise deny access to the output file.
- `dist/` and `build/` are ignored by Git because they are generated outputs.
- The packaged EXE does not need Python installed on the target machine, but it
  does need WSL available for path conversion.
- Do not commit a desktop `.lnk` file. The build script creates it locally.
