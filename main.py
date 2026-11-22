#!/usr/bin/env python3
"""THE WORLD TODAY - Saturday 21 November 2026.

Renders one day of world news as a single 1024x1024 newspaper front
page (entry.png) for the make.fun news-image-20261121 bounty.

Design notes
------------
* Pure Python 3 standard library (itertools, os, struct, zlib).
* The page is drawn into an in-memory RGB framebuffer and encoded as
  a PNG directly (IHDR/IDAT/IEND, zlib stream) - no image libraries.
* Type is a hand-drawn proportional bitmap font on a 13-row grid:
  capitals stand 10 rows tall, lower case sits on a 7-row x-height
  with ascenders and descenders, and every glyph carries its own
  width, so text is measured exactly and wrapped inside its column.
* Stories flow as continuous briefs: a bold headline, the detail in
  sentence case, and the source in red, separated by a small red
  square.  The eight sections are shared between three columns by an
  exact search that minimises the tallest column.
* Output is deterministic: two runs produce byte-identical files.
"""

import os
import struct
import zlib
from itertools import combinations

# ------------------------------------------------------------------ canvas
W = H = 1024
PAPER = (247, 243, 232)          # newsprint
INK = (20, 18, 14)               # press black
RED = (164, 22, 26)              # press red

MARGIN = 16
GUTTER = 8
COLW = (W - 2 * MARGIN - 2 * GUTTER) // 3   # 325 px text columns
PITCH = 12                       # body line pitch (13-row grid)
HEAD_PITCH = 26                  # lead headline pitch at scale 2
BAR_H = 15                       # section / band header bar height
BAR_GAP = 3                      # gap under a header bar
STORY_GAP = 2                    # gap between story briefs
SECTION_GAP = 6                  # gap after a section

