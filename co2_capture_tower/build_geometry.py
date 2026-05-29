# ================================================================
# Torre de Captura de CO2 — Coluna de Absorção Industrial
# Geometria CFD-friendly para STAR-CCM+ (Eulerian Multiphase)
#
# Processo: Absorção de CO2 com MEA 30% (monoetanolamina)
# Escala: unidade industrial pequena / piloto grande
#
# build123d v0.10.0
# CRÍTICO: M = 1000 → build123d usa mm internamente
#          Todos os valores em metros × 1000 = mm
#
# Zonas (de baixo para cima, eixo Z):
#   01_Sump_Inferior    → fluido  (gás entra, líquido sai)
#   02_Recheio_Inferior → poroso  (absorção principal)
#   03_Redistribuicao   → fluido  (redistribuidor de líquido)
#   04_Recheio_Superior → poroso  (acabamento / polishing)
#   05_Secao_Superior   → fluido  (gás sai, MEA entra)
#   06_Bocal_GasInlet   → nozzle horizontal (gás rico em CO2)
#   07_Bocal_GasOutlet  → nozzle horizontal (gás tratado)
#
# Boundaries nomeadas no STAR-CCM+:
#   Sump:     SumpBot_LiquidOutlet, SumpWall, SumpTop (interface)
#   Pack1:    Pack1_Wall, Pack1_Bot (interface), Pack1_Top (interface)
#   Redist:   Redist_Wall, Redist_Bot, Redist_Top
#   Pack2:    Pack2_Wall, Pack2_Bot, Pack2_Top
#   TopSec:   TopSec_Wall, TopSec_Bot, TopSec_GasOutlet_face
#   GasIn:    GasInlet (face externa do bocal)
#   GasOut:   GasOutlet (face externa do bocal)
#   LiqIn:    TopSec_LiquidInlet (face superior da seção topo)
# ================================================================

from build123d import *
import os

# ============================================================
# FATOR DE ESCALA — metros → milímetros
# ============================================================
M = 1000  # NUNCA remova este fator!

# ============================================================
# DIMENSÕES INDUSTRIAIS
# ============================================================
# Coluna principal
D_col  = 1.20 * M   # diâmetro interno da coluna  [mm] = 1.20 m
R_col  = D_col / 2  # raio = 600 mm

# Bocais laterais (gás)
D_noz_g = 0.25 * M  # diâmetro bocal de gás       [mm] = 0.25 m
R_noz_g = D_noz_g / 2
L_noz_g = 0.35 * M  # comprimento bocal gás       [mm] = 0.35 m

# Bocal axial superior (MEA lean entra pelo topo)
D_noz_l = 0.15 * M  # diâmetro bocal líquido      [mm] = 0.15 m
R_noz_l = D_noz_l / 2
L_noz_l = 0.30 * M  # comprimento bocal líquido   [mm] = 0.30 m

# ============================================================
# ALTURAS DAS ZONAS
# (simplificação CFD: sem internos complexos)
# ============================================================
h_sump   = 1.0 * M   # Sump inferior (fluido)      [mm] = 1.0 m
h_pack1  = 5.0 * M   # Recheio inferior (poroso)   [mm] = 5.0 m
h_redist = 0.5 * M   # Redistribuição (fluido)     [mm] = 0.5 m
h_pack2  = 3.5 * M   # Recheio superior (poroso)   [mm] = 3.5 m
h_top    = 1.0 * M   # Seção superior (fluido)     [mm] = 1.0 m

# ============================================================
# POSIÇÕES Z — origem no fundo da torre (z=0 = base do sump)
# ============================================================
z_sump_bot  = 0
z_pack1_bot = z_sump_bot  + h_sump    #  1000 mm =  1.0 m
z_redist_bot= z_pack1_bot + h_pack1   #  6000 mm =  6.0 m
z_pack2_bot = z_redist_bot + h_redist #  6500 mm =  6.5 m
z_top_bot   = z_pack2_bot + h_pack2   # 10000 mm = 10.0 m
z_total     = z_top_bot   + h_top     # 11000 mm = 11.0 m

# ============================================================
# OUTPUT
# ============================================================
out_dir = os.path.join(os.path.dirname(__file__), "step")
os.makedirs(out_dir, exist_ok=True)

print("=" * 60)
print("  Torre de Captura de CO2 — Geração de Geometria")
print("=" * 60)
print(f"  Diâmetro coluna : {D_col/M:.2f} m")
print(f"  Altura total    : {z_total/M:.2f} m")
print(f"  Zonas porosas   : Pack1={h_pack1/M:.1f}m + Pack2={h_pack2/M:.1f}m")
print("=" * 60)

# ============================================================
# FUNÇÃO AUXILIAR — cria e exporta cilindro simples
# ============================================================
def cilindro_zona(nome, z_centro, altura, raio):
    with BuildPart() as parte:
        with Locations((0, 0, z_centro)):
            Cylinder(radius=raio, height=altura)
    caminho = os.path.join(out_dir, nome + ".step")
    export_step(parte.part, caminho)
    z0 = z_centro - altura / 2
    z1 = z_centro + altura / 2
    print(f"  ✓ {nome}: Z={z0/M:.2f}–{z1/M:.2f} m | R={raio/M:.3f} m → {os.path.basename(caminho)}")
    return parte

