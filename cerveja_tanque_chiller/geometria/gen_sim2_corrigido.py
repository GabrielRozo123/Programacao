"""
gen_sim2_corrigido.py — Sim 2 CORRIGIDA (recirculação) — cerveja / TAG 3.500 L

⚠️ CORREÇÃO após ler o DIAGRAMA DO CLIENTE (EGISA 055.2254, anotado à mão):
   A recirculação NÃO usa bocais laterais. O diagrama mostra:
     • SAÍDA  → pelo **DRENO CENTRAL DO CONE** (fundo, no ápice) → bomba (12 m³/h)
     • ENTRADA→ por **CIMA, na TAMPA**, fora do eixo (nozzle no topo, r ≈ 665 mm)

   O que estava ERRADO na versão anterior (cerveja_sim2_fluido.step):
     ✗ saída da recirc  : bocal LATERAL a z=100 mm    → correto: ápice do cone (centro, z=-268)
     ✗ entrada da recirc: bocal LATERAL a z=1430 mm   → correto: pelo TOPO, r≈665 mm

   O CHILLER está correto e não muda:
     • saída p/ chiller  : lateral a z=1350 mm  ("Saída para chiller — 1,35 m")
     • retorno do chiller: lateral a z=50 mm    ("Retorno para tanque")
     • (o bocal de 0,85 m aparece RISCADO no diagrama — não é usado)

Datum z=0 = início da parede cilíndrica (igual ao diagrama).
"""
import cadquery as cq
import numpy as np
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── Cotas do tanque (mm) — do diagrama EGISA ──────────────────────────────
R       = 1659.0/2     # raio (Ø1659) = 829,5
H_LIQ   = 1530.0       # nível de líquido (1,53 m) ✅ diagrama
H_CONE  = 268.0        # cone de fundo
R_APEX  = 40.0         # raio do ápice do cone (Ø80 = o dreno central)

# ── Bocais do CHILLER (inalterados, DN150 do STEP do cliente) ─────────────
DN_CH   = 150.0; R_CH = DN_CH/2
Z_SUC   = 1350.0       # saída p/ chiller   ✅ "1,35 m"
Z_RETC  =   50.0       # retorno do chiller ✅ "Retorno para tanque"
STUB    =  130.0

# ── RECIRCULAÇÃO (CORRIGIDA) ──────────────────────────────────────────────
DN_REC  =  65.0        # ⚠️ SUPOSTO — linha de 12 m³/h. Ver nota no final.
R_REC   = DN_REC/2
R_TOP   = 665.0        # raio onde o bocal do TOPO entra (medido no diagrama: r/R ≈ 0,80)
L_DRENO = 150.0        # stub do dreno abaixo do ápice
L_TOPO  = 120.0        # stub acima da superfície de líquido


def tank():
    cyl  = cq.Solid.makeCylinder(R, H_LIQ, cq.Vector(0,0,0), cq.Vector(0,0,1))
    cone = cq.Solid.makeCone(R_APEX, R, H_CONE, cq.Vector(0,0,-H_CONE), cq.Vector(0,0,1))
    return cyl.fuse(cone)

def stub_radial(z, az_deg, r_n):
    a = np.radians(az_deg); d = cq.Vector(np.cos(a), np.sin(a), 0.0)
    x0 = R - 120.0
    base = cq.Vector(x0*np.cos(a), x0*np.sin(a), z)
    return cq.Solid.makeCylinder(r_n, 120.0 + STUB, base, d)

def build():
    body = tank()
    # CHILLER (mesmo lado, az 0) — inalterado
    body = body.fuse(stub_radial(Z_SUC,  0, R_CH))   # saída p/ chiller
    body = body.fuse(stub_radial(Z_RETC, 0, R_CH))   # retorno do chiller
    # RECIRC — SAÍDA pelo DRENO CENTRAL (ápice do cone, para baixo)
    dreno = cq.Solid.makeCylinder(R_APEX, L_DRENO,
                cq.Vector(0,0,-H_CONE-L_DRENO), cq.Vector(0,0,1))
    body = body.fuse(dreno)
    # RECIRC — ENTRADA pelo TOPO (vertical, fora do eixo)
    topo = cq.Solid.makeCylinder(R_REC, L_TOPO + 60.0,
                cq.Vector(R_TOP, 0, H_LIQ - 60.0), cq.Vector(0,0,1))
    body = body.fuse(topo)
    return body.clean()

fl = build()
bb = fl.BoundingBox()
Q = 12.0/3600
print("="*70)
print(" SIM 2 CORRIGIDA — recirculação conforme o diagrama do cliente")
print("="*70)
print(f"  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m3 ({fl.Volume()/1e6:.0f} L)")
print(f"  bbox Z: [{bb.zmin:.0f}, {bb.zmax:.0f}] mm\n")
print("  BOCAIS:")
print(f"    CHILLER saída   : lateral z={Z_SUC:.0f} mm, az 0, DN{DN_CH:.0f}")
print(f"    CHILLER retorno : lateral z={Z_RETC:.0f} mm, az 0, DN{DN_CH:.0f}")
print(f"    RECIRC  SAÍDA   : DRENO CENTRAL no ápice, z={-H_CONE-L_DRENO:.0f} mm, Ø{2*R_APEX:.0f}")
print(f"    RECIRC  ENTRADA : TOPO vertical, r={R_TOP:.0f} mm, z={H_LIQ+L_TOPO:.0f} mm, DN{DN_REC:.0f}")
print(f"\n  velocidades a 12 m3/h:")
print(f"    no dreno (Ø{2*R_APEX:.0f}) : {Q/(np.pi*(R_APEX/1000)**2):.2f} m/s")
print(f"    no topo  (DN{DN_REC:.0f}) : {Q/(np.pi*(R_REC/1000)**2):.2f} m/s")
p = os.path.join(OUT, "cerveja_sim2_CORRIGIDO_fluido.step")
cq.exporters.export(fl, p)
print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)} bytes)")
