"""Leitura de gravações do sistema Pulse VA (XML) e dos valores de referência.

Formato do XML (Pulse DAQ 3.x)::

    <DataFile SampleRate="800" RevolutionsPerMinute="728" Inclination="18.0" ...>
        <DataList Source="R1" Orientation="Side">
            <DataPoint X="0.63" Y="0.15" Z="0.35"/>   # aceleração em g
            ...
        </DataList>
        ...
    </DataFile>

Cada ``DataList`` corresponde a um acelerômetro triaxial sem fio (L1..L4 no
lado esquerdo, R1..R4 no lado direito). Os dados estão em g e incluem a
componente DC (gravidade), pois os sensores MEMS são acoplados em DC.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

#: Ordem de apresentação usada nos relatórios do Pulse (de cima para baixo).
SENSOR_ORDER = ("L4", "L3", "L2", "L1", "R4", "R3", "R2", "R1")


def _local(tag: str) -> str:
    """Remove o namespace de uma tag XML ('{ns}DataList' -> 'DataList')."""
    return tag.rsplit("}", 1)[-1]


@dataclass
class Record:
    """Uma gravação do Pulse: 8 sensores x 3 eixos, em g."""

    path: Path
    meta: dict
    fs: float
    sensors: dict[str, np.ndarray] = field(repr=False)  # nome -> array (N, 3)

    @property
    def names(self) -> list[str]:
        known = [s for s in SENSOR_ORDER if s in self.sensors]
        return known + [s for s in self.sensors if s not in known]

    @property
    def n_samples(self) -> int:
        return min(len(a) for a in self.sensors.values())

    @property
    def duration(self) -> float:
        return self.n_samples / self.fs

    @property
    def rpm_header(self) -> float | None:
        v = self.meta.get("RevolutionsPerMinute")
        return float(v) if v not in (None, "") else None

    @property
    def inclination_deg(self) -> float | None:
        v = self.meta.get("Inclination")
        return float(v) if v not in (None, "") else None

    def time(self) -> np.ndarray:
        return np.arange(self.n_samples) / self.fs

    def summary(self) -> str:
        m = self.meta
        return (
            f"Arquivo       : {self.path.name}\n"
            f"Identificação : {m.get('Serial', '-')}\n"
            f"Início / fim  : {m.get('StartDateTime', '-')} / {m.get('EndDateTime', '-')}\n"
            f"Alimentação   : {'com carga' if m.get('MaterialFeed') == 'true' else 'sem carga'}\n"
            f"Taxa amostral : {self.fs:.0f} Hz  |  amostras/canal: {self.n_samples}"
            f"  |  duração: {self.duration:.2f} s\n"
            f"Sensores      : {', '.join(self.names)} (3 eixos cada = {3 * len(self.names)} canais)\n"
            f"RPM (cabeçalho): {self.rpm_header}  |  Inclinação: {self.inclination_deg}°"
        )


def load_pulse_xml(path: str | Path) -> Record:
    """Lê um arquivo XML exportado pelo Pulse DAQ e devolve um :class:`Record`."""
    path = Path(path)
    root = ET.parse(path).getroot()
    meta = dict(root.attrib)
    fs = float(meta.get("SampleRate", "nan"))
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("SampleRate ausente ou inválido no XML")

    sensors: dict[str, np.ndarray] = {}
    for dl in root:
        if _local(dl.tag) != "DataList":
            continue
        name = dl.attrib.get("Source", f"S{len(sensors) + 1}")
        pts = [
            (float(p.attrib["X"]), float(p.attrib["Y"]), float(p.attrib["Z"]))
            for p in dl
            if _local(p.tag) == "DataPoint"
        ]
        sensors[name] = np.asarray(pts, dtype=float)
    if not sensors:
        raise ValueError("Nenhum <DataList> encontrado no XML")
    n = min(len(a) for a in sensors.values())
    sensors = {k: v[:n] for k, v in sensors.items()}
    return Record(path=path, meta=meta, fs=fs, sensors=sensors)


def load_reference(path: str | Path) -> dict:
    """Carrega os valores de um relatório Pulse transcritos para JSON."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
