"""Glue frontmatter.py + shortcode_parser.py into a full Markdown -> IR reader."""

from __future__ import annotations

from .frontmatter import split_frontmatter
from .ir import make_ir, make_print, make_resume_meta, validate_ir
from .shortcode_parser import parse_body


def _normalize_contact(raw_contact: list) -> list[dict]:
    contact = []
    for item in raw_contact or []:
        contact.append(
            {
                "label": item.get("label"),
                "value": item.get("value", ""),
                "href": item.get("href"),
            }
        )
    return contact


def _normalize_resume_meta(fm: dict, title: str) -> dict:
    raw_resume = fm.get("resume") or {}
    raw_print = raw_resume.get("print") or {}
    return make_resume_meta(
        name=raw_resume.get("name") or title,
        tagline=list(raw_resume.get("tagline") or []),
        contact=_normalize_contact(raw_resume.get("contact") or []),
        print_=make_print(
            paper=raw_print.get("paper", "letter"),
            qrtarget=raw_print.get("qrtarget", False),
        ),
    )


def md_to_ir(raw_text: str) -> dict:
    """Parse a full Hugo résumé Markdown file (front matter + body) into IR."""
    fm, body_text = split_frontmatter(raw_text)

    title = fm.get("title", "")
    draft = bool(fm.get("draft", False))
    resume_meta = _normalize_resume_meta(fm, title)
    body_nodes = parse_body(body_text)

    ir = make_ir(title=title, draft=draft, resume=resume_meta, body=body_nodes)
    validate_ir(ir)
    return ir
