#!/usr/bin/env python3
"""THE WORLD TODAY - the news of Saturday 21 November 2026 in one image.

Entry for the make.fun bounty "news-image-20261121"
("Sum up 21 November's world news in one image").

The program draws a dense newspaper front page - masthead, a lead story,
three columns of regional news briefs (bold headline, one tight clause,
named source, flowing with red square separators), a UTC timeline strip
and a date-check footer - into an in-memory framebuffer and writes it as
one 1024x1024 PNG.  Python 3 standard library only, no network at run
time, pure integer arithmetic, so two runs write byte-identical files.

The type is a hand-drawn proportional bitmap font on a 13-row grid
(capitals 10 rows tall, x-height 6) - far larger and cleaner than the
5x7 dot-matrix of the first version, and readable at full size.

Output: $MAKEFUN_OUTPUT_DIR/entry.png when that variable is set, else
/output/entry.png; if that directory cannot be created or written, the
image falls back to ./entry.png in the working directory.
"""

import itertools
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- colours
PAPER = (247, 243, 232)      # newsprint
INK = (20, 18, 14)           # near-black
ACCENT = (164, 22, 26)       # press red
GREY = (92, 86, 74)          # source tags, rules
WHITE = (250, 248, 242)
BODY = (56, 51, 43)          # detail text
RULE_LT = (203, 196, 178)    # faint rule

# ------------------------------------------------------------------- font
# A proportional bitmap font drawn for this entry on a 13-row grid
# (rows 0..12).  Capitals sit on rows 1..10, lower-case x-height on rows
# 5..10, ascenders reach row 1 and descenders row 12.  Each glyph is
# (width, {row: pattern}); '#' is a filled cell.  Because the font is
# proportional, text packs the way real type does instead of on a rigid
# monospace grid, which is what makes 52 briefs in genuinely readable
# type fit one page.

