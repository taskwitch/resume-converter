"""IR <-> JSON. The IR dict is directly json.dumps-able; this is a thin wrapper."""

from __future__ import annotations

import json

from .ir import validate_ir


def ir_to_json(ir: dict, *, indent: int = 2) -> str:
    return json.dumps(ir, indent=indent, ensure_ascii=False) + "\n"


def json_to_ir(text: str) -> dict:
    ir = json.loads(text)
    validate_ir(ir)
    return ir
