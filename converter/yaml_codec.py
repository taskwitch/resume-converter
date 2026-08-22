"""IR <-> YAML. The IR dict is directly yaml.dump-able; this is a thin wrapper."""

from __future__ import annotations

import yaml

from .ir import validate_ir


def ir_to_yaml(ir: dict) -> str:
    return yaml.dump(
        ir,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )


def yaml_to_ir(text: str) -> dict:
    ir = yaml.safe_load(text)
    validate_ir(ir)
    return ir
