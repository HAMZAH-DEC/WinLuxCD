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

### Added

- Custom blue title bar in the Windows app with minimise and close buttons;
  the window can be dragged by its title bar.
- Automatic conversion when a path is pasted into the Windows or WSL path
  field (Ctrl+V or Shift+Insert), not just via the Paste button.
- A Recent drop-down list under the converter. Selecting an entry
  repopulates the path field and converts it; history is stored in
  `%LOCALAPPDATA%\WinLuxCD\history.json` (newest first, capped at 12) and
  survives restarts. A Clear button empties it.
- The window opens 1000 px wide by default so longer paths stay visible,
  and its minimum size keeps every control on screen.
- A Clear button under Paste that empties the path field.
- Corner drag-resize: grab the grip at the bottom-right corner to resize the
  window; the size and position are saved on close and restored on the next
  launch (`%LOCALAPPDATA%\WinLuxCD\settings.json`).
- Per-monitor DPI awareness so the app stays crisp on scaled displays.

### Changed

- Recent history is a drop-down box instead of wrapping link chips.

### Fixed

- The window no longer opens cut off at the bottom with controls hidden.
- The blue title bar spans the full window width, so no dark gap shows beside
  the close button.

Reserved for changes after the 1.1.0 release.
