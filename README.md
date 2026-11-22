[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/sata333/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/sata333/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

# Saturday 21 November 2026: 52 sourced stories, a UTC timeline and a date check

One day of world news as a single newspaper front page. The image
leads with the Russian missile that came down in Poland, then packs
51 further stories into eight regional and topical sections —
Europe, the Americas, the Middle East, Asia-Pacific, Africa,
Business, Tech & Science and Sport. Every story is a wire-tight
brief (headline plus one short clause) named to the outlet that
reported it: BBC, Reuters, AP, Al Jazeera, the Japan Times,
One Turn, UKMTO, Outlook India, PIB and others. A "THE DAY IN UTC"
band replays seven of the day's moments in chronological order,
and a date check in the footer states that every event on the page
happened, or was first reported, on Saturday 21 November 2026.

## How it works

`main.py` is a single self-contained Python 3 program using only
the standard library (`itertools`, `os`, `struct`, `zlib`). It
draws the page into an in-memory RGB framebuffer and encodes the
PNG itself — IHDR/IDAT/IEND chunks with a zlib stream — so there
are no image libraries and no external assets.

Type is a hand-drawn proportional bitmap font embedded in the
program as data: every glyph is defined on a 13-row grid (capitals
10 rows tall, a 7-row x-height, ascenders and descenders) with its
own width. Because each string is measured exactly, headlines,
details and source tags are wrapped by a styled-run word wrapper
that guarantees nothing overflows its column. Stories flow as
continuous briefs — bold headline, sentence-case detail, red
source tag — separated by small red squares.

The eight sections are assigned to the three columns by an exact
search over every split of the section sequence, choosing the
partition whose tallest column is shortest, so the page fills
evenly. Colours are a newsprint paper (247, 243, 232), press ink
(20, 18, 14) and press red (164, 22, 26). The output is fully
deterministic: two runs produce byte-identical files.

## Running it

```sh
python3 main.py
```

This writes `entry.png` (1024×1024, 67,074 bytes) to
`/output/entry.png` by default. Set the `MAKEFUN_OUTPUT_DIR`
environment variable to write it somewhere else:

```sh
MAKEFUN_OUTPUT_DIR=. python3 main.py
```

## Verifying the output

The renderer is deterministic, so the committed `entry.png` can be
checked byte for byte. Run the generator twice and compare hashes:

```sh
MAKEFUN_OUTPUT_DIR=. python3 main.py && sha256sum entry.png
```

Expected SHA-256 for the entry as committed:

```
b6e80e02cb02e1aee395afc6d48ebbb78330ddf2e7c7e2456dc2da4aed67ffc9
```

## License

MIT. The generator code is original; the news briefs summarise
reporting by the outlets named in each source tag.