FONT_SPEC = {
"A": (6, {1:".####.",2:"#....#",3:"#....#",4:"#....#",5:"######",6:"#....#",7:"#....#",8:"#....#",9:"#....#",10:"#....#"}),
"B": (6, {1:"####..",2:"#...#.",3:"#...#.",4:"#...#.",5:"####..",6:"#...#.",7:"#...#.",8:"#...#.",9:"#...#.",10:"####.."}),
"C": (6, {1:".####.",2:"#....#",3:"#.....",4:"#.....",5:"#.....",6:"#.....",7:"#.....",8:"#.....",9:"#....#",10:".####."}),
"D": (6, {1:"####..",2:"#...#.",3:"#...#.",4:"#...#.",5:"#...#.",6:"#...#.",7:"#...#.",8:"#...#.",9:"#...#.",10:"####.."}),
"E": (5, {1:"#####",2:"#....",3:"#....",4:"####.",5:"#....",6:"#....",7:"#....",8:"#....",9:"#....",10:"#####"}),
"F": (5, {1:"#####",2:"#....",3:"#....",4:"####.",5:"#....",6:"#....",7:"#....",8:"#....",9:"#....",10:"#...."}),
"G": (6, {1:".####.",2:"#....#",3:"#.....",4:"#.....",5:"#..###",6:"#...#.",7:"#...#.",8:"#...#.",9:"#....#",10:".####."}),
"H": (6, {1:"#....#",2:"#....#",3:"#....#",4:"#....#",5:"######",6:"#....#",7:"#....#",8:"#....#",9:"#....#",10:"#....#"}),
"I": (3, {1:"###",2:".#.",3:".#.",4:".#.",5:".#.",6:".#.",7:".#.",8:".#.",9:".#.",10:"###"}),
"J": (5, {1:"..###",2:"...#.",3:"...#.",4:"...#.",5:"...#.",6:"...#.",7:"...#.",8:"...#.",9:"#..#.",10:".##.."}),
"K": (6, {1:"#....#",2:"#...#.",3:"#..#..",4:"#.#...",5:"##....",6:"#.#...",7:"#..#..",8:"#...#.",9:"#...#.",10:"#....#"}),
"L": (5, {1:"#....",2:"#....",3:"#....",4:"#....",5:"#....",6:"#....",7:"#....",8:"#....",9:"#....",10:"#####"}),
"M": (7, {1:"#.....#",2:"##...##",3:"#.#.#.#",4:"#.#.#.#",5:"#..#..#",6:"#.....#",7:"#.....#",8:"#.....#",9:"#.....#",10:"#.....#"}),
"N": (6, {1:"#....#",2:"##...#",3:"#.#..#",4:"#.#..#",5:"#..#.#",6:"#..#.#",7:"#...##",8:"#...##",9:"#....#",10:"#....#"}),
"O": (6, {1:".####.",2:"#....#",3:"#....#",4:"#....#",5:"#....#",6:"#....#",7:"#....#",8:"#....#",9:"#....#",10:".####."}),
"P": (6, {1:"####..",2:"#...#.",3:"#...#.",4:"#...#.",5:"####..",6:"#.....",7:"#.....",8:"#.....",9:"#.....",10:"#....."}),
"Q": (6, {1:".####.",2:"#....#",3:"#....#",4:"#....#",5:"#....#",6:"#....#",7:"#....#",8:"#.#.#.",9:"#..#..",10:".##.##"}),
"R": (6, {1:"####..",2:"#...#.",3:"#...#.",4:"#...#.",5:"####..",6:"#.#...",7:"#..#..",8:"#...#.",9:"#...#.",10:"#...#."}),
"S": (6, {1:".####.",2:"#....#",3:"#.....",4:"#.....",5:".####.",6:".....#",7:".....#",8:".....#",9:"#....#",10:".####."}),
"T": (6, {1:"######",2:"...#..",3:"...#..",4:"...#..",5:"...#..",6:"...#..",7:"...#..",8:"...#..",9:"...#..",10:"...#.."}),
"U": (6, {1:"#....#",2:"#....#",3:"#....#",4:"#....#",5:"#....#",6:"#....#",7:"#....#",8:"#....#",9:"#....#",10:".####."}),
"V": (7, {1:"#.....#",2:"#.....#",3:"#.....#",4:"#.....#",5:".#...#.",6:".#...#.",7:"..#.#..",8:"..#.#..",9:"...#...",10:"...#..."}),
"W": (7, {1:"#.....#",2:"#.....#",3:"#.....#",4:"#.....#",5:"#..#..#",6:"#..#..#",7:"#.#.#.#",8:"#.#.#.#",9:"##...##",10:"#.....#"}),
"X": (6, {1:"#....#",2:".#..#.",3:".#..#.",4:"..##..",5:"..##..",6:".#..#.",7:".#..#.",8:"#....#",9:"#....#",10:"#....#"}),
"Y": (6, {1:"#....#",2:"#....#",3:".#..#.",4:".#..#.",5:"..##..",6:"...#..",7:"...#..",8:"...#..",9:"...#..",10:"...#.."}),
"Z": (6, {1:"######",2:".....#",3:"....#.",4:"...#..",5:"..#...",6:"..#...",7:".#....",8:".#....",9:"#.....",10:"######"}),
"0": (5, {1:".###.",2:"#...#",3:"#...#",4:"#...#",5:"#...#",6:"#...#",7:"#...#",8:"#...#",9:"#...#",10:".###."}),
"1": (4, {1:"..#.",2:".##.",3:".#..",4:".#..",5:".#..",6:".#..",7:".#..",8:".#..",9:".#..",10:".###"}),
"2": (6, {1:".####.",2:"#....#",3:".....#",4:".....#",5:"....#.",6:"...#..",7:"..#...",8:".#....",9:"#.....",10:"######"}),
"3": (6, {1:"####..",2:"....#.",3:"....#.",4:"....#.",5:".###..",6:"....#.",7:"....#.",8:"....#.",9:"#...#.",10:".###.."}),
"4": (6, {1:"...#..",2:"..##..",3:"..#.#.",4:".#..#.",5:"#...#.",6:"######",7:"....#.",8:"....#.",9:"....#.",10:"....#."}),
"5": (6, {1:"######",2:"#.....",3:"#.....",4:"#####.",5:".....#",6:".....#",7:".....#",8:".....#",9:"#....#",10:".####."}),
"6": (6, {1:"..##..",2:".#....",3:"#.....",4:"#.....",5:"####..",6:"#...#.",7:"#...#.",8:"#...#.",9:"#...#.",10:".###.."}),
"7": (6, {1:"######",2:".....#",3:".....#",4:"....#.",5:"....#.",6:"...#..",7:"...#..",8:"..#...",9:"..#...",10:"..#..."}),
"8": (6, {1:".####.",2:"#....#",3:"#....#",4:"#....#",5:".####.",6:"#....#",7:"#....#",8:"#....#",9:"#....#",10:".####."}),
"9": (6, {1:".####.",2:"#....#",3:"#....#",4:"#....#",5:".#####",6:".....#",7:".....#",8:".....#",9:"....#.",10:".##..."}),
"a": (5, {5:".###.",6:"....#",7:".####",8:"#...#",9:"#...#",10:".####"}),
"b": (5, {1:"#....",2:"#....",3:"#....",4:"#....",5:"####.",6:"#...#",7:"#...#",8:"#...#",9:"#...#",10:"####."}),
"c": (5, {5:".####",6:"#....",7:"#....",8:"#....",9:"#....",10:".####"}),
"d": (5, {1:"....#",2:"....#",3:"....#",4:"....#",5:".####",6:"#...#",7:"#...#",8:"#...#",9:"#...#",10:".####"}),
"e": (5, {5:".###.",6:"#...#",7:"#####",8:"#....",9:"#....",10:".###."}),
"f": (4, {1:".##.",2:".#..",3:".#..",4:"####",5:".#..",6:".#..",7:".#..",8:".#..",9:".#..",10:".#.."}),
"g": (5, {5:".####",6:"#...#",7:"#...#",8:"#...#",9:".####",10:"....#",11:"#...#",12:".###."}),
"h": (5, {1:"#....",2:"#....",3:"#....",4:"#....",5:"####.",6:"#...#",7:"#...#",8:"#...#",9:"#...#",10:"#...#"}),
"i": (2, {3:"##",5:"#.",6:"#.",7:"#.",8:"#.",9:"#.",10:"#."}),
"j": (3, {3:".##",5:"..#",6:"..#",7:"..#",8:"..#",9:"..#",10:"..#",11:"..#",12:".#."}),
"k": (5, {1:"#....",2:"#....",3:"#....",4:"#....",5:"#..#.",6:"#.#..",7:"##...",8:"#.#..",9:"#..#.",10:"#..#."}),
"l": (3, {1:".#.",2:".#.",3:".#.",4:".#.",5:".#.",6:".#.",7:".#.",8:".#.",9:".#.",10:".##"}),
"m": (7, {5:"##.###.",6:"#.#.#.#",7:"#.#.#.#",8:"#.#.#.#",9:"#.#.#.#",10:"#.#.#.#"}),
"n": (5, {5:"####.",6:"#...#",7:"#...#",8:"#...#",9:"#...#",10:"#...#"}),
"o": (5, {5:".###.",6:"#...#",7:"#...#",8:"#...#",9:"#...#",10:".###."}),
"p": (5, {5:"####.",6:"#...#",7:"#...#",8:"#...#",9:"####.",10:"#....",11:"#....",12:"#...."}),
"q": (5, {5:".####",6:"#...#",7:"#...#",8:"#...#",9:".####",10:"....#",11:"....#",12:"....#"}),
"r": (4, {5:"##.#",6:"#..#",7:"#...",8:"#...",9:"#...",10:"#..."}),
"s": (5, {5:".####",6:"#....",7:".###.",8:"....#",9:"....#",10:"####."}),
"t": (4, {1:".#..",2:".#..",3:".#..",4:"####",5:".#..",6:".#..",7:".#..",8:".#..",9:".#..",10:"..##"}),
"u": (5, {5:"#...#",6:"#...#",7:"#...#",8:"#...#",9:"#..##",10:".##.#"}),
"v": (5, {5:"#...#",6:"#...#",7:"#...#",8:"#...#",9:".#.#.",10:"..#.."}),
"w": (7, {5:"#.....#",6:"#.....#",7:"#..#..#",8:"#.#.#.#",9:"#.#.#.#",10:".#...#."}),
"x": (5, {5:"#...#",6:".#.#.",7:"..#..",8:"..#..",9:".#.#.",10:"#...#"}),
"y": (5, {5:"#...#",6:"#...#",7:"#...#",8:".#.#.",9:"..#..",10:"..#..",11:".#...",12:".#..."}),
"z": (5, {5:"#####",6:"....#",7:"...#.",8:"..#..",9:".#...",10:"#####"}),
" ": (3, {}),
".": (2, {9:"##",10:"##"}),
",": (3, {10:"##.",11:"##.",12:".#."}),
"'": (2, {1:"##",2:"#."}),
"-": (4, {7:"####"}),
":": (2, {5:"##",6:"##",9:"##",10:"##"}),
";": (3, {5:"##.",6:"##.",9:"##.",10:"##.",11:".#.",12:"#.."}),
"!": (2, {1:"##",2:"##",3:"##",4:"##",5:"##",6:"##",7:"##",9:"##",10:"##"}),
"?": (5, {1:".###.",2:"#...#",3:"....#",4:"...#.",5:"..#..",6:"..#..",7:"..#..",10:".##.."}),
"(": (4, {1:"...#",2:"..#.",3:"..#.",4:".#..",5:".#..",6:".#..",7:".#..",8:"..#.",9:"..#.",10:"...#"}),
")": (4, {1:"#...",2:".#..",3:".#..",4:"..#.",5:"..#.",6:"..#.",7:"..#.",8:".#..",9:".#..",10:"#..."}),
"/": (5, {1:"....#",2:"....#",3:"...#.",4:"...#.",5:"..#..",6:"..#..",7:".#...",8:".#...",9:"#....",10:"#...."}),
"&": (6, {1:".###..",2:"#...#.",3:"#...#.",4:".###..",5:".#....",6:"#.##..",7:"##..#.",8:"#...#.",9:"#...##",10:".####."}),
"$": (5, {1:"..#..",2:".####",3:"#.#..",4:"#.#..",5:".###.",6:"..#.#",7:"..#.#",8:".####",9:"..#..",10:"..#.."}),
'"': (3, {1:"#.#",2:"#.#"}),
"\u00b7": (2, {7:"##",8:"##"}),
}

