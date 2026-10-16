# VKB STECS Space Mini Left Hand

Prepared October 14, 2026 from TyWuNon's emailed bindings and VKBDevCfg
screenshots. Hardware ID `231D0136` appears in both the .binds and the owner's
PID 0136 screenshot. Firmware is v2.20C, profile 0, with no custom button remaps
reported by the owner. Do not attach the different Max/STEM ID `231D0139` to
this Mini template without a separate comparison.

Published on beta on October 16, 2026 as mapping ID `5`, after TyWuNon confirmed
the shown setup and axes. The four other mapping rows, including the community
drafts, remain unchanged. The emailed XML stays outside the web-served configs
tree; only the rendered controller image is shared.

## Logical button assignments

Numbers below come from the screenshot's logical destinations, not the
physical input numbers. They correspond to `Joy_N` in the game profile.

| Physical group | Row order | Logical buttons |
| --- | --- | --- |
| Main Trigger | Press | 9 |
| B1 | Press | 8 |
| B2 | Press | 10 |
| H1 | Push, up, down | 26, 25, 24 |
| H2 | Push, left, right | 29, 27, 28 |
| HAT1 | Push, up, down, left, right | 15, 23, 22, 20, 21 |
| Pointer Hat | Push, up, down, left, right | 14, 16, 17, 18, 19 |
| Speed Lim | Push, encoder first/second output | 11, 12, 13 |
| Base | Modes 1-5, START, SYS | 3, 4, 5, 6, 7, 2, 1 |

These rows cover logical buttons 1-29, including unused buttons in the owner's
.binds. The owner's preview approval confirms the shown encoder assignments.
Hat directions remain rows within one physical group, not separate boxes.

## Validated logical axes

The owner's configuration enables HID outputs X, Y, Z, RX and RY. His file
uses X, Y, Z, positive RX and RY. The template's full `Joy_RXAxis` row covers
the positive-direction digital bindings without inventing another physical
control. RY is virtual in this profile, not a fifth independent physical sensor.

The enabled outputs appear in one `AXES: GAME INPUT CODES` block without a
leader line. Owner approval covers the logical codes and shown commands, not
individual physical sensor positions. RZ, Slider and Dial are not enabled in
this reviewed profile and are not added from generic product specifications.

## Final card and verification

- [Beta editor](https://beta.edrefcard.info/admin/mapping-editor?device=231D0136)
- [Final owner-profile card](https://beta.edrefcard.info/configs/dd/ddpreview-compact-owner-f72b7d9824704403b5cfc22e7616319a-vkb-stecs-space-mini-lh-final-eae3ca447a2842cdbaade9e35173ff3f.jpg)
- [A4 export](https://beta.edrefcard.info/download/ddpreview-compact-owner-f72b7d9824704403b5cfc22e7616319a/pdf?format=A4)
- [Letter export](https://beta.edrefcard.info/download/ddpreview-compact-owner-f72b7d9824704403b5cfc22e7616319a/pdf?format=Letter)

The final 3600 x 2400 card uses the intact [VKB product photograph](https://flightsimcontrols.com/wp-content/uploads/2025/08/STECS-Mini-STG-L_04_1200.webp)
on a white canvas with runtime-generated frames. It replaces the earlier
fixed-height PDF worksheet, so unused groups disappear and dense encoder
commands have enough room. No worksheet artwork is reused in this final image.
The rear trigger and base group have descriptive labels rather than speculative
leader lines. Other digital groups point to the corresponding visible controls.

Verification on October 16:

- All 34 template inputs render: 29 digital buttons and five enabled axis codes.
- All 26 inputs used by Ty are covered: 21 buttons and five axis codes.
- His 56 displayed command labels all fit at the renderer's maximum body size
  of 40 px, about 9.35 pt in the A4 export and 8.79 pt in Letter.
- Both PDF exports reopen as one landscape page with an unclipped image and
  were visually inspected after rasterization.
- The published revision is selected by the deployed web/API rendering helper
  in all four styles, with no missing-input warning.
- The public device catalogue lists this controller. No synthetic catalogue
  record was added; all 3,098 existing configurations were retained.
- All 50 Python tests pass without skips in the server runtime. Real-Wand/Flask
  integration checks pass, including three legacy templates and both PDF sizes.

Commit `aaa06cd` also fixes a renderer crash discovered with the real profile:
unknown or empty command categories/groups now use their General style. Tests
cover modified and unmodified bindings. The correction was deployed through
staging and beta, with the deployed renderer file hash checked in both.

Commit `fa80c95` fixes the spacing of generated frames. Real-profile previews
and generated cards measure row heights from wrapped command text, retain
consistent padding and shrink frames within their reserved geometry. With Ty's
profile, BASE is 160 px high instead of 610 px; SPEED LIM uses 60/180/180 px
rows instead of three 260 px rows. All 56 command labels retain the 40 px font.
Fixed artwork, imported PDF slots and tiny constrained frames keep their
existing fitting behavior. Editor previews without a reference profile retain
the full editable geometry.

Stéphane approved the compact rendering before promotion. Beta verification
checks the deployed file hash, an authenticated HTTPS preview's frame pixels,
four real-profile styles and preservation of all mapping rows. The subsequent
backup/PDF reliability release validates existing PDF caches against their
source images and regenerates stale exports on access. The linked A4 and Letter
exports were checked again through the deployed beta download routes.

The private review source is retained in a restricted, non-web-served location,
and a pre-change database backup plus the final mapping and review artifacts
are preserved outside the container. No original owner XML, screenshots,
credentials or private infrastructure paths are committed to Git.
