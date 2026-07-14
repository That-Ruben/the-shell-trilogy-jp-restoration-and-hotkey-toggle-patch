"""Generate pc/<lang>/mw/mwlang.png - sprite for the in-game EN/JP toggle
button added to the small message-window button row.

Four vertically stacked 21x32 cells, matching the style of the existing
small icons (bt_voice / bt_close / bt_back in mw/mw.png):
  y=0   normal   white glyph, dark 1px contour, in the cell's lower half
  y=32  hover    white glyph, red contour + soft red glow
  y=64  inactive normal glyph at reduced alpha
  y=96  hidden   empty
"""
import sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CELL_W, CELL_H = 21, 32
TEXT = "JP"
INK_BOTTOM = 29          # existing small glyphs occupy roughly y 18..28
DARK = (35, 35, 35)
HOVER_CELL = (288, 192)  # bt_close (envelope) hover state in mw/mw.png


def sample_hover_color(mw_png):
    """The game's hover accent (part 1: dark red, part 2: orange),
    sampled from an existing icon's hover cell."""
    im = Image.open(mw_png).convert("RGBA")
    px = im.load()
    ox, oy = HOVER_CELL
    colors = Counter(
        px[x, y][:3]
        for y in range(oy, oy + CELL_H) for x in range(ox, ox + CELL_W)
        if px[x, y][3] > 200 and sum(px[x, y][:3]) < 500)
    return colors.most_common(1)[0][0]


def glyph_layer(font, contour):
    """Render TEXT white-filled with a 1px contour, on transparent."""
    layer = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), TEXT, font=font, stroke_width=1)
    w = bb[2] - bb[0]
    x = (CELL_W - w) // 2 - bb[0]
    y = INK_BOTTOM - bb[3]
    d.text((x, y), TEXT, font=font, fill=(255, 255, 255, 255),
           stroke_width=1, stroke_fill=contour + (255,))
    return layer


def make(font_path, out_png, mw_png):
    accent = sample_hover_color(mw_png)
    font = ImageFont.truetype(font_path, 13)
    im = Image.new("RGBA", (CELL_W, CELL_H * 4), (0, 0, 0, 0))

    normal = glyph_layer(font, DARK)
    im.paste(normal, (0, 0))

    # hover: accent-colored glow behind an accent-contoured glyph
    acc = glyph_layer(font, accent)
    glow = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    mask = acc.split()[3].filter(ImageFilter.GaussianBlur(2))
    glow.paste(Image.new("RGBA", (CELL_W, CELL_H), accent + (255,)),
               (0, 0), mask)
    hover = Image.alpha_composite(glow, acc)
    im.paste(hover, (0, CELL_H))

    # inactive: faded normal
    faded = normal.copy()
    faded.putalpha(faded.split()[3].point(lambda a: a * 2 // 5))
    im.paste(faded, (0, CELL_H * 2))

    im.save(out_png)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
