"""
Domínio FLUIDO do ejetor (eductor) — v2 REVISADO, paramétrico e validado.
Topologia: 7 bicos Ø9 (hex) confirmada pelas medidas ASME do CAD (7 faces cilíndricas idênticas).
Escala: já em mm REAIS (modelo Star ÷25,4 aplicado). Datum z=0 = boca da lança (saída p/ tanque).
Fluxo: entra Ø52 (topo) → 7 bicos Ø9 → câmara Ø60 → lança ID62,7 → sai (fundo).
Saída: eductor_dominio_fluido_v2.step  (+ preview)
[SUPOSTO] = confirmar com Marcus/Ito/GA (marcado abaixo).
"""
import cadquery as cq
import numpy as np

# ── Cotas reais (mm) — confirmadas por rótulos ASME salvo [SUPOSTO] ──────────────
D_IN    = 52.0     # entrada motriz (2" ID, pós redutor 4→2)     ✓ ASME
L_IN    = 25.0     # câmara de entrada (montante da placa)        [SUPOSTO ~1"]
D_NOZ   = 9.0      # cada bico                                    ✓ ASME (7× Ø9)
N_NOZ   = 7        # 1 central + 6 em hexágono                    ✓ (7 faces)
R_PITCH = 14.0     # raio do círculo dos 6 externos               [SUPOSTO — falta pitch do GA]
L_NOZ   = 50.0     # comprimento do bico (corpo ~50 mm)           ✓ (BICO corpo)
D_CH    = 60.0     # câmara de mistura                            [SUPOSTO ~60 — refinar]
L_CH    = 56.0     # comprimento da câmara                        ✓ (~56, z −19,57→−21,00)
D_LANCA = 62.7     # lança 2½" Sch40 ID                           ✓ ASME
L_LANCA = 500.0    # stub da lança (real 3,0 m — subdomínio CFD)  ✓ (subdomínio)
D_AIR   = 1.0      # furos de ar                                  ✓ (Marcus Ito)
N_AIR   = 6        # nº de furos de ar (anel na câmara)           [SUPOSTO — confirmar nº/posição]
Z_AIRoff= 8.0      # furos a 8 mm abaixo do topo da câmara        [SUPOSTO — junto aos jatos]
OVL     = 0.8      # overlap p/ boolean robusto (evita face coincidente)

# ── Empilhamento por z (0 = boca da lança) ──────────────────────────────────────
z_lanca0 = 0.0
z_ch0    = L_LANCA                    # topo da lança / base da câmara
z_ch1    = z_ch0 + L_CH               # topo da câmara / base dos bicos
z_noz1   = z_ch1 + L_NOZ              # topo dos bicos / base da entrada
z_in1    = z_noz1 + L_IN             # topo da entrada

def cyl(d, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(d/2, z1-z0, cq.Vector(x, y, z0), cq.Vector(0,0,1))

def air_stub(az_deg, z):
    a = np.radians(az_deg); d = cq.Vector(np.cos(a), np.sin(a), 0.0)
    x0 = D_CH/2 - OVL                    # começa dentro da parede da câmara
    base = cq.Vector(x0*np.cos(a), x0*np.sin(a), z)
    return cq.Solid.makeCylinder(D_AIR/2, OVL + 6.0, base, d)   # até 6 mm p/ fora (face externa = BC ar)

# ── Sólidos do domínio fluido ───────────────────────────────────────────────────
body = cyl(D_LANCA, z_lanca0, z_ch0 + OVL)                       # lança (entra na câmara p/ fundir)
body = body.fuse(cyl(D_CH, z_ch0, z_ch1 + OVL))                  # câmara de mistura
# 7 bicos (central + 6 hex), com overlap nas duas pontas
noz_pos = [(0.0,0.0)] + [(R_PITCH*np.cos(np.radians(60*k)), R_PITCH*np.sin(np.radians(60*k))) for k in range(6)]
for (x,y) in noz_pos:
    body = body.fuse(cyl(D_NOZ, z_ch1 - OVL, z_noz1 + OVL, x, y))
body = body.fuse(cyl(D_IN, z_noz1, z_in1))                       # câmara de entrada Ø52
# furos de ar (anel de N_AIR na câmara)
for k in range(N_AIR):
    body = body.fuse(air_stub(360.0*k/N_AIR, z_ch1 - Z_AIRoff))

def render(solid, path):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    v,t = solid.tessellate(0.6)
    P = np.array([[p.x,p.y,p.z] for p in v])
    fig = plt.figure(figsize=(4,9),dpi=100); ax = fig.add_subplot(111,projection="3d")
    ax.add_collection3d(Poly3DCollection([[P[a],P[b],P[c]] for a,b,c in t],
                        facecolor="#7FB3D5",edgecolor=(0,0,0,0.12),lw=0.1))
    c=P.mean(0); r=(P.max(0)-P.min(0)).max()/2
    ax.set_xlim(c[0]-r,c[0]+r); ax.set_ylim(c[1]-r,c[1]+r); ax.set_zlim(c[2]-r,c[2]+r)
    ax.view_init(elev=8,azim=35); ax.set_axis_off(); ax.set_box_aspect((1,1,3))
    ax.set_title("Eductor v2 — 7 bicos Ø9\n(entrada Ø52 · câmara Ø60 · lança Ø62,7)",fontsize=9,fontweight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=100); plt.close(fig)

if __name__ == "__main__":
    print("valido =", body.isValid())
    print(f"volume = {body.Volume()/1000:.1f} cm3")
    cq.exporters.export(cq.Workplane(obj=body), "eductor_dominio_fluido_v2.step")
    render(body, "eductor_v2_preview.png")
    print("z: lanca[0,%.0f] camara[%.0f,%.0f] bicos[%.0f,%.0f] entrada[%.0f,%.0f]" % (
        z_ch0, z_ch0, z_ch1, z_ch1, z_noz1, z_noz1, z_in1))
    print("STEP: eductor_dominio_fluido_v2.step")
