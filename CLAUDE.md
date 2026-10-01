# UKAHFT course of fire generator

Builds a 30-shot Hunter Field Target (HFT) course of fire that conforms to the
UKAHFT Rules and Course Setting Guidelines REV 01.2 (28.05.2020), and writes it
to an Excel workbook with position icons and rule-compliance checks.

Rules source: `docs/ukahft_2020_rules_rev_01.2.pdf` (section
numbers below refer to it).

## Files
- `course.json` - the course: shot number, position, range in yards, hit zone in mm. Edit this to change the course.
- `build.py` - exports the icons and builds the workbook (openpyxl). `--course`/`--out` to build another course,
  `--icons v1` to use the original line-figure icons in the workbook (default v2).
- `icons.py` - icon geometry (one source per style) and export: PNG for the workbook, SVG for apps.
  Two styles: v1 = original line figures; v2 = filled pictograms with a scoped-rifle silhouette and
  square posts, separated by knockout gaps ("X" items: transparent in PNG, `<mask>` in SVG).
- `rules.py` - the checks as data (`CHECKS`). Generates the Checks sheet formulas and is the Python
  validator: `python rules.py [course.json]` (exit code 1 if not compliant).
- `generate.py` - random compliant course: `python generate.py [--seed N] [--out course_generated.json]`.
- `icons/` - generated icons: pr, po, us, uk, ss, sk. v1 in `icons/`, v2 in `icons/v2/`; each has PNG (96px),
  SVG in `svg/{24,48,96}/`, and `svg/sprite.svg` with `<symbol id="hft-pr">` etc. Inline the sprite in the page
  and use `<svg><use href="#hft-pr"/></svg>` (v2 symbols use masks, which are unreliable via an external sprite file).
- `build_app.py` - builds `app/scorecard.html` (scorecard web app) from `app/scorecard.template.html`, inlining
  `course.json` and the v2 sprite. Published as a claude.ai artifact: https://claude.ai/artifact/UKHGAgso4C3c3nzgkzux6n
  (republish after rebuilding). Also on GitHub Pages: https://owensparkspersonal.github.io/OS_HFT/ (built by
  `.github/workflows/pages.yml` on every push to main; off claude.ai results save in the browser only). Results save per course in the browser and, when signed in, to the viewer's private db doc.
- `UKAHFT_course_of_fire.xlsx` - output. Sheets: "Course of fire", "Checks".

## Run
    pip install pillow openpyxl
    python build.py
Then recalculate so formulas have cached values (openpyxl writes none), e.g.
LibreOffice headless: `soffice --headless --convert-to xlsx --outdir out UKAHFT_course_of_fire.xlsx`
and confirm the Checks sheet shows OK on every row with no formula errors.
`python rules.py` gives the same result without a spreadsheet app; build.py also prints any failing checks.
When adding a check, add it to `CHECKS` in rules.py only - the sheet and validator both follow.

## Course rules (30 shots, max 60 points)
Scoring: hit = 2, plate = 1, miss = 0. 2 minutes per target. Distances are measured
from the leading edge of the peg to the target faceplate. Hit zones 15-45mm.
Faceplate margin: >=10mm for prone targets, >=20mm for positional targets.

Prone shots (24 here, incl. exactly 3 "Prone Only" which may be any size):
| Hit zone | Distance | Count |
|---|---|---|
| 15-19mm | 13-25 yd | 4-6 |
| 20-24mm | 8-30 yd | 2 (or 3) |
| 25-34mm | 8-35 yd | 4 |
| 25-34mm | 35.01-40 yd | 4 (or 3) |
| 35-45mm | 8-45 yd | remainder |
Table 1A: either (2 x 20-24mm, 4 near + 4 far 25-34mm) or (3 x 20-24mm, 4 near + 3 far 25-34mm).
Both options make 20-24mm + far 25-34mm = 6; the Checks sheet tests that so mixed options (2 + 3, 3 + 4) fail.

Positional shots (exactly 6):
- Unsupported standing x1 and unsupported kneeling x1: 35-45mm at 8-35 yd.
- Supported standing x2: each either 25-34mm at 8-30 yd or 35-45mm at 8-35 yd.
- Supported kneeling x2 (Table 3): (2 x 25-34mm <=30 yd) | (1 x 25-34mm <=30 yd + 1 x 35-45mm <=35 yd) |
  (2 x 35-45mm <=35 yd) | (1 x 25-34mm <=30 yd + 1 x 35-45mm 35.01-40 yd) | (1 x 35-45mm <=35 yd + 1 x 35-45mm 35.01-40 yd).
  If a kneeling target is beyond 35 yd the support must also allow a standing shot.

Elevated prone shots (>30 degrees from parallel, measured 200mm above the peg): a target
higher than 12 ft must not be closer than 20 yd; if closer than 20 yd and higher than 12 ft
it needs a hit zone of at least 35mm. Unsupported kneeling targets must be within 30 degrees
above or below parallel (measured 800mm above the peg). The current course has no elevated shots.

## Decisions made so far
- Table 1A Option 1 (2 x 20-24mm, 4 + 4 x 25-34mm), 5 x 15-19mm, 9 x 35-45mm prone.
- Supported kneeling uses Table 3 Option 2 (no standing-capable support needed).
- Prone Only shots are shots 7, 16 and 29 (a small, a medium and a large target).
- Range (m) = ROUND(yards x 0.9144, 2), a formula that references the factor on the Checks sheet.
- Generator: random Table 1A option and 15-19mm count (4-6); Table 3 Option 2; Prone Only on one small,
  one medium (20-34mm) and one large target; whole yards (35.01-40 yd -> 36-40); order fully shuffled.
- SVG icons keep the fixed colours (not currentColor) because the colours carry meaning.

## Workbook conventions
- Arial throughout. Blue font = inputs (position, yards, hit zone size). Black = formulas.
- Column order: Shot, Icon, Position, Range (yd), Range (m), Target type (size in mm, e.g. 45mm; no "knockover"/"hit zone" wording).
- Checks sheet is formula-driven (SUMPRODUCT) and must stay at OK for every row.
- Icon colours (v1): black = prone and unsupported, blue = supported, amber = Prone Only (with a down-arrow badge).
- Icon colours (v2): one colour per position, all at relative luminance ~0.20 so they work in light and dark
  mode (~4.2:1 on white, ~3.9:1 on #1e1e1e): Prone green #308c43, Prone Only amber #b9660c (with badge),
  unsupported standing red #da4646, unsupported kneeling magenta #ca46a6, supported standing blue #3a7bd3,
  supported kneeling teal #128892. Posts and ground grey #7b7b7b. Keep new colours at the same luminance.

## Known quirks in the rules document
- Table 3 labels a column "34-45mm" where the text says 35-45mm; 35-45mm is used.
- Section 4 refers to "Section 10" for target distances; they are in Section 11.

## Ideas for next steps
- Add a lane/peg layout view and elevated-shot support with angle and height checks.
