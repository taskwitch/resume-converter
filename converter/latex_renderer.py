"""Render IR to LaTeX, matching the résumé page's visual style.

Body nodes are rendered to LaTeX fragments in plain Python (not Jinja loops)
before ever reaching the template — this keeps the Jinja2 template a simple,
robust flat substitution (name/tagline/contact/body) rather than a template
that has to reason about node types itself. Jinja2 is still used, with
LaTeX-safe delimiters, for the outer document skeleton (see
templates/resume.tex.j2), per the standard "LaTeX + Jinja2" pattern that
avoids colliding with LaTeX's own `{ }`/`%` syntax.
"""

from __future__ import annotations

from pathlib import Path

import jinja2

from .latex_escape import escape_latex
from .pandoc_bridge import markdown_to_latex

TEMPLATES_DIR = Path(__file__).parent / "templates"

_GEOMETRY_OPTS = {
    "letter": "letterpaper,margin=0.75in",
    "a4": "a4paper,margin=18mm",
}


def _jinja_env() -> jinja2.Environment:
    return jinja2.Environment(
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    )


def _render_title_cell(entry: dict) -> str:
    title = escape_latex(entry.get("title") or "")
    link = entry.get("title_link")
    if link:
        return f"\\href{{{link}}}{{{title}}}"
    return title


def _render_entry(entry: dict) -> str:
    title_cell = _render_title_cell(entry)
    subtitle = escape_latex(entry.get("subtitle") or "")
    date = escape_latex(entry.get("date") or "")
    # aside/body are raw markdown in the IR (Hugo markdownifies them) -> pandoc.
    aside = markdown_to_latex(entry.get("aside"))
    body = markdown_to_latex(entry.get("body"))
    return f"\\resumeentry{{{title_cell}}}{{{subtitle}}}{{{date}}}{{{aside}}}{{{body}}}"


def _render_body_node(node: dict) -> str:
    node_type = node["type"]
    if node_type == "heading":
        return f"\\resumesection{{{escape_latex(node['text'])}}}"
    if node_type == "markdown_block":
        return markdown_to_latex(node["markdown"])
    raise ValueError(f"unknown IR body node type {node_type!r}")


def _render_body_nodes(nodes: list[dict]) -> str:
    """Render body nodes, wrapping each run of consecutive `entry` nodes in
    one \\resumeSubHeadingListStart...End list (see resume.sty) -- each
    \\resumeentry call now begins with \\item, so it must live inside such a
    list. A non-entry node (heading, or a stray markdown_block sibling from
    the malformed-shortcode case) ends the current run; a later entry opens
    a fresh list rather than continuing the old one.
    """
    parts: list[str] = []
    entry_buffer: list[str] = []

    def flush_entries() -> None:
        if entry_buffer:
            body = "\n".join(entry_buffer)
            parts.append(f"\\resumeSubHeadingListStart\n{body}\n\\resumeSubHeadingListEnd")
            entry_buffer.clear()

    for node in nodes:
        if node["type"] == "entry":
            entry_buffer.append(_render_entry(node))
        else:
            flush_entries()
            parts.append(_render_body_node(node))
    flush_entries()

    return "\n\n".join(parts)


def _render_tagline(tagline: list[str]) -> str:
    lines = [escape_latex(line) for line in tagline]
    return " \\\\\n      ".join(lines)


def _render_contact(contact: list[dict]) -> str:
    parts = []
    for item in contact:
        value = escape_latex(item.get("value") or "")
        href = item.get("href")
        parts.append(f"\\href{{{href}}}{{{value}}}" if href else value)
    return " \\\\\n      ".join(parts)


def ir_to_latex(ir: dict, *, paper: str | None = None) -> str:
    resume = ir.get("resume") or {}
    print_meta = resume.get("print") or {}
    paper = paper or print_meta.get("paper") or "letter"
    if paper not in _GEOMETRY_OPTS:
        raise ValueError(f"unknown paper size {paper!r}; expected 'letter' or 'a4'")

    name = escape_latex(resume.get("name") or ir.get("title") or "")
    tagline_latex = _render_tagline(resume.get("tagline") or [])
    contact_latex = _render_contact(resume.get("contact") or [])

    body_latex = _render_body_nodes(ir.get("body") or [])

    env = _jinja_env()
    template = env.get_template("resume.tex.j2")
    return template.render(
        geometry_opts=_GEOMETRY_OPTS[paper],
        name=name,
        tagline_latex=tagline_latex,
        contact_latex=contact_latex,
        body_latex=body_latex,
    )
