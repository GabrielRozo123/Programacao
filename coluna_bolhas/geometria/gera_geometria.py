"""
gera_geometria.py
=================
Gera as geometrias da coluna de bolhas em STEP (AP214, unidades em mm),
com as faces nomeadas para virar as condições de contorno no STAR-CCM+.

  coluna_3D_D150_H1200.step       → caso principal 3D (transiente)
      eixo da coluna = +Z, fundo em z = 0
      faces: Aspersor (fundo), Topo, Parede

  coluna_2D_axi_R75_H1200.step    → versão rápida axissimétrica
      convenção do STAR-CCM+ p/ Axisymmetric: eixo de simetria = eixo X,
      raio = +Y; gravidade = [-9.81, 0] m/s² (igual ao tutorial Hibiki).
      Placa fina (espessura 10 mm em Z) p/ usar "Convert to 2D":
      faces: Aspersor (x=0), Topo (x=H), Parede (y=R), Eixo (y=0),
             Plano_2D (z=0, a face que vira o domínio 2D), Plano_tras (z=e)

Uso:
    pip install cadquery
    python gera_geometria.py --D 150 --H 1200
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cadquery as cq


def _nomeia(assy: cq.Assembly, corpo: cq.Workplane, nome_corpo: str, faces: dict):
    """Adiciona as faces nomeadas (seletor cadquery → nome) ao assembly."""
    for seletor, nome in faces.items():
        face = corpo.faces(seletor).val()
        assy.addSubshape(face, name=nome)
    return assy


def coluna_3d(D: float, H: float) -> cq.Assembly:
    corpo = cq.Workplane("XY").circle(D / 2).extrude(H)
    assy = cq.Assembly(name="Coluna_Bolhas_3D")
    assy.add(corpo, name="Coluna")
    return _nomeia(assy, corpo, "Coluna",
                   {"<Z": "Aspersor", ">Z": "Topo", "%CYLINDER": "Parede"})


def coluna_2d_axi(D: float, H: float, esp: float = 10.0) -> cq.Assembly:
    corpo = cq.Workplane("XY").rect(H, D / 2, centered=False).extrude(esp)
    assy = cq.Assembly(name="Coluna_Bolhas_2D_Axi")
    assy.add(corpo, name="Coluna")
    return _nomeia(assy, corpo, "Coluna",
                   {"<X": "Aspersor", ">X": "Topo", ">Y": "Parede", "<Y": "Eixo",
                    "<Z": "Plano_2D", ">Z": "Plano_tras"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--D", type=float, default=150.0, help="diâmetro [mm]")
    ap.add_argument("--H", type=float, default=1200.0, help="altura total [mm]")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent)
    a = ap.parse_args()

    f3d = a.out / f"coluna_3D_D{a.D:.0f}_H{a.H:.0f}.step"
    f2d = a.out / f"coluna_2D_axi_R{a.D/2:.0f}_H{a.H:.0f}.step"
    coluna_3d(a.D, a.H).export(str(f3d))
    coluna_2d_axi(a.D, a.H).export(str(f2d))
    print(f"gerado: {f3d}\ngerado: {f2d}")


if __name__ == "__main__":
    main()
