#!/usr/bin/env python3
"""THE WORLD TODAY - front page summing up world news of Tuesday 24 November 2026.

Draws a 1024x1024 newspaper front page entirely from code, Python 3.13
standard library only. No network access, no clock, no randomness: the same
program always renders the same bytes. Writes one PNG to /output/entry.png
(falls back to ./output/ when /output is not writable).

News (all as reported on 23-24 November 2026, verified from public sources):
  LEAD 1. Ukraine says seven naval drones sank the Russian corvette Merkury
     at the Benghazi naval base in Libya on Sunday 22 Nov, destroying a
     Ka-27 helicopter on board; a second strike hit the cargo ship MV Angara.
     (Military Times, MarineLink, ABC News, 23 Nov 2026.)
  LEAD 2. Nvidia's board voted unanimously to reinstate Jensen Huang as
     president and chief executive, under two weeks after he resigned on
     12 Nov; shares jumped about 30 percent. The board says his return
     poses no national security risk. (Morningstar, TechCrunch, Bloomberg
     Law, The Register, 23 Nov 2026.)
  ALSO: a candy factory fire in Indonesia kills at least 24; COP31 climate
     talks in Antalya collapse with no deal; the Russian cargo ship Sparta II
     catches fire in the Gulf of Finland after a drone strike; Zelensky says
     intelligence shows Russia planning new strikes as the Dymer toll rises
     to 11; the UN's top court rules Myanmar committed genocide against the
     Rohingya; world chess champion Gukesh begins his title defence against
     Sindarov in Geneva.
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 234)
INK = (17, 17, 17)
RED = (185, 28, 28)
NAVY = (23, 42, 69)
GREY = (85, 85, 85)
LIGHT = (226, 220, 208)

# 5x7 bitmap font, written fresh for this page. Each glyph is 7 rows of
# 5 cells; '#' is ink, '.' is blank. Parsed once into row bit-masks.
FONT_SRC = {
    "A": ("#####", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}


def _parse_font(src):
    out = {}
    for ch, rows in src.items():
        bits = []
        for row in rows:
            mask = 0
            for cell in row:
                mask = (mask << 1) | (1 if cell == "#" else 0)
            bits.append(mask)
        out[ch] = tuple(bits)
    return out


FONT = _parse_font(FONT_SRC)

NORMALIZE = {"\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
             "\u201c": '"', "\u201d": '"'}


def clean(text):
    out = []
    for ch in text:
        ch = NORMALIZE.get(ch, ch)
        out.append(ch if ch in FONT else " ")
    return "".join(out)


class Page:
    """An RGB canvas with rectangle and bitmap-text drawing."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def text(self, x, y, s, scale, color):
        s = clean(s)
        cx = x
        for ch in s:
            rows = FONT.get(ch)
            if rows is None:
                cx += 6 * scale
                continue
            for ry, mask in enumerate(rows):
                for rx in range(5):
                    if mask & (1 << (4 - rx)):
                        self.rect(cx + rx * scale, y + ry * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(clean(s)) * 6 * scale - scale

    def centered(self, y, s, scale, color):
        w = self.text_width(s, scale)
        self.text((self.w - w) // 2, y, s, scale, color)
        return y + 7 * scale


def wrap(text, scale, max_px):
    """Greedy word wrap; returns a list of lines that fit max_px."""
    words = clean(text).split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) * 6 * scale - scale <= max_px:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _chunk(kind, data):
    body = struct.pack(">I", len(data)) + kind + data
    return body + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path, page):
    raw = b"".join(
        b"\x00" + bytes(page.px[y * page.w * 3:(y + 1) * page.w * 3])
        for y in range(page.h)
    )
    ihdr = struct.pack(">IIBBBBB", page.w, page.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(raw, 9))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------------------
# News content for Tuesday 24 November 2026 (verified from public sources).
# ---------------------------------------------------------------------------

