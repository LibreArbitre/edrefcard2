# EdRefCard2 stabilization and controller delivery

Updated on 2026-10-17. Use the dated delivery checkpoints below rather than old
roadmap completion percentages to assess release readiness. STECS Space Mini
LH and WINCTRL Orion pedals are now published after owner validation. Other controller pilots remain
separate work; finish their review before adding more editor features.

## Initial deployment and data before stabilization

- Fork `origin/dev` and `origin/main`: `8283300669e68e8016445afa9695a0dc08d1ed5e`.
- Upstream `beta`: `7d71ff3070906da8b42c5c699b933c6c8cc948c7`.
- Upstream historical `librearbitre-pull-request`: `7c6d0702a714e69f21b24aa718dae3f267dc01c8`.
- Beta: `https://beta.edrefcard.info`, also `https://edrefcard2.l0l.fr`.
- Staging: `https://edrefcard2-dev.l0l.fr`.
- Beta container: `infra-edrefcard-2ru5iv-edrefcard-1` on Dokploy.
- Staging container: `edrefcard2-dev-teqvm9-edrefcard-1` on Dokploy2.
- SHA256 checks match local, beta and staging for `web.py`, `scripts/database.py`,
  `scripts/pdf_import.py` and `admin/templates/admin/mapping_editor.html`.
- SQLite `PRAGMA quick_check`: `ok` in both environments.
- Beta: 3,076 configurations; staging: 2,912. Counts are a dated snapshot.
- Beta contains three data-driven mappings, not a missing-drafts incident:

| Mapping | Hardware ID | State | Current contents |
| --- | --- | --- | --- |
| VIRPIL CDT-AEROMAX R | 334444B0 | Published | 12 groups, 25 rows; retained initial mapping; no button anchors in current document |
| Thrustmaster SOL-R4 Stick | 044F0422 | Draft | 48 groups, 56 rows; image present; input and rendering review needed |
| Thrustmaster SOL-R4 Throttle | 044F0447 | Draft | 19 groups, 24 rows; image present; two rows have no input code |

The registry has 66 legacy controller entries, plus Keyboard. No legacy aliases
have been attached in the beta database. The seven new IDs listed below are not
in that registry. Staging contains the AEROMAX mapping only; controller data is
not automatically synchronized between environments.

Local `output/controller-drafts/` holds the generated VKB Space LH, STEM and ATEM
images, JSON and review sheets. These are local preparation files, not saved
beta mappings. Preserve them and Merc's existing beta drafts.

## Existing capabilities

The editor supports grouped hats, stamping, positioning, zoom, pan,
multi-selection, alignment, undo/redo, JSON import/export and local recovery.
Mapper accounts, draft/public revision separation, publication review,
optimistic concurrency, history and audit logging exist. Unknown-device review
can target both data-driven mappings and legacy controllers. PDF import supports
specific VIRPIL and VKB form conventions, not arbitrary fillable PDFs.

Historical P0/P1/P2/P4 completion means these features were implemented. It does
not certify every rendered controller card or the complete contributor workflow.

## Confirmed stabilization issues

1. **False TARGET warning.** `web.py` checks whether the matched Warthog registry
   entry contains `ThrustMasterWarthogCombined`. That entry also handles the
   physical stick and throttle, so a physical Warthog triggers the warning.
   Alicina's public `iapcqr` file has the physical stick and throttle and no
   Combined device. The previous explanation about stale Combined bindings was
   incorrect for this file. Check the actual input device, and use factual wording
   even when the virtual device is present. Existing stored warnings also need a
   defined refresh behavior when a configuration is reopened.
2. **Small boxes can produce invalid text dimensions.** The first SOL-R4 stick
   box is 193 x 40 px. The renderer reserves a fixed 40 px label header, then
   subtracts text padding. An isolated call to the deployed drawing function
   yields text height `-12`. Handle small valid boxes safely, bound font fitting,
   and make preview geometry agree with final rendering before publication.
3. **Directional axis codes do not match consistently.** SOL-R4 drafts contain
   `Neg_Joy_RYAxis`, `Pos_Joy_RYAxis` and RZ equivalents. The parser removes
   these prefixes from `physical_keys['Key']`, but the data-driven renderer
   compares that normalized key with the literal mapping code. Define consistent
   directional matching without losing the distinction between opposite actions.
4. **PDF rows move when only some directions are bound.** Generation filters
   unused rows before drawing a grouped `no_chrome` box. In a four-row test,
   binding only row 2 moves its text from y=206 to y=106. Manufacturer badges and
   lines remain baked into the background, so the action can appear beside the
   wrong direction. Retain original per-row field geometry for imported artwork.
5. **Incomplete mappings can silently omit commands.** Missing used inputs are
   logged after rendering, while the device is still marked handled. Review
   coverage with a real `.binds` before publishing and surface useful coverage
   information to reviewers. The preview endpoint currently renders the mapping
   without real user bindings; a draft needs a practical end-to-end preview.
6. **Invalid empty bindings enter the unknown queue.** The `None` entry attached
   to `x56hybrid44-4-2` comes from empty Primary/Secondary XML nodes without a
   Device attribute. It is not an unknown X56 hardware ID. Ignore such nodes at
   parsing time; any cleanup of historical queue data is a separate action.

The SOL-R4 stick also repeats five axis codes. Repeated labels may be deliberate,
so review with Merc rather than deleting or reassigning them automatically.

## New community evidence

