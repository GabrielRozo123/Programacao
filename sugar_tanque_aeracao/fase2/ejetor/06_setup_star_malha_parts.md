# 06 — Setup no STAR: malha, derived parts e sondas (nó de aeração, do STEP nativo)

> Domínio: `dominio_fluido_no_NATIVO_7furos.step` (nó de aeração, 7×Ø9). Region `Ejetor_DF`,
> boundaries `Xarope_in` / `Ar_in` / `Outlet` / `Walls`. Marcos (mm, eixo Z = escoamento):
> `Xarope_in z=0` · ar em `z=40` · redução `z=280–330` · **bico 7×Ø9 z=335–380** · descarga `z=380–500`.
> Furos em PCD Ø27 (r13,5) + 1 central. Jato nos furos ~**20 m/s, Re≈37 (laminar)**.

## 1. Malha

**Meshers:** Surface Remesher + **Polyhedral** + **Prism Layer**.
- (Poliédrico é robusto p/ a inicialização e o jato primário. Para o VOF depois, avaliar **Trimmer**
  (hexas) — interface mais nítida — ou **AMR** na iso de fração volumétrica.)

**Sizes (chave: resolver o Ø9):**
| Parâmetro | Valor | Porquê |
|---|---|---|
| Base size | **5 mm** | referência global |
| Surface target / min | 100% / **8%** (0,4 mm) | deixa o remesher afinar nos furos |
| **Volumetric Control** (cilindro em torno do bico+jato) | z=**270→470**, raio **65 mm** → **0,8 mm** isotrópico | ~**11 células** no Ø9; resolve redução, furos e jato |
| (opcional, furos) | z=330→390, r=30 → **0,4 mm** | se quiser cravar o perfil no furo |
| Prism Layers (Walls) | **4 camadas**, stretch 1,3, total **0,8 mm** | gradiente de parede (cisalhamento laminar) |

**Estimativa:** ~1–2 M células. **Checar:** ≥10 células no Ø9; qualidade de célula (skewness/validade);
prism sem colapsar dentro dos furos (se colapsar, reduzir nº de camadas nos furos via surface control).

> ⚠️ **Resolução × física da bolha:** microbolha <300 µm **não** é resolvida por VOF nesta malha (célula
> 0,8 mm). O VOF aqui captura **jato + quebra primária** (ligamentos ~mm); o tamanho fino sai da **âncora
> VOF+AMR** (refinar só a interface) e do preditor analítico. Não tente resolver 300 µm com malha global.

## 2. Derived Parts (planos)

| Nome | Tipo | Origem / Normal | O que mostra |
|---|---|---|---|
| **plano_axial** | Plane Section | origem (0,0,0), **normal (0,1,0)** | corta o eixo + a **porta de ar** + os furos → o filme principal |
| **plano_furos** | Plane Section | origem (0,0,**357**), **normal (0,0,1)** | corte transversal nos 7 furos (padrão hex) |
| (VOF) **iso_ar** | Isosurface | `Volume Fraction of Ar = 0,5` | interface/bolhas quando ligar o multifásico |

Cenas: pressão e velocidade no `plano_axial` (ver a depressão da garganta e a aceleração no furo);
vetores no `plano_furos`.

## 3. Sondas (sondas) — ❗lição da cerveja: NUNCA Max/Min report p/ ponto

| Sonda | Tipo | Local | Reporta |
|---|---|---|---|
| **linha_eixo** | Line Probe | (0,0,0)→(0,0,500) | p(z) e |U|(z) — depressão da garganta, aceleração no furo |
| **p_garganta** | Point Probe | (0,0,**333**) | pressão logo antes do bico → **cai abaixo do suprimento de ar?** |
| **p_saida_furo** | Point Probe | (0,0,**380**) | velocidade/pressão na saída do furo central |
| **linha_no_furo** | Line Probe | (13,5,0,335)→(13,5,0,380) | perfil dentro de um furo externo (checar laminar resolvido) |
| **VF_descarga** | Volume Average | região z>380 | **holdup** de ar (fração volumétrica média) |

**Reports/monitors (convergência + balanço):**
- **Mass Flow** em `Xarope_in`, `Ar_in`, `Outlet` → balanço de massa fecha? (critério de parada real)
- **ΔP** `Xarope_in`→`Outlet`.
- **Pressão estática** em `p_garganta` (viabilidade do arraste).
- **Máx. velocidade** nos furos (Volume, via `p_saida_furo`/linha, não Max report de ponto).

## 4. Condições de contorno (referência)
- **Xarope_in:** Velocity/Mass-Flow — **32,5 m³/h/lança** (130÷4) → **1,10 m/s** no 4" (ou 11,7 kg/s). μ=6,5 Pa·s, ρ≈1300.
- **Ar_in:** **Stagnation Inlet**, pressão total **98 / 196 / 294 kPa** (1/2/3 kgf/cm²), VF_ar=1, **gás ideal/compressível**.
- **Outlet:** Pressure Outlet (pressão de jusante/submersão).
- **Walls:** no-slip.

## 5. Ordem de execução (robustez)
1. **Init monofásico** (steady, laminar, só xarope) — poucos passos → campo de pressão/deformação + seed.
2. **Liga o multifásico** a partir do campo inicializado (transiente).
3. Bolha fina: **VOF + AMR** na interface (âncora de nascimento) — não kernel turbulento (Re~37 é laminar).
