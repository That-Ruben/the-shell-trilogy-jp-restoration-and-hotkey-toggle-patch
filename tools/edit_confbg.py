"""Add a Japanese row to the Language Select panel on the config screen.

Works for both The Shell games: the panel geometry is identical
(rows at y=241/274/307 with pitch 33, label ink left edge x=1077,
checkbox at x=1150, dashed separator at y=340, panel bottom edge ~349)
while the visual style differs (part 1: flat light panel, outlined gray
labels; part 2: dark textured panel, plain white labels).  All colors and
the label style are therefore sampled from the image being edited:

  1. the bottom strip (dash + panel edge) moves down 33 px,
  2. the tw row band (texture + label + checkbox) is copied down 33 px,
  3. the copied tw label is erased with clean interior texture tiled from
     the gap between the label rows,
  4. 日本語 is drawn in the sampled label style,
  5. an L-key hotkey hint is drawn below the panel, styled like the
     game's small "Return settings to default" helper text.
"""
import sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

BAND_X0, BAND_X1 = 1032, 1262   # working column window (panel + margin)
ROW_PITCH = 33
NEW_Y0 = 340                    # new row band: 340..372
# the copied band and the moved strip start 2 rows early: part 3's dashed
# separator sits at y=339..340 (parts 1/2: y=340..341) and must be fully
# covered; rows 338..339 are clean interior in all three games
STRIP_Y0, STRIP_Y1 = 338, 356   # dash + interior bottom + panel edge
ROWSRC_Y0 = 305                 # tw row band (+2 lead rows of interior)
ERASE_X0, ERASE_X1 = 1050, 1143  # label columns (checkbox untouched)
CLEAN_Y0, CLEAN_Y1 = 302, 314   # label-free interior rows (verified)
LABEL = "日本語"
LABEL_LEFT = 1077               # ink left edge, same as the other labels
LABEL_TOP = NEW_Y0 + 10         # ink top, same offset as the other rows
FONT_SIZE = 16
CN_LABEL_BOX = (ERASE_X0, 282, ERASE_X1, 300)  # sampled for label style
HINT = "Press L to switch EN/JP in game"
HINT_TOP = 392
HINT_SIZE = 14
SUBTITLE_BOX = (1060, 160, 1240, 195)  # "Return settings to default"


def _sample_styles(px):
    """Label fill/outline and hint outline, from the panel style.

    Light panel (part 1): the labels are near-interior-colored with a dark
    contour - contrast sampling cannot recover that fill, so the measured
    constants are used.  Dark panel (part 2): plain bright labels, fill
    sampled from the cn label, no contour; the hint needs a black contour
    to read on the light textured page."""
    ref = Counter(px[x, y] for y in range(CLEAN_Y0, CLEAN_Y1)
                  for x in range(ERASE_X0, ERASE_X1)).most_common(1)[0][0]
    if sum(ref) > 450:
        return (216, 216, 216), (74, 74, 74), (74, 74, 74)

    x0, y0, x1, y1 = CN_LABEL_BOX
    bright = [px[x, y] for y in range(y0, y1) for x in range(x0, x1)
              if sum(px[x, y]) > sum(ref) + 250]
    fill = Counter(bright).most_common(1)[0][0]
    return fill, None, (0, 0, 0)


def edit(src_png, out_png, font_path):
    im = Image.open(src_png).convert("RGB")
    d = ImageDraw.Draw(im)
    fill, outline, hint_outline = _sample_styles(im.load())

    # 1. lift the bottom strip before overwriting it
    strip = im.crop((BAND_X0, STRIP_Y0, BAND_X1, STRIP_Y1)).copy()

    # 2. new row band: copy of the tw row (texture, label, checkbox)
    band = im.crop((BAND_X0, ROWSRC_Y0,
                    BAND_X1, ROWSRC_Y0 + ROW_PITCH + (NEW_Y0 - STRIP_Y0)))
    im.paste(band, (BAND_X0, STRIP_Y0))

    # 3. bottom strip moved down one row
    im.paste(strip, (BAND_X0, STRIP_Y0 + ROW_PITCH))

    # 4. erase the copied tw label with tiled clean interior
    clean = im.crop((ERASE_X0, CLEAN_Y0, ERASE_X1, CLEAN_Y1)).copy()
    ch = CLEAN_Y1 - CLEAN_Y0
    y = NEW_Y0 + 6
    while y < NEW_Y0 + 6 + 2 * ch:
        im.paste(clean, (ERASE_X0, y))
        y += ch

    # 5. label, ink-aligned to the existing rows, in the sampled style
    font = ImageFont.truetype(font_path, FONT_SIZE)
    stroke = 1 if outline else 0
    bb = d.textbbox((0, 0), LABEL, font=font, stroke_width=stroke)
    d.text((LABEL_LEFT - bb[0], LABEL_TOP - bb[1]), LABEL, font=font,
           fill=fill, stroke_width=stroke, stroke_fill=outline)

    # 6. hotkey hint below the panel
    hfont = ImageFont.truetype(font_path, HINT_SIZE)
    bb = d.textbbox((0, 0), HINT, font=hfont, stroke_width=1)
    cx = (BAND_X0 + BAND_X1) // 2
    d.text((cx - (bb[0] + bb[2]) // 2, HINT_TOP - bb[1]), HINT, font=hfont,
           fill=(250, 250, 250), stroke_width=1, stroke_fill=hint_outline)

    im.save(out_png)


if __name__ == "__main__":
    edit(sys.argv[1], sys.argv[2], sys.argv[3])
