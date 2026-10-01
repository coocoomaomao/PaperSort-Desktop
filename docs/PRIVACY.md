# PaperSort Desktop Privacy Notes — v0.2

PaperSort Desktop v0.2 is local-first.

- PDF bytes are read locally for metadata/text extraction and hashing.
- No PDF content is uploaded by the application.
- No account is required by the application.
- No analytics or telemetry are included in v0.2.
- No online DOI/Crossref lookup is enabled in v0.2.
- Scan results remain in memory unless the user applies a rename/move operation.
- Applied operations create a local JSON undo manifest under `.papersort/history`.

Future online metadata features, if added, should be opt-in and clearly describe what identifiers are sent.
