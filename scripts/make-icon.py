#!/usr/bin/env python3
"""Render the WinLuxCD icon at multiple sizes (PNG + multi-resolution ICO).

Mirrors icons/winluxcd.svg using only Pillow, so the full dist does not depend
on ImageMagick / rsvg / inkscape.  Run via scripts/make-icon.sh.
"""
import sys
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else "icons"

BG        = (13, 27, 42, 255)      # tile background
BG_RING   = (51, 80, 110, 255)     # tile outline
FLAG_BLUE = (74, 144, 226, 255)    # Windows flag panes
ARROW_W   = (248, 250, 252, 255)   # arrow first half
ARROW_G   = (74, 222, 128, 255)    # arrow second half
BODY      = (31, 41, 55, 255)      # Tux body
BELLY     = (248, 250, 252, 255)   # Tux belly / eyes
WING      = (11, 18, 32, 255)      # Tux wings / pupils
ORANGE    = (249, 115, 22, 255)    # beak / feet


def draw(size: int) -> Image.Image:
    S = size / 512.0

    def R(v):
        return round(v * S)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # rounded tile
    d.rounded_rectangle((R(8), R(8), R(504), R(504)), radius=R(112),
                        fill=BG, outline=BG_RING, width=max(1, R(6)))

    # Windows flag (2x2 panes)
    for (x, y) in ((126, 188), (194, 188), (126, 258), (194, 258)):
        d.rounded_rectangle((R(x), R(y), R(x + 56), R(y + 56)), radius=R(8),
                            fill=FLAG_BLUE)

    # arrow: two thick chevron strokes (white then green)
    w = max(4, R(34))
    d.line([(R(268), R(218)), (R(330), R(256))], fill=ARROW_W, width=w, joint="curve")
    d.line([(R(330), R(256)), (R(268), R(294))], fill=ARROW_G, width=w, joint="curve")

    # Tux
    d.ellipse((R(342), R(162), R(474), R(354)), fill=BODY)             # body
    d.ellipse((R(366), R(220), R(450), R(348)), fill=BELLY)            # belly
    d.ellipse((R(333), R(212), R(367), R(304)), fill=WING)             # left wing
    d.ellipse((R(449), R(212), R(483), R(304)), fill=WING)             # right wing
    d.ellipse((R(372), R(210), R(396), R(234)), fill=BELLY)            # left eye
    d.ellipse((R(420), R(210), R(444), R(234)), fill=BELLY)            # right eye
    d.ellipse((R(381), R(219), R(392), R(230)), fill=WING)             # left pupil
    d.ellipse((R(425), R(219), R(436), R(230)), fill=WING)             # right pupil
    d.polygon([(R(390), R(242)), (R(408), R(232)), (R(426), R(248)),
               (R(408), R(264)), (R(390), R(252))], fill=ORANGE)       # beak
    d.ellipse((R(366), R(347), R(398), R(365)), fill=ORANGE)           # left foot
    d.ellipse((R(418), R(347), R(450), R(365)), fill=ORANGE)           # right foot
    return img


def render(size: int) -> Image.Image:
    """Draw at 4x then downscale with Lanczos for smooth edges."""
    big = draw(size * 4)
    return big.resize((size, size), Image.LANCZOS)


def main() -> None:
    sizes = [512, 256, 128, 64, 32, 16]
    for s in sizes:
        render(s).save(f"{OUT}/winluxcd-{s}.png")
    # multi-resolution Windows .ico (taskbar / desktop)
    render(256).save(f"{OUT}/winluxcd.ico", format="ICO",
                     sizes=[(16, 16), (32, 32), (48, 48), (64, 64),
                            (128, 128), (256, 256)])
    print("wrote: " + ", ".join(f"winluxcd-{s}.png" for s in sizes) + ", winluxcd.ico")


if __name__ == "__main__":
    main()
