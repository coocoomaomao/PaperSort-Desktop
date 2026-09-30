# 🐈‍⬛ PaperSort Desktop

**把乱糟糟的论文 PDF，整理成真正找得到的文献库。**

PaperSort Desktop is a local-first, open-source Windows app for researchers who have accumulated a folder full of badly named academic PDFs.

[![CI](https://github.com/coocoomaomao/PaperSort-Desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/coocoomaomao/PaperSort-Desktop/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## v0.2 — Open Source Preview

- Drag in a folder and recursively scan PDF papers.
- Extract title, author, year and DOI locally when they can be determined reliably.
- Detect **exact duplicates** by SHA-256 and **same-DOI duplicates**.
- Review duplicate groups in a side-by-side comparison window before deciding what to process.
- Generate readable filenames such as `2026_Smith_Clean_Research_Title.pdf`.
- Customize the rename template with `{year}`, `{author}`, `{title}` and `{doi}` while keeping a full preview before changes.
- Preview every rename before anything changes.
- Duplicate candidates are **not selected by default**.
- Optional organization into library-level year folders.
- Export the scanned library as CSV or BibTeX.
- Apply selected changes only after confirmation.
- Save an undo manifest and restore the last operation.
- Best-effort rollback if a batch rename fails partway through.
- No paper upload and no automatic deletion.

## Product principle

> 能确定的问题才做，不能确定的就让用户确认。

PaperSort is deliberately conservative. Metadata extraction may be incomplete or wrong in unusual PDFs, so the app always shows a preview before modifying files.

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
papersort
```

Development:

```bash
pip install -e ".[dev]"
pytest
```

## Windows installer

GitHub Actions contains a Windows build workflow that creates a PyInstaller + Inno Setup installer. Tagged builds (`v*`) and pull requests can run the packaging workflow.

## Privacy

The v0.2 scanner runs locally. It does not upload PDF content and does not use papers for model training. Online metadata lookup is not enabled in v0.1. See [Privacy Notes](docs/PRIVACY.md).

## Safety

PaperSort never deletes duplicate files automatically. Rename/move operations are explicitly confirmed and written to a local undo manifest under `.papersort/history` inside the selected library folder.

## Contributing

Issues and pull requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting larger changes.

## License

MIT — see [LICENSE](LICENSE).

## MeowBuild Lab

**一只猫，认真造点有用的。**
