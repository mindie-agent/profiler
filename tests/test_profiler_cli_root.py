import json
import pytest
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


def test_inspect_op_abi_and_aclgraph_cli_wiring(capsys, tmp_path):
    for subcmd in ("inspect-op-abi", "aclgraph"):
        with pytest.raises(SystemExit) as exc:
            main([subcmd, "--help"])
        assert exc.value.code == 0
        help_out = capsys.readouterr().out
        assert subcmd in help_out

    assert main(["inspect-op-abi", "--op", "aclnnPagedAttention", "--cann-version", "8.0"]) == 0
    abi_card = json.loads(capsys.readouterr().out)
    assert abi_card["card"]["api"] == "aclnnPagedAttention"
    assert abi_card["identity"]["version_supported"] is True
    assert abi_card["identity"]["requested_version"] == "8.0"

    out_path = tmp_path / "launch_floor.json"
    assert main([
        "aclgraph",
        "--tool",
        "aclgraph_launch_floor",
        "--args-json",
        '{"mode": "full", "superkernel": true}',
        "--output",
        str(out_path),
    ]) == 0
    floor_stdout = json.loads(capsys.readouterr().out)
    floor_saved = json.loads(out_path.read_text(encoding="utf-8"))
    assert floor_stdout["ok"] == 1
    assert floor_stdout["mode"] == "full"
    assert floor_stdout["sk"] == 1
    assert floor_saved == floor_stdout

    assert main(["aclgraph", "--tool", "aclgraph_launch_floor", "--args-json", "{bad"]) == 2
    assert "invalid --args-json" in capsys.readouterr().err
