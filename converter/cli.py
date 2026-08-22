"""Command-line interface: python -m converter INPUT --to FORMAT [-o OUTPUT]."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from .ir import validate_ir
from .json_codec import ir_to_json, json_to_ir
from .latex_renderer import TEMPLATES_DIR, ir_to_latex
from .md_reader import md_to_ir
from .md_writer import ir_to_md
from .yaml_codec import ir_to_yaml, yaml_to_ir

_EXT_TO_FORMAT = {".md": "md", ".markdown": "md", ".yaml": "yaml", ".yml": "yaml", ".json": "json"}
_FORMAT_TO_EXT = {"md": ".md", "yaml": ".yaml", "json": ".json", "latex": ".tex"}

_READERS = {"md": md_to_ir, "yaml": yaml_to_ir, "json": json_to_ir}


class ConverterError(Exception):
    """User-facing error: caught in main() and printed without a traceback."""


def detect_format(path: Path) -> str:
    fmt = _EXT_TO_FORMAT.get(path.suffix.lower())
    if fmt is None:
        raise ConverterError(
            f"can't auto-detect input format from extension {path.suffix!r}; pass --from explicitly"
        )
    return fmt


def _read_ir(input_path: Path, from_format: str | None) -> dict:
    fmt = from_format or detect_format(input_path)
    reader = _READERS.get(fmt)
    if reader is None:
        raise ConverterError(f"can't read format {fmt!r} as input (expected md, yaml, or json)")
    text = input_path.read_text(encoding="utf-8")
    try:
        return reader(text)
    except Exception as exc:  # noqa: BLE001 - re-raised as a clean user-facing error
        raise ConverterError(f"failed to parse {input_path} as {fmt}: {exc}") from exc


def _resolve_output_path(input_path: Path, to_format: str, output_arg: str | None) -> Path:
    default_name = input_path.stem + _FORMAT_TO_EXT[to_format]
    if output_arg is None:
        return input_path.with_name(default_name)

    out = Path(output_arg)
    if out.is_dir() or output_arg.endswith(("/", "\\")):
        return out / default_name
    return out


def convert(
    input_path: Path,
    to_format: str,
    *,
    from_format: str | None = None,
    output_path: Path | None = None,
    paper: str | None = None,
) -> Path:
    """Convert ``input_path`` to ``to_format``, writing the result and returning its path."""
    ir = _read_ir(input_path, from_format)
    try:
        validate_ir(ir)
    except ValueError as exc:
        raise ConverterError(f"invalid résumé data: {exc}") from exc

    if output_path is None:
        output_path = _resolve_output_path(input_path, to_format, None)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if to_format == "json":
        output_path.write_text(ir_to_json(ir), encoding="utf-8")
    elif to_format == "yaml":
        output_path.write_text(ir_to_yaml(ir), encoding="utf-8")
    elif to_format == "md":
        output_path.write_text(ir_to_md(ir), encoding="utf-8")
    elif to_format == "latex":
        try:
            latex_text = ir_to_latex(ir, paper=paper)
        except RuntimeError as exc:
            raise ConverterError(str(exc)) from exc
        output_path.write_text(latex_text, encoding="utf-8")
        shutil.copyfile(TEMPLATES_DIR / "resume.sty", output_path.parent / "resume.sty")
    else:
        raise ConverterError(f"unknown output format {to_format!r}")

    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-converter",
        description="Convert a Hugo résumé Markdown file (content/resume/*.md) to/from LaTeX, YAML, or JSON.",
    )
    parser.add_argument("input", type=Path, help="input file (.md, .yaml, or .json)")
    parser.add_argument(
        "--to", required=True, choices=["latex", "yaml", "json", "md"], help="output format"
    )
    parser.add_argument(
        "--from", dest="from_format", choices=["md", "yaml", "json"], default=None,
        help="input format (auto-detected from the input file's extension if omitted)",
    )
    parser.add_argument("-o", "--output", default=None, help="output file or directory")
    parser.add_argument(
        "--paper", choices=["letter", "a4"], default=None,
        help="override resume.print.paper for --to latex output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 1

    output_path = _resolve_output_path(args.input, args.to, args.output)

    try:
        result_path = convert(
            args.input,
            args.to,
            from_format=args.from_format,
            output_path=output_path,
            paper=args.paper,
        )
    except ConverterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