ROWS = 13


def _build_font():
    font = {}
    for ch, (w, rows) in FONT_SPEC.items():
        grid = []
        for r in range(ROWS):
            pat = rows.get(r, "." * w)
            assert len(pat) == w, (ch, r)
            grid.append(pat)
        font[ch] = tuple(grid)
    return font


FONT = _build_font()
WIDTH = {ch: spec[0] for ch, spec in FONT_SPEC.items()}
SEP = "\x01"          # story separator token: a small red square
SEP_W = 9             # its advance at scale 1 (5px square plus air)

# Typographic characters in the copy are folded onto the glyphs above.
_FOLD = {
    "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...",
    "\u00a3": "GBP", "\u20ac": "EUR",
}


def clean(text):
    """Fold any character the font lacks onto one it has, else '?'."""
    out = []
    for ch in text:
        if ch in FONT or ch == SEP:
            out.append(ch)
        elif ch in _FOLD:
            out.append(_FOLD[ch])
        else:
            out.append("?")
    return "".join(out)


def char_adv(ch, bold):
    """Horizontal advance of one character at scale 1."""
    if ch == SEP:
        return SEP_W
    return WIDTH[ch] + (2 if bold else 1)


def text_w(s, scale=1, bold=False):
    """Pixel width of a line of text at the given scale."""
    s = clean(s)
    if not s:
        return 0
    trail = 0 if s.endswith(SEP) else (2 if bold else 1)
    return (sum(char_adv(c, bold) for c in s) - trail) * scale


