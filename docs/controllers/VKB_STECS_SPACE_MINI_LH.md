# VKB STECS Space Mini Left Hand draft

Prepared October 14, 2026 from TyWuNon's emailed bindings and VKBDevCfg
screenshots. Hardware ID `231D0136` appears in both the .binds and the owner's
PID 0136 screenshot. Firmware is v2.20C, profile 0, with no custom button remaps
reported by the owner. Do not attach the different Max/STEM ID `231D0139` to
this Mini template without a separate comparison.

Beta draft ID `5` is saved, not published. The four existing mapping rows were
verified unchanged. The emailed XML is kept outside the web-served configs
tree. Only the rendered STECS review image is linked below.

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

The two encoder directions still need owner validation. Together these rows
cover logical buttons 1-29, including unused buttons in the owner's .binds.
They remain individual rows within grouped hats, not separate groups per hat
direction.

## Axis validation pending

The file uses X, Y, Z, positive RX, and RY. Their real game actions are shown
in a separate box labelled `AXIS CODES: PHYSICAL LOCATIONS UNVERIFIED`, with no
leader line. The five physical axis slots in the manufacturer artwork stay
unassigned until the owner confirms their correspondence.

The preview covers all 26 used input codes: 21 buttons and five axis codes.
Zero missing used inputs is a coverage result, not confirmation of physical
axis placement or exhaustive hardware support. Publication is blocked by the
input-verification metadata.

## Review links and rendering correction

- [Beta editor](https://beta.edrefcard.info/admin/mapping-editor?device=231D0136)
- [Corrected owner-profile preview](https://beta.edrefcard.info/configs/dd/ddpreview-cc30e714a8f5447b96753d29ce52d663-vkb-stecs-space-mini-lh-9a5fb4c3a4074059b20b1ea54ef6c34d.jpg)

The preview uses the manufacturer artwork, retaining UntoldForce's credit.
Unused printed frames remain visible. Dense encoder rows are small at this
sheet's fixed geometry and need a readability pass before release.

The corrected preview was rendered with the tested follow-up renderer in a
scratch copy. This correction adds `show_title: false` for artwork which already
contains its title, and `url_xy: [44, 1810]` to put the generated URL in the
bottom margin. Both are optional; older mappings keep their existing defaults.
The correction is not yet promoted to the beta application, so its ordinary
Preview button still uses the previous header behavior until promotion.

All 43 Python tests passed with the runtime dependencies, without skips.
The corrected image was loaded and visually reviewed in the browser.

The private review source is retained in a restricted, non-web-served location,
and a pre-change database backup is preserved. No original owner XML,
screenshots or private infrastructure paths are committed to Git.
