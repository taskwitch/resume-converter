"""Reconstruct Hugo résumé Markdown (front matter + body + shortcodes) from IR.

The output is not guaranteed to be a byte-for-byte diff of any particular
source file — it is guaranteed to be valid Hugo content that renders
identically. Known, documented lossy aspects: HTML comments from the
original source are never present in the IR (see shortcode_parser.py) so
they cannot be reconstructed, and a literal ``"`` inside a plain-text
shortcode attribute value is not re-escaped (no current fixture hits this).
"""

from __future__ import annotations

import yaml

_ATTR_ORDER = (
    ("title", "title"),
    ("title_link", "title-link"),
    ("subtitle", "subtitle"),
    ("date", "date"),
    ("aside", "aside"),
)


def _render_entry_shortcode(node: dict) -> str:
    attr_parts = []
    for ir_key, hugo_key in _ATTR_ORDER:
        value = node.get(ir_key)
        if value is not None:
            attr_parts.append(f'{hugo_key}="{value}"')
    open_tag = "{{< resume/entry " + " ".join(attr_parts) + " >}}"

    body = node.get("body")
    if body:
        return f"{open_tag}\n{body}\n{{{{< /resume/entry >}}}}"
    return f"{open_tag}{{{{< /resume/entry >}}}}"


def _render_body_node(node: dict) -> str:
    node_type = node["type"]
    if node_type == "heading":
        return "#" * node["level"] + " " + node["text"]
    if node_type == "entry":
        return _render_entry_shortcode(node)
    if node_type == "markdown_block":
        return node["markdown"]
    raise ValueError(f"unknown IR body node type {node_type!r}")


def _build_front_matter(ir: dict) -> dict:
    resume = ir.get("resume") or {}
    fm: dict = {"title": ir["title"]}
    if ir.get("draft"):
        fm["draft"] = True

    print_meta = resume.get("print") or {}
    fm["resume"] = {
        "name": resume.get("name"),
        "tagline": list(resume.get("tagline") or []),
        "contact": [dict(c) for c in resume.get("contact") or []],
        "print": {
            "paper": print_meta.get("paper", "letter"),
            "qrtarget": print_meta.get("qrtarget", False),
        },
    }
    return fm


def ir_to_md(ir: dict) -> str:
    fm = _build_front_matter(ir)
    fm_text = yaml.dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=100
    )

    body_parts = [_render_body_node(node) for node in ir.get("body") or []]
    body_text = "\n\n".join(body_parts)

    return f"---\n{fm_text}---\n\n{body_text}\n"