# -------------------------------------------------------------- framebuffer

class Page:
    """An RGB framebuffer with rectangle and bitmap-text drawing."""

    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.px = bytearray(bg) * (width * height)

    def rect(self, x, y, w, h, rgb):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(rgb) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def text(self, x, y, s, scale, rgb, bold=False):
        """Draw one line of text; returns the x just past its end."""
        s = clean(s)
        cx = x
        for ch in s:
            if ch == SEP:
                self.rect(cx + 2 * scale, y + 6 * scale,
                          5 * scale, 5 * scale, ACCENT)
                cx += SEP_W * scale
                continue
            glyph = FONT.get(ch, FONT["?"])
            w = WIDTH[ch]
            for gy, row in enumerate(glyph):
                for gx, cell in enumerate(row):
                    if cell == "#":
                        self.rect(cx + gx * scale, y + gy * scale,
                                  scale, scale, rgb)
                        if bold:
                            # A 1px echo emboldens at any scale.
                            self.rect(cx + gx * scale + 1, y + gy * scale,
                                      scale, scale, rgb)
            cx += (w + (2 if bold else 1)) * scale
        return cx

    def png_bytes(self):
        raw = bytearray()
        stride = self.w * 3
        for yy in range(self.h):
            raw.append(0)  # filter: none, on every row
            raw += self.px[yy * stride:(yy + 1) * stride]

        def chunk(tag, data):
            body = tag + data
            return (struct.pack(">I", len(data)) + body
                    + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                + chunk(b"IEND", b""))


def wrap_runs(runs, scale, max_w):
    """Wrap styled runs into lines.

    runs is a list of (text, bold, rgb) pieces that flow together as one
    paragraph.  Returns a list of lines; each line is a list of
    (word, bold, rgb).  Every word is measured with the proportional
    font, so no line ever exceeds max_w; a word longer than the line
    (none in this copy) is hard-split rather than clipped.
    """
    words = []
    for text, bold, rgb in runs:
        for word in clean(text).split(" "):
            if word:
                words.append((word, bold, rgb))
    space_w = text_w(" ", scale)
    lines = []
    line = []
    line_w = 0
    for word, bold, rgb in words:
        ww = text_w(word, scale, bold)
        while ww > max_w:  # hard-split an over-long word
            take, acc = 0, 0
            for ch in word:
                a = char_adv(ch, bold) * scale
                if take and acc + a > max_w:
                    break
                acc += a
                take += 1
            head, word = word[:take], word[take:]
            if line:
                lines.append(line)
                line, line_w = [], 0
            lines.append([(head, bold, rgb)])
            ww = text_w(word, scale, bold) if word else -1
        if ww < 0:
            continue
        add = ww if not line else ww + space_w
        if line and line_w + add > max_w:
            lines.append(line)
            line, line_w = [], 0
            add = ww
        line.append((word, bold, rgb))
        line_w += add
    if line:
        lines.append(line)
    return lines


