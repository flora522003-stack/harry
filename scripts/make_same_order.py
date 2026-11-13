#!/usr/bin/env python3
"""Create the requested same-order backs (not a matched duplex layout)."""
from pathlib import Path
import pymupdf as fitz

src = fitz.open('print_ready/all_characters_A4_duplex.pdf')
out = fitz.open()
scale = 0.95
for i, page in enumerate(src):
    w, h = page.rect.width, page.rect.height
    x, y = w * (1-scale) / 2, h * (1-scale) / 2
    dest = out.new_page(width=w, height=h)
    if i % 2 == 0:
        dest.show_pdf_page(fitz.Rect(x, y, x + w*scale, y + h*scale), src, i)
    else:
        # Exchange the two columns without mirroring or rotating their pixels.
        for source_col in (0, 1):
            clip = fitz.Rect(source_col*w/2, 0, (source_col+1)*w/2, h)
            target_col = 1-source_col
            target = fitz.Rect(x+target_col*w*scale/2, y,
                               x+(target_col+1)*w*scale/2, y+h*scale)
            dest.show_pdf_page(target, src, i, clip=clip)
out.set_metadata({'title': 'Chocolate Frog cards - backs in the same order',
                  'subject': 'A4, 95%, same-order backs (not duplex matched)'})
path = Path('print_ready/cards_same_order_wide_margins.pdf')
out.save(path, garbage=4, deflate=True)
print(f'{path}: {len(out)} pages')
