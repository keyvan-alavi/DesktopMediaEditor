# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-11-08

### Added
- Version number display and About section in Settings
- Undo / Redo support for image editing (up to 20 steps)
- Live Brightness & Contrast sliders
- Status bar with helpful messages
- Tooltips on most buttons
- Better cross-platform FFmpeg detection (tries system PATH first, then local folder)
- Professional UI polish (improved spacing, modern card-style groups, better hover states, focus styles)
- GitHub Actions workflow for automatic Windows builds and Releases
- PyInstaller spec file for packaging
- Improved error messages and user feedback

### Changed
- Window title now includes version
- More consistent bilingual labels and layout
- Cleaner theme application and settings persistence
- Better cache handling

### Fixed
- Hardcoded Windows-only ffmpeg.exe path
- Some layout glitches on maximize/resize

## [0.1.0] - 2025-09-23

### Added
- Initial release
- Image filters, quality adjustments, rotate, resize
- Video trim and MP3 extraction
- Multiple themes + dark mode
- QSettings persistence