def draw_runs(page, x, y, runs, scale, line_h, max_w):
    """Draw a wrapped paragraph; returns the y just past its last line."""
    lines = wrap_runs(runs, scale, max_w)
    space_w = text_w(" ", scale)
    for line in lines:
        cx = x
        for word, bold, rgb in line:
            cx = page.text(cx, y, word, scale, rgb, bold)
            cx += space_w
        y += line_h
    return y

# ------------------------------------------------------------------ content
# Researched on Saturday 21 November 2026 from the day's reporting by the
# outlets named in each source tag.  Only events that happened, or were
# first reported, on 21 November 2026 (in some time zone) are included.
# Copy is kept wire-tight: a headline plus one short clause per story.
# This is the same verified story set as the first version of the entry;
# only the rendering changed.

LEAD = ('Russian missile comes down in Poland, Tusk says', "A Russian missile came down in Poland during the night's strike on Ukraine, as Kyiv's allies held an exercise nearby. PM Tusk called it a deliberate provocation; NATO called it a grave airspace violation.", 'BBC')

# (section name, [(headline, detail, source), ...]) - most important first.
SECTIONS = [
    ('EUROPE', [
        ('Second night of strikes hits 18 sites in Ukraine',
         'Strikes hit 18 locations overnight; Austrian and Dutch embassies in Kyiv were damaged, no staff hurt.', 'BBC'),
        ("Zelensky: Putin is 'a killer'",
         'He reacted after Trump called the Russian leader his friend, as the attacks on Kyiv continued.', 'BBC'),
        ('Burnham: UK to explore even closer EU ties',
         'After the Brussels deal on food, carbon and youth mobility, the PM said Britain would go further.', 'BBC'),
        ('Gen Z protests sweep 25 European countries',
         'Youth-led cost-of-living protests spread to 25 countries, the widest wave of demonstrations this year.', 'One Turn'),
        ('Denmark foils alleged Russian murder plot',
         'The PET service accused Russia of plotting to kill a US-Ukrainian rapper on Danish soil.', 'BBC'),
        ('French officers sentenced over Zecler beating',
         'A court upheld racism as an aggravating factor in the 2020 beating of producer Michel Zecler.', 'BBC'),
        ('Spain heads toward a 29 November election',
         "Conservative support is growing and the government's majority is fraying ahead of the vote.", 'One Turn'),
        ('Burnham: my big worry is Trump and Iran',
         "Britain's PM said his biggest worry is neither Brexit nor welfare, but Trump and the Iran war.", 'Japan Times'),
    ]),
    ('AMERICAS', [
        ('Congress heads toward a Christmas shutdown',
         'Fights over Iran war funding and a $350bn Pentagon demand threaten to derail any budget deal.', 'Reuters'),
        ('Trump ousts cyber chief after tech outages',
         'The White House removed its cyber-security director after outages and breaches drew criticism.', 'BBC'),
        ('FBI and farm ministry breached by hackers',
         "Hackers breached the FBI's criminal database and Agriculture Department systems, reports said.", 'Japan Times'),
        ('Man convicted of starting Palisades fire',
         'A Los Angeles man was convicted over the wildfire that killed 12 people and destroyed 6,800 buildings.', 'BBC'),
        ('Mamdani: Rikers jail to close by 2032',
         "New York's mayor announced a plan to shut the troubled Rikers Island jail complex by 2032.", 'BBC'),
        ("Court lets Trump end Venezuelans' protection",
         'An appeals court let the administration end protected status for about 600,000 Venezuelans.', 'AP'),
        ('19 years for plot to kill Sikh separatist',
         'An Indian man was jailed in the US over the plot to assassinate separatist leader Pannun.', 'BBC'),
        ("Trump: flight systems 'ancient' but safe",
         'After a nationwide ground stop, the president called US flight systems outdated but secure.', 'BBC'),
    ]),
    ('MIDDLE EAST', [
        ('Coalition downs 3 Houthi missiles at Riyadh',
         'Three ballistic missiles fired at Riyadh were intercepted; emergency alerts were issued, then lifted.', 'Al Jazeera'),
        ('Tanker hit leaving the Strait of Hormuz',
         'An unknown projectile struck a tanker; UKMTO counts six tanker attacks around the strait in a week.', 'UKMTO'),
        ("Iran: Hormuz could reopen 'in two hours'",
         'FM Araghchi said the US deal is off the table, but the strait could reopen fast if terms are met.', 'Al Jazeera'),
        ("Air attack reported on Yemen's Mocha port",
         'Houthi media reported a coalition strike on Mocha, as Houthis demanded Saudi ports be evacuated.', 'Outlook India'),
        ('Drone strike wounds three in Gaza',
         'An Israeli drone strike in al-Mawasi wounded three; a man was shot dead near Ramallah.', 'Outlook India'),
        ('Pakistan condemns attack on Riyadh',
         "PM Shehbaz Sharif condemned the Houthi attack on Riyadh's financial district as unacceptable.", 'Al Jazeera'),
        ('Myanmar ruling may bolster Gaza ICJ case',
         "Lawyers say the Myanmar genocide judgment may strengthen South Africa's Gaza case against Israel.", 'Japan Times'),
    ]),
    ('ASIA-PACIFIC', [
        ('Japan wary of regular three-power summits',
         'Tokyo is wary of Washington, Moscow and Beijing making the Shenzhen summits a regular fixture.', 'Japan Times'),
        ('Why Kim did not meet Trump, despite hype',
         'For all the speculation, Kim Jong Un never met Trump - a look at what Pyongyang wanted instead.', 'Japan Times'),
        ('South Korea catches 111 exam cheats',
         'New measures caught 111 students cheating in the high-stakes university entrance exams.', 'BBC'),
        ("Nepal PM's India test on first visit",
         "Balendra Shah's first India visit puts trade and connectivity at the top of the agenda.", 'BBC'),
        ('India launches first H5N1 bird-flu vaccine',
         'India introduced its first home-developed H5N1 vaccine for chickens, to protect poultry farms.', 'PIB'),
        ('Modi opens SCO dialogue forum in Delhi',
         'PM Modi opened a three-day SCO forum in New Delhi meant to boost cultural cooperation.', 'PIB'),
    ]),
    ('AFRICA', [
        ("South Africa's first female deputy president dies",
         'Phumzile Mlambo-Ngcuka, also a former UN Women chief, has died at the age of 71.', 'Reuters'),
        ("ANC fights to hold South Africa's big cities",
         'After a local election setback, the ANC resists copying its national power-sharing deal locally.', 'BBC'),
        ('Nearly 600 women killed in three months',
         'New figures renew anger over femicide in South Africa, with nearly 600 women killed in a quarter.', 'BBC'),
        ('Nigeria moves to end jail for suicide bids',
         'Nigeria is moving to scrap prison terms for attempted suicide, a colonial-era law.', 'BBC'),
    ]),
    ('BUSINESS', [
        ("Wall Street's worst week in over 18 months",
         "The AI sell-off erased the Nasdaq's 2026 gains and pushed the S&P 500 into correction.", 'AP'),
        ('Anthropic stumble checks the AI trade',
         "The shares' post-debut slide is a reality check days after the record $81bn market debut.", 'Japan Times'),
        ('Judge approves $7.25bn Roundup settlement',
         'A US judge approved the $7.25bn settlement of cancer claims over the Roundup weedkiller.', 'BBC'),
        ('Honda and Toyota recall 1.6m vehicles',
         'The carmakers recalled 1.6 million vehicles over a Takata airbag rupture risk.', 'Japan Times'),
        ('Bitcoin slides toward $62,000 in rout',
         'Crypto liquidations topped $2bn as bitcoin fell toward $62,000 in the wider sell-off.', 'IQMIA'),
        ('Euro zone consumer morale beats forecasts',
         'Consumer confidence rose to -16.9 in November, the Commission said, beating forecasts of a fall.', 'Reuters'),
    ]),
    ('TECH & SCIENCE', [
        ("Claude may have solved maths' greatest riddle",
         'An Anthropic researcher said Claude had solved a legendary open problem; experts are checking.', 'Japan Times'),
        ('Cancer pill clears tumours in trial',
         'The pill daraxonrasib made pancreatic cancer undetectable on scans in one in 12 trial patients.', 'One Turn'),
        ("Path opens toward a 'killer robots' pact",
         'Negotiators opened a path to a treaty on autonomous weapons after years of deadlock.', 'Japan Times'),
        ('Trump threatens overseas AI centre ban',
         'The president threatened to bar US firms from building AI data centres overseas.', 'BBC'),
        ('GTA VI smashes records, sales top $2.3bn',
         'Grand Theft Auto VI drew rave reviews as estimated sales passed $2.3bn, a record opening.', 'BBC'),
        ('US declassifies more UFO footage',
         'The US released more declassified footage of unidentified objects filmed over the Middle East.', 'BBC'),
    ]),
    ('SPORT', [
        ('Antonelli fastest, Verstappen takes pole',
         "Antonelli's 1:33.893 topped Las Vegas qualifying, but a grid penalty hands pole to Verstappen.", 'GPToday'),
        ('Lakers rally past Kings 106-104',
         'Luka Doncic scored 25 points with eight assists as the Lakers rallied to beat Sacramento.', 'Reuters'),
        ('Rahul hits 136 as India take charge',
         'Rahul made 136 and Gill 98 as India reached 486 for 4 on day three against New Zealand.', 'Sunday Guardian'),
        ('Shimada leads Finlandia Trophy',
         "Japan's Mao Shimada grabbed the lead at the Finlandia Trophy after the short program.", 'Japan Times'),
        ('Alcaraz sets up ATP semi with Shelton',
         'Alcaraz beat Cobolli 6-4, 6-1 at the ATP Finals despite a hamstring worry, and faces Shelton.', 'Pollar'),
        ('Australia, England open T20 series at MCG',
         'The five-match Twenty20 series began at the Melbourne Cricket Ground on Saturday.', 'Sunday Guardian'),
    ]),
]

