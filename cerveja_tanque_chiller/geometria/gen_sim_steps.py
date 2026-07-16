"""
Gera os domínios fluidos das DUAS simulações (cerveja / TAG 3.500 L):
  - Sim 1: sucção do chiller a 1,35 m + retorno do chiller no fundo.
  - Sim 2: + recirculação (captação no fundo, retorno no topo).
Bocais DN 150 mm (extraído do STEP do cliente v3_1). Datum z=0 = início da parede cilíndrica.
Saídas: cerveja_sim1_fluido.step, cerveja_sim2_fluido.step (+ preview).
"""
import cadquery as cq
import numpy as np

# ── Cotas (mm) ────────────────────────────────────────────────────────────────
R      = 1659.0/2      # raio do cilindro (Ø1659)
H_LIQ  = 1530.0        # nível de líquido (1,53 m)
H_CONE = 268.0         # cone de fundo (fecha ~3510 L)
R_APEX = 40.0          # apice do cone
DN     = 150.0         # DN dos bocais (do STEP do cliente)
R_N    = DN/2          # 75
STUB   = 130.0         # comprimento do stub p/ fora da parede (face externa = BC)

Z_SUC   = 1350.0       # sucção chiller (NOVO)
Z_RETC  = 50.0         # retorno chiller (fundo)
Z_RCAP  = 100.0        # recirc captação (fundo)
Z_RRET  = 1500.0       # recirc retorno (topo)


def tank():
    """Domínio de líquido: cone + cilindro até o nível."""
    cyl  = cq.Solid.makeCylinder(R, H_LIQ, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    cone = cq.Solid.makeCone(R_APEX, R, H_CONE, cq.Vector(0, 0, -H_CONE), cq.Vector(0, 0, 1))
    return cyl.fuse(cone)


def stub(z, az_deg):
    """Stub radial DN150 na parede, no azimute az (graus), altura z.
    Vai de dentro da parede (R-120) até fora (R+STUB) → união limpa + face externa p/ BC."""
    a = np.radians(az_deg)
    d = cq.Vector(np.cos(a), np.sin(a), 0.0)              # direção radial
    x0 = (R - 120.0)                                       # começa dentro do tanque
    base = cq.Vector(x0*np.cos(a), x0*np.sin(a), z)
    return cq.Solid.makeCylinder(R_N, 120.0 + STUB, base, d)


def build(nozzles):
    """nozzles = lista de (z, azimute). Une o tanque com os stubs."""
    body = tank()
    for z, az in nozzles:
        body = body.fuse(stub(z, az))
    return body


def render(solid, path, title):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    v, t = solid.tessellate(3.0)
    P = np.array([[p.x, p.y, p.z] for p in v])
    fig = plt.figure(figsize=(6, 8), dpi=100); ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection([[P[a], P[b], P[c]] for a, b, c in t],
                        facecolor="#5BC8AC", edgecolor=(0, 0, 0, 0.10), lw=0.15))
    c = P.mean(0); r = (P.max(0)-P.min(0)).max()/2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.view_init(elev=12, azim=35); ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
    fig.tight_layout(); fig.savefig(path, dpi=100); plt.close(fig)


if __name__ == "__main__":
    # Sim 1: sucção chiller (1,35m, az 0) + retorno chiller (fundo, az 180)
    sim1 = build([(Z_SUC, 0), (Z_RETC, 180)])
    cq.exporters.export(cq.Workplane(obj=sim1), "cerveja_sim1_fluido.step")
    render(sim1, "preview_sim1.png", "Sim 1 — sucção 1,35m + retorno fundo")

    # Sim 2: + recirc captação (fundo, az 90) + recirc retorno (topo, az 270)
    sim2 = build([(Z_SUC, 0), (Z_RETC, 180), (Z_RCAP, 90), (Z_RRET, 270)])
    cq.exporters.export(cq.Workplane(obj=sim2), "cerveja_sim2_fluido.step")
    render(sim2, "preview_sim2.png", "Sim 2 — + recirc (fundo→topo)")

    for nm, s in [("Sim1", sim1), ("Sim2", sim2)]:
        print(f"{nm}: valido={s.isValid()}  vol={s.Volume()/1e6:.0f} L  bocais DN{int(DN)}")
    print("STEPs: cerveja_sim1_fluido.step, cerveja_sim2_fluido.step")
