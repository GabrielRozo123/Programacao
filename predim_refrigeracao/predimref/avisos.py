"""Registro de avisos de projeto (premissas fora de faixa, riscos, inconsistências)."""
from __future__ import annotations

from dataclasses import dataclass, field


class ErroProjeto(ValueError):
    """Entrada fisicamente impossível ou incoerente (p. ex. COP acima do de Carnot)."""


@dataclass
class Aviso:
    nivel: str      # "INFO", "ATENCAO" ou "CRITICO"
    origem: str
    mensagem: str

    def __str__(self) -> str:
        return f"[{self.nivel}] {self.origem}: {self.mensagem}"


@dataclass
class Avisos:
    itens: list[Aviso] = field(default_factory=list)

    def info(self, origem: str, msg: str) -> None:
        self.itens.append(Aviso("INFO", origem, msg))

    def atencao(self, origem: str, msg: str) -> None:
        self.itens.append(Aviso("ATENCAO", origem, msg))

    def critico(self, origem: str, msg: str) -> None:
        self.itens.append(Aviso("CRITICO", origem, msg))

    def extend(self, origem: str, msgs: list[str], nivel: str = "ATENCAO") -> None:
        for m in msgs:
            self.itens.append(Aviso(nivel, origem, m))

    def __iter__(self):
        return iter(self.itens)

    def __len__(self) -> int:
        return len(self.itens)

    def texto(self) -> str:
        ordem = {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}
        return "\n".join(str(a) for a in sorted(self.itens, key=lambda a: ordem[a.nivel]))
