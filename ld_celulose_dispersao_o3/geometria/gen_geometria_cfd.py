"""
gen_geometria_cfd.py — gera a geometria LIMPA do modelo CFD a partir de uma tabela de objetos.

Ideia: em vez de limpar dezenas de milhares de peças do CAD da planta, usar o CAD só como
referência de medidas (Solid Edge > Inspect > medir) e REMODELAR cada obstáculo relevante como
primitiva (caixa, cilindro, silo com cone, duto de descarga) — critérios em ../05_limpeza_CAD_criterios.md.

Uso:
    python3 gen_geometria_cfd.py objetos_exemplo.csv --out geometria_cfd.step
    python3 gen_geometria_cfd.py ../_privado/objetos_real.csv --out ../_privado/geometria_cfd.step

Saída: STEP com um sólido por objeto, nomeado (o nome vira part/boundary no STAR), e um resumo
com contagem por zona e área frontal projetada em 8 direções de vento (verificação da §6 do 05).
Requer: pip install cadquery
"""
import argparse, csv, math
import cadquery as cq


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        linhas = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    return list(csv.DictReader(linhas))


def solido(o):
    t = o["tipo"].strip()
    x0, y0, z0 = (float(o[k]) for k in ("x0", "y0", "z0"))
    a, b, h, rot = (float(o[k] or 0) for k in ("a", "b", "h", "rot"))
    if t == "caixa":
        s = cq.Workplane("XY").box(a, b, h, centered=False)
        s = s.rotate((0, 0, 0), (0, 0, 1), rot).translate((x0, y0, z0))
    elif t in ("cilindro", "duto"):
        s = cq.Workplane("XY").circle(a / 2).extrude(h).translate((x0, y0, z0))
    elif t == "silo":  # cone de fundo de altura b (ponta com 20 % do diâmetro) + corpo cilíndrico
        cone = cq.Solid.makeCone(0.1 * a, a / 2, b)
        corpo = cq.Workplane("XY").workplane(offset=b).circle(a / 2).extrude(h - b)
        s = corpo.union(cq.Workplane("XY").add(cone)).translate((x0, y0, z0))
    else:
        raise ValueError(f"tipo desconhecido: {t} ({o['nome']})")
    return s.val()


def area_frontal(solidos, direcao_graus):
    """Área projetada num plano normal à direção do vento (aprox. pela caixa envolvente girada)."""
    th = math.radians(direcao_graus)
    total = 0.0
    for s in solidos:
        bb = s.BoundingBox()
        dx, dy, dz = bb.xlen, bb.ylen, bb.zlen
        largura = abs(dx * math.sin(th)) + abs(dy * math.cos(th))
        total += largura * dz
    return total


ap = argparse.ArgumentParser()
ap.add_argument("tabela")
ap.add_argument("--out", default="geometria_cfd.step")
a = ap.parse_args()

objs = ler(a.tabela)
montagem = cq.Assembly()
por_zona = {}
solidos = []
for o in objs:
    s = solido(o)
    solidos.append(s)
    montagem.add(s, name=o["nome"].strip())
    por_zona.setdefault(o["zona"].strip(), []).append(o["nome"].strip())
montagem.export(a.out)

print(f"{len(objs)} objetos -> {a.out}")
for z, n in sorted(por_zona.items()):
    print(f"  {z}: {len(n)}  ({', '.join(n)})")
print("Área frontal (aprox., caixa envolvente) por direção de onde vem o vento:")
for d in range(0, 360, 45):
    print(f"  {d:3d}°: {area_frontal(solidos, d):8.0f} m²")