Reviewed [Frontier page 23](https://forums.frontier.co.uk/threads/627609/page-23)
through the last visible post, #448, dated 2026-09-30. Private-message facts below
come from the screenshots supplied by Stephane; no mailbox was accessed.

| Contributor | Evidence | Next action |
| --- | --- | --- |
| Alicina | `.binds` reference `iapcqr`, USB VID 4098/PID BEF0, owner-confirmed yaw `Joy_RZAxis`, right pedal `Joy_RXAxis`, left pedal `Joy_RYAxis` | Prepare a complete three-axis Orion draft and real-bind preview. Ask her to confirm physical left/right placement. No need to request her existing file again. |
| Sans Frontieres | Post #446 confirms `231D0125` = Gunfighter MCG Ultimate XT2 v2.20C; `231D0139` = STECS SPACE-L MAX STEM XT2 v2.20C; customized setup; fresh `.binds` and five VKBDevCfg screenshots accessible | Use the screenshots to decode physical inputs. Treat customized configuration explicitly; do not blindly alias either ID to existing STECS artwork. |
| TyWuNon | Owns STECS Space Mini Left-Hand; cannot attach files/screenshots/URLs in the forum MP | Offer the email address already provided by Stephane, or an unlisted beta upload and its reference URL. Do not require a fully bound profile. |
| Zach Drachenherz | SOL-R HOSAS artwork comes from Scythia-1's Google Drawing; promised `.binds` later | Retain source credit; request adaptation permission from the original author if reusing the artwork. Confirm L/R numbering from a real owner before publishing. |
| Martyn_Skytech | Post #447, reference `nealnn`, actual `.binds` IDs `10F57150` and `10F57154`, three official fillable Turtle Beach PDFs | Confirm stick/throttle correspondence; written IDs `E8BC1` and `AA52D` differ from the game's IDs. A dedicated PDF adapter is required. |
| RahmBro | Post #448, reference `keogws`, actual `.binds` IDs `334440CC` and `33440194`, ALPHA R and T-50CM3 hardware, new VIRPIL software | Compare button/axis numbering with existing templates and manufacturer sheets. These are alias candidates, not verified aliases yet. |

Alicina's current file uses RZ for `YawAxisRaw`, `SteeringAxis` and
`HumanoidRotateAxis`. The absent RX/RY bindings do not mean the brakes are absent;
their codes are now confirmed by the owner. The [official product page](https://winctrl.com/view/goods-details.html?id=546)
has clean 1600 x 1600 product images and larger detail images. There is enough
evidence to start without waiting for more correspondence.

The [SOL-R Reddit post](https://www.reddit.com/r/starcitizen/comments/1kd2f6k/share_my_editable_hosas_bind_sheet_for/)
links to an accessible [Google Drawing](https://docs.google.com/drawings/d/1ixPq9XD2CthwENaWs2aGavdwGxIzxGUjpLZ4S9ImrJ0/edit).
It is editable by copying, with original author credit. The author mentions using
both sticks in right-hand mode and Joystick Gremlin for some behavior. Its drawing
is therefore a layout reference, not proof of default Elite input numbering.

Public supporting files:

- [VKB current bindings](https://forums.frontier.co.uk/attachments/hcs-custom-4-2-binds-txt.468272/)
- [VKB external configuration](https://forums.frontier.co.uk/attachments/vkb-stecs-external-png.468273/)
- [VKB STECS axes](https://forums.frontier.co.uk/attachments/vkb-stecs-axis-png.468274/)
- [VKB STECS buttons](https://forums.frontier.co.uk/attachments/vkb-stecs-buttons-png.468275/)
- [VKB Gunfighter axes](https://forums.frontier.co.uk/attachments/vkb-gunfighter-axis-png.468276/)
- [VKB Gunfighter buttons](https://forums.frontier.co.uk/attachments/vkb-gunfighter-buttons-png.468277/)
- [Turtle Beach bindings](https://forums.frontier.co.uk/attachments/custom-4-2-txt.468475/)
- [VIRPIL bindings](https://forums.frontier.co.uk/attachments/rahmbrovpc-4-2-txt.468657/)

Turtle Beach forms were inspected in memory on staging: HOTAS 92 fields,
Flightstick II 49 fields, Dual Throttle 44 fields. All three fail the current
importer with "No fillable description fields found" despite being AcroForms.

## Bounded delivery plan

### Lot 1 Reliable rendering and review

Fix the six stabilization issues above, with representative tests rather than a
new editor redesign. Check manufacturer row positions, small/dense groups,
partial hats, axis directions, modifiers, None/Group/Category/Modifier styling,
and output PDF in A4 and Letter. Reviewers must be able to inspect real actions
from a `.binds` against a draft before making it public.

Acceptance: upload, saved-card reopening and API agree; unused inputs cause no
wrong labels or lost used commands; pathological dimensions terminate safely;
saving a draft preserves the published card and its image.

### Lot 2 Finish controller pilots

Finish Orion pedals first: three known axes and a clean image make this a small,
fully reviewable controller. Then review Merc's existing SOL-R4 drafts and validate
one STECS Space configuration using the owner screenshots and imported artwork.
Compare RahmBro's IDs for low-effort aliases in parallel. Keep Turtle Beach as a
separate adapter task after the rendering fixes.

Acceptance: a reusable controller template covers the physical inputs confirmed
by documentation/owners; it does not store one user's game commands as its model.
Unbound controls remain supported for other users. Hats stay grouped. Each pilot
is checked with a real owner profile and a synthetic coverage/density profile.

### Lot 3 Release checks and documentation

Run the full contributor path: identify device, create/import, verify input codes,
preview real binds, save draft, reopen/recover, review, publish, generate card,
reopen and export PDF. Validate representative legacy controllers as well.
Update the English mapper guide to the actual workflow and show final staging
renders to Stephane before promoting approved changes to beta.

The stable delivery consists of this verified workflow and validated pilots.
The 20+ additional controller requests remain a contribution backlog, not a
requirement to keep rewriting the editor indefinitely. CSP nonces, vision AI,
general legacy migration and multi-device composition remain outside this lot.

## Verification limits and preservation

All 24 current tests passed against the deployed staging code on 2026-10-03,
including four PDF import tests. The local run passed 20 and skipped four because
local PyMuPDF is unavailable. The coordinate probes above execute the deployed
drawing function with a recording text-layout stub; they verify calculated
rectangles, not final visual quality. Full real-card/PDF visual checks remain in
Lot 1 and Lot 3.

The initial investigation did not publish, attach, delete or modify any live mapping or
configuration. No code fix or deployment was performed during that investigation. Preserve beta/staging
data independently, mapper contributions, version history and uploaded images.
Commits belong to LibreArbitre only. No subagents. Product and admin UI remain in
English. Do not infer device ownership or an alias from a configuration filename.

## Implementation checkpoint October 3 2026

The first implementation batch was tested locally and then deployed to staging
on October 3. It has not been promoted to beta:

- Detection now checks the actual virtual Warthog device, and old TARGET notices
  are recomputed when the .binds source is available. Empty XML nodes are ignored.
- Each parsed action retains its raw input key. Half-axis rows filter the correct
  direction while legacy full-axis rows retain aggregated behavior.
- Small boxes use proportional headers and gutters. Font fitting has a minimum
  size and a bounded search; impossible fits fail with a useful message.
- Imported artwork retains unused row slots. New VKB imports retain relative
  field rectangles, including gaps and side-by-side fields. Existing imports
  without that metadata keep their original row count; irregular original field
  geometry still needs review against the source PDF.
- Real generation never substitutes stored example actions for unassigned rows.
- Modifier-only inputs are rendered and included in coverage reports.
- Preview accepts a saved configuration reference, renders its real commands
  without saving a draft/publication, reports missing inputs, and uses unique
  output files to avoid concurrent mapper collisions. The endpoint accepts an
  optional device_index; the UI currently previews the first matching instance.
- Public generation, reopening and API use the same coverage checks. Coverage
  warnings are surfaced, and regenerated notices replace their previous version.
- Canvas row/header geometry and legacy symbol glyphs agree more closely with
  the renderer. The English guide no longer promises a fixed completion time or
  assumes mirrored hardware uses the same numbering.

Verification against scratch copies in the staging runtime: 38 tests passed,
zero skips; real Wand rendering covered dense commands, modifiers, all four
styles, isolated preview requests, concurrent output names and input errors.
Synthetic profiles also rendered successfully on the legacy Warthog, X56 and
TCA-left templates, with no false TARGET warning.
The existing PDF export helper generated A4 and Letter pages, reopened with
PyMuPDF and visually inspected. The browser fixture passed 17 checks including
preview coverage, undo/redo, local recovery, save conflicts and network failures.
All browser requests were intercepted; no mapper data was modified.

Desktop fixture checked at 1440 x 1000, without horizontal overflow. At 390 x
844 the editor still overflows horizontally. Mobile layout is a known separate
limitation, not a passed check. Real-controller visual approval, authenticated
staging integration, broader legacy visual checks and promotion remain
to be done. This checkpoint does not declare Lot 1 or the project fully released.

Community replies are drafted in [Community reply drafts](COMMUNITY_REPLIES_2026_10_03.md),
including both private messages. Nothing has been sent to the forum or by email.

## Authenticated staging validation October 3

The deployed core changes match commit `a50a993` by SHA256 for the editor,
renderer and web routes. The current staging compose is `9u4MIXvnm49dpxCsfhM66`
on Dokploy2, using branch `dev` and domain `edrefcard2-dev.l0l.fr`.

A SQLite backup was retained on the VPS at
`/var/tmp/edrefcard-before-stabilization-1791033482.sqlite` before deployment.
The original mapping row hash remained
`0216d96f08ff950594573e683ee2d20ff49d4533924db19b3e7bf0e5e5a54c05`.
The configuration catalogue stayed at 2,912 records. No beta deployment or data
modification was performed.

Authenticated HTTPS requests against the deployed app verified:

- The editor serves the new reference and coverage controls.
- A real owner's profile renders correctly, with missing-input coverage.
- Simultaneous preview names differ; preview does not save or publish a mapping.
- All four styling modes render successfully.
- Missing source returns 404; invalid references, traversal, wrong hardware and
  nonexistent device instances return 400.
- An intentionally incomplete mapping reports `Joy_RZAxis` as missing.
- An outdated draft save returns 409, preserving the newer version.

### Orion pilot draft

Staging draft ID `11` represents WINCTRL Orion Rudder Pedals, hardware
`4098BEF0`. The source image is the clean 1600-square manufacturer photograph
from the [Orion product page](https://winctrl.com/view/goods-details.html?id=546),
uploaded with the existing side-margins helper to make a 4800 x 1600 canvas.
No photo retouching or AI generation was used.

The owner's September 22 message confirms yaw `Joy_RZAxis`, right toe brake
`Joy_RXAxis`, and left toe brake `Joy_RYAxis`. All three axes are present in
the template. Her actual public `iapcqr` source uses yaw only, so both brake
groups disappear in the real-profile preview. A separate synthetic profile
checks all three groups; its Pitch/Roll commands are test labels, not the owner's
bindings or recommended pedal assignments.

The validation sources are filesystem-only staging fixtures, not public
catalogue entries: `orion-owner-validation-20261003` and
`orion-three-axis-validation-20261003`.

[Open the staging draft](https://edrefcard2-dev.l0l.fr/admin/mapping-editor?device=4098BEF0&from=orion-owner-validation-20261003).
Owner validation and visual approval are still required before publication.

Live image review also revealed an HTTP printed origin behind Traefik. The
follow-up gives the explicitly configured external `APP_URL` priority over
the proxy's internal request scheme. Three regression tests cover configured
origins and both unconfigured fallbacks.

The browser view of the generated Orion images was inspected at 1440 x 1000.
The authenticated endpoint checks are actual HTTPS requests. The 17 editor
interaction checks described above remain isolated browser-fixture tests;
they are not a claim that a full authenticated browser journey was executed.
Mobile editor overflow remains known and outside this batch.

## Beta promotion October 3

Stéphane requested beta evaluation, so the tested changes through `bf425e2`
were fast-forwarded from `dev` to `main` and deployed through Dokploy compose
`t9mEDDtK0_JFCQX1XR2oo`. The editor and models SHA256 hashes match the tested
source. Authenticated HTTPS requests confirm the new preview controls are served.

Before deployment, a SQLite backup was retained outside the container at
`/var/tmp/edrefcard-beta-before-befac61bf0a845bca307fcf07d62eefa.sqlite`.
The beta had 3,076 configurations and three existing controller mappings.
Those three mapping rows were verified byte-for-byte unchanged after adding
Orion. The configuration catalogue was not replaced or populated with tests.

Orion is beta draft ID `4`, not published support. Only its clean image, mapping
and two filesystem-only review sources were transferred from staging. No
database, mapper account, other contribution or version history was copied
between environments.

- [Orion beta editor](https://beta.edrefcard.info/admin/mapping-editor?device=4098BEF0&from=orion-owner-validation-20261003)
- [Owner profile preview](https://beta.edrefcard.info/configs/dd/ddpreview-324de2a55ba74678a887d16ae3c4d97e-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)
- [Three-axis synthetic preview](https://beta.edrefcard.info/configs/dd/ddpreview-f2b620ffe5024ae2b78cc92b03577a76-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)

Both previews report no missing used inputs. The real image was also opened
and visually checked in the browser on the beta domain. Synthetic Pitch/Roll
labels remain test data, not Alicina's assignments. Owner/visual approval is
still needed before publishing the Orion template.

## STECS Mini delivery October 16

The [STECS Space Mini Left-Hand](controllers/VKB_STECS_SPACE_MINI_LH.md)
is published on beta for hardware `231D0136`, after TyWuNon confirmed his
setup and axes. The card covers 29 logical buttons and five enabled axis codes.
Axes stay in a global block: RY is virtual in this profile and no unconfirmed
physical sensor placement is asserted. This does not publish support for the
different Max/STEM ID `231D0139`.

The final card uses a clean manufacturer photograph with larger generated
frames, replacing the fixed-height worksheet. All 56 displayed commands in
the owner's profile retain the maximum 40 px body font. A4 and Letter exports
were reopened, rasterized and visually checked. All 26 used input codes are
covered; a synthetic inventory fixture also renders all 34 template inputs.

Commit `aaa06cd` fixes missing command-style fallback discovered in the Category
rendering test. The 44 Python tests pass without skips in the server runtime,
and real-Wand/Flask integration checks pass, including legacy cards and PDF
exports. Staging and beta renderer hashes match the tested commit. The
published web/API helper renders the real profile in all four styles without
a coverage warning, and the public device catalogue lists the new controller.

The four other mapping rows are unchanged, including Merc's drafts and Orion.
The configuration catalogue retains all 3,098 records; no test catalogue record
was created. A pre-change database backup and final review artifacts are
preserved outside the container. The private owner XML remains non-web-served.

Next controller work remains Orion owner/visual sign-off, Merc's SOL-R4 drafts,
and a separate review of STECS Max/STEM. This checkpoint completes the Mini
pilot, not the entire controller backlog or the mobile editor work.

## Compact generated frames promoted October 16

After visual approval, commit `fa80c95` was promoted from `dev` to `main` and
deployed on beta. Generated controller rows now use content-based heights and
consistent padding, bounded by the editor's reserved dimensions. Sparse groups
shrink instead of stretching their remaining rows. Digital hats stay grouped.
Imported PDF artwork slots and the legacy renderer remain unchanged.

All 50 Python tests pass without skips in the beta runtime. The deployed
renderer hash matches staging and the tested commit. An authenticated HTTPS
preview verifies the compact frame in the actual output pixels. Ty's profile
renders in all four styles with 26 used inputs covered and all 56 command
labels at 40 px. BASE measures 160 px; SPEED LIM row heights are 60/180/180 px.
The compact A4 and Letter exports were reopened and visually inspected.

All five mapping rows and the 3,098 pre-existing configurations are preserved;
the pre-promotion backup is retained outside the container. The controller
evidence and current review links are in the STECS Mini delivery note.

The PDF cache follow-up identified here is resolved by the reliability release
below. Historical configurations are retained; no bulk PDF deletion is needed.

## Backup and PDF reliability October 16

Commits `fb0a31e` and `afd3252` are deployed on staging and beta. New version 2
backup archives include controller source images alongside the database by
default. A bindings-only backup or restore remains bindings-only. The database
is captured with SQLite's online backup API, including committed WAL data.
Generated card images and PDFs remain regenerable and are not archived.

New local archives live in the persistent configs volume's `.backups` folder.
Remaining archives in the previous application data folder stay accessible.
Archive names are unique even within the same second. A failed safety backup
aborts restoration, and database reconnection failures are not reported as
successful restores. Older archives without controller images remain readable
without deleting existing assets. Image restoration rejects traversal and
link entries and replaces individual images atomically.

PDF caches embed a SHA256 signature of the ordered source image names and
contents. Changed, added or removed sources invalidate the cache even when
timestamps are preserved. Untouched content reuses it. Legacy or damaged caches
are regenerated on access. Exports use stable image-byte snapshots and atomic
PDF replacement; a failed image or write does not overwrite the last good PDF
with a partial export. Keyboard pages remain last.

All 68 Python tests pass with the server dependencies. Staging and beta code
hashes match the tested files. Actual HTTPS requests verify A4 and Letter cache
reuse and invalidation, and the owner-profile exports were reopened and visually
checked. A new full beta archive was restored only into an isolated folder:
3,099 configuration records, 3,078 bindings files and 12 source images. Restored
images are byte-identical. The five live mappings and live maintenance state
remain unchanged. Authenticated archive download returns 200; unauthenticated
access through the public configs route is denied.

Run administrative CLI backup jobs as the container's `appuser`, matching the
web workers, so private archive ownership remains compatible with downloads.
The final production archive and restoration check were repeated under that
account. The archive is retained on the persistent volume with an additional
private copy outside the container. This release does not claim a new off-site
SFTP transfer or a live database restoration.

## Orion readiness review October 16

Stephane confirmed a feature freeze: finish and validate existing work before
adding editor capabilities. Review of the beta database confirms Orion remains
draft ID 4, hardware `4098BEF0`, with no published snapshot. All five saved mapping
rows remained unchanged during this review.

The three owner-confirmed axes are present: yaw RZ, left toe brake RY and right
toe brake RX. Both validation sources remain available. However, the stored
draft still places yaw at the upper left and the left brake at the lower left;
the previously requested visual swap was not saved. A candidate preview moves
the left brake to the upper left and yaw to the lower left, leaving the right
brake at the lower right. It does not save or publish that candidate.

- [Candidate three-axis layout](https://beta.edrefcard.info/configs/dd/ddpreview-18e1d06085274e3383fc5e0e77f0cddc-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)
- [Candidate with Alicina's actual bindings](https://beta.edrefcard.info/configs/dd/ddpreview-3cd0e68e74f441f9a8c7c269db851d1a-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)

Actual authenticated HTTPS previews passed for the owner's profile in all four
styles and for the three-axis synthetic profile, with no missing used inputs.
Her profile uses RZ only, so the brake boxes correctly disappear. On-foot Turn
shares Yaw's input and is intentionally suppressed by the existing HideIfSameAs
rule, not lost through an incomplete mapping. A4 and Letter exports of the
candidate owner preview were reopened, rasterized and visually inspected.

Remaining gates: Stephane approves the candidate placement, save that placement
through the normal draft workflow, obtain Alicina's confirmation of the pedal
callouts, then authorize publication and verify public generation. No new file
or fully bound profile is needed from her. No deployment or mapping publication
was performed during this review.

### Orion aligned preview October 17

Stephane rejected the October 16 elbow-line candidate. The replacement aligns
each one-row box center with its existing physical anchor and uses equal-size
850 x 80 px frames. Preview and compact owner renders have straight horizontal
leaders. The four owner styling previews and the three-axis synthetic preview
report no missing used inputs. All five saved mappings remain unchanged.

- [Replacement three-axis layout](https://beta.edrefcard.info/configs/dd/ddpreview-036c132060454bb78dcf20d44c70696d-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)
- [Replacement owner preview](https://beta.edrefcard.info/configs/dd/ddpreview-0662ea6b21f44188b50e811583cdd522-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)

This is an unsaved visual candidate, not a published template. Final geometry
still needs visual approval and a dense-axis profile check before saving.

### Approved Orion placement saved October 17

After Stephane's explicit visual approval, the aligned candidate was saved to
beta draft ID 4 through the authenticated editor save route with optimistic
concurrency. A SQLite online snapshot was retained privately outside the
container. The other four mappings remain byte-for-byte unchanged; Orion is
still a draft without a published snapshot. Reopening the editor and previewing
the saved document succeed, with no missing used inputs in Alicina's profile.

The actual owner render retains 40 px command text. A synthetic test with six
independent contexts on each of the three axes renders all 18 labels without
clipping or omission, using 23 px text. That denser case is readable at native
resolution but is not equivalent to the owner's 40 px output. Neither the
synthetic bindings nor an example game assignment was saved in the template.

- [Saved owner-profile preview](https://beta.edrefcard.info/configs/dd/ddpreview-1263a383f4054059b15737729bdec831-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)
- [Approved three-axis diagram](https://beta.edrefcard.info/configs/dd/ddpreview-036c132060454bb78dcf20d44c70696d-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)

Next gate: Alicina confirms the physical callout locations, then authorize
publication and check public generation. No application deployment was needed.

## Public forum evidence refreshed October 17

Read all 12 posts on page 23 (#441-452); it is currently the last page and the
latest visible post is dated October 10. Earlier evidence through #448 remains
valid. The October 3 progress update is posted as #449. Merc's #450 comment
about a semicolon in the beta hyperlink is already resolved in the live #449
link; the old quoted link in his reply is not the current hyperlink.

Two additional actionable controller dossiers were inspected, including their
actual downloadable XML and original image attachments. No mapping was created,
attached or published, and no forum reply was sent during this inspection.

### BigJ: VIRPIL VMAX Prime Throttle

- [Post #451](https://forums.frontier.co.uk/threads/627609/post-10899893), October 5.
- [Device identity screenshot](https://forums.frontier.co.uk/attachments/1791154555484-png.469106/)
  explicitly shows L-VPC VMAX Prime Throttle, VID 3344, PID 8196. It also shows
  R-VPC Stick WarBRD-D, VID 3344, PID 43F5; that identifies the base, not its grip.
- [Actual bindings](https://forums.frontier.co.uk/attachments/custom-4-2-binds-txt.469108/)
  parse successfully and contain `33448196` and `334443F5`, plus GamePad.
  The throttle uses 30 distinct input codes, including X, Y and RX axes. This
  is usage in this file, not an exhaustive hardware inventory.
- [Numbered controller worksheet](https://forums.frontier.co.uk/attachments/vmax-prime-throttle-button-mapping-jpg.469110/)
  is a 4000 x 2823 JPEG. It depicts grouped hats, axes, and the A-F controls
  in both five-way shift-modifier and no-shift configurations. Establish which
  logical configuration the owner uses before claiming a universal mapping.
- XML SHA256: `53f1a7d53734ffd50d73cf04d0807ff5782e4451fae5c77580b80f9f7b8707fb`.
- Next: acknowledge the supplied files, confirm any VPC logical remapping and
  shift-selector configuration, then prepare/review a template when this dossier
  reaches the controller queue. Do not ask for the same bindings or IDs again.

### Judder Man: WINCTRL URSA MINOR Combat Throttle Metal.EX 1.0

- [Post #452](https://forums.frontier.co.uk/threads/627609/post-10903289), October 10.
- [Actual bindings](https://forums.frontier.co.uk/attachments/custom-4-2-binds-txt.469731/)
  parse successfully. `4098BC2A` matches the existing URSA MINOR Fighter Right
  legacy entry; `4098B970` is the distinct throttle and has no current template.
- The throttle uses 19 distinct input codes: 16 buttons and three axes (Z, RX,
  RZ). These are the used subset, not the controller's full inventory.
- Three configuration screenshots show physical numbering, including the
  button bank, hats, axes, switches, encoder and controls up to button 77:
  [first view](https://forums.frontier.co.uk/attachments/screenshot-2026-10-10-074426-png.469725/),
  [second view](https://forums.frontier.co.uk/attachments/screenshot-2026-10-10-074448-png.469726/),
  [third view](https://forums.frontier.co.uk/attachments/screenshot-2026-10-10-074504-png.469727/).
- XML SHA256: `4423bdf1b2df502447da602d8b14b148abf563744e97b478891a9498f7a7439a`.
- Next: acknowledge that the stick is covered but the throttle is separate.
  Confirm custom logical remapping, if any; begin with supplied screenshots and
  the normal profile rather than requesting a fully bound file.

User reports that the latest Orion preview message has been sent to Alicina,
and the request for Modern Standard details has been sent to vishnus by private
message. Neither reply has arrived in this conversation yet. Preserve the
feature freeze: finish existing pilots and workflow verification before adding
editor capabilities. These new files expand the contribution queue, not the
release acceptance scope.

## Merc SOL-R4 draft review October 17

Read-only review of beta mapping IDs 2 and 3 confirms both remain drafts with
no published snapshots, last updated by Merc on July 9 and July 7 respectively.
There are no saved version rows for these older drafts. Both source images are
present and match their declared dimensions. All five saved mappings remained
byte-for-byte unchanged throughout the review. No publication, attachment,
draft save or application deployment was performed.

### Confirmed defects

- Stick: 48 groups, 56 rows, 51 distinct non-empty codes. Five full axes are
  each repeated twice (X, Y, Z, RX, RZ). Real rendering confirms identical
  command lists appear twice; the Analogue/Digital row type does not make
  these full-axis keys direction-specific. RY is represented only by its two
  half-axis codes, so a normal full RY binding is not covered.
- Stick: 11 public compatible source profiles were parsed. Only the two recent
  sol-r profiles have no missing used inputs. The other nine use POV directions
  absent from the draft; four also use full RY. These are anonymous compatible
  profiles, not proof that Merc owns any particular source.
- Stick: the two recent real profiles render without an exception, but their
  smallest command font is 6 px; some trigger and multi-context blocks are not
  acceptably readable. The URL overlaps upper boxes, many leaders cross, and
  the lower portion of the canvas is largely unused.
- Throttle: 19 groups, 24 rows, 22 distinct non-empty codes. Two rows have empty
  joy values (groups labelled Joy_ZAxis and AXIS). The first omission causes
  actual throttle-axis commands to disappear from all three available public
  compatible profiles. Their used-input coverage reports missing Joy_ZAxis.
- Throttle: the first two POV rows pair Joy_POV1Down with an up symbol and
  Joy_POV1Up with a down symbol. The code/symbol inconsistency is confirmed;
  final physical orientation is part of owner review.
- Throttle: only negative and positive RZ are mapped. A full analogue RZ use
  case is uncovered. A full-axis synthetic test reproduces that limitation.
  Existing real-profile fonts shrink to 11 px; a two-axis group is only 45 px
  high and some boxes obscure the product image.

### Manufacturer checks

The official [flightstick manual](https://ts.thrustmaster.com/download/accessories/Manuals/SOL-R/Sol-R_FlightStick_user-manual_21L.pdf)
was read with pypdf and its printed mapping pages 20-22 rendered with Poppler
and visually inspected. It documents right/left modes and POV enabled/disabled
variants. Preserve that distinction rather than assuming one hat numbering
mode covers every owner. Base controls, physical hat/button groups and the
existing clean image/anchors can be reused.

The official [SOL-R 6 throttle manual](https://ts.thrustmaster.com/download/accessories/Manuals/SOL-R/Sol-R_6_Throttle_user-manual.pdf),
printed mapping page 14, confirms the main Z throttle, X/Y mini-stick, RZ rocker,
Slider 0 antenna control, POV and buttons. The remaining empty field appears to
target the antenna knob. Its actual Elite input code still needs confirmation:
Joy_UAxis was used as a diagnostic hypothesis, not established as fact from
the current owner files, which do not bind it.

### Review artifacts and next action

- [Current stick with real bindings](https://beta.edrefcard.info/configs/dd/ddpreview-solr-review-2-689785ca2ca34bcd8929020e23c7ad90-sol-r4.jpg)
- [Current throttle with real bindings](https://beta.edrefcard.info/configs/dd/ddpreview-solr-review-3-20e57c4dac3a4e369fbbf253871c8c3d-sol-r4-throttle.jpg)

The generated diagnostic report and original source snapshots are retained
locally outside tracked source. Synthetic inventory outputs are not public
catalogue records and do not recommend any game assignments.

Recommendation: prepare unsaved corrected template candidates using Merc's
images and physical anchors; restore the main throttle input, make full/half
axis handling unambiguous, support documented hat modes, group physical hats
and enlarge/reposition frames for real command density. Review candidates with
Stephane before asking Merc to confirm hardware-specific details. Do not
overwrite his drafts or add editor features under this review authorization.

## Separate SOL-R candidates prepared October 17

With Stephane's approval to prepare previews, two corrected candidates were
built separately from Merc's database rows. No draft save, publication, alias
attachment, source-image overwrite or application deployment occurred. All
five saved mappings and both original image hashes remain unchanged.

The stick candidate groups the existing physical banks, hats, encoder,
selector and grip controls: 17 groups and 54 unique input rows, including full
RY and four POV directions. It is explicitly a right-handed grip candidate;
it does not promise correct physical placement for the left-handed mode.
Repeated full-axis rows were collapsed so actions are not printed twice.

The throttle candidate has nine groups and 22 known input rows. Main throttle
Z is restored, the POV arrows match their direction codes, the physical hats
are grouped and the full RZ row covers full-axis and half-axis uses. This
aggregation retains all commands but needs owner review for direction clarity.
The antenna knob is deliberately not assigned a guessed code. A visible review
note flags the remaining unknown input instead of implying exhaustive support.

Original photos were only cropped, scaled and repositioned on separate review
canvases, without retouching or AI generation. Original anchors were transformed
with the photos; grouped controls use the centroid of their existing anchors.
Candidate JSON retains original source-group indices and anchor coordinates
for traceability. These physical locations are inherited evidence, not newly
owner-validated positions.

Twenty-two actual engine renders pass: all 11 public stick profiles and three
public throttle profiles in Group style; the latest common profile additionally
in None, Category and Modifier for each controller; and both synthetic input
inventories. There are no missing used inputs. Captured rendered commands
match the expected per-input command multiset, including modifiers, without
introduced duplication or loss. All rendered command text remains 40 px,
including the dense 135-label stick profile. Normal specialization suppression
is retained. Main and dense output images were visually inspected.

- [Stick candidate with real bindings](https://beta.edrefcard.info/configs/dd/ddpreview-solr-candidate-2-b7c9bc4a2dbb41e7adf2a298bd97e8b0-solr-candidate-2-69222327c8574c37b6e2455d08cfcbd8.jpg)
- [Throttle candidate with real bindings](https://beta.edrefcard.info/configs/dd/ddpreview-solr-candidate-3-42e42154733e40ff851d36c0e0a884f7-solr-candidate-3-836fe769094a4db3a8cd7e409712b85d.jpg)
- [Dense stick profile](https://beta.edrefcard.info/configs/dd/ddpreview-solr-candidate-2-1918370183174b3bb56ee0e4748be8df-solr-candidate-2-69222327c8574c37b6e2455d08cfcbd8.jpg)

Candidate sources, JSON, original JSON snapshots and results are retained
locally outside tracked source and privately outside the container. Only the
anonymous generated JPEG previews are served on beta. They are not catalogue
configuration entries or editable registered mappings. No new PDF export or
authenticated editor-flow validation is claimed for these candidates yet.

Next: Stephane reviews the two visual candidates, then prepare Merc's focused
validation message covering inherited physical callouts, right-handed/POV mode,
trigger behavior, axis direction clarity and the antenna's actual Elite code.
Do not overwrite Merc's drafts or publish on the basis of preview tests alone.

## SOL-R leader and endpoint review October 17

Stephane requested fewer crossing leaders and more visible endpoints. Separate
preview candidates now order frames by the vertical positions of their physical
anchors. Leaders start at the actual compact frame edge, use a diagonal section
and a short horizontal approach to the control. The preview stroke is 7 px red
over a 13 px white halo; each hardware endpoint has a red 15 px-radius marker
with a 5 px white outline. The separate top view of the stick base is retained.

All 22 rendering checks pass again: used-input coverage and command multisets
are unchanged, with command text at 40 px. Geometric checks find no proper
leader intersections or leader crossings through other frame edges in these
outputs. These checks do not establish a general-purpose collision-free layout
algorithm for arbitrary mappings. Main stick, throttle and dense stick images
were visually inspected after rendering.

- [Revised stick preview](https://beta.edrefcard.info/configs/dd/ddpreview-solr-candidate-2-4f13f665284943568a1bcf4f18934748-solr-candidate-2-026dbcff521b486c8fa35e7752a233bb.jpg)
- [Revised throttle preview](https://beta.edrefcard.info/configs/dd/ddpreview-solr-candidate-3-3b1b2f6663ef4abc90ab865f7dcddfe1-solr-candidate-3-7a0a0348f09b4d36923d1885f71b4bc5.jpg)
- [Revised dense stick preview](https://beta.edrefcard.info/configs/dd/ddpreview-solr-candidate-2-45f8b88487fa44ec8521ca9bac48e20d-solr-candidate-2-026dbcff521b486c8fa35e7752a233bb.jpg)

The routing and drawing override runs only in an isolated diagnostic process.
The installed renderer, all saved mappings and both original image files remain
unchanged. Candidate sources and results are retained privately outside the
container and locally outside tracked source. No publication or application
deployment occurred. Await Stephane's visual approval before integrating the
leader style into the application; Merc's hardware review remains necessary.

## Shared leader style integrated and staging verified October 17

Stephane approved the revised previews and explicitly approved generalizing
the thicker leaders and outlined hardware endpoints to data-driven cards.
Commit `5dd9c27` adds the same 7 px red stroke, 13 px white halo and red endpoint
with a 5 px white outline to the shared drawing function. Existing per-controller
frame positions, anchors and elbow routes are retained. This is not a global
auto-layout change. The SOL-R diagonal routing and revised source canvases are
still separate review candidates, not saved mappings.

Legacy artwork and imported `no_chrome` PDF fields are untouched. Mappings
without anchors remain pixel-identical. Existing downloaded images are not
rewritten in bulk; the new style appears when a card or preview is rendered
again. Existing source-sensitive PDF caching handles changed generated images.

Verification:

- All 71 unit tests pass in the staging runtime, with no skipped tests.
- Real-Wand/Flask integration passes: anchored previews, four styles, coverage,
  dense modifiers, three legacy templates, input errors and A4/Letter exports.
- Twenty before/after renders cover all five saved controllers in four styles,
  using real bindings. The private owner fixture is used for STECS and is never
  added to Git or the public catalogue. Every text command, font size and text
  position matches before/after. AEROMAX, which has no stored anchors, remains
  byte-identical. All saved mapping rows remain unchanged.
- Orion and STECS output images were visually inspected.
- Staging deployment is verified by the exact installed renderer SHA256 and an
  authenticated HTTP preview whose served JPEG contains the expected endpoint
  pixel. Mapping rows remain unchanged and SQLite quick_check returns ok.

Beta promotion is the next step under Stephane's visual approval. No mapper
draft or controller publication is part of this renderer-only release.

## Shared leader style delivered to beta October 17

Main and dev were aligned at `806494a` for delivery; the rendering change is
`5dd9c27`. Dokploy beta deployment completed and the installed renderer SHA256
matches staging and the reviewed source. An authenticated preview request to
beta produced a served JPEG with the expected red endpoint at its actual
anchor, verifying the live request path rather than only an HTTP 200 or build
status. All 71 unit tests and the real-Wand/Flask/PDF integration suite pass
again in the delivered beta runtime.

A coherent pre-deployment SQLite snapshot was preserved privately outside the
container. Post-deployment checks confirm all 3,100 existing configuration IDs
are still present, all five mapping rows match their pre-deployment hash, all
12 controller source assets match their hashes, and SQLite quick_check is ok.
No controller draft was saved or published in this release. The separate SOL-R
layout candidates still await hardware review before replacing Merc's drafts.

The release applies the visibility style on subsequent data-driven renders, not
as a bulk rewrite of saved JPEGs or previously downloaded files. Legacy artwork
and no_chrome imported PDF artwork retain their original lines and markers.

## Blocking CI and real contributor journey October 17

Commit `c2be23f` replaces the best-effort Python test step with blocking Python,
real-Wand/PDF and authenticated browser workflow checks. Container build and
startup remain blocking in their own job. Legacy Ruff/Mypy debt is explicitly
advisory in a separate job, not silently treated as a clean codebase. Existing
GitHub branch protection and merge permissions were not changed.

[GitHub Actions run 39054468836](https://github.com/LibreArbitre/edrefcard2/actions/runs/39054468836)
passed all three jobs. Evidence includes 71 Python tests plus 15 subtests with
no skips/failures, real rendering and A4/Letter integration, and 25 browser
workflow assertions. The CI produced screenshots, synthetic PDFs and machine-
readable results; selected desktop screenshots and the PDF raster were visually
inspected. Browser JavaScript errors and application HTTP 5xx counts are zero.

The browser journey uses real sessions, pages, routes, SQLite and generated
images. It covers mapper creation/permissions, photo upload, scaffold, anchors,
real-bind preview, save/reopen, local recovery, stale-tab conflict, publication,
replacement-photo draft isolation, rollback as a new draft, republication,
fresh web upload, API generation and saved-card reopening. Public JPEG hashes
are compared before/after draft edits and rollback to prove publication isolation.
No application responses are intercepted or successful saves mocked.

An independent scratch copy of the application was also exercised using the
staging runtime through a private SSH tunnel. The live staging database contains
none of the synthetic users, hardware IDs or profile records and quick_check is
ok. The disposable server and tunnel were stopped after testing. The fixture
overrides inherited credentials, database location and scheduler mode; generated
test credentials stay outside source and uploaded CI artifacts. The browser
checks a per-instance nonce before making its first write.

Reproduction commands and limits are documented in [Testing](TESTING.md).
This certifies the tested desktop Chromium flow, not mobile editor layout,
every device variant, HTTPS cookie behavior or multi-worker scaling. Hardware
owner sign-off remains necessary for Orion and the separate SOL-R candidates.
No new user feature, beta data change or application deployment is needed for
this test-only batch.

## Bounded static-debt and reliability lot October 17

Commit `ccaacd6` fixes two concrete defects without changing the editor workflow:

- An unexpected preview-rendering failure used an unimported `logError`, masking
  the intended JSON error response with a second exception. The real authenticated
  workflow now checks a missing image and its expected HTTP 500 JSON response.
- The shared font fitter checked individual command width only for the first
  command on a line. A later overlong command could wrap but still overflow its
  box. Every command is now checked at each candidate size. A regression test
  failed before the fix, and an additional real-Wand metrics check passes.

PDF worksheet fields, scaffold grouping and recent-error types are made explicit;
an optional database filter is narrowed once. These changes preserve stored JSON
formats and runtime behavior. The same-runtime full Mypy comparison falls from
174 to 119 diagnostics, with no new ignores. GitHub's different dependency set
reports 120 remaining Mypy diagnostics and 32 Ruff diagnostics. This is a bounded
reduction, not a claim that all static debt is resolved.

The three clarified modules have a blocking targeted Mypy check. Undefined names
and loop-variable shadowing are also blocking Ruff checks. The full legacy static
analysis remains visible and advisory.

[CI run 39056087037](https://github.com/LibreArbitre/edrefcard2/actions/runs/39056087037)
passes 72 Python tests, real rendering/PDF checks, 26 real mapper workflow checks,
the targeted static gates and container build/startup. Staging is deployed and
verified by three installed source hashes, an authenticated HTTPS preview and the
expected JSON error response. Real-Wand/PDF integration also passes in that
deployed runtime. The deliberately induced error is not an unexpected page error.

A coherent SQLite snapshot was preserved privately outside the container before
deployment. All 2,912 existing configuration IDs, saved mapping rows and four
controller source assets are unchanged; SQLite quick_check is ok. No draft was
saved, published or replaced. Beta/main promotion has not been performed for this
lot; the verified application change is currently on dev/staging only.

## Orion owner approval and reliability lot delivered to beta October 17

Alicina replied "Looks great! Thanks so much!" to the final request to check the
physical callouts. Stephane authorized Orion publication, reliability promotion,
and reuse of the already approved shared leader/endpoint style on this controller.

Main was fast-forwarded to `bd85a48` and manually deployed through Dokploy. The
installed renderer and admin source hashes match the staging-tested application.
[Main CI run 39056835710](https://github.com/LibreArbitre/edrefcard2/actions/runs/39056835710)
is green. The real-Wand/rendering/PDF suite also passes in the delivered beta
runtime, including the overlong-command regression.

Orion mapping ID 4, hardware `4098BEF0`, is now published through the normal admin
publication endpoint with its reviewed revision timestamp. Its saved mapping JSON
and placement were not modified. All three controls use the shared 7 px red
leader, 13 px white halo and filled, white-outlined hardware endpoint. New
inventory and owner previews were rendered through authenticated HTTPS and the
served endpoint pixels checked; the inventory image was visually inspected.

- [All three controls with clearer hardware markers and canonical beta URL](https://beta.edrefcard.info/configs/dd/ddpreview-9ae9a5881e6b4e0c982dbacd0f06abd4-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg)
- [Public renderer using Alicina's existing source](https://beta.edrefcard.info/binds/orion-owner-validation-20261003)

The public saved-card route renders the published Orion and its real actions;
unused brake axes remain hidden for this profile. Both A4 and Letter downloads
return PDFs and the device appears on the supported-device page. No synthetic
configuration was added to the catalogue. Previously downloaded images are not
modified; new renders use the shared style.

A coherent pre-deploy snapshot remains privately outside the container. All
3,100 prior configuration IDs and 12 controller source assets are preserved,
SQLite quick_check is ok, and the four other mapping rows are unchanged,
including both Merc drafts. This closes the Orion hardware-review/publication
gate. SOL-R owner verification remains separate and pending. Staging controller
data was not overwritten with the beta database.

## Canonical beta URL corrected October 17

The deployed APP_URL still referenced https://edrefcard2.l0l.fr. Config.webRoot
intentionally uses the configured external URL, not the request Host, so opening
an editor preview through beta.edrefcard.info did not change its printed address.
After Stephane's approval, only APP_URL was changed in the persistent Dokploy
Compose environment to https://beta.edrefcard.info and the stack redeployed.
Every other environment line was compared privately and remains identical.

The running container now has the canonical beta URL. Fresh Orion inventory and
owner previews were generated through HTTPS; the printed beta.edrefcard.info
address was visually checked. The owner saved-card route and A4/Letter downloads
were regenerated and checked as well. The fresh owner preview is:

[Orion with actual owner bindings and canonical beta URL](https://beta.edrefcard.info/configs/dd/ddpreview-9cb10200ca0b4c5f8b13fba01d5d5f2c-winctrl-orion-rudder-a107b27b7378499a8b9ec7f1939c9c18.jpg).

Saved mapping rows, all 3,100 existing configuration IDs and 12 controller source
assets are unchanged, and SQLite quick_check is ok. The prior environment and a
coherent database snapshot are preserved privately outside the container. No
source-code change or bulk rewrite of historical preview images was needed.
Old preview URLs and downloaded images can still show the old printed address;
share the fresh links above. Future renders use the canonical beta URL.
