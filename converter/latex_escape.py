"""Escape plain-text fields for LaTeX output.

Only for fields Hugo never markdownifies (title/subtitle/date/tagline/
contact value) — anything that passes through pandoc (pandoc_bridge.py)
must never also go through this, or LaTeX specials get double-escaped.
"""

from __future__ import annotations

_LATEX_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\u2014": "---",  # em dash
    "\u2013": "--",  # en dash
}


def escape_latex(text: str | None) -> str:
    """Escape LaTeX special characters in ``text``.

    Character-by-character mapping, not chained ``.replace()`` calls, so
    the backslashes introduced by earlier replacements (e.g. ``\\&``) are
    never themselves re-escaped by a later rule.
    """
    if text is None:
        return ""
    return "".join(_LATEX_MAP.get(ch, ch) for ch in text)
