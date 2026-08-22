"""Split a Hugo content file into its YAML front matter and raw Markdown body."""

from __future__ import annotations

import yaml


def split_frontmatter(raw_text: str) -> tuple[dict, str]:
    """Split ``raw_text`` into (front_matter_dict, body_text).

    Hand-rolled rather than depending on python-frontmatter: the format is a
    trivial ``---\\n<yaml>\\n---\\n<body>`` convention and Hugo requires the
    delimiters to be bare ``---`` lines.
    """
    lines = raw_text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("expected file to start with a '---' front matter delimiter")

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break
    if end_index is None:
        raise ValueError("front matter is not closed with a second '---' delimiter")

    fm_text = "".join(lines[1:end_index])
    front_matter = yaml.safe_load(fm_text) or {}
    if not isinstance(front_matter, dict):
        raise ValueError("front matter must be a YAML mapping")

    body_text = "".join(lines[end_index + 1 :])
    # Drop at most one leading blank line so body parsing starts cleanly.
    if body_text.startswith("\n"):
        body_text = body_text[1:]
    elif body_text.startswith("\r\n"):
        body_text = body_text[2:]

    return front_matter, body_text
