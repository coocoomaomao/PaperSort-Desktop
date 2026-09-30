# Contributing to PaperSort Desktop

Thanks for helping improve PaperSort Desktop.

## Before opening a pull request

1. Keep the app local-first by default.
2. Do not add destructive automatic deduplication.
3. Any rename/move behavior must remain previewable and reversible where practical.
4. New online metadata features must be opt-in and document what is sent.
5. Add or update tests for behavior changes.

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Small, focused pull requests are preferred. For larger feature ideas, opening an issue first is helpful.
