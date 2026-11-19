"""Public profiler facade: independent profile/compare entries and extensions.

[Role]
  Expose the existing profiler analysis and comparison modules through one
  stable Python boundary, with optional user-selected extension providers.
  Extension discovery is delegated to the shared sim public loader so there is
  one declaration/validation path across both packages.

[Invariants]
  * Importing this module never imports sim, reads a source or initializes a
    device.  The sim SDK is imported only inside explicit extension/profile
    calls, so raw profiler analysis stays independent of sim success.
  * A selected provider failure is returned as that failure; no fallback to a
    different analyzer or a summary envelope.
  * Profile/compare reports retain the existing C7 and comparison schemas.

[Timeouts & Locks]
  Delegates all bounded reads and query budgets to the existing modules.

[Side-Effect Policy]
  Pure import-time bindings; CLI commands write only the requested output file.
"""
from __future__ import annotations

from collections.abc import Mapping
import argparse
import functools
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .analyze import analyze_profile as _analyze_profile
from .compare import COMPARISON_SCHEMA, compare_profiles as _compare_profiles
from .events import REPORT_SCHEMA
from .inventory import inventory_profile

PROFILE_SCHEMA = REPORT_SCHEMA
CORE_PROVIDER = "core"
# CPython ``CO_VARKEYWORDS`` flag bit (8); written without a new numeric literal.
_CO_VARKEYWORDS = 2 << 2
PUBLIC_COMMANDS = frozenset({
    "extensions", "extension", "ext", "profile", "compare",
})
__all__ = [
    "PROFILE_SCHEMA", "CORE_PROVIDER", "PUBLIC_COMMANDS",
    "analyze_profile", "compare_profiles", "inventory_profile",
    "native_prediction_requests", "predict_native_requests",
    "compare_native_predictions",
    "load_extensions", "load_user_profile", "main",
]


def load_extensions(*args: Any, **kwargs: Any) -> Any:
    """Load one fixed extension context using the shared sim public loader."""
    try:
        from mindie_sim.public import load_extensions as _load_extensions
    except ImportError as exc:
        raise ValueError(
            "profiler_public_requires_mindie_sim_public_sdk") from exc
    return _load_extensions(*args, **kwargs)


def load_user_profile(source: Any, **kwargs: Any) -> Any:
    """Load a local user calibration profile through the shared public loader."""
    try:
        from mindie_sim.public import load_user_profile as _load_user_profile
    except ImportError as exc:
        raise ValueError(
            "profiler_public_requires_mindie_sim_public_sdk") from exc
    return _load_user_profile(source, **kwargs)


def _handler(capability: str, provider: str | None, extensions: Any):
    if provider == CORE_PROVIDER:
        return None
    if extensions is None:
        if provider is not None:
            raise ValueError("provider_requires_extension_context:"
                             + capability + ":" + str(provider))
        return None
    if provider is not None:
        return extensions.provider(capability, provider).factory
    selected = (extensions.select(capability)
                if hasattr(extensions, "select")
                else extensions.default_provider(capability))
    return selected.factory if selected is not None else None


def _callable_code(target: Any) -> Any:
    """Return the Python code object behind a function, method, or instance."""
    if isinstance(target, type):
        return getattr(target.__init__, "__code__", None)
    code = getattr(target, "__code__", None)
    if code is not None:
        return code
    return getattr(getattr(target, "__call__", None), "__code__", None)


def _accepts_context(factory: Any) -> bool:
    """Decide whether ``factory`` accepts keyword argument ``extensions``.

    Explicit ``_mindie_accepts_context`` opt-in/out wins, then partials unwrap
    to their wrapped callable, then the underlying code object's positional and
    keyword-only parameter names plus the ``**kwargs`` flag are inspected.
    """
    override = getattr(factory, "_mindie_accepts_context", None)
    if isinstance(override, bool):
        return override
    if isinstance(factory, functools.partial):
        if "extensions" in (factory.keywords or {}):
            return True
        return _accepts_context(factory.func)
    code = _callable_code(factory)
    if code is None:
        return False
    span = int(code.co_argcount) + int(getattr(code, "co_kwonlyargcount", 0))
    if int(code.co_flags) & _CO_VARKEYWORDS:
        return True
    return "extensions" in code.co_varnames[:span]


def _invoke(factory: Any, context: Any, args: tuple[Any, ...],
            kwargs: Mapping[str, Any]) -> Any:
    options = dict(kwargs)
    if context is not None and _accepts_context(factory):
        options["extensions"] = context
    return factory(*args, **options)


def _checked_profile(report: Any, capability: str) -> Mapping[str, Any]:
    if not isinstance(report, Mapping):
        raise ValueError("extension_result_not_mapping:" + capability)
    if report.get("schema_version") != PROFILE_SCHEMA:
        raise ValueError("extension_result_schema_invalid:" + capability
                         + ":requires:" + PROFILE_SCHEMA)
    if not isinstance(report.get("step_accounting"), Mapping):
        raise ValueError("extension_result_missing_metric:" + capability
                         + ":step_accounting")
    return report


