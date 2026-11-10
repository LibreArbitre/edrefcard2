"""Human-readable differences between two revisions of a controller mapping.

Used by the review page (/admin/controllers/compare/<id>): before publishing a
mapper's draft, the admin sees what changed compared with the public revision
instead of publishing blind.
"""


def _label(box, index):
    return str(box.get('label') or f'box {index + 1}')


def _codes(box):
    return [row.get('joy') or '' for row in box.get('rows') or [] if isinstance(row, dict)]


def _pair_boxes(old_boxes, new_boxes):
    """Pair boxes of both revisions: by label when it is unique on both
    sides, then by identical input codes, so a renamed or moved box is
    reported as changed rather than as one removal plus one addition."""
    pairs, used_old, used_new = [], set(), set()

    def unique(boxes):
        seen = {}
        for index, box in enumerate(boxes):
            seen.setdefault(_label(box, index), []).append(index)
        return {label: indexes[0] for label, indexes in seen.items() if len(indexes) == 1}

    old_by_label, new_by_label = unique(old_boxes), unique(new_boxes)
    for label, old_index in old_by_label.items():
        if label in new_by_label:
            pairs.append((old_index, new_by_label[label]))
            used_old.add(old_index)
            used_new.add(new_by_label[label])
    for old_index, old_box in enumerate(old_boxes):
        if old_index in used_old or not any(_codes(old_box)):
            continue
        for new_index, new_box in enumerate(new_boxes):
            if new_index not in used_new and _codes(new_box) == _codes(old_box):
                pairs.append((old_index, new_index))
                used_old.add(old_index)
                used_new.add(new_index)
                break
    return pairs, used_old, used_new


def _row_text(row):
    parts = [str(row.get(key)) for key in ('symbol', 'number', 'joy') if row.get(key) not in (None, '')]
    return ' '.join(parts) or 'empty row'


def diff_mappings(old, new):
    """List of plain-text change descriptions from `old` (public) to `new` (draft)."""
    old = old if isinstance(old, dict) else {}
    new = new if isinstance(new, dict) else {}
    changes = []

    if (old.get('title') or '') != (new.get('title') or ''):
        changes.append(f'Title: "{old.get("title") or ""}" becomes "{new.get("title") or ""}".')
    if old.get('image') != new.get('image'):
        changes.append('The controller image was replaced.')
    if (old.get('width'), old.get('height')) != (new.get('width'), new.get('height')):
        changes.append(f'Image size: {old.get("width")}x{old.get("height")} becomes '
                       f'{new.get("width")}x{new.get("height")}.')
    if old.get('show_title', True) != new.get('show_title', True):
        changes.append('The title is now ' + ('printed' if new.get('show_title', True) else 'hidden') + '.')
    for key, label in (('title_xy', 'title'), ('url_xy', 'card URL')):
        if old.get(key) != new.get(key):
            changes.append(f'The {label} was moved.')

    old_ids = [str(v).upper() for v in old.get('device_ids') or []]
    new_ids = [str(v).upper() for v in new.get('device_ids') or []]
    added = [v for v in new_ids if v not in old_ids]
    removed = [v for v in old_ids if v not in new_ids]
    if added:
        changes.append('Hardware IDs added: ' + ', '.join(added) + '.')
    if removed:
        changes.append('Hardware IDs removed: ' + ', '.join(removed) + '.')

    old_boxes = [box for box in old.get('boxes') or [] if isinstance(box, dict)]
    new_boxes = [box for box in new.get('boxes') or [] if isinstance(box, dict)]
    pairs, used_old, used_new = _pair_boxes(old_boxes, new_boxes)

    for index, box in enumerate(new_boxes):
        if index not in used_new:
            codes = [code for code in _codes(box) if code]
            changes.append(f'Box added: "{_label(box, index)}"'
                           + (f' ({", ".join(codes)})' if codes else ' (no input code)') + '.')
    for index, box in enumerate(old_boxes):
        if index not in used_old:
            changes.append(f'Box removed: "{_label(box, index)}".')

    for old_index, new_index in sorted(pairs, key=lambda pair: pair[1]):
        before, after = old_boxes[old_index], new_boxes[new_index]
        name = _label(after, new_index)
        details = []
        if _label(before, old_index) != name:
            details.append(f'renamed from "{_label(before, old_index)}"')
        moved = before.get('box_xy') != after.get('box_xy')
        resized = before.get('box_wh') != after.get('box_wh')
        if moved and resized:
            details.append('moved and resized')
        elif moved:
            details.append('moved')
        elif resized:
            details.append('resized')
        if before.get('button_xy') != after.get('button_xy'):
            details.append('anchor point ' + ('removed' if after.get('button_xy') is None
                                              else 'added' if before.get('button_xy') is None else 'moved'))
        if bool(before.get('no_chrome')) != bool(after.get('no_chrome')):
            details.append('frame ' + ('hidden' if after.get('no_chrome') else 'shown'))
        old_rows = [row for row in before.get('rows') or [] if isinstance(row, dict)]
        new_rows = [row for row in after.get('rows') or [] if isinstance(row, dict)]
        old_texts, new_texts = [_row_text(row) for row in old_rows], [_row_text(row) for row in new_rows]
        if old_texts != new_texts:
            gone = [text for text in old_texts if text not in new_texts]
            come = [text for text in new_texts if text not in old_texts]
            if come:
                details.append('rows added or changed: ' + '; '.join(come))
            if gone:
                details.append('rows removed or replaced: ' + '; '.join(gone))
            if not come and not gone:
                details.append('rows reordered')
        if details:
            changes.append(f'Box "{name}": ' + ', '.join(details) + '.')
    return changes
