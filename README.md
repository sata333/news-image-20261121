[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/sata333/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/sata333/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

# THE WORLD TODAY — the news of 21 November 2026 in one image

Entry for the make.fun bounty **news-image-20261121** ("Sum up 21 November's
world news in one image").

Proposed entry title: **Saturday 21 November 2026: 52 sourced stories, a UTC
timeline and a date check**.

`main.py` draws a dense newspaper front page for **Saturday 21 November
2026** — a masthead ("THE WORLD TODAY"), a lead story, eight regional and
thematic sections carrying 51 further stories, a "THE DAY IN UTC" timeline
strip with seven timed events, and a footer with the story count, the
sources and a date-check line — and writes it as a single 1024×1024 PNG.
Every story is a headline plus one short clause, tagged with the outlet
that reported it.

## How it works

- Python 3, **standard library only** (`os`, `struct`, `zlib`), no network
  access at runtime.
- The page is rendered into an in-memory framebuffer: a hand-drawn 5×7
  bitmap font (upper and lower case, digits, punctuation) provides the
  typography, with styled runs (headline / detail / source tag) wrapped by
  a small layout engine that assigns sections to the shorter of two
  columns and never overflows the page.
- The PNG is encoded directly (IHDR/IDAT/IEND with `zlib`) from pure
  integer arithmetic, so the output is fully deterministic.

## Run it

```sh
python3 main.py                            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py  # writes /tmp/out/entry.png
```

If the output directory cannot be created or written, the program falls
back to `./entry.png` in the working directory.

## The stories shown, and their sources

Researched on Saturday 21 November 2026 from that day's reporting across
several independent outlets. Only events that happened, or were first
reported, on 21 November 2026 (in some time zone) are included.

**The lead** — Russian missile comes down in Poland, Tusk says (BBC).

**Europe (8)** — Second night of strikes hits 18 sites in Ukraine (BBC) ·
Zelensky: Putin is 'a killer' (BBC) · Burnham: UK to explore even closer
EU ties (BBC) · Gen Z protests sweep 25 European countries (One Turn) ·
Denmark foils alleged Russian murder plot (BBC) · French officers
sentenced over Zecler beating (BBC) · Spain heads toward a 29 November
election (One Turn) · Burnham: my big worry is Trump and Iran (Japan Times).

**Americas (8)** — Congress heads toward a Christmas shutdown (Reuters) ·
Trump ousts cyber chief after tech outages (BBC) · FBI and farm ministry
breached by hackers (Japan Times) · Man convicted of starting Palisades
fire (BBC) · Mamdani: Rikers jail to close by 2032 (BBC) · Court lets
Trump end Venezuelans' protection (AP) · 19 years for plot to kill Sikh
separatist (BBC) · Trump: flight systems 'ancient' but safe (BBC).

**Middle East (7)** — Coalition downs 3 Houthi missiles at Riyadh
(Al Jazeera) · Tanker hit leaving the Strait of Hormuz (UKMTO) · Iran:
Hormuz could reopen 'in two hours' (Al Jazeera) · Air attack reported on
Yemen's Mocha port (Outlook India) · Drone strike wounds three in Gaza
(Outlook India) · Pakistan condemns attack on Riyadh (Al Jazeera) ·
Myanmar ruling may bolster Gaza ICJ case (Japan Times).

**Asia-Pacific (6)** — Japan wary of regular three-power summits (Japan
Times) · Why Kim did not meet Trump, despite hype (Japan Times) · South
Korea catches 111 exam cheats (BBC) · Nepal PM's India test on first
visit (BBC) · India launches first H5N1 bird-flu vaccine (PIB) · Modi
opens SCO dialogue forum in Delhi (PIB).

**Africa (4)** — South Africa's first female deputy president dies
(Reuters) · ANC fights to hold South Africa's big cities (BBC) · Nearly
600 women killed in three months (BBC) · Nigeria moves to end jail for
suicide bids (BBC).

**Business (6)** — Wall Street's worst week in over 18 months (AP) ·
Anthropic stumble checks the AI trade (Japan Times) · Judge approves
$7.25bn Roundup settlement (BBC) · Honda and Toyota recall 1.6m vehicles
(Japan Times) · Bitcoin slides toward $62,000 in rout (IQMIA) · Euro zone
consumer morale beats forecasts (Reuters).

**Tech & Science (6)** — Claude may have solved maths' greatest riddle
(Japan Times) · Cancer pill clears tumours in trial (One Turn) · Path
opens toward a 'killer robots' pact (Japan Times) · Trump threatens
overseas AI centre ban (BBC) · GTA VI smashes records, sales top $2.3bn
(BBC) · US declassifies more UFO footage (BBC).

**Sport (6)** — Antonelli fastest, Verstappen takes pole (GPToday) ·
Lakers rally past Kings 106-104 (Reuters) · Rahul hits 136 as India take
charge (Sunday Guardian) · Shimada leads Finlandia Trophy (Japan Times) ·
Alcaraz sets up ATP semi with Shelton (Pollar) · Australia, England open
T20 series at MCG (Sunday Guardian).

**Timeline (UTC)** — 00:01 Rikers plan (BBC) · 01:02 $811m migrant bail
scam investigation (BBC) · 02:09 Tusk on the missile in Poland (BBC) ·
04:32 Zelensky calls Putin 'a killer' (BBC) · 05:44 Mlambo-Ngcuka's death
announced (Reuters) · 07:06 Mocha port attack reported (Outlook India) ·
07:56 Tanker hit leaving Hormuz (UKMTO).

## Verification

Two consecutive runs into different output directories produce
byte-identical files:

- `entry.png`: **62,973 bytes** (limit 1 MiB), **1024×1024** px
- SHA-256: `8a9b56f95947cba9c9fd91c698d21cda55426d6bafc9f73c90d348f2333715a0`
  (identical for both runs)

## Layout of this directory

- `main.py` — the program (the entry)
- `entry.png` — the image it produces
- `LICENSE` — license for this repository