SECTION_ORDER = ["EUROPE", "AMERICAS", "MIDDLE EAST", "ASIA-PACIFIC",
                 "AFRICA", "BUSINESS", "TECH & SCIENCE", "SPORT"]

# The day in UTC: (time, label, source) - times as first reported (UTC).
# Labels are shortened for the strip; the full facts are in the sections
# and the lead above.
TIMELINE = [
    ('00:01', 'Mamdani: Rikers jail to close by 2032', 'BBC'),
    ('01:02', 'Probe: $811m migrant bail scam kept running', 'BBC'),
    ('02:09', 'Tusk: Russian missile down in Poland', 'BBC'),
    ('04:32', "Zelensky calls Putin 'a killer'", 'BBC'),
    ('05:44', 'South Africa: Mlambo-Ngcuka dies at 71', 'Reuters'),
    ('07:06', "Coalition air attack on Yemen's Mocha port", 'Outlook India'),
    ('07:56', 'Tanker hit leaving Strait of Hormuz', 'UKMTO'),
]

SOURCES_LINE = 'Sources include BBC, Reuters, AP, Al Jazeera, the Japan Times, One Turn, UKMTO, Outlook India and PIB.'
DATE_CHECK = 'Date check: every event on this page happened, or was first reported, on Saturday 21 November 2026. All times UTC.'

