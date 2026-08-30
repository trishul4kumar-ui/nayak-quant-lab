# Packaging QUANT LAB

## Decision

**PyInstaller** is the packaging path for a development/distributable desktop build.

| Tool | Why not (now) |
|---|---|
| Nuitka | Harder debug cycle; native compile of numpy/Qt is costly |
| Briefcase | Extra mobile/desktop scaffolding we do not need |
| PyInstaller | One-folder/one-file, handles PySide6 and numpy, inspectable spec |

The user should eventually receive an installer + application, not a requirement to `pip install` dozens of packages. That is not required for Prompt 03 definition of done.

## Development executable

```bash
pip install pyinstaller
pyinstaller packaging/quantlab.spec
```

The spec is `onedir` so Qt plugins remain on disk. Codesigning/notarization for macOS and an MSI/NSIS installer for Windows are later operations.

Application data must still use the OS data directory (see `quantlab.app.paths`), not a path beside the source tree.

## Versions to keep distinct

- Application version (`quantlab.__version__`)
- Experiment / dataset versions on the ledger
- Future database schema version

Never silently invalidate old research artifacts on upgrade.
