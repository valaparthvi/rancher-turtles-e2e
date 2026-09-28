# Qase IDs

Tests are tied to Qase TestOps cases by wrapping them. `cypress-qase-reporter` accepts the
wrapper in either of two places, and both are read:

```ts
qase(651, it('title', () => {}))    // the wrapper takes the test
it(qase(651, 'title'), () => {})    // the wrapper takes the title
```

The `describe`/`context` titles map 1:1 to the Qase suite tree and the `it` title to the case
title, so a test is identified by its suite path plus its title.

`.github/scripts/qase-sync/qase-sync.mjs` compares the specs against the live Qase project and
reports:

* **stale** — `qase(<id>, ...)` points at a case that no longer exists
* **missing** — an `it()` has no `qase(...)` wrapper
* **duplicate** — two tests carry the same `qase(<id>, ...)`, so one of them has to move
* **qase-only** — a Qase case that no local test claims
* **mismatched** — the ID resolves, but the case's title or suite path no longer matches the test

Run it from the repository root:

```
(cd .github/scripts/qase-sync && npm install)
export QASE_API_TOKEN=<your token>
node .github/scripts/qase-sync/qase-sync.mjs          # report only; exits 1 if there is drift
node .github/scripts/qase-sync/qase-sync.mjs --fix    # repair stale IDs and insert missing ones
```

## Configuration

Which specs are read comes from `qase-sync.config.json` — the nearest one at or above the
working directory, so the project being synced is the one you are standing in, not the one the
script lives in. The same script runs against any Cypress project (fleet-e2e, for instance)
given a config of its own:

```json
{
  "projectCode": "RT",
  "specs": ["tests/cypress/latest/e2e/*.spec.ts"]
}
```

Paths are relative to the config file, and a glob starting with `!` excludes what it matches.
The glob above is deliberately non-recursive, which is what keeps the `legacy/` sub-folder out.

`QASE_API_TOKEN` is required. `QASE_PROJECT_CODE` is optional and overrides `projectCode`, for
syncing a checkout against a scratch Qase project — if it disagrees with the config the run
says so on stderr, since a stray value left in a shell otherwise compares one project's specs
against another project's cases in silence.

## What `--fix` will and will not do

Only stale, missing and duplicate are repaired, and only when exactly one unclaimed Qase case
matches the test's suite path and title; anything ambiguous is reported for you to resolve.
Qase-only cases always need a human — they are either a test that was never automated or a
duplicate case that should be deleted in Qase.

When a test needs a wrapper inserted, the shape is copied from the nearest already-wrapped test
in the same file, falling back to whichever shape the rest of the project uses. A project with
no wrapped test anywhere is left alone rather than guessed at: wrap one by hand and every run
after follows it.

A mismatch is only ever a warning and never fails the run: renaming a test or moving it between
`describe` blocks is a legitimate thing to do, and the ID still points at the right case. It is
printed so the drift is visible — either retitle the case in Qase or accept that the two sides
read differently. A leading `RT-651: ` on either side is ignored when matching; the ID that
counts is the one in the `qase()` call.

When no case matches, the report lists every Qase case sharing the test's title, marked
`unclaimed` or `claimed by <file>:<line>` — an unclaimed one is almost always the case the test
should point at, with the suite spelled differently on one of the two sides.

Each test carries exactly one ID. Anything the script cannot read as a plain number — tests
generated inside a `forEach` loop, or a `qase(...)` whose ID is an expression — is listed under
**needs manual review** and left untouched. Those entries do fail the run: the exit code is 1
whenever anything is left for a person, whether or not `--fix` repaired the rest.

## CI

Nothing runs on a PR. `.github/workflows/qase-id-check.yaml` runs it monthly (the 1st at 06:00
UTC) and on manual dispatch, commits whatever `--fix` repaired onto `qase-sync-ids-<branch>`
and opens a PR against the branch it ran on. That job then fails if any ID was left for a
human, so a red monthly run means the report needs reading.