# ------------------------------------------------------------------- layout
# Three columns of flowing briefs.  Within a section the stories run on
# as one paragraph - bold headline, detail, source tag, red square -
# which packs the page the way real newspaper briefs do and leaves no
# half-empty last lines.  Sections are assigned to columns by an exact
# search that minimises the tallest column, so no column is left with a
# dead gap while another overflows.  Nothing is dropped: if a section
# did not fit, the plan would overflow visibly rather than clip text.

MX = 16                      # page margin
CW = W - 2 * MX              # content width (992)
NCOL = 3
GUTTER = 16
COLW = (CW - (NCOL - 1) * GUTTER) // NCOL   # 320
COL_X = tuple(MX + i * (COLW + GUTTER) for i in range(NCOL))
COL_TOP = 192
COL_BOT = 900
LINE_H = 13                  # body lines: 13-row glyphs, 1px of air
HDR_H = 28                   # section header bar
HDR_GAP = 4                  # bar to first text line
SEC_GAP = 7                  # between sections in a column


def section_runs(stories):
    runs = []
    for i, (headline, detail, source) in enumerate(stories):
        if i:
            runs.append((" " + SEP + " ", False, ACCENT))
        runs.append((headline.upper(), True, INK))
        runs.append((" " + detail, False, BODY))
        runs.append((" (" + source + ")", False, GREY))
    return runs


def section_height(name, stories):
    lines = wrap_runs(section_runs(stories), 1, COLW)
    return HDR_H + HDR_GAP + len(lines) * LINE_H


def plan_columns():
    """Assign each section to a column, minimising the tallest column.

    Returns (plan, total, bottoms): plan is a list of
    (section name, column index, top y, stories); bottoms is the final
    y of each column.  The search is exhaustive over 3**8 assignments
    with a fixed iteration order, so the plan is deterministic.
    """
    by_name = dict(SECTIONS)
    heights = {name: section_height(name, by_name[name])
               for name in SECTION_ORDER}
    best = None
    for assign in itertools.product(range(NCOL),
                                    repeat=len(SECTION_ORDER)):
        col_h = [0] * NCOL
        counts = [0] * NCOL
        for name, ci in zip(SECTION_ORDER, assign):
            col_h[ci] += heights[name] + (SEC_GAP if counts[ci] else 0)
            counts[ci] += 1
        key = (max(col_h), max(col_h) - min(col_h))
        if best is None or key < best[0]:
            best = (key, assign)
    assign = best[1]
    plan = []
    col_y = [COL_TOP] * NCOL
    for name, ci in zip(SECTION_ORDER, assign):
        plan.append((name, ci, col_y[ci], by_name[name]))
        col_y[ci] += heights[name] + SEC_GAP
    total = sum(len(stories) for _, stories in SECTIONS)
    bottoms = [y - SEC_GAP for y in col_y]
    return plan, total, bottoms


