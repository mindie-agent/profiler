from mindie_profiler.__main__ import SUBCOMMANDS, main


def test_root_help_lists_all_commands(capsys):
    for flag in ("-h", "--help"):
        assert main([flag]) == 0
        out = capsys.readouterr().out
        for name in SUBCOMMANDS:
            assert name in out


def test_unknown_command_exits_2_with_choices(capsys):
    assert main(["bogus"]) == 2
    err = capsys.readouterr().err
    assert "bogus" in err
    for name in SUBCOMMANDS:
        assert name in err


def test_option_first_dispatches_to_analyze(monkeypatch):
    seen = {}
    monkeypatch.setattr("mindie_profiler.__main__._run_analyze", lambda rest: seen.setdefault("rest", rest) and 0)
    assert main(["--root", "x"]) == 0
    assert seen["rest"] == ["--root", "x"]


def test_subcommand_help_still_routes(capsys):
    try:
        main(["analyze", "-h"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "--root" in capsys.readouterr().out
