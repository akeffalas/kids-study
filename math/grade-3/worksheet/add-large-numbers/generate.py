r"""Generate the Pac-Man four-addend addition worksheet. Answers are computed.

Writes pacman-addition-maze.html next to this file. Render it with:

    uv run worksheet build \
        --source grade-3/worksheet/add-large-numbers/pacman-addition-maze.html \
        --output grade-3/worksheet/add-large-numbers/PacMan-Addition-Maze.pdf
"""

from pathlib import Path

PROBLEMS = [
    (125, 231, 402, 130),  # no carrying
    (213, 142, 321, 104),  # one carry
    (258, 314, 129, 163),  # two carries
    (407, 285, 136, 219),  # carries into the thousands
    (389, 276, 451, 198),  # a carry of 3
    (869, 578, 693, 745),  # biggest sum
]
EXAMPLE = (247, 135, 318, 126)
ADDENDS = 4
SMALLEST, LARGEST = 100, 999  # three-digit numbers only
BASE = 10
HUNDREDS = 2  # index of the hundreds column, which writes its whole total

for p in [*PROBLEMS, EXAMPLE]:
    if len(p) != ADDENDS or not all(SMALLEST <= n <= LARGEST for n in p):
        raise ValueError(f"not four 3-digit addends: {p}")

# Arcade fruit levels, easiest first: (name, first problem, last problem)
LEVELS = [("Cherry", 1, 2), ("Strawberry", 3, 4), ("Ghost", 5, 6)]

INK = "#1B2A41"
PAC = f"""<svg class="{{cls}}" viewBox="0 0 100 100" aria-label="Pac-Man">
  <path d="M50,50 L93,27 A48,48 0 1,0 93,73 Z" fill="#FFD21F" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
  <circle cx="50" cy="26" r="6" fill="{INK}"/></svg>"""


def ghost(color: str, cls: str = "icon") -> str:
    """Draw a ghost in the given body colour."""
    return f"""<svg class="{cls}" viewBox="0 0 100 100" aria-label="ghost">
  <path d="M10,92 L10,48 A40,40 0 0,1 90,48 L90,92 L77,80 L63,92 L50,80 L37,92 L23,80 Z"
        fill="{color}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
  <ellipse cx="35" cy="46" rx="11" ry="13" fill="#fff" stroke="{INK}" stroke-width="3"/>
  <ellipse cx="65" cy="46" rx="11" ry="13" fill="#fff" stroke="{INK}" stroke-width="3"/>
  <circle cx="39" cy="49" r="5" fill="{INK}"/><circle cx="69" cy="49" r="5" fill="{INK}"/></svg>"""


FRUIT = {
    "Cherry": f"""<svg class="icon" viewBox="0 0 100 100" aria-label="cherries">
  <path d="M30,62 C40,30 55,18 78,10 M70,60 C68,40 72,24 78,10" fill="none" stroke="#2E6B2E" stroke-width="6" stroke-linecap="round"/>
  <circle cx="30" cy="70" r="18" fill="#E0322B" stroke="{INK}" stroke-width="5"/>
  <circle cx="70" cy="68" r="18" fill="#E0322B" stroke="{INK}" stroke-width="5"/></svg>""",
    "Strawberry": f"""<svg class="icon" viewBox="0 0 100 100" aria-label="strawberry">
  <path d="M50,94 C22,74 14,52 20,36 C30,26 70,26 80,36 C86,52 78,74 50,94 Z" fill="#E0322B" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M26,34 L40,22 L50,32 L60,22 L74,34 Z" fill="#3E9B3E" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
  <g fill="#FFF3B0"><circle cx="38" cy="50" r="3.5"/><circle cx="60" cy="48" r="3.5"/><circle cx="48" cy="64" r="3.5"/>
  <circle cx="34" cy="68" r="3.5"/><circle cx="64" cy="66" r="3.5"/><circle cx="50" cy="80" r="3.5"/></g></svg>""",
    "Ghost": ghost("#3FC7E0"),
}


def level_of(n: int) -> str:
    """Name the fruit level that problem n belongs to."""
    return next(name for name, lo, hi in LEVELS if lo <= n <= hi)