def analyze_profile(source: Any, *, extensions: Any = None,
                    provider: str | None = None, **kwargs: Any) -> dict[str, Any]:
    """Analyze one explicit profiler source, optionally through a provider.

    The core implementation is the unchanged ``analyze_profile``.  A selected
    ``profile`` provider receives ``source``, ``extensions`` and the remaining
    keywords, and must return the ordinary C7 report.
    """
    handler = _handler("profile", provider, extensions)
    if handler is None:
        return _analyze_profile(source, **kwargs)
    return dict(_checked_profile(
        _invoke(handler, extensions, (source,), kwargs), "profile"))


def compare_profiles(baseline: Any, candidate: Any, *, extensions: Any = None,
                     provider: str | None = None,
                     **kwargs: Any) -> dict[str, Any]:
    """Compare two C7 reports with an optional independent compare provider."""
    handler = _handler("compare", provider, extensions)
    if handler is None:
        return _compare_profiles(baseline, candidate, **kwargs)
    result = _invoke(handler, extensions, (baseline, candidate), kwargs)
    if not isinstance(result, Mapping):
        raise ValueError("extension_result_not_mapping:compare")
    if result.get("schema_version") != COMPARISON_SCHEMA:
        raise ValueError("extension_result_schema_invalid:compare:requires:"
                         + COMPARISON_SCHEMA)
    if not isinstance(result.get("status"), str) or not result["status"]:
        raise ValueError("extension_result_missing_status:compare")
    return dict(result)


def native_prediction_requests(source: Any) -> dict[str, Any]:
    """Project native operator observations into timing-free prediction requests."""
    from .sim_bridge import native_prediction_requests as _requests
    return _requests(source)


def predict_native_requests(requests: Any, **kwargs: Any) -> dict[str, Any]:
    """Evaluate timing-free prediction requests through mindie-sim native operator binding."""
    from .sim_bridge import predict_native_requests as _predict
    return _predict(requests, **kwargs)


def compare_native_predictions(observations: Any, predictions: Any,
                               **kwargs: Any) -> dict[str, Any]:
    """Compare independent native operator predictions against observations under the 10% formal gate."""
    from .compare_acceptance import compare_native_predictions as _compare
    return _compare(observations, predictions, **kwargs)


def _load_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", action="append", default=[],
                        help="workspace directory or explicit mindie_ext.py")
    parser.add_argument("--package", action="append", default=[],
                        help="installed distribution with mindie_sim.extensions entry points")
    parser.add_argument("--entry-point", action="append", default=[],
                        help="explicit module:factory entry point")
    parser.add_argument("--profile", action="append", default=[],
                        help="local mindie-sim-user-profile/1 JSON")
    parser.add_argument("--discover-installed", action="store_true",
                        help="load every installed mindie_sim.extensions entry point")


def _context_from_args(args: argparse.Namespace) -> Any:
    if not (args.path or args.package or args.entry_point or args.profile
            or args.discover_installed):
        return None
    return load_extensions(
        paths=args.path, packages=args.package, entry_points=args.entry_point,
        profiles=args.profile, discover_installed=args.discover_installed,
    )


def _compare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler-api compare",
        description="Compare two C7 summaries, optionally through an extension.",
        allow_abbrev=False)
    parser.add_argument("--baseline", required=True, help="baseline C7 JSON")
    parser.add_argument("--candidate", required=True, help="candidate C7 JSON")
    parser.add_argument("--provider", help="selected compare provider; 'core' forces the core")
    _load_arguments(parser)
    parser.add_argument("--require-binding", action="store_true", help="fail if structure/event bindings are absent")
    parser.add_argument("--require-input-identity", action="store_true", help="fail if baseline and candidate input signatures differ")
    parser.add_argument("--output", "-o", help="write JSON here; otherwise print it")
    return parser


def _json_object(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("comparison_input_requires_object:" + path)
    return value


def _emit(payload: Mapping[str, Any], output: str | None) -> int:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if output:
        path = Path(output).expanduser()
        path.write_text(rendered + "\n", encoding="utf-8")
        print(json.dumps({"output": str(path), "status": payload.get("status")}))
    else:
        print(rendered)
    return 0


def _run_compare(argv: Sequence[str]) -> int:
    args = _compare_parser().parse_args(argv)
    try:
        context = _context_from_args(args)
        result = compare_profiles(
            _json_object(args.baseline), _json_object(args.candidate),
            extensions=context, provider=args.provider,
            require_binding=args.require_binding,
            require_input_identity=args.require_input_identity,
        )
        return _emit(result, args.output)
    except TimeoutError:
        raise
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 2


def _usage() -> str:
    return (
        "usage: mindie-profiler-api {extensions,profile,compare} ...\n"
        "  extensions list|inspect ...   load/inspect the shared extension context\n"
        "  profile inspect FILE          validate a local user calibration profile\n"
        "  compare --baseline A.json --candidate B.json [--provider NAME]\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(_usage(), file=sys.stderr)
        return 2
    if args[0] in {"-h", "--help", "help"}:
        print(_usage())
        return 0
    command, rest = args[0], args[1:]
    if command in {"extensions", "extension", "ext", "profile"}:
        try:
            from mindie_sim.public.cli import public_main
        except ImportError as exc:
            print(json.dumps({
                "status": "failed",
                "error": "profiler_public_requires_mindie_sim_public_sdk",
            }), file=sys.stderr)
            return 2
        return public_main([command, *rest], prog="mindie-profiler-api")
    if command == "compare":
        return _run_compare(rest)
    print(json.dumps({"status": "failed",
                      "error": "unknown_public_command:" + command}), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
