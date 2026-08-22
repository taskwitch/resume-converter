"""The intermediate representation (IR) shared by every format in this tool.

The IR is a plain nested dict/list/str/bool/None structure. There is no
dataclass or custom encoder: ``json.dumps(ir)`` and
``yaml.dump(ir, sort_keys=False)`` work directly on it, and *are* the YAML
and JSON output formats this tool produces — this is not an internal-only
shape. Dict insertion order (fixed by the factory functions below) controls
the key order YAML/JSON dump in, for readability.

Field notes:
- ``title``/``subtitle``/``date`` on an entry, and ``tagline``/
  ``contact[].value`` in the header, hold plain text — Hugo's
  ``resume/entry`` shortcode never markdownifies these fields, so a LaTeX
  renderer must escape them, never run them through a markdown converter.
- ``aside`` and an entry's ``body`` hold **raw, unconverted markdown** —
  Hugo does run these through ``markdownify``, so a LaTeX renderer must
  convert them via a markdown-to-LaTeX pipeline, never LaTeX-escape them
  directly.
"""

from __future__ import annotations


def make_contact_item(label: str | None, value: str, href: str | None) -> dict:
    return {"label": label, "value": value, "href": href}


def make_print(paper: str = "letter", qrtarget: bool | str = False) -> dict:
    return {"paper": paper, "qrtarget": qrtarget}


def make_resume_meta(
    name: str | None = None,
    tagline: list[str] | None = None,
    contact: list[dict] | None = None,
    print_: dict | None = None,
) -> dict:
    return {
        "name": name,
        "tagline": tagline or [],
        "contact": contact or [],
        "print": print_ or make_print(),
    }


def make_ir(
    title: str,
    draft: bool = False,
    resume: dict | None = None,
    body: list[dict] | None = None,
) -> dict:
    return {
        "title": title,
        "draft": draft,
        "resume": resume or make_resume_meta(),
        "body": body or [],
    }


def make_heading(level: int, text: str) -> dict:
    return {"type": "heading", "level": level, "text": text}


def make_entry(
    title: str,
    title_link: str | None = None,
    subtitle: str | None = None,
    date: str | None = None,
    aside: str | None = None,
    body: str | None = None,
) -> dict:
    return {
        "type": "entry",
        "title": title,
        "title_link": title_link,
        "subtitle": subtitle,
        "date": date,
        "aside": aside,
        "body": body,
    }


def make_markdown_block(markdown: str) -> dict:
    return {"type": "markdown_block", "markdown": markdown}


def validate_ir(ir: dict) -> None:
    """Light validation only — this is a personal utility with trusted input.

    Checks just enough to fail fast with a clear message rather than a
    confusing downstream KeyError/AttributeError.
    """
    if not isinstance(ir, dict):
        raise ValueError("IR must be a mapping")
    title = ir.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("IR is missing a non-empty 'title'")
    body = ir.get("body", [])
    if not isinstance(body, list):
        raise ValueError("IR 'body' must be a list")
    for i, node in enumerate(body):
        if not isinstance(node, dict) or "type" not in node:
            raise ValueError(f"IR body node {i} is missing a 'type'")
        if node["type"] not in ("heading", "entry", "markdown_block"):
            raise ValueError(f"IR body node {i} has unknown type {node['type']!r}")