# ============================================================
# 01 — SUMP INFERIOR (fluido)
#      Gás rico em CO2 entra pelo bocal lateral
#      Líquido rico (rich MEA) sai pela base
# ============================================================
cilindro_zona(
    "01_Sump_Inferior",
    z_centro = z_sump_bot + h_sump / 2,
    altura   = h_sump,
    raio     = R_col
)

# ============================================================
# 02 — RECHEIO INFERIOR — Lower Packing (poroso)
#      Zona principal de absorção de CO2
#      Packing: Raschig rings 50mm ou Mellapak 250Y
#      ε = 0.70 (recheio estruturado)
# ============================================================
cilindro_zona(
    "02_Recheio_Inferior",
    z_centro = z_pack1_bot + h_pack1 / 2,
    altura   = h_pack1,
    raio     = R_col
)

# ============================================================
# 03 — REDISTRIBUIÇÃO (fluido)
#      Redistribuidor de líquido entre os dois leitos
#      Simplificado como zona fluida sem internos
# ============================================================
cilindro_zona(
    "03_Redistribuicao",
    z_centro = z_redist_bot + h_redist / 2,
    altura   = h_redist,
    raio     = R_col
)

# ============================================================
# 04 — RECHEIO SUPERIOR — Upper Packing (poroso)
#      Zona de polishing (acabamento da absorção)
#      ε = 0.70
# ============================================================
cilindro_zona(
    "04_Recheio_Superior",
    z_centro = z_pack2_bot + h_pack2 / 2,
    altura   = h_pack2,
    raio     = R_col
)

# ============================================================
# 05 — SEÇÃO SUPERIOR / DEMISTER (fluido)
#      MEA lean entra pelo topo (LiquidInlet)
#      Gás tratado sai pelo bocal lateral (GasOutlet)
# ============================================================
cilindro_zona(
    "05_Secao_Superior",
    z_centro = z_top_bot + h_top / 2,
    altura   = h_top,
    raio     = R_col
)

# ============================================================
# 06 — BOCAL GÁS ENTRADA — GasInlet (horizontal, +X)
#      Posição: meio do Sump (Z = 500 mm = 0.5 m)
#      Direção: fluxo em -X (entra na coluna)
# ============================================================
z_gasin = z_sump_bot + h_sump / 2   # 500 mm
cx_gasin = R_col + L_noz_g / 2      # centro do bocal em X

with BuildPart() as bocal_gasin:
    with Locations((cx_gasin, 0, z_gasin)):
        Cylinder(radius=R_noz_g, height=L_noz_g,
                 rotation=(0, 90, 0))

caminho = os.path.join(out_dir, "06_Bocal_GasInlet.step")
export_step(bocal_gasin.part, caminho)
print(f"  ✓ 06_Bocal_GasInlet: Z={z_gasin/M:.2f} m | D={D_noz_g/M:.2f} m → {os.path.basename(caminho)}")

# ============================================================
# 07 — BOCAL GÁS SAÍDA — GasOutlet (horizontal, +X)
#      Posição: meio da Seção Superior (Z = 10500 mm = 10.5 m)
#      Direção: fluxo em +X (sai da coluna)
# ============================================================
z_gasout = z_top_bot + h_top / 2    # 10500 mm
cx_gasout = R_col + L_noz_g / 2

with BuildPart() as bocal_gasout:
    with Locations((cx_gasout, 0, z_gasout)):
        Cylinder(radius=R_noz_g, height=L_noz_g,
                 rotation=(0, 90, 0))

caminho = os.path.join(out_dir, "07_Bocal_GasOutlet.step")
export_step(bocal_gasout.part, caminho)
print(f"  ✓ 07_Bocal_GasOutlet: Z={z_gasout/M:.2f} m | D={D_noz_g/M:.2f} m → {os.path.basename(caminho)}")

# ============================================================
# RESUMO FINAL
# ============================================================
print()
print("=" * 60)
print("  RESUMO DA TORRE")
print("=" * 60)
print(f"  01_Sump_Inferior    : Z  0.00 – {h_sump/M:.2f} m  [FLUIDO]")
print(f"  02_Recheio_Inferior : Z  {h_sump/M:.2f} – {(h_sump+h_pack1)/M:.2f} m  [POROSO ε=0.70]")
print(f"  03_Redistribuicao   : Z  {(h_sump+h_pack1)/M:.2f} – {(h_sump+h_pack1+h_redist)/M:.2f} m  [FLUIDO]")
print(f"  04_Recheio_Superior : Z  {(h_sump+h_pack1+h_redist)/M:.2f} – {(h_sump+h_pack1+h_redist+h_pack2)/M:.2f} m  [POROSO ε=0.70]")
print(f"  05_Secao_Superior   : Z {(h_sump+h_pack1+h_redist+h_pack2)/M:.2f} – {z_total/M:.2f} m  [FLUIDO]")
print(f"  06_Bocal_GasInlet   : Z  {z_gasin/M:.2f} m (lateral, horizontal)")
print(f"  07_Bocal_GasOutlet  : Z {z_gasout/M:.2f} m (lateral, horizontal)")
print()
print("  Boundaries chave:")
print("    GasInlet   → face externa do 06_Bocal_GasInlet")
print("    GasOutlet  → face externa do 07_Bocal_GasOutlet")
print("    LiquidInlet→ face superior do 05_Secao_Superior")
print("    LiquidOut  → face inferior do 01_Sump_Inferior")
print()
print(f"  ✅ 7 STEP files gerados em ./step/")
print("=" * 60)
