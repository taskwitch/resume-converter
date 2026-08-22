"""Parse the raw Markdown body of a résumé page into ordered IR body nodes.

This is a hand-written scanner for the one Hugo shortcode actually used in
``content/resume/``: ``resume/entry`` (see
``layouts/_shortcodes/resume/entry.html``). It is not a general Hugo
shortcode engine — there is no self-closing variant, no nesting, and
attributes always appear on a single line in every file under
``content/resume/``, so a single linear regex scan is sufficient and far
simpler than a full parser.
"""

from __future__ import annotations

import re

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

TOKEN_RE = re.compile(
    r"(?P<heading>^#{1,6}[ \t]+.*$)"
    r"|(?P<entry_open>\{\{<\s*resume/entry\s+.*?>\}\})",
    re.MULTILINE,
)

ENTRY_CLOSE = "{{< /resume/entry >}}"

ATTR_RE = re.compile(r'(?P<key>[\w-]+)\s*=\s*"(?P<value>(?:[^"\\]|\\.)*)"')

_ATTR_KEYS = ("title", "title-link", "subtitle", "date", "aside")


def _parse_attrs(entry_open_tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for m in ATTR_RE.finditer(entry_open_tag):
        key = m.group("key").replace("-", "_")
        value = m.group("value")
        attrs[key] = value
    return attrs


def _make_entry_node(attrs: dict[str, str], body: str | None) -> dict:
    return {
        "type": "entry",
        "title": attrs.get("title", ""),
        "title_link": attrs.get("title_link"),
        "subtitle": attrs.get("subtitle"),
        "date": attrs.get("date"),
        "aside": attrs.get("aside"),
        "body": body,
    }


def parse_body(body_text: str) -> list[dict]:
    """Parse a résumé page's Markdown body into a list of IR body nodes.

    HTML comments are stripped before scanning, so commented-out shortcode
    blocks (e.g. a disabled entry wrapped in ``<!-- ... -->``) are invisible
    to the parser and never produce a node — matching the fact that they
    render as nothing on the live site.
    """
    text = HTML_COMMENT_RE.sub("", body_text)

    nodes: list[dict] = []
    cursor = 0

    def flush_markdown(span: str) -> None:
        if span.strip():
            nodes.append({"type": "markdown_block", "markdown": span})

    for match in TOKEN_RE.finditer(text):
        flush_markdown(text[cursor : match.start()])

        if match.group("heading") is not None:
            heading_line = match.group("heading")
            stripped = heading_line.lstrip("#")
            level = len(heading_line) - len(stripped)
            nodes.append({"type": "heading", "level": level, "text": stripped.strip()})
            cursor = match.end()
            continue

        # entry_open
        open_tag = match.group("entry_open")
        attrs = _parse_attrs(open_tag)

        close_idx = text.find(ENTRY_CLOSE, match.end())
        if close_idx == -1:
            raise ValueError(
                f"unclosed {{{{< resume/entry >}}}} shortcode starting at offset {match.start()}"
            )

        inner = text[match.end() : close_idx]
        inner = inner.strip("\n")
        body = inner if inner.strip() else None

        nodes.append(_make_entry_node(attrs, body))
        cursor = close_idx + len(ENTRY_CLOSE)

    flush_markdown(text[cursor:])

    return nodes
