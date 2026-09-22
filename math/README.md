# Hyrule Math Quest

A printable Grade 5 maths pre-test: Roman numerals, place value to millions,
decimals to thousandths, rounding, comparing and ordering, the properties of
operations, and a five-addend word problem, plus an answer key on page four.

Python 3.14, managed with uv.

## Build

```sh
uv run worksheet build    # render the PDF
uv run worksheet audit    # run the quality gates
uv run worksheet check    # build, then audit
```

`audit` and `check` exit non-zero when a gate fails, so either can gate a
commit. Shared options work on both sides of the subcommand:

```sh
uv run worksheet audit --source other.html
uv run worksheet --source other.html audit
```

## Why the gates exist

### Correctness

A wrong answer key is the worst thing this project could ship, so no answer is
typed. `content.py` holds each question's own numbers, and every answer is
*derived* from them: Roman numerals by algorithm, rounding by `Decimal` with
half-up (schools teach half-up; Python's default would round 2.5 to 2), number
names by a speller, comparisons by comparing.

Two gates then bind that model to the document, in both directions:

- **givens** — every number a question is built from must appear in the printed
  question.
- **answers** — every derived answer must appear in the printed key.

One direction alone is not enough. Checking answers only, a change to an
ingredient weight in the HTML leaves the derived total self-consistent and the
key still passing, while the printed question has moved underneath it. That gap
was real and is why the givens gate exists.

The property equations get the same treatment: `shown` is built from the same
operands the truth test uses, so the printed equation and the verified equation
cannot disagree, and `holds` proves each one is actually true.

### Print legibility

The worksheet gets printed in greyscale. A luminance-based greyscale conversion
preserves relative luminance, and WCAG contrast is defined purely in terms of
relative luminance, so a colour pair that clears its WCAG threshold also clears
it on a monochrome laser. The contrast gate therefore proves greyscale
legibility without simulating a printer.

- **tokens** — every colour and font size in a rule must go through a design
  token. This is what stops the palette drifting back to the 33 one-off hexes
  it started with.
- **binding** — each check names the CSS rule it models, and that rule must
  still declare that token. Without this the contract is only a *model* of the
  document: restyle `.ask` to a different token and the check would keep
  asserting a pairing that no longer exists.
- **contrast** — text pairs need 4.5:1, UI graphics 3:1.
- **artwork** — an outlined shape passes on *either* its fill or its stroke.
  Demanding both fails correct artwork: gold on cream cannot reach 3:1 at any
  value, yet a dark outline makes the shape perfectly legible. The shield crest
  is the mirror case, passing on fill while its outline disappears into the
  blue. Getting this backwards produces a false failure and a pointless colour
  change, which is exactly what happened before the rule was written down.
- **page count** — the PDF must be four pages. A layout change that pushes a
  question onto a fifth page is otherwise easy to miss.

Checks live in `spec.py` as data and reference tokens **by name**. Editing a
token in the HTML re-points every check at the new value, rather than leaving
the contract quietly stale.

### What is still only modelled

The binding gate proves each colour is declared by the rule it names. It does
**not** prove which text sits on which background — that needs a layout engine.
Move a paragraph into a differently-tinted container and the pairing in
`spec.py` becomes wrong while every gate still passes. The pixel comparison
below is the backstop for that: the pairing would be wrong, but the page would
look different, and that fails.

## Develop

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run lint-imports
uv run pytest --cov   # branch coverage, fails under 90%
```

CI runs all of these on every push.

### Layout

```
hyrule-math-review.html   the worksheet (source of truth)
Hyrule-Math-Quest.pdf     build output
worksheet/
  numerals.py             Roman numerals, place value, rounding, number names
  colors.py               sRGB and WCAG maths
  spec.py                 the print contract, as data
  content.py              the worksheet's maths, derived from its own numbers
  stylesheet.py           the token palette and CSS declarations
  document.py             the worksheet as visible text
  audit.py                runs the gates
  render.py               headless Chrome -> PDF
  __main__.py             build | audit | check
```

`lint-imports` holds that shape: the CLI sits above the gates, which sit above
the maths; measuring the document and producing it stay independent; the
worksheet's maths knows nothing of how it is styled; and `numerals`, `content`,
`colors` and `spec` may not import `subprocess`, `pathlib` or `pypdf`, so the
domain layer cannot quietly start touching the filesystem.

Chrome does the rendering because the layout leans on flexbox, CSS custom
properties and paged-media rules that the lightweight Python renderers do not
implement faithfully.

### Type checking

`ty` runs against Python 3.14 with `python-platform = "all"` so `sys.platform`
stays unspecialised: the Chrome lookup has macOS paths and a Linux fallback,
and CI runs Linux. Warnings fail the build, and rules ty leaves off by default
are promoted to errors.

`unsound-return-statement` earned its keep immediately. It caught `float ** float`
inferring as `Any` (a negative base with a fractional exponent yields a complex
number, so the operator is typed loosely) and `re.Match.group` returning
`str | Any`. Both sat in the contrast maths, where a silent `Any` would have
meant a gate that computed nothing and passed anyway.

### Tests

The gates run against the real worksheet, not a fixture. A synthetic document
would let the shipped file drift while the suite stayed green, which is the
failure these checks exist to catch.

Several tests deliberately break the worksheet in a temp copy and assert the
gate fires: lighten `--rule` and the contrast gate must fail, add a stray hex
literal and the token gate must fail, change an ingredient weight and the
givens gate must fail. A gate that cannot fail is decoration.

**Visual regression.** The worksheet is a visual artifact, so the other gates
miss the failures that matter most. Sub-question labels riding above their
baseline, a measure narrow enough to orphan "box." onto its own line, a change
that pushed the sheet onto a fifth page: only the last of those was gated, and
all three were found by looking. `tests/reference/page-*.png` holds a greyscale
raster of each page, and `test_visual.py` compares against it with a 0.2% pixel
budget for Chrome's antialiasing noise. Rasterising in greyscale means a
reference image also records what comes out of a mono laser.

Regenerate deliberately, once the change is confirmed wanted:

```sh
UPDATE_REFERENCE=1 uv run pytest tests/test_visual.py
```

The Chrome-dependent tests skip where there is no browser, and the pixel test
also needs ImageMagick. Both skip on CI rather than failing, since the
references carry macOS font metrics. The correctness, contrast, token and
binding gates need only the HTML, so every change to the maths, the stylesheet
or the palette is still covered there.

### Known limitation

The build is not byte-reproducible: Chrome stamps a creation date into the PDF,
so consecutive builds differ in hash while being identical in content. The page
count is gated; the bytes are not.
