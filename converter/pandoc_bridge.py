"""Convert genuine Markdown fragments to LaTeX via pandoc (subprocess).

Used for the IR fields Hugo actually runs through ``markdownify`` —
``aside``, an entry's ``body``, and standalone ``markdown_block`` text.
Never used for plain-text fields (title/subtitle/date/...); those go
through latex_escape.py instead.
"""

from __future__ import annotations

import re
import shutil
import subprocess

PANDOC_ARGS = ["-f", "markdown", "-t", "latex", "--wrap=preserve"]

# \LaTeX/\TeX (and our resume.sty's \KaTeX, which is built on \TeX) manipulate
# \spacefactor internally, which is undefined in math mode -- a hard compile
# error. Inline KaTeX-style source like "$\rm\LaTeX$" or "$\KaTeX$" (valid in
# a browser, since KaTeX doesn't track TeX's mode distinctions) becomes real
# LaTeX math mode once pandoc converts "$...$" to "\(...\)", so these logo
# macros need to be wrapped in \mbox{} to force them back into text mode.
# \mbox{\LaTeX} behaves identically to bare \LaTeX in text mode, so this is
# applied unconditionally rather than only inside detected math spans.
_TEX_LOGO_RE = re.compile(r"\\(LaTeX|KaTeX|TeX)\b")


def _mbox_wrap_tex_logos(latex_text: str) -> str:
    return _TEX_LOGO_RE.sub(lambda m: f"\\mbox{{\\{m.group(1)}}}", latex_text)


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def markdown_to_latex(md_text: str | None) -> str:
    if not md_text or not md_text.strip():
        return ""

    try:
        result = subprocess.run(
            ["pandoc", *PANDOC_ARGS],
            input=md_text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pandoc is required to convert Markdown fields to LaTeX but was not found on PATH"
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace")
        raise RuntimeError(f"pandoc failed converting markdown to latex: {stderr}")

    return _mbox_wrap_tex_logos(result.stdout.decode("utf-8").strip())
