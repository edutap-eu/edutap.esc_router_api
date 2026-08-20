# Working documents

Specs, plans and handoffs. Snapshots of what was intended and where the work stood on a
date — not descriptions of the current state, and not rewritten to match a later one. A
changed intention gets a new document.

Excluded from the published documentation build (`docs/conf.py`, `exclude_patterns`).
They are readable here, in the repository, where their date is visible next to them.

| Document | Date | About |
| --- | --- | --- |
| [`specs/2026-08-14-httpx2-and-release.md`](specs/2026-08-14-httpx2-and-release.md) | 2026-08-14 | Moving to httpx2, an injected client, spec-faithful models, and a release path to PyPI. |

Decisions that outlive the work go to [`docs/adr/`](../adr/) instead. The distinction in
one sentence: an ADR records **why** something is the way it is and survives the project;
a document here records **what is being worked on** and disappears when it is done.
