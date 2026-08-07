# Changelog

All notable WinLuxCD changes are documented here.

## [1.1.0] - 2026-08-07

### Added

- Windows desktop GUI built with Tkinter.
- PyInstaller build script that creates a one-file `WinLuxCD.exe`.
- Real Windows desktop shortcut creation with the embedded application icon.
- Shared Python conversion core and unit tests.
- Paste, convert, and copy controls in the Windows app.
- Automatic conversion when the GUI Paste button is used.
- Navy and blue desktop-app theme with Denville Energy Consulting Ltd footer
  branding.

### Changed

- Renamed the project command and assets from `wincd` to `winluxcd`.
- Improved Windows path handling for forward slashes, quotes, spaces, drive
  letters, UNC paths, and WSL paths.
- Added clear validation for URLs and other clipboard text that is not a path.
- Added safe Windows `wslpath` execution with a minimal child environment.

### Fixed

- Desktop launch no longer routes clipboard content through the legacy
  PowerShell script.
- Windows shortcut targets the built EXE in `dist` instead of an image or a
  script-only launcher.
- Copy-ready shell commands escape characters that Bash would otherwise expand.

## [Unreleased]

Reserved for changes after the 1.1.0 release.
