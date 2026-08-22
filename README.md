# Résumé Converter

Converts a Hugo résumé Markdown file (`content/resume/*.md`, using the
`layout: resume` front matter and the `resume/entry` shortcode — see
`docs/resume-page.md` at the repo root) to **LaTeX** (visually matching the
live page's style), **YAML**, or **JSON**. YAML/JSON can also be converted
back to Markdown. Everything pivots through a shared intermediate
representation (IR), which is also directly what the YAML/JSON output *is*
— see "Intermediate Representation" below.

The Hugo shortcode syntax is parsed by a small hand-written scanner in this
tool (`converter/shortcode_parser.py`) — Hugo itself is never
invoked.

## Requirements

Confirmed working with:
- Python 3.12 (no venv required — see below)
- [`pandoc`](https://pandoc.org/) on `PATH` (used to convert genuine
  Markdown fragments — bullet lists, links, inline math — to LaTeX)
- `pdflatex` on `PATH`, to compile the generated `.tex` file yourself

```sh
pip install -r requirements.txt   # PyYAML, Jinja2 — likely already installed globally
```

This is a small, personal utility with two lightweight dependencies, not
part of the Hugo build pipeline, so no virtualenv is set up by default. If
your global environment ever conflicts: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

## Usage

Run from inside this directory (or `pip install -e .` for a
`resume-converter` console script):

```sh
python3 -m converter ../../content/resume/work-study.md --to latex
python3 -m converter ../../content/resume/work-study.md --to yaml
python3 -m converter ../../content/resume/work-study.md --to json
python3 -m converter work-study.yaml --to md
```

- `--from {md,yaml,json}` — input format; auto-detected from the input
  file's extension if omitted.
- `-o OUTPUT` — output file, or a directory to place the default-named
  output file into. Defaults to the input's directory, with its extension
  swapped for the target format's.
- `--paper {letter,a4}` — overrides `resume.print.paper` for `--to latex`
  output only; doesn't touch the source file.

### Compiling the LaTeX output

`--to latex` copies `resume.sty` alongside the generated `.tex` file, so
the output directory is self-contained:

```sh
python3 -m converter ../../content/resume/work-study.md --to latex -o build/work-study/
cd build/work-study
pdflatex -interaction=nonstopmode work-study.tex
```

## Intermediate Representation

The IR is a plain nested dict/list of strings, booleans, and `None` — it is
exactly what gets serialized as YAML/JSON, not an internal-only shape:

```yaml
title: "Résumé for Software Engineering Internship"
draft: false
resume:
  name: "Jordan Rivera"
  tagline: ["...", "..."]
  contact:
    - {label: "Phone", value: "+1...", href: "tel:+1..."}
  print:
    paper: letter        # letter | a4
    qrtarget: false       # false | "permalink" | a custom URL string
body:
  - {type: heading, level: 2, text: "Education"}
  - type: entry
    title: "Example University"
    title_link: null      # or a URL
    subtitle: "B.Sc. Computer Science (In-Progress)"
    date: "2026 – Present"
    aside: null            # markdown, or null
    body: "- bullet one\n- bullet two"   # markdown, or null
  - {type: markdown_block, markdown: "- a plain bullet list, or prose"}
```

**Field-type note, important if hand-editing YAML/JSON**: `title`,
`subtitle`, `date`, `tagline[]`, and `contact[].value` are **plain text**
(Hugo's `resume/entry` shortcode never runs these through its Markdown
renderer — that mirrors `title="**Bold**"` rendering as literal asterisks
on the live site). `aside` and an entry's `body` are **raw Markdown** (Hugo
does render these), so `aside: "[GitHub](https://...)"` is valid and
becomes a real link.

`contact[].label` has no effect on the rendered page (the Hugo template
never reads it) but is preserved here since real content includes it.

## Known Limitations

- **LaTeX → Markdown is not implemented.** The IR/renderer architecture is
  designed so this could be added later as a dedicated parser for this
  tool's own generated LaTeX output — arbitrary/hand-written LaTeX is not a
  goal.
- **HTML comments are dropped**, not round-tripped. They render as nothing
  on the live site, so this can't change what a Markdown → IR → Markdown
  round trip *renders* as, but it does mean the output isn't a byte-diff of
  hand-authored comments.
- **No self-closing shortcode variant** (`{{< resume/entry ... />}}`) is
  supported — it isn't used anywhere in `content/resume/`.
- **Malformed shortcode usage is replicated, not corrected.** If a
  `resume/entry` block is closed immediately and followed by an
  un-indented list with no blank line (as happens once in
  `work-study.md`), that list is parsed as a separate, sibling
  `markdown_block` — exactly matching what actually renders on the live
  Hugo site, not what was probably intended.
- Reconstructed Markdown (`--to md`) doesn't escape a literal `"` inside a
  plain-text shortcode attribute value. No current fixture hits this.
- The LaTeX font is Bitstream Charter (`charter.sty`, already bundled with
  most TeX distributions), used as a faithful stand-in for the site's
  XCharter webfont — it's literally the second entry in the site's own CSS
  font-stack fallback.
