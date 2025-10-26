from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.services.rules_dsl import RuleDSLParser


@dataclass(slots=True)
class RulePack:
    slug: str
    name: str
    description: str
    version: str | None
    yaml: str


_PACK_DEFINITIONS = [
    {
        "slug": "zfm_baseline",
        "name": "Pacote ZFM",
        "description": "Conjunto inicial de regras fiscais para operações com Zona Franca de Manaus.",
        "version": "2024.04",
        "file": Path(__file__).resolve().parent.parent / "rules" / "packs" / "zfm_baseline.yaml",
    }
]

_parser = RuleDSLParser()


def iter_rule_packs() -> Iterable[RulePack]:
    for definition in _PACK_DEFINITIONS:
        yaml_text = definition["file"].read_text(encoding="utf-8")
        # Valida o conteúdo, garantindo que o pacote siga o DSL
        _parser.parse(yaml_text)
        yield RulePack(
            slug=definition["slug"],
            name=definition["name"],
            description=definition["description"],
            version=definition.get("version"),
            yaml=yaml_text,
        )


def get_rule_pack(slug: str) -> RulePack:
    for pack in iter_rule_packs():
        if pack.slug == slug:
            return pack
    raise KeyError(f"Pacote de regras '{slug}' não encontrado")
