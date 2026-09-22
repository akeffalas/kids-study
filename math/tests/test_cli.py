"""Exit codes are the contract CI depends on, so they are pinned here."""

from pathlib import Path

import pytest

from worksheet.__main__ import EXIT_BAD_INPUT, EXIT_GATE_FAILED, EXIT_OK, main

SOURCE = Path(__file__).resolve().parent.parent / "hyrule-math-review.html"
NO_PDF = "does-not-exist.pdf"


@pytest.mark.parametrize(
    "argv",
    [
        ["--source", str(SOURCE), "audit"],
        ["audit", "--source", str(SOURCE)],
    ],
    ids=["before-subcommand", "after-subcommand"],
)
def test_shared_options_work_on_either_side_of_the_subcommand(argv, capsys):
    """`worksheet audit --source x` is what people actually type."""
    assert main([*argv, "--output", NO_PDF]) == EXIT_OK
    assert "checks passed" in capsys.readouterr().out


def test_a_passing_audit_exits_zero(capsys):
    code = main(["audit", "--source", str(SOURCE), "--output", NO_PDF])
    capsys.readouterr()
    assert code == EXIT_OK


def test_a_missing_source_exits_two(tmp_path, capsys):
    code = main(["audit", "--source", str(tmp_path / "absent.html")])
    assert code == EXIT_BAD_INPUT
    assert "error:" in capsys.readouterr().err


def test_a_failing_gate_exits_one(tmp_path, capsys):
    broken = tmp_path / "broken.html"
    broken.write_text(
        SOURCE.read_text(encoding="utf-8").replace(
            "--rule:    #A8863F;", "--rule:    #E8DCC0;", 1
        ),
        encoding="utf-8",
    )
    code = main(["audit", "--source", str(broken), "--output", NO_PDF])
    assert code == EXIT_GATE_FAILED
    assert "FAIL" in capsys.readouterr().out


def test_failures_are_summarised_after_the_table(tmp_path, capsys):
    broken = tmp_path / "broken.html"
    broken.write_text(
        SOURCE.read_text(encoding="utf-8").replace(
            "--rule:    #A8863F;", "--rule:    #E8DCC0;", 1
        ),
        encoding="utf-8",
    )
    main(["audit", "--source", str(broken), "--output", NO_PDF])
    assert "failure(s):" in capsys.readouterr().out


def test_an_unknown_subcommand_exits_two():
    with pytest.raises(SystemExit) as excinfo:
        main(["frobnicate"])
    assert excinfo.value.code == EXIT_BAD_INPUT


def test_a_missing_subcommand_is_rejected():
    with pytest.raises(SystemExit):
        main([])
