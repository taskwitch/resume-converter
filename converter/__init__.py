"""Convert Hugo résumé Markdown (content/resume/*.md) to/from LaTeX, YAML, and JSON."""

from .ir import validate_ir
from .json_codec import ir_to_json, json_to_ir
from .latex_renderer import ir_to_latex
from .md_reader import md_to_ir
from .md_writer import ir_to_md
from .yaml_codec import ir_to_yaml, yaml_to_ir

__version__ = "0.1.0"

__all__ = [
    "md_to_ir",
    "ir_to_md",
    "ir_to_json",
    "json_to_ir",
    "ir_to_yaml",
    "yaml_to_ir",
    "ir_to_latex",
    "validate_ir",
]
