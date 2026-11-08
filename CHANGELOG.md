# Changelog

## [0.4.1] - 2026-11-08

### Fixed
- Crop crash (0xC0000409) on Windows: replaced QRubberBand with custom painted selection (safer on Windows/PyQt)
- **GitHub Actions Release**: workflow rewritten for PowerShell (windows-latest default shell). Previous cmd `if exist` syntax never ran correctly, so no .exe was attached to Releases.

### Changed
- **Modular architecture** started:
  - `app/core/` — image_ops, workers, ffmpeg_utils
  - `app/ui/` — main_window, preview, styles
  - `main.py` — thin entry point only
- build.spec updated to bundle the `app` package

## [0.4.0] - 2026-11-08
- Interactive crop, non-blocking filters, quality fixes, card UI separation

## [0.3.0] - 2026-11-08
- Card UI, before/after, flip, auto-enhance

## [0.2.0] - 2026-11-08
- Undo/Redo, packaging, GitHub Actions

## [0.1.0] - 2025-09-23
- Initial release
