# Releasing

The version is **not** written anywhere in this repository. `hatch-vcs` derives it from
the git tag and the distance to it, so `v0.1.0` builds `0.1.0` and the fourth commit
after it builds `1.0.0b2.dev4`.

That is not a style preference. Every merge to `main` uploads to test.pypi.org, and
test.pypi refuses a version it has already seen. With a version in `pyproject.toml`, every
merge would need a bump by hand, and the merge that forgot would fail in the upload step —
long after review, and looking like an infrastructure problem.

## The two paths

| Trigger | Goes to | Version |
| --- | --- | --- |
| Any merge to `main` | test.pypi.org | `1.0.0b2.dev7` — a development version |
| A published GitHub Release | pypi.org | `1.0.0b2` — whatever the tag says |

Both run the repository's CI first, by calling `.github/workflows/ci.yml` rather than
restating it.

## Making a release

1. Merge everything that belongs in it. Confirm the test.pypi upload on the last merge
   succeeded — that is the dress rehearsal, and it is free.
2. Tag it. [PEP 440](https://peps.python.org/pep-0440/) spellings only:

   ```console
   git tag -a v0.1.0 -m "0.1.0"
   git push origin v0.1.0
   ```

3. Draft a **GitHub Release** on that tag and publish it. Publishing is what fires the
   upload to pypi.org; pushing the tag alone does not.
4. Watch the `release-pypi` job. Confirm on <https://pypi.org/project/edutap-esc-router-api/>.

Write the release notes from `docs/explanation/migrating-to-0-1-0.md` where a release breaks
something. Four things break in 0.1.0, one of them silently — `delete_person()` returned
`True` and now returns `None`, so `if await delete_person(esi):` still compiles and is
always false.

## One-time setup — needs the repository owner

Neither of these can be done from a pull request, and until both are done the upload jobs
fail with an authorisation error rather than with anything about packaging.

### 1. GitHub environments

In **Settings → Environments**, create `release-test-pypi` and `release-pypi`. They may be
empty; the workflow names them so that the OIDC identity it presents is scoped to one of
them. Adding a required reviewer to `release-pypi` is worth considering — it puts a human
between a published Release and pypi.org.

### 2. Trusted publishers

There are no API tokens anywhere in this repository, and there should not be. Both indexes
authenticate the workflow by OIDC.

On **<https://test.pypi.org/manage/account/publishing/>** and on
**<https://pypi.org/manage/account/publishing/>**, add a pending publisher:

| Field | Value |
| --- | --- |
| PyPI project name | `edutap-esc-router-api` |
| Owner | `edutap-eu` |
| Repository name | `edutap.esc_router_api` |
| Workflow name | `release.yaml` |
| Environment name | `release-test-pypi` / `release-pypi` respectively |

The project name is the **normalised** one. PEP 503 folds every run of `.`, `-` and `_`
into a single hyphen and lowercases the result, so `edutap.esc_router_api` becomes
`edutap-esc-router-api` — both the dot and the underscore go. Getting this wrong produces
an error about the project not existing rather than about the name.

Checked on 2026-08-14: the project exists on neither index, so both entries are *pending*
publishers. Once the first upload succeeds the entry moves under the project itself, and a
later change is made there rather than on the pending list.

### 3. The first tag

This repository has never been tagged. Until it is, `hatch-vcs` produces `0.1.devN`, which
is a legal version and not the one anybody wants on PyPI. Tag before the first release, not
after.

## When an upload fails

**`File already exists`** on test.pypi — two builds produced the same version. Almost
always a shallow clone: without `fetch-depth: 0` there are no tags, so hatch-vcs falls
back to `0.1.dev0` every time. The workflows set it; a new job that does not will hit this.

**`invalid-publisher`** — the pending publisher does not match. Check all five fields
above, the environment name included.

**The `release` run was cancelled** — the concurrency group is missing `github.event_name`,
so the `push` from the tag and the `release` from publishing collided. It is in the
workflow with a comment; do not simplify it away.