# ------------------------------------------------------------------ font
# A hand-drawn proportional bitmap font.  Every glyph is a tuple of
# 13 strings of '#' and '.', one string per grid row, all of equal
# length (the glyph's own width).  Capitals occupy rows 1-10,
# x-height letters rows 4-10, ascenders rows 1-10 and descenders
# reach row 12.  Row 0 and rows 11-12 are breathing room, which is
# what makes a 12 px line pitch safe.
FONT = {
    'A': ("......", "..##..", ".#..#.", "#....#", "#....#", "######", "#....#", "#....#", "#....#", "#....#", "#....#", "......", "......"),
    'B': ("......", "#####.", "#....#", "#....#", "#....#", "#####.", "#....#", "#....#", "#....#", "#....#", "#####.", "......", "......"),
    'C': ("......", ".#####", "#....#", "#.....", "#.....", "#.....", "#.....", "#.....", "#.....", "#....#", ".#####", "......", "......"),
    'D': ("......", "####..", "#...#.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#...#.", "####..", "......", "......"),
    'E': (".....", "#####", "#....", "#....", "#....", "####.", "#....", "#....", "#....", "#....", "#####", ".....", "....."),
    'F': (".....", "#####", "#....", "#....", "#....", "####.", "#....", "#....", "#....", "#....", "#....", ".....", "....."),
    'G': ("......", ".#####", "#....#", "#.....", "#.....", "#..###", "#....#", "#....#", "#....#", "#....#", ".#####", "......", "......"),
    'H': ("......", "#....#", "#....#", "#....#", "#....#", "######", "#....#", "#....#", "#....#", "#....#", "#....#", "......", "......"),
    'I': ("...", "###", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", "###", "...", "..."),
    'J': (".....", "#####", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "#...#", ".###.", ".....", "....."),
    'K': ("......", "#....#", "#...#.", "#..#..", "#.#...", "##....", "#.#...", "#..#..", "#...#.", "#....#", "#....#", "......", "......"),
    'L': (".....", "#....", "#....", "#....", "#....", "#....", "#....", "#....", "#....", "#....", "#####", ".....", "....."),
    'M': ("........", "#......#", "##....##", "#.#..#.#", "#.#..#.#", "#..##..#", "#......#", "#......#", "#......#", "#......#", "#......#", "........", "........"),
    'N': ("......", "#....#", "##...#", "##...#", "#.#..#", "#..#.#", "#...##", "#...##", "#....#", "#....#", "#....#", "......", "......"),
    'O': ("......", ".####.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####.", "......", "......"),
    'P': ("......", "#####.", "#....#", "#....#", "#....#", "#####.", "#.....", "#.....", "#.....", "#.....", "#.....", "......", "......"),
    'Q': ("......", ".####.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#..#.#", "#...##", ".###.#", "......", "......"),
    'R': ("......", "#####.", "#....#", "#....#", "#....#", "#####.", "#.#...", "#..#..", "#...#.", "#....#", "#....#", "......", "......"),
    'S': ("......", ".#####", "#.....", "#.....", ".####.", ".....#", ".....#", ".....#", ".....#", "#....#", ".####.", "......", "......"),
    'T': ("......", "######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "......", "......"),
    'U': ("......", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####.", "......", "......"),
    'V': ("......", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".#..#.", ".#..#.", "..##..", "..##..", "......", "......"),
    'W': ("........", "#......#", "#......#", "#......#", "#......#", "#..##..#", "#..##..#", "#.#..#.#", "#.#..#.#", ".#....#.", ".#....#.", "........", "........"),
    'X': ("......", "#....#", ".#..#.", "..##..", "..##..", "..##..", "..##..", "..##..", ".#..#.", "#....#", "#....#", "......", "......"),
    'Y': ("......", "#....#", "#....#", "#....#", ".#..#.", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "......", "......"),
    'Z': ("......", "######", ".....#", "....#.", "...#..", "..#...", "..#...", ".#....", "#.....", "#.....", "######", "......", "......"),
    'a': (".....", ".....", ".....", ".....", ".###.", "....#", ".####", "#...#", "#...#", "#...#", ".####", ".....", "....."),
    'b': (".....", "##...", "##...", "##...", "####.", "##..#", "##..#", "##..#", "##..#", "##..#", "####.", ".....", "....."),
    'c': ("....", "....", "....", "....", ".###", "##..", "##..", "##..", "##..", "##..", ".###", "....", "...."),
    'd': (".....", "...##", "...##", "...##", ".####", "#..##", "#..##", "#..##", "#..##", "#..##", ".####", ".....", "....."),
    'e': (".....", ".....", ".....", ".....", ".###.", "#...#", "#####", "#....", "#....", "#...#", ".###.", ".....", "....."),
    'f': ("...", ".##", "#..", "#..", "###", "#..", "#..", "#..", "#..", "#..", "#..", "...", "..."),
    'g': (".....", ".....", ".....", ".....", ".####", "#...#", "#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."),
    'h': (".....", "##...", "##...", "##...", "####.", "##..#", "##..#", "##..#", "##..#", "##..#", "##..#", ".....", "....."),
    'i': ("..", "##", "##", "..", "##", "##", "##", "##", "##", "##", "##", "..", ".."),
    'j': ("...", ".##", ".##", "...", ".##", ".##", ".##", ".##", ".##", ".##", ".##", ".##", "##."),
    'k': ("....", "##..", "##..", "##..", "#..#", "#.#.", "##..", "#.#.", "#..#", "#..#", "#..#", "....", "...."),
    'l': ("..", "##", "##", "##", "##", "##", "##", "##", "##", "##", "##", "..", ".."),
    'm': ("........", "........", "........", "........", "##.##.##", "##.##.##", "##.##.##", "##.##.##", "##.##.##", "##.##.##", "##.##.##", "........", "........"),
    'n': (".....", ".....", ".....", ".....", "####.", "##..#", "##..#", "##..#", "##..#", "##..#", "##..#", ".....", "....."),
    'o': (".....", ".....", ".....", ".....", ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", ".....", "....."),
    'p': (".....", ".....", ".....", ".....", "####.", "##..#", "##..#", "##..#", "##..#", "####.", "##...", "##...", "##..."),
    'q': (".....", ".....", ".....", ".....", ".####", "#..##", "#..##", "#..##", "#..##", ".####", "...##", "...##", "...##"),
    'r': ("....", "....", "....", "....", "####", "##.#", "##..", "##..", "##..", "##..", "##..", "....", "...."),
    's': (".....", ".....", ".....", ".....", ".####", "##...", ".###.", "....#", "....#", "#...#", ".###.", ".....", "....."),
    't': ("...", "...", "##.", "##.", "###", "##.", "##.", "##.", "##.", "##.", ".##", "...", "..."),
    'u': (".....", ".....", ".....", ".....", "##..#", "##..#", "##..#", "##..#", "##..#", "##.##", ".###.", ".....", "....."),
    'v': (".....", ".....", ".....", ".....", "##..#", "##..#", "##..#", "##..#", ".#.#.", ".#.#.", "..#..", ".....", "....."),
    'w': (".......", ".......", ".......", ".......", "##...##", "##...##", "##.#.##", "##.#.##", ".##.##.", ".##.##.", "..#.#..", ".......", "......."),
    'x': (".....", ".....", ".....", ".....", "#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#", ".....", "....."),
    'y': (".....", ".....", ".....", ".....", "#...#", "#...#", "#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."),
    'z': ("....", "....", "....", "....", "####", "...#", "..#.", ".#..", "#...", "#...", "####", "....", "...."),
    '0': (".....", ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", ".....", "....."),
    '1': ("...", ".#.", "##.", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", "###", "...", "..."),
    '2': (".....", ".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#....", "#....", "#....", "#####", ".....", "....."),
    '3': (".....", ".###.", "#...#", "....#", "..##.", "....#", "....#", "....#", "....#", "#...#", ".###.", ".....", "....."),
    '4': (".....", "...#.", "...#.", "..##.", ".#.#.", "#..#.", "#####", "....#", "....#", "....#", "....#", ".....", "....."),
    '5': (".....", "#####", "#....", "#....", "####.", "....#", "....#", "....#", "....#", "#...#", ".###.", ".....", "....."),
    '6': (".....", ".###.", "#...#", "#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#", ".###.", ".....", "....."),
    '7': (".....", "#####", "....#", "....#", "...#.", "...#.", "..#..", "..#..", "..#..", ".#...", ".#...", ".....", "....."),
    '8': (".....", ".###.", "#...#", "#...#", ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", ".....", "....."),
    '9': (".....", ".###.", "#...#", "#...#", "#...#", "#...#", ".####", "....#", "....#", "#...#", ".###.", ".....", "....."),
    ' ': ("..", "..", "..", "..", "..", "..", "..", "..", "..", "..", "..", "..", ".."),
    '.': ("..", "..", "..", "..", "..", "..", "..", "..", "..", "##", "##", "..", ".."),
    ',': ("...", "...", "...", "...", "...", "...", "...", "...", "...", "##.", "##.", ".#.", "#.."),
    ':': ("..", "..", "..", "..", "##", "##", "..", "..", "..", "##", "##", "..", ".."),
    ';': ("...", "...", "...", "...", ".#.", ".#.", "...", "...", "...", "##.", "##.", ".#.", "#.."),
    "'": ("##", "##", "#.", "..", "..", "..", "..", "..", "..", "..", "..", "..", ".."),
    '"': ("#..#", "#..#", "#..#", "....", "....", "....", "....", "....", "....", "....", "....", "....", "...."),
    '-': ("....", "....", "....", "....", "....", "....", "####", "....", "....", "....", "....", "....", "...."),
    '–': (".....", ".....", ".....", ".....", ".....", ".....", "#####", ".....", ".....", ".....", ".....", ".....", "....."),
    '—': (".......", ".......", ".......", ".......", ".......", ".......", "#######", ".......", ".......", ".......", ".......", ".......", "......."),
    '!': ("..", "##", "##", "##", "##", "##", "##", "##", "..", "##", "##", "..", ".."),
    '?': (".....", ".###.", "#...#", "....#", "...#.", "..#..", "..#..", "..#..", ".....", "..#..", "..#..", ".....", "....."),
    '(': ("...", "...", ".##", ".#.", "#..", "#..", "#..", "#..", "#..", "#..", ".#.", ".##", "..."),
    ')': ("...", "...", "##.", ".#.", "..#", "..#", "..#", "..#", "..#", "..#", ".#.", "##.", "..."),
    '/': (".....", "....#", "....#", "...#.", "...#.", "..#..", "..#..", ".#...", ".#...", "#....", "#....", ".....", "....."),
    '&': ("......", ".###..", "#...#.", "#...#.", ".###..", ".#.#..", "#...#.", "#..#.#", "#.#.#.", "##..##", ".##.#.", "......", "......"),
    '$': ("......", ".#####", "#.##..", "#.##..", ".####.", "..##.#", "..##.#", "..##.#", "..##.#", "#.##.#", ".####.", "......", "......"),
    '%': (".......", ".##....", "#..#..#", "#..#.#.", ".##.#..", "...#...", "..#....", ".#..##.", "#..#..#", "#..#..#", ".#..##.", ".......", "......."),
    '+': (".....", ".....", ".....", ".....", "..#..", "..#..", "#####", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '*': (".....", ".....", ".....", ".....", "#.#.#", ".###.", "#.#.#", ".....", ".....", ".....", ".....", ".....", "....."),
    '•': ("...", "...", "...", "...", "...", ".##", ".##", "...", "...", "...", "...", "...", "..."),
}

# Sanity: every glyph must be 13 rows of one consistent width.
for _ch, _rows in FONT.items():
    assert len(_rows) == 13, _ch
    assert len({len(_r) for _r in _rows}) == 1, _ch

# Typographic aliases: curly quotes render as straight ones.
ALIASES = {'‘': "'", '’': "'", '“': '"', '”': '"'}


def glyph_rows(ch):
    """The 13 grid rows for a character, with a '?' fallback."""
    return FONT.get(ALIASES.get(ch, ch), FONT['?'])


def _track(bold):
    """Horizontal tracking per character.  Bold is drawn by doubling
    each pixel into the tracking column, so bold and regular text
    share the same advance - the extra ink fills the tracking."""
    return 1


def text_width(s, scale=1, bold=False):
    """Exact advance width of a string in the bitmap font."""
    if not s:
        return 0
    adv = sum(len(glyph_rows(c)[0]) + _track(bold) for c in s)
    return (adv - _track(bold)) * scale


def wrap_runs(runs, maxw, scale=1):
    """Wrap styled text into lines that fit maxw pixels.

    runs is a list of (text, bold, colour) segments.  Returns a list
    of lines; each line is a list of (x, word, bold, colour) tokens
    with x precomputed, so the drawer and the measurer always agree.
    Words are never split unless a single word exceeds the line.
    """
    words = []
    for text, bold, colour in runs:
        for w in text.split(' '):
            if w:
                words.append((w, bold, colour))
    lines = []
    cur = []
    x = 0
    for word, bold, colour in words:
        ww = text_width(word, scale, bold)
        sp = (2 + _track(cur[-1][2])) * scale if cur else 0
        if cur and x + sp + ww > maxw:
            lines.append(cur)
            cur = []
            x = 0
            sp = 0
        if not cur:
            cur = [(0, word, bold, colour)]
            x = ww
        else:
            cur.append((x + sp, word, bold, colour))
            x += sp + ww
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    """An RGB framebuffer filled with the paper colour."""

    def __init__(self):
        self.px = bytearray(bytes(PAPER) * (W * H))

    def rect(self, x, y, w, h, colour):
        """Fill a clipped rectangle."""
        if w <= 0 or h <= 0:
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(colour) * (x1 - x0)
        n = len(row)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.px[i:i + n] = row

    def text(self, s, x, y, scale=1, bold=False, colour=INK):
        """Draw a string with its top-left at (x, y); return end x."""
        cx = x
        for ch in s:
            rows = glyph_rows(ch)
            gw = len(rows[0])
            for r, row in enumerate(rows):
                for c, cell in enumerate(row):
                    if cell == '#':
                        px = cx + c * scale
                        py = y + r * scale
                        self.rect(px, py, scale, scale, colour)
                        if bold:
                            self.rect(px + scale, py, scale, scale, colour)
            cx += (gw + _track(bold)) * scale
        return cx

    def text_right(self, s, right, y, scale=1, bold=False, colour=INK):
        """Draw a string ending at the given right edge."""
        return self.text(s, right - text_width(s, scale, bold), y,
                         scale, bold, colour)

    def text_centred(self, s, y, scale=1, bold=False, colour=INK):
        """Draw a string centred on the page."""
        return self.text(s, (W - text_width(s, scale, bold)) // 2, y,
                         scale, bold, colour)

    def draw_line(self, line, x, y, scale=1):
        """Draw one wrapped line produced by wrap_runs."""
        for dx, word, bold, colour in line:
            self.text(word, x + dx, y, scale, bold, colour)

    def hrule(self, x, y, w, thick=1, colour=INK):
        self.rect(x, y, w, thick, colour)


def png_bytes(canvas):
    """Encode the framebuffer as a PNG (filter 0 rows, zlib IDAT)."""
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + chunk(b'IEND', b''))


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


# ------------------------------------------------------------------ layout
def story_runs(story):
    """A story brief as styled runs: bold headline, detail, source."""
    head, detail, src = story
    return [(head, True, INK), (detail, False, INK),
            ('(' + src + ')', True, RED)]


def story_lines(story):
    return wrap_runs(story_runs(story), COLW - 10)


def section_height(sec):
    """Exact height of a section in a column, in pixels."""
    _name, stories = sec
    h = BAR_H + BAR_GAP
    for i, st in enumerate(stories):
        h += len(story_lines(st)) * PITCH
        if i < len(stories) - 1:
            h += STORY_GAP
    return h + SECTION_GAP


def draw_section(fb, x, y, sec):
    """Draw one section with its ink bar header; return its height."""
    name, stories = sec
    fb.rect(x, y, COLW, BAR_H, INK)
    fb.text(name, x + 6, y + 1, 1, True, PAPER)
    fb.text_right('%d STORIES' % len(stories), x + COLW - 6, y + 1,
                  1, True, PAPER)
    yy = y + BAR_H + BAR_GAP
    for i, st in enumerate(stories):
        fb.rect(x, yy + 3, 6, 6, RED)
        for line in story_lines(st):
            fb.draw_line(line, x + 10, yy)
            yy += PITCH
        if i < len(stories) - 1:
            yy += STORY_GAP
    return yy - y + SECTION_GAP


def best_partition(heights):
    """Split the section sequence into three contiguous groups so
    that the tallest column is as short as possible (exact search
    over every pair of split points)."""
    best = None
    for i, j in combinations(range(1, len(heights)), 2):
        cols = (sum(heights[:i]), sum(heights[i:j]), sum(heights[j:]))
        if best is None or max(cols) < best[0]:
            best = (max(cols), i, j)
    return best[1], best[2]


def masthead(fb, y):
    fb.hrule(MARGIN, y, W - 2 * MARGIN, 3)
    fb.hrule(MARGIN, y + 5, W - 2 * MARGIN, 1)
    y += 10
    fb.text_centred('THE WORLD TODAY', y, 3, True, INK)
    y += 13 * 3 + 1
    fb.text_centred('SATURDAY 21 NOVEMBER 2026', y, 2, True, RED)
    y += 13 * 2 + 2
    fb.text("THE DAY'S NEWS, IN ONE IMAGE", MARGIN, y, 1, True, INK)
    fb.text_right('ALL TIMES UTC', W - MARGIN, y, 1, True, INK)
    y += 13 + 2
    fb.hrule(MARGIN, y, W - 2 * MARGIN, 1)
    y += 5
    fb.text('52 SOURCED STORIES — EACH NAMED TO ITS OUTLET',
            MARGIN, y, 1, True, INK)
    fb.text_right('PLUS A UTC TIMELINE AND A DATE CHECK',
                  W - MARGIN, y, 1, True, INK)
    y += 13 + 2
    fb.hrule(MARGIN, y, W - 2 * MARGIN, 1)
    return y + 4


def lead_block(fb, y):
    fb.text('THE LEAD', MARGIN, y, 1, True, RED)
    y += 13 + 2
    head, detail, src = LEAD
    for line in wrap_runs([(head, True, INK)], W - 2 * MARGIN, 2):
        fb.draw_line(line, MARGIN, y, 2)
        y += HEAD_PITCH
    y += 1
    runs = [(detail, False, INK), ('(' + src + ')', True, RED)]
    for line in wrap_runs(runs, W - 2 * MARGIN):
        fb.draw_line(line, MARGIN, y)
        y += PITCH
    return y + 4


def timeline(fb, y):
    fb.rect(MARGIN, y, W - 2 * MARGIN, BAR_H, INK)
    fb.text('THE DAY IN UTC', MARGIN + 6, y + 1, 1, True, PAPER)
    fb.text_right('SATURDAY 21 NOVEMBER 2026, HOUR BY HOUR',
                  W - MARGIN - 6, y + 1, 1, True, PAPER)
    yy = y + BAR_H + 3
    runs = []
    for i, (time, label, src) in enumerate(TIMELINE):
        runs.append((time, True, RED))
        runs.append((label, False, INK))
        tag = '(' + src + ')' + ('•' if i < len(TIMELINE) - 1 else '')
        runs.append((tag, True, RED))
    for line in wrap_runs(runs, W - 2 * MARGIN - 12):
        fb.draw_line(line, MARGIN + 6, yy)
        yy += PITCH
    return yy + 2


def footer(fb, y):
    fb.hrule(MARGIN, y, W - 2 * MARGIN, 1)
    y += 4
    runs = [('52 STORIES ON THIS PAGE.', True, INK),
            (SOURCES_LINE, False, INK)]
    for line in wrap_runs(runs, W - 2 * MARGIN):
        fb.draw_line(line, MARGIN, y)
        y += PITCH
    for line in wrap_runs([(DATE_CHECK, False, INK)], W - 2 * MARGIN):
        fb.draw_line(line, MARGIN, y)
        y += PITCH
    return y + 1


def build():
    fb = Canvas()
    y = masthead(fb, MARGIN)
    y = lead_block(fb, y)
    secs = sorted(SECTIONS, key=lambda s: SECTION_ORDER.index(s[0]))
    heights = [section_height(s) for s in secs]
    i, j = best_partition(heights)
    groups = [secs[:i], secs[i:j], secs[j:]]
    bottom = y
    for ci, group in enumerate(groups):
        x = MARGIN + ci * (COLW + GUTTER)
        cy = y
        for sec in group:
            cy += draw_section(fb, x, cy, sec)
        bottom = max(bottom, cy)
    y = timeline(fb, bottom + 1)
    y = footer(fb, y)
    if os.environ.get('MAKEFUN_DEBUG'):
        print('section heights:', heights)
        print('partition:', i, j, 'columns end at:', bottom)
        print('page bottom:', y, 'of', H)
    return fb


def main():
    data = png_bytes(build())
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    path = os.path.join(outdir, 'entry.png')
    with open(path, 'wb') as fh:
        fh.write(data)
    print('wrote %s (%d bytes)' % (path, len(data)))


if __name__ == '__main__':
    main()
