# EdRefCard2 stabilization and controller delivery

Verified on 2026-10-03. This is the current restart point, replacing old roadmap
completion percentages as a measure of release readiness. The editor features
exist, but reliable rendering and owner validation of additional controllers
remain unfinished. Finish a bounded delivery before adding more editor features.

## Verified deployment and data

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