def cells(chars: str, cls: str = "") -> str:
    """One grid cell per character; a space becomes an empty cell."""
    return "".join(f'<i class="{cls}">{c.strip()}</i>' for c in chars)


def column_grid(
    nums: tuple[int, ...], carries: str = "  ", answer: str = "    ", label: bool = False
) -> str:
    """Op column, then thousands/hundreds/tens/ones. Carry boxes sit over hundreds and tens."""
    lab = '<i class="lab">carry</i>' if label else "<i></i>"
    rows = ["<i></i>" + lab + cells(carries, "cy") + "<i></i>"]
    for k, n in enumerate(nums):
        last = k == len(nums) - 1
        rows.append(
            f'<i class="op{" last" if last else ""}">{"+" if last else ""}</i>'
            + cells(str(n).rjust(4), "d last" if last else "d")
        )
    rows.append(
        f'<i></i><i class="ans opt">{answer[0].strip()}</i>' + cells(answer[1:], "ans")
    )
    return "".join(rows)


def columns(nums: tuple[int, ...]) -> list[tuple[str, int, int]]:
    """For ones, tens, hundreds: (expression, column total, carry into it)."""
    out: list[tuple[str, int, int]] = []
    carry = 0
    for place in (1, BASE, BASE * BASE):
        digits = [n // place % BASE for n in nums]
        expr = "+".join(str(d) for d in ([carry] if carry else []) + digits)
        total = sum(digits) + carry
        out.append((expr, total, carry))
        carry = total // BASE
    return out


def problem(n: int, nums: tuple[int, ...]) -> str:
    """Draw problem n as a card: number, level, check box, then the column grid."""
    lvl = level_of(n)
    return f"""<div class="prob"><div class="side">
    <div class="pellet">{n}</div>{FRUIT[lvl]}<div class="lvl">{lvl}</div>
    <div class="chk"><span></span>I checked</div></div>
  <div class="cgrid num">{column_grid(nums, label=n == 1)}</div></div>"""


def example() -> str:
    """Draw the worked example, with its carries and answer filled in."""
    cols = columns(EXAMPLE)
    carries = f"{cols[2][2] or ' '}{cols[1][2] or ' '}"
    answer = str(sum(EXAMPLE)).rjust(4)
    ones = cols[0]
    return f"""<div class="prob ex"><div class="exhead">Watch me first! <span class="extag">EXAMPLE</span></div>
  <div class="exbody"><div class="cgrid small num">{column_grid(EXAMPLE, carries, answer)}</div>
  <ol class="steps">
    <li><b>Add the ones.</b> <span class="num grp">{ones[0].replace("+", " + ")} = {ones[1]}</span></li>
    <li><b>Write {ones[1] % 10}</b>, carry <b class="num">{ones[1] // 10}</b> to the tens.</li>
    <li><b>Tens, then hundreds.</b> Add the carry!</li>
    <li><b>Check:</b> add again bottom up, then tick <b>I checked</b>.</li>
  </ol></div></div>"""


def finish() -> str:
    """Draw the finish-line tracker and score."""
    # a snake: 1-3 left to right, turn, then 4-6 back right to left
    order = [1, 2, 3, 6, 5, 4]
    dots = "".join(f'<span class="dot num">{i}</span>' for i in order)
    return f"""<div class="prob finish"><div class="exhead">Finish line!</div>
  <p>Color in a dot for each problem you finish.</p>
  <div class="lane"><span class="start">{PAC.format(cls="icon")}</span><div class="dots">{dots}</div>
  <span class="end">{FRUIT["Cherry"]}</span></div>
  <div class="score">Score <span></span><b class="num">/ 6</b></div></div>"""


def header(page: str, title: str = "Pac-Man Addition Maze", *, name: bool = True) -> str:
    """Draw the running header for pages after the first."""
    field = '<div class="mname">Name: <span></span></div>' if name else ""
    return f"""<div class="mini">{PAC.format(cls="pacsm")}
  <h1>{title}</h1>
  <div class="pg">{page}</div>
  {field}
</div>"""


def key_rows() -> str:
    """Build the answer-key table rows, grouped by level."""
    rows = []
    for name, lo, hi in LEVELS:
        rows.append(
            f'<tr class="lv"><td colspan="6">{FRUIT[name]} {name} level</td></tr>'
        )
        for n in range(lo, hi + 1):
            p = PROBLEMS[n - 1]
            tds = []
            for i, (expr, total, _) in enumerate(columns(p)):
                th, rest = divmod(total, BASE)
                if total < BASE:
                    note = f"write {total}"
                elif i < HUNDREDS:
                    note = f"write {rest}, carry {th}"
                else:
                    plural = "s" if th > 1 else ""
                    note = f"write {total} ({th} thousand{plural}, {rest} hundreds)"
                tds.append(
                    f'<td><span class="num">{expr} = {total}</span><small>{note}</small></td>'
                )
            rows.append(f"""<tr><td class="n num">{n}</td>
  <td class="num">{" + ".join(str(x) for x in p)}</td>{"".join(tds)}
  <td class="a num">{sum(p):,}</td></tr>""")
    return "".join(rows)


page1 = example() + "".join(problem(i, p) for i, p in enumerate(PROBLEMS, 1)) + finish()

html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pac-Man Addition Maze</title>
<style>
  :root {{
    --t-xs: 11px; --t-sm: 13px; --t-md: 15px; --t-lg: 18px; --t-xl: 26px; --t-display: 30px;
    --s1: 4px; --s2: 8px; --s3: 16px; --s4: 24px;
    --ink: #1B2A41; --ink2: #4A5A72; --maze: #1F3FBF;
    --pellet: #FFD21F; --rule: #6A7F9E; --green: #0F6E5C;
    --red: #A8321A; --wash: #F5F7FE;
    --faded: #7D8BA0;  /* example digits: 3.2:1 on wash, a clear step lighter than --red in grey */
    --hair: #8E9CB3;   /* table rules that must survive a mono laser */
  }}
  @page {{ size: letter; margin: 0.38in 0.5in; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; color: var(--ink);
         font-family: "Chalkboard SE", "Comic Sans MS", "Marker Felt", sans-serif;
         -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .num {{ font-family: "Avenir Next", "Helvetica Neue", Helvetica, sans-serif;
          font-weight: 700; font-variant-numeric: tabular-nums; }}
  .page {{ page-break-after: always; }}
  .page:last-child {{ page-break-after: auto; }}
  .icon {{ width: 30px; height: 30px; }}

  /* maze-wall frame: the arcade's double blue line */
  .banner, .mini {{ border: 7px double var(--maze); border-radius: 18px; background: var(--wash); }}
  .banner {{ display: flex; align-items: center; gap: var(--s3);
             padding: var(--s2) var(--s4); margin-bottom: var(--s3); }}
  .banner h1 {{ margin: 0 0 var(--s2); font-size: var(--t-display); color: var(--maze); letter-spacing: .02em; }}
  .banner .mid {{ flex: 1; }}
  .pacbig {{ width: 64px; height: 64px; flex: 0 0 auto; }}
  .ghosts {{ display: flex; gap: var(--s1); }}
  .ghosts .icon {{ width: 34px; height: 34px; }}
  .fields {{ display: flex; gap: var(--s4); font-size: var(--t-sm); color: var(--ink2); }}
  .fields div {{ display: flex; gap: var(--s2); align-items: baseline; }}
  .fields div:first-child {{ flex: 1; }}
  .fields span {{ flex: 1; min-width: 90px; border-bottom: 2.5px dotted var(--rule); }}

  .mini {{ display: flex; align-items: center; gap: var(--s3); padding: var(--s1) var(--s3);
           margin-bottom: var(--s3); }}
  .mini h1 {{ margin: 0; font-size: var(--t-lg); color: var(--maze); }}
  .pacsm {{ width: 34px; height: 34px; }}
  .mini .pg {{ margin-left: auto; font-size: var(--t-sm); color: var(--ink2); font-style: italic; }}
  .mini .mname {{ font-size: var(--t-sm); color: var(--ink2); }}
  .mini .mname span {{ display: inline-block; min-width: 150px; border-bottom: 2.5px dotted var(--rule); }}

  /* ---------- cards: 2 columns, 3 rows per page ---------- */
  .probs {{ display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: 204px; gap: 12px var(--s3); }}
  .prob {{ border: 3px solid var(--maze); border-radius: 14px; background: #fff;
           padding: 8px var(--s3) 8px 8px; display: flex; gap: var(--s3);
           page-break-inside: avoid; }}
  /* left rail: number, level fruit, and a box to tick once the answer is re-checked */
  .side {{ flex: 0 0 64px; display: flex; flex-direction: column; align-items: center; gap: 2px; }}
  .side .icon {{ width: 26px; height: 26px; margin-top: var(--s1); }}
  .lvl {{ font-size: var(--t-xs); color: var(--ink2); }}
  .chk {{ margin-top: auto; display: flex; flex-direction: column; align-items: center; gap: 2px;
          font-size: var(--t-xs); color: var(--ink2); }}
  .chk span {{ width: 22px; height: 22px; border: 2.5px solid var(--ink); border-radius: 6px; }}
  .pellet {{ width: 32px; height: 32px; border-radius: 50%; background: var(--pellet);
             border: 3px solid var(--ink); font-size: var(--t-lg); font-weight: 700;
             display: flex; align-items: center; justify-content: center; }}

  /* one digit per cell so every column lines up */
  .cgrid {{ flex: 1; display: grid; justify-content: center; align-content: center;
            grid-template-columns: 40px repeat(4, 34px);
            grid-template-rows: 26px repeat(4, 30px) 34px; font-size: var(--t-xl); }}
  .cgrid i {{ font-style: normal; text-align: center; line-height: 30px; }}
  .cgrid i.d {{ color: var(--green); }}
  /* pulled right, into the empty thousands column, to sit near its number */
  .cgrid i.op {{ position: relative; left: 18px; text-align: center; color: var(--ink); font-weight: 900; font-size: 28px; }}
  .cgrid i.last {{ border-bottom: 3.5px solid var(--ink); }}
  .cgrid i.lab, .cgrid i.cy {{ line-height: 19px; }}
  .cgrid i.lab {{ font-size: var(--t-xs); font-weight: 400; font-style: italic; color: var(--ink2);
                  text-align: right; padding-right: 2px; }}
  /* carry boxes: small, so carries stay smaller than the digits */
  .cgrid i.cy {{ margin: 1px 7px 4px; border: 2px dashed var(--rule); border-radius: 5px;
                 font-size: var(--t-md); color: var(--red); }}
  .cgrid i.ans {{ margin: 4px 2px 0; border: 2.5px solid var(--green); border-radius: 7px;
                  line-height: 26px; color: var(--red); }}

  /* ---------- worked example ---------- */
  .finish {{ justify-content: center; }}
  .ex, .finish {{ flex-direction: column; gap: 2px; padding: 8px var(--s3); background: var(--wash); }}
  .exhead {{ font-size: var(--t-md); font-weight: 700; color: var(--maze); }}
  .exbody {{ display: flex; gap: var(--s2); align-items: center; flex: 1; }}
  .cgrid.small {{ flex: 0 0 auto; grid-template-columns: 26px repeat(4, 26px);
                  grid-template-rows: 18px repeat(4, 26px) 32px; font-size: 19px; }}
  .cgrid.small i {{ line-height: 26px; }}
  .cgrid.small i.d {{ color: var(--faded); }}
  /* filled-in work is handwriting, so it differs from the printed digits by shape too, not only colour */
  .cgrid.small i.cy, .cgrid.small i.ans {{ font-family: "Chalkboard SE", "Comic Sans MS", sans-serif; }}
  .cgrid.small i.op {{ color: var(--faded); }}
  .extag {{ margin-left: var(--s1); font-size: var(--t-xs); letter-spacing: .12em; color: #fff;
            background: var(--ink2); border-radius: 999px; padding: 1px var(--s2); vertical-align: 2px; }}
  .cgrid.small i.op {{ font-size: 22px; left: 12px; }}
  .cgrid.small i.cy {{ margin: 1px 5px 2px; line-height: 13px; height: 15px; font-size: var(--t-sm); }}
  .cgrid.small i.ans {{ line-height: 24px; }}
  /* the thousands box is only for answers of 1,000 or more */
  .cgrid i.ans.opt {{ border: 2px dashed var(--rule); }}
  .steps {{ margin: 0; padding-left: 18px; font-size: 12px; line-height: 1.25; }}
  .steps li {{ margin-bottom: 4px; }}
  .steps .grp {{ white-space: nowrap; }}
  .steps b {{ color: var(--maze); }}

  /* ---------- finish line ---------- */
  .finish p {{ margin: 0; font-size: var(--t-sm); }}
  .lane {{ display: grid; grid-template-columns: 40px 1fr; grid-template-rows: 32px 32px;
           column-gap: var(--s1); row-gap: 10px; margin-top: var(--s2); }}
  .lane .icon {{ width: 32px; height: 32px; display: block; }}
  .lane .start {{ grid-area: 1 / 1; }}
  .lane .end {{ grid-area: 2 / 1; }}
  .dots {{ grid-area: 1 / 2 / 3 / 3; position: relative; display: grid;
           grid-template-columns: repeat(3, 1fr); grid-template-rows: 32px 32px; row-gap: 10px;
           justify-items: center; align-items: center; }}
  /* the dashed track behind the dots, with a U-turn after dot 3 */
  .dots::before {{ content: ""; position: absolute; left: -14px; right: 2px; top: 16px; bottom: 16px;
                   border: 3px dashed var(--rule); border-left: none; border-radius: 0 26px 26px 0; }}
  .dot {{ position: relative; }}
  .dot {{ width: 30px; height: 30px; border-radius: 50%; border: 3px solid var(--ink); background: #fff;
          font-size: var(--t-xs); color: var(--ink2); display: flex; align-items: center;
          justify-content: center; }}
  .score {{ margin-top: var(--s2); align-self: center; display: flex; align-items: baseline; gap: var(--s2);
            font-size: var(--t-lg); color: var(--maze); font-weight: 700; }}
  .score span {{ display: inline-block; width: 46px; border-bottom: 3px dotted var(--rule); height: 24px; }}

  .footer {{ margin: var(--s3) 0 0; text-align: center; font-size: var(--t-md); color: var(--ink2); }}

  /* ---------- answer key ---------- */
  .key table {{ width: 100%; border-collapse: collapse; font-size: var(--t-sm); }}
  .key th {{ text-align: left; font-size: var(--t-xs); color: var(--ink2); font-weight: 700;
            padding: 0 var(--s2) var(--s1); border-bottom: 3px solid var(--maze); }}
  .key td {{ padding: 5px var(--s2); border-bottom: 1px solid var(--hair); vertical-align: top; }}
  .key td small {{ display: block; font-size: var(--t-xs); color: var(--ink2); font-style: italic; }}
  .key td.n {{ color: var(--maze); }}
  .key td.a {{ color: var(--green); font-size: var(--t-lg); text-align: right; }}
  .key th:last-child {{ text-align: right; }}
  .key tr.lv td {{ padding-top: var(--s3); font-weight: 700; color: var(--maze); border-bottom: none; }}
  .key tr.lv .icon {{ width: 20px; height: 20px; vertical-align: -4px; }}
  .tip {{ font-size: var(--t-sm); color: var(--ink2); margin: var(--s3) 0 0; line-height: 1.5; }}
</style></head>
<body>

<div class="page">
<div class="banner">
  {PAC.format(cls="pacbig")}
  <div class="mid">
    <h1>Pac-Man Addition Maze</h1>
    <div class="fields"><div>Name: <span></span></div><div>Date: <span></span></div></div>
  </div>
  <div class="ghosts">{ghost("#E0322B")}{ghost("#F7A1C4")}</div>
</div>
<div class="probs">{page1}</div>
</div>

<div class="page key">
{header("For the grown-up", "Answer Key", name=False)}
<table>
  <thead><tr><th>#</th><th>Problem</th><th>Ones</th><th>Tens</th><th>Hundreds</th><th>Answer</th></tr></thead>
  <tbody>{key_rows()}</tbody>
</table>
<p class="tip">Each column shows the digits added, with the carry from the column before it listed
  first. The most common mistake is forgetting to add the carry, so an answer comes out 10 or 100
  too small: find the first column where the work differs from this table.</p>
</div>

</body></html>
"""

(Path(__file__).parent / "pacman-addition-maze.html").write_text(html)
