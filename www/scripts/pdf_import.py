"""Import a manufacturer AcroForm reference sheet (VIRPIL-style) as a mapping.

VIRPIL (and similar) fillable PDFs are semantically structured:
  - the page artwork (photo + callout boxes + leader lines) is page CONTENT,
  - the fillable fields are annotations laid over it, one family per physical
    input: BTN<n>, HAT<n>_{U,R,D,L,P}, SWT<n>_S<k>, AXS1D<n>, AXS2D<n>_{H,V},
  - each family has _Name (the Joy number / axis letter), _Desc (the writing
    area = our box, with its exact position) and optional _Min/_Max/_Mid.

So one import gives us: a clean rendered background (annotations excluded,
keeping the manufacturer's own boxes and leader lines) plus every box already
positioned. Imported boxes carry no_chrome=True so the engine only writes the
binding text inside the manufacturer's artwork instead of redrawing frames.
"""

import io
import re

import fitz  # PyMuPDF
from PIL import Image

# Axis letters as printed on the sheets -> Elite DirectInput key names
_AXIS_JOY = {
    'X': 'Joy_XAxis', 'Y': 'Joy_YAxis', 'Z': 'Joy_ZAxis',
    'RX': 'Joy_RXAxis', 'RY': 'Joy_RYAxis', 'RZ': 'Joy_RZAxis',
    'SLDR': 'Joy_UAxis', 'SLIDER': 'Joy_UAxis',
    'DIAL': 'Joy_VAxis',
}

_DIR_SYMBOL = {'U': 'up', 'R': 'right', 'D': 'down', 'L': 'left', 'P': 'press'}

_ROLE_RE = re.compile(r'_(Name|Desc|Min|Max|Mid)$')


def _family_boxes(page):
    """Group the page's widgets into {family: {role: widget}} dicts."""
    fams = {}
    for w in page.widgets() or []:
        name = w.field_name or ''
        m = _ROLE_RE.search(name)
        fam, role = (name[:m.start()], m.group(1)) if m else (name, 'Self')
        fams.setdefault(fam, {})[role] = w
    return fams


def _row_for(family, name_value):
    """Build the mapping row (symbol/number/joy/type) for one field family."""
    val = (name_value or '').strip()
    # Axis families (AXS...): _Name holds the axis letter
    if family.upper().startswith('AXS'):
        joy = _AXIS_JOY.get(val.upper().replace(' ', ''), '')
        return {'symbol': None, 'number': val or None, 'joy': joy,
                'type': 'Analogue'}
    # Button-like families: _Name holds the Joy_N number; the suffix of the
    # family name carries the hat direction (HAT6_U) or switch position.
    symbol = 'press'
    m = re.search(r'_([URDLP])$', family)
    if m:
        symbol = _DIR_SYMBOL[m.group(1)]
    number = val if val else None
    joy = f'Joy_{val}' if val.isdigit() else ''
    return {'symbol': symbol, 'number': number, 'joy': joy, 'type': 'Digital'}


def _label_for(family, row):
    """Editor-panel label (headers are not drawn for no_chrome boxes)."""
    label = family.replace('_', ' ')
    if row['type'] == 'Analogue' and row.get('number'):
        label = f"AXIS {row['number']}"
    return label


def extract_mapping_from_pdf(pdf_bytes, zoom=1.0):
    """Convert an AcroForm reference sheet into (mapping_dict, jpeg_bytes).

    The mapping has one no_chrome box per fillable _Desc area, positioned on
    the manufacturer's own artwork; the JPEG is the page rendered WITHOUT
    annotations (empty boxes, ready to be written into by the engine).
    """
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    if doc.page_count < 1:
        raise ValueError('Empty PDF')
    # Pick the page with the most widgets (sheets are usually single-page)
    page = max(doc, key=lambda p: len(list(p.widgets() or [])))
    fams = _family_boxes(page)

    boxes = []
    for family, roles in sorted(fams.items()):
        desc = roles.get('Desc')
        if desc is None:
            continue  # ProfileName, Mid markers, decorations...
        name_w = roles.get('Name')
        row = _row_for(family, name_w.field_value if name_w else '')
        # The manufacturer number/letter is already printed in the artwork
        # badge next to the writing area, so the engine must not repeat it.
        row['number'] = None
        r = desc.rect
        boxes.append({
            'label': _label_for(family, row),
            'box_xy': [int(r.x0 * zoom), int(r.y0 * zoom)],
            'box_wh': [int(r.width * zoom), int(r.height * zoom)],
            'button_xy': None,
            'no_chrome': True,
            'rows': [row],
        })
    if not boxes:
        raise ValueError('No fillable description fields found in this PDF '
                         '(is it an AcroForm reference sheet?)')

    # Render the page WITH annotations so the manufacturer numbers (the _Name
    # values printed in the artwork badges) stay visible, but delete the
    # standalone placeholder fields first (e.g. 'Profile ... by ...'): value
    # blanking alone does not always refresh the appearance stream.
    for family, roles in fams.items():
        w = roles.get('Self')
        if w is not None and (w.field_value or '').strip():
            try:
                page.delete_widget(w)
            except Exception:
                pass
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92)

    mapping = {
        'title': '',
        'image': None,           # set by the caller after saving the JPEG
        'device_ids': [],
        'styling': 'Group',
        'width': pix.width,
        'height': pix.height,
        'boxes': boxes,
    }
    return mapping, buf.getvalue()