def draw_masthead(page, total):
    page.rect(MX, 8, CW, 3, INK)
    title = "THE WORLD TODAY"
    page.text((W - text_w(title, 5, True)) // 2, 11, title, 5, INK,
              bold=True)
    date = "SATURDAY 21 NOVEMBER 2026"
    page.text((W - text_w(date, 2, True)) // 2, 63, date, 2, ACCENT,
              bold=True)
    page.text(MX, 69, "THE DAY'S NEWS, IN ONE IMAGE", 1, GREY)
    right = "ALL TIMES UTC"
    page.text(MX + CW - text_w(right, 1), 69, right, 1, GREY)
    page.rect(MX, 88, CW, 3, INK)
    page.rect(MX, 94, CW, 1, INK)
    left = "%d SOURCED STORIES - EACH NAMED TO ITS OUTLET" % total
    page.text(MX, 99, left, 1, INK, bold=True)
    right = "PLUS A UTC TIMELINE AND A DATE CHECK"
    page.text(MX + CW - text_w(right, 1), 99, right, 1, GREY)


def draw_lead(page):
    headline, detail, source = LEAD
    page.text(MX, 115, "THE LEAD", 1, ACCENT, bold=True)
    page.rect(MX + text_w("THE LEAD", 1, True) + 8, 121, 120, 1, RULE_LT)
    page.text(MX, 129, headline.upper(), 2, INK, bold=True)
    runs = [(detail, False, BODY), (" (" + source + ")", False, GREY)]
    draw_runs(page, MX, 155, runs, 1, 13, CW)
    page.rect(MX, 186, CW, 1, RULE_LT)


def draw_columns(page, plan):
    for gi in range(NCOL - 1):
        gx = MX + COLW + GUTTER // 2 - 1 + gi * (COLW + GUTTER)
        page.rect(gx, COL_TOP, 1, COL_BOT - COL_TOP, RULE_LT)
    for name, ci, y, stories in plan:
        x = COL_X[ci]
        page.rect(x, y, COLW, HDR_H, INK)
        page.text(x + 8, y + 3, name, 2, WHITE, bold=True)
        tag = "%d STORIES" % len(stories)
        page.text(x + COLW - 8 - text_w(tag, 1), y + 9, tag, 1, WHITE)
        draw_runs(page, x, y + HDR_H + HDR_GAP,
                  section_runs(stories), 1, LINE_H, COLW)


def draw_timeline(page):
    y = 906
    page.rect(MX, y, CW, 22, INK)
    page.text(MX + 8, y - 1, "THE DAY IN UTC", 2, WHITE, bold=True)
    tag = "SATURDAY 21 NOVEMBER 2026, HOUR BY HOUR"
    page.text(MX + CW - 8 - text_w(tag, 1), y + 6, tag, 1, WHITE)
    for hour in range(0, 25, 4):
        tx = MX + (CW * hour) // 24
        label = "%02d:00" % hour
        lw = text_w(label, 1)
        lx = min(max(tx - lw // 2, MX), MX + CW - lw)
        page.text(lx, 932, label, 1, GREY)
        page.rect(tx, 944, 1, 5, GREY)
    page.rect(MX, 946, CW, 1, GREY)
    for time_s, _label, _src in TIMELINE:
        hh = int(time_s[:2])
        mm = int(time_s[3:])
        tx = MX + (CW * (hh * 60 + mm)) // (24 * 60)
        page.rect(tx - 2, 944, 5, 5, ACCENT)
    runs = []
    for i, (time_s, label, source) in enumerate(TIMELINE):
        if i:
            runs.append((" \u00b7 ", False, GREY))
        runs.append((time_s + " ", True, ACCENT))
        runs.append((label, False, INK))
        runs.append((" (" + source + ")", False, GREY))
    draw_runs(page, MX, 951, runs, 1, 12, CW)


def draw_footer(page, total):
    page.rect(MX, 980, CW, 2, INK)
    line1 = ("%d stories on this page, each as reported by the outlet "
             "named after it." % total)
    page.text(MX, 986, line1, 1, INK)
    page.text(MX, 998, DATE_CHECK, 1, GREY)
    page.text(MX, 1010, SOURCES_LINE, 1, GREY)


def build():
    page = Page(W, H, PAPER)
    plan, placed, bottoms = plan_columns()
    total = placed + 1  # plus the lead story
    draw_masthead(page, total)
    draw_lead(page)
    draw_columns(page, plan)
    draw_timeline(page)
    draw_footer(page, total)
    if os.environ.get("NEWS_DEBUG"):
        import sys
        print("plan bottoms: %s (limit %d)" % (bottoms, COL_BOT),
              file=sys.stderr)
        assert max(bottoms) <= COL_BOT, "column overflow"
    return page, total


def main():
    page, total = build()
    data = page.png_bytes()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "entry.png")
        with open(path, "wb") as fh:
            fh.write(data)
    except OSError:
        path = os.path.join(".", "entry.png")
        with open(path, "wb") as fh:
            fh.write(data)
    print("wrote %s: %d bytes, %d stories" % (path, len(data), total))


if __name__ == "__main__":
    main()
