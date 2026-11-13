#!/usr/bin/env python3
"""Arrange the release's single-character PDFs for A4 long-edge duplex printing.

Usage: python scripts/make_duplex.py /path/to/release-pdfs [output.pdf]
Dependencies: PyMuPDF, Pillow, numpy, scipy.
"""
import io
import sys
from pathlib import Path

import numpy as np
import pymupdf as fitz
from PIL import Image
from scipy.ndimage import label, find_objects

FILES = [
    'albus_dumbledore.pdf', 'bertie_botts.pdf', 'filius_flitwick.pdf',
    'gilderoy_lockhart.pdf', 'godric_gryffindor.pdf', 'helga_hufflepuff.pdf',
    'horace_slughorn.pdf', 'lord_voldemort.pdf', 'minerva_mcgonagoll.pdf',
    'quirinus_quirrell.pdf', 'rolanda_hooch.pdf', 'rowena_ravenclaw.pdf',
    'rubeus_hagrid.pdf', 'salazar_slytherin.pdf', 'severus_snape.pdf', 'sprout3.pdf',
]
MM = 72 / 25.4
DPI = 300
SCALE = DPI / 72


def extract_sides(filename):
    """Find the two large blue pentagon outlines, then crop the rendered page."""
    with fitz.open(filename) as doc:
        assert len(doc) == 1, f'{filename}: expected a single source page'
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    a = np.asarray(image).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (b > r * 1.15) & (b > g * 1.15) & (b > 60) & (b < 160) & (r < 100) & (g < 100)
    components, _ = label(mask)
    candidates = []
    for bounds in find_objects(components):
        if bounds is None:
            continue
        ys, xs = bounds
        width, height = xs.stop - xs.start, ys.stop - ys.start
        if width > 1000 and height > 950:
            candidates.append((xs.start, ys.start, xs.stop, ys.stop))
    candidates.sort(key=lambda box: box[1])
    if len(candidates) != 2:
        raise ValueError(f'{filename}: expected two card outlines, got {candidates}')
    sides = []
    for x0, y0, x1, y1 in candidates:
        # Include anti-aliased edges outside the detected blue outline.
        pad = 3
        card = image.crop((x0-pad, y0-pad, x1+pad, y1+pad))
        data = io.BytesIO()
        card.save(data, format='JPEG', quality=96, subsampling=0, optimize=True)
        sides.append(data.getvalue())
    print(filename.name, candidates, flush=True)
    return sides


def main():
    source = Path(sys.argv[1])
    output = Path(sys.argv[2] if len(sys.argv) > 2 else 'print_ready/all_characters_A4_duplex.pdf')
    missing = [f for f in FILES if not (source / f).is_file()]
    if missing:
        raise FileNotFoundError(f'Missing source files: {missing}')
    cards = [(name, extract_sides(source / name)) for name in FILES]
    page_w, page_h = fitz.paper_size('a4')
    card_w, card_h = 96.6 * MM, 91.7 * MM
    gap_x, gap_y = 4 * MM, 4 * MM
    left = (page_w - 2 * card_w - gap_x) / 2
    top = (page_h - 3 * card_h - 2 * gap_y) / 2
    assert left > 5 * MM and top > 5 * MM
    out = fitz.open()
    for start in range(0, len(cards), 6):
        batch = cards[start:start + 6]
        for side in (0, 1):
            page = out.new_page(width=page_w, height=page_h)
            for index, (_, images) in enumerate(batch):
                row, col = divmod(index, 2)
                # Reverse columns (not pixels!) on the back for portrait long-edge flip.
                if side == 1:
                    col = 1 - col
                x, y = left + col * (card_w + gap_x), top + row * (card_h + gap_y)
                page.insert_image(fitz.Rect(x, y, x + card_w, y + card_h),
                                  stream=images[side], keep_proportion=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.set_metadata({'title': 'Chocolate Frog cards — A4 duplex', 'subject': '16 characters, long-edge duplex'})
    out.save(output, garbage=4, deflate=True)
    print(f'Wrote {output}: {len(cards)} characters, {len(out)} pages')


if __name__ == '__main__':
    main()
