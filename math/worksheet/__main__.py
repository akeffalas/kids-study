"""Command line entry point: `uv run worksheet build | audit | check`."""

import argparse
import sys
from pathlib import Path

from .audit import Report, Status, audit
from .render import ChromeNotFoundError, RenderError, render_pdf
from .stylesheet import StylesheetError

DEFAULT_SOURCE = Path("chapter-1/hyrule-math-review.html")
DEFAULT_OUTPUT = Path("chapter-1/Hyrule-Math-Quest.pdf")

MARK = {Status.PASS: "ok  ", Status.FAIL: "FAIL"}

EXIT_OK = 0
EXIT_GATE_FAILED = 1
EXIT_BAD_INPUT = 2


def print_report(report: Report) -> None:
    """Print every finding, grouped, then a pass/fail summary."""
    for group, findings in report.by_group().items():
        print(f"\n{group}")
        for finding in findings:
            print(f"  {MARK[finding.status]}  {finding.label:<34} {finding.detail}")

    failures = report.failures
    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for finding in failures:
            print(f"  - {finding.label}: {finding.detail}")
    else:
        print(f"all {len(report.findings)} checks passed")


def run_build(args: argparse.Namespace) -> int:
    """Render the PDF."""
    pdf = render_pdf(args.source, args.output, args.chrome)
    print(f"built {pdf} ({pdf.stat().st_size:,} bytes)")
    return EXIT_OK


def run_audit(args: argparse.Namespace) -> int:
    """Run the quality gates against the source, and the PDF if it exists."""
    report = audit(args.source, args.output if args.output.is_file() else None)
    print_report(report)
    return EXIT_OK if report.ok else EXIT_GATE_FAILED


def run_check(args: argparse.Namespace) -> int:
    """Build, then audit. This is what CI runs."""
    run_build(args)
    return run_audit(args)


def shared_options() -> argparse.ArgumentParser:
    """Options accepted both before and after the subcommand.

    Attached to the root parser *and* to every subparser, because
    `worksheet audit --source x` is what people actually type; argparse
    otherwise accepts it only ahead of the subcommand.
    """
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--source", type=Path, default=DEFAULT_SOURCE, help="worksheet HTML"
    )
    shared.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="PDF to write"
    )
    shared.add_argument(
        "--chrome", type=Path, default=None, help="explicit browser binary"
    )
    return shared


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    shared = shared_options()
    parser = argparse.ArgumentParser(
        prog="worksheet",
        description=__doc__.splitlines()[0] if __doc__ else None,
        parents=[shared],
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text, run in (
        ("build", "render the PDF", run_build),
        ("audit", "run quality gates", run_audit),
        ("check", "build, then audit", run_check),
    ):
        sub.add_parser(name, help=help_text, parents=[shared]).set_defaults(run=run)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Build or gate the worksheet. Returns a process exit code."""
    args = parse_args(argv)
    try:
        return int(args.run(args))
    except (
        ChromeNotFoundError,
        RenderError,
        StylesheetError,
        FileNotFoundError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
