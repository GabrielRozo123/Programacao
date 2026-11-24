"""
gera_geometria_darmana.py
=========================
Coluna pseudo-2D de Darmana et al. (2007) para o STAR-CCM+ (STEP AP214, mm).

Domínio = região de líquido (H = 1000 mm). O topo é a superfície de *degassing*
(Phase Permeable), como em Krauß & Rzehak (2018); a coluna real tem 1500 mm, mas
a elevação do nível com α_G ≈ 1–2 % é desprezível.

Sistema de coordenadas (o mesmo dos artigos): origem no centro do fundo,
  x = largura (−100 … +100 mm), y = vertical (0 … 1000 mm), z = profundidade (−15 … +15 mm)
  ⇒ no STAR: gravidade = [0, −9,81, 0] m/s²
  Sensor de pH: (0, 980, 0) mm   |   PIV: (−50, 500, 0) mm   |   perfis laterais: y = 750 mm

Faces nomeadas:
  Aspersor        retângulo 30 × 10 mm no centro do fundo (21 agulhas, 7 × 3, passo de 5 mm)
  Fundo           restante do fundo
  Topo            y = 1000 mm (degassing)
  Parede_Frente / Parede_Tras   (z = ±15 mm)
  Parede_Esq / Parede_Dir       (x = ∓100 mm)

Uso:  pip install cadquery ; python gera_geometria_darmana.py
"""
from pathlib import Path

import cadquery as cq

W, H, P = 200.0, 1000.0, 30.0          # largura, altura do líquido, profundidade (mm)
WA, PA = 30.0, 10.0                     # aspersor (x × z)


def main():
    caixa = cq.Solid.makeBox(W, H, P, pnt=cq.Vector(-W / 2, 0, -P / 2))
    # face do aspersor no plano y = 0, usada para dividir o fundo
    ret = cq.Wire.makePolygon([cq.Vector(-WA / 2, 0, -PA / 2), cq.Vector(WA / 2, 0, -PA / 2),
                               cq.Vector(WA / 2, 0, PA / 2), cq.Vector(-WA / 2, 0, PA / 2)], close=True)
    face_asp = cq.Face.makeFromWires(ret)
    corpo = caixa.split(face_asp)                    # imprime o retângulo no fundo
    corpo = corpo.Solids()[0] if hasattr(corpo, "Solids") and corpo.Solids() else corpo

    def faces_onde(cond):
        return [f for f in corpo.Faces() if cond(f.Center(), f.Area())]

    nomes = {
        "Aspersor": faces_onde(lambda c, a: abs(c.y) < 1e-6 and abs(a - WA * PA) < 1e-3),
        "Fundo": faces_onde(lambda c, a: abs(c.y) < 1e-6 and abs(a - WA * PA) > 1e-3),
        "Topo": faces_onde(lambda c, a: abs(c.y - H) < 1e-6),
        "Parede_Frente": faces_onde(lambda c, a: abs(c.z - P / 2) < 1e-6),
        "Parede_Tras": faces_onde(lambda c, a: abs(c.z + P / 2) < 1e-6),
        "Parede_Esq": faces_onde(lambda c, a: abs(c.x + W / 2) < 1e-6),
        "Parede_Dir": faces_onde(lambda c, a: abs(c.x - W / 2) < 1e-6),
    }
    for k, v in nomes.items():
        assert len(v) == 1, (k, len(v))
        print(f"{k:14s} área = {v[0].Area():9.1f} mm²")
    assy = cq.Assembly(name="Coluna_Darmana")
    assy.add(cq.Workplane().add(corpo), name="Liquido")
    for k, v in nomes.items():
        assy.addSubshape(v[0], name=k)
    out = Path(__file__).parent / "coluna_darmana_200x1000x30.step"
    assy.save(str(out), exportType="STEP")
    print("salvo:", out, "| faces:", len(corpo.Faces()), "| volume =", round(corpo.Volume() / 1e6, 3), "L")


if __name__ == "__main__":
    main()