MASTHEAD = "THE WORLD TODAY"
DATELINE_LEFT = "TUESDAY 24 NOVEMBER 2026"
DATELINE_RIGHT = "ONE IMAGE - THE WHOLE DAY"

LEAD1_KICKER = "UKRAINE - LIBYA"
LEAD1_HEAD = ["UKRAINE SINKS RUSSIAN", "WARSHIP OFF LIBYA"]
LEAD1_BODY = (
    "Kyiv says seven naval drones sank the Russian corvette Merkury at "
    "Benghazi on Sunday, destroying a Ka-27 helicopter on board. A second "
    "strike hit the cargo ship MV Angara, which Kyiv says Moscow used to "
    "move weapons."
)

LEAD2_KICKER = "NVIDIA - SILICON VALLEY"
LEAD2_HEAD = ["HUANG BACK AT NVIDIA", "AS SHARES SOAR"]
LEAD2_BODY = (
    "Nvidia's board voted unanimously to reinstate Jensen Huang as chief "
    "executive, under two weeks after he resigned. Shares jumped about 30 "
    "percent. The board says his return poses no national security risk."
)

BRIEFS = [
    ("INDONESIA FIRE KILLS 24",
     "A blaze at a candy factory leaves at least 24 dead as rescuers "
     "search for missing workers."),
    ("COP31 ENDS WITH NO DEAL",
     "Climate talks in Antalya collapse without a main agreement. "
     "Negotiations may resume next year."),
    ("RUSSIAN SHIP ABLAZE IN BALTIC",
     "The cargo ship Sparta II catches fire in the Gulf of Finland after "
     "a drone strike."),
    ("KYIV BRACES FOR NEW STRIKES",
     "Zelensky says intelligence shows Russia is planning fresh attacks. "
     "The Dymer toll rises to 11."),
    ("MYANMAR GUILTY OF GENOCIDE",
     "The UN's top court rules Myanmar committed genocide against the "
     "Rohingya minority."),
    ("CHESS CROWN ON THE LINE",
     "World champion Gukesh begins his title defence against Sindarov "
     "in Geneva."),
]

FOOTER = "THE WORLD TODAY - 24 NOVEMBER 2026 - DRAWN ENTIRELY IN CODE"

MARGIN = 48
CONTENT_W = W - 2 * MARGIN


def para(page, x, y, text, scale, color, max_px, leading=None):
    """Draw wrapped paragraph lines; return the y below the last line."""
    lh = leading if leading is not None else 9 * scale
    for line in wrap(text, scale, max_px):
        page.text(x, y, line, scale, color)
        y += lh
    return y


def draw_sea_scene(page, x, y, w, h):
    """Stylised strip: grey sky, navy sea, a corvette silhouette, smoke
    and seven small red drone dots. All rectangles, fully deterministic."""
    page.rect(x, y, w, h, LIGHT)
    sea_y = y + h - 26
    page.rect(x, sea_y, w, 26, NAVY)
    # Smoke plume: stacked grey blocks above the funnel.
    page.rect(x + 430, y + 8, 26, 10, GREY)
    page.rect(x + 446, y + 20, 30, 10, GREY)
    page.rect(x + 462, y + 32, 26, 10, GREY)
    # Funnel and hull.
    page.rect(x + 470, y + 40, 14, 14, INK)
    page.rect(x + 380, y + 54, 260, 16, INK)
    page.rect(x + 360, y + 58, 20, 12, INK)   # bow step
    page.rect(x + 640, y + 58, 16, 12, INK)   # stern step
    # Mast.
    page.rect(x + 520, y + 22, 4, 32, INK)
    page.rect(x + 500, y + 22, 44, 4, INK)
    # Seven naval drones: small red squares in the sky.
    drones = [(90, 14), (170, 30), (250, 12), (700, 18),
              (780, 34), (850, 14), (300, 44)]
    for dx, dy in drones:
        page.rect(x + dx, y + dy, 7, 7, RED)
    # Wake lines.
    page.hline(x + 340, sea_y + 8, 340, PAPER, 2)
    page.hline(x + 380, sea_y + 16, 260, PAPER, 2)


