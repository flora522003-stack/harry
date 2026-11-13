#!/usr/bin/env python3
"""Create centered, duplex-ready variants from the generated card sheets.

Requires PyMuPDF. A small back-side horizontal correction reduces the
measured outline discrepancy introduced by the asymmetrical source artwork.
"""
from pathlib import Path
import pymupdf as fitz

SOURCE = Path('print_ready/all_characters_A4_duplex.pdf')
MM = 72 / 25.4


def make_variant(name, scale, short_edge):
    src = fitz.open(SOURCE)
    out = fitz.open()
    assert len(src) == 6
    for i, page in enumerate(src):
        w, h = page.rect.width, page.rect.height
        target = fitz.Rect(w * (1 - scale) / 2, h * (1 - scale) / 2,
                           w * (1 + scale) / 2, h * (1 + scale) / 2)
        is_back = i % 2 == 1
        rotate = 180 if is_back and short_edge else 0
        if is_back:
            # After viewing through the sheet, the long-edge design needs
            # +0.17 mm; on the printed back this means shifting left.
            dx = 0.17 * MM * scale * (1 if rotate else -1)
            target = target + (dx, 0, dx, 0)
        result = out.new_page(width=w, height=h)
        result.show_pdf_page(target, src, i, rotate=rotate, keep_proportion=True)
    out.set_metadata({'title': name, 'subject': 'Chocolate Frog cards — A4 duplex'})
    path = Path('print_ready') / name
    out.save(path, garbage=4, deflate=True)
    print(path, path.stat().st_size, 'bytes')


if __name__ == '__main__':
    make_variant('cards_long_edge_corrected.pdf', 1.0, False)
    make_variant('cards_long_edge_wide_margins.pdf', 0.95, False)
    make_variant('cards_short_edge_wide_margins.pdf', 0.95, True)
