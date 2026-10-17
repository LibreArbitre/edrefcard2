# Regression checks

The CI workflow has three independently reported jobs. Python regressions,
ImageMagick/PDF integration, the real mapper journey and the container startup
check are blocking: any failure makes the workflow fail. Ruff and Mypy findings
against the legacy code are explicitly advisory in a separate job. This does
not configure GitHub branch-protection or change merge permissions.

## Python and rendering

Use Python 3.13, the application's requirements and the ImageMagick shared
library. On Debian/Ubuntu the native package is `libmagickwand-dev`.

```sh
python -m pip install -r requirements.txt
python -m pytest
python tests/rendering_integration.py "$PWD" "$PWD/www" /tmp/edrefcard-render-evidence
```

The integration runner uses temporary output folders and a synthetic profile.
It checks real rendering, all four styles, directional inputs, modifiers,
coverage, representative legacy templates and A4/Letter PDF output. It does
not connect to an application's live database. The final optional argument
collects selected output images and a result summary for review.

## Real mapper browser journey

Use the Linux application runtime and Node.js 22. The CI installs the test-only
Playwright package outside the repository and downloads its matching Chromium.
Neither is an application dependency.

```sh
npm install --prefix /tmp/edrefcard-browser --no-save --package-lock=false playwright@1.62.1
/tmp/edrefcard-browser/node_modules/.bin/playwright install --with-deps chromium
python tests/mapper_e2e_server.py --source-www "$PWD/www" --state-file /tmp/mapper-state.json
# In a second terminal:
NODE_PATH=/tmp/edrefcard-browser/node_modules node tests/mapper_workflow.cjs \
  /tmp/mapper-state.json /tmp/edrefcard-browser-evidence
```

The fixture copies application code to a new private temporary folder, shares
only read-only source artwork/fonts, and initializes a new SQLite database.
Inherited admin credentials, application URL, scheduler mode and configs path
are overridden. It creates synthetic product images and a synthetic bindings
profile; no contributor's files or account are needed. A per-instance response
header must match the fixture's random nonce before the browser makes its
first mutation. Never point the script at production or reuse production data.

The journey uses actual pages, session authentication, routes, image rendering
and SQLite writes. It does not intercept requests or mock successful saves.
It covers:

- Admin login, mapper creation and mapper login; role restrictions.
- Photo upload, blank scaffold, physical anchors, real-bind preview and coverage.
- Draft save, reopen and browser-local recovery after reload.
- First publication and actual public card generation.
- Editing both the title and photo without changing the public card's bytes.
- A stale second tab receiving HTTP 409 without losing its unsaved work.
- Publishing a reviewed revision and downloading both PDF formats.
- History inspection, rollback as a new draft, and explicit republication.
- Fresh web upload, API generation and reopening of generated cards.
- Browser JavaScript errors and application HTTP 5xx responses.

`PLAYWRIGHT_EXECUTABLE_PATH` can select an installed Chromium-based executable
for a local check; Playwright still creates fresh, isolated browser profiles.
The optional fourth argument overrides the local fixture-files folder when
the server is reached through a private SSH tunnel from another machine.

Stop the fixture process when finished. Its temporary folder is retained for
investigation. The state file contains generated test credentials and must
not be committed or uploaded as a CI artifact. CI uploads only the selected
screenshots, synthetic PDFs, server log and test summaries for seven days.

## Scope and limits

This desktop Chromium check does not certify mobile layout, every hardware
variant, production HTTPS cookies, or multi-process server scaling. Existing
authenticated HTTPS checks and concurrent database tests cover different
parts of those concerns. Manufacturer/owner confirmation is still required
for physical button numbering and placement. Passing CI does not publish a
controller or overwrite any mapper draft.