def draw_chip_strip(page, x, y, w, h):
    """Stylised strip: a chip with pins on the left, the share jump on
    the right."""
    page.rect(x, y, w, h, LIGHT)
    # Chip body with pins.
    cx, cy, s = x + 24, y + (h - 56) // 2, 56
    for i in range(4):
        page.rect(cx + 10 + i * 12, cy - 8, 6, 8, NAVY)
        page.rect(cx + 10 + i * 12, cy + s, 6, 8, NAVY)
        page.rect(cx - 8, cy + 10 + i * 12, 8, 6, NAVY)
        page.rect(cx + s, cy + 10 + i * 12, 8, 6, NAVY)
    page.rect(cx, cy, s, s, NAVY)
    page.rect(cx + 16, cy + 16, 24, 24, PAPER)
    page.rect(cx + 24, cy + 24, 8, 8, RED)
    # Text.
    tx = x + 116
    page.text(tx, y + 12, "SHARES JUMP ABOUT 30%", 3, NAVY)
    page.text(tx, y + 44, "BOARD VOTE WAS UNANIMOUS", 2, GREY)


def render():
    page = Page(W, H, PAPER)

    # Masthead.
    y = 24
    y = page.centered(y, MASTHEAD, 6, INK)
    y = 82
    page.hline(MARGIN, y, CONTENT_W, RED, 3)
    # Dateline strip.
    y = 94
    page.text(MARGIN, y, DATELINE_LEFT, 2, GREY)
    rw = page.text_width(DATELINE_RIGHT, 2)
    page.text(W - MARGIN - rw, y, DATELINE_RIGHT, 2, GREY)
    page.hline(MARGIN, 116, CONTENT_W, INK, 2)
    page.hline(MARGIN, 120, CONTENT_W, INK, 1)

    # Lead story 1.
    y = 136
    page.text(MARGIN, y, LEAD1_KICKER, 2, RED)
    y = 160
    for line in LEAD1_HEAD:
        page.text(MARGIN, y, line, 4, INK)
        y += 30
    y = para(page, MARGIN, y + 8, LEAD1_BODY, 2, INK, CONTENT_W)
    y += 14
    draw_sea_scene(page, MARGIN, y, CONTENT_W, 80)
    y += 80 + 16
    page.hline(MARGIN, y, CONTENT_W, INK, 2)
    y += 18

    # Lead story 2.
    page.text(MARGIN, y, LEAD2_KICKER, 2, RED)
    y += 24
    for line in LEAD2_HEAD:
        page.text(MARGIN, y, line, 4, INK)
        y += 30
    y = para(page, MARGIN, y + 8, LEAD2_BODY, 2, INK, CONTENT_W)
    y += 14
    draw_chip_strip(page, MARGIN, y, CONTENT_W, 70)
    y += 70 + 16
    page.hline(MARGIN, y, CONTENT_W, INK, 2)
    y += 20

    # Briefs: two columns, three rows.
    col_w = (CONTENT_W - 40) // 2
    row_y = y
    for row in range(3):
        for col in range(2):
            idx = row * 2 + col
            title, body = BRIEFS[idx]
            bx = MARGIN + col * (col_w + 40)
            page.rect(bx, row_y + 2, 10, 10, RED)
            page.text(bx + 18, row_y, title, 2, INK)
            para(page, bx, row_y + 22, body, 2, GREY, col_w)
        row_y += 84

    # Footer.
    page.hline(MARGIN, 934, CONTENT_W, INK, 2)
    page.centered(948, FOOTER, 2, GREY)
    return page


def main():
    page = render()
    out_dir = "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
        probe = os.path.join(out_dir, ".writetest")
        with open(probe, "wb") as f:
            f.write(b"")
        os.remove(probe)
    except OSError:
        out_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, page)
    print("WROTE %s %d bytes" % (path, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
