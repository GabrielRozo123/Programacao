# Biblioteca de tutoriais do STAR-CCM+

Notas de estudo dos tutoriais oficiais do **Simcenter STAR-CCM+ 2602**, com comentários de engenharia
sobre **como transpor cada técnica para casos reais**. Genérico e reutilizável entre projetos — sem
dados de cliente.

> As notas são resumos e comentários nossos, não cópia da documentação Siemens.

## Índice

| # | tutorial | categoria | tema | status |
|---|---|---|---|---|
| 00 | [Passive Scalar](00_Passive_Scalar.md) | referência | escalar passivo, superposição, idade do ar | ✅ |
| 01 | [Eulerian: Conjugate Heat Transfer Wall Boiling](01_Eulerian_CHT_Wall_Boiling.md) | Multiphase | ebulição na parede (RPI) + CHT | ✅ |
| 02 | [Eulerian: Wall Boiling](02_Eulerian_Wall_Boiling.md) | Multiphase | RPI em tubo de Bartolomei a 45 bar, caso parametrizado por Field Functions | ✅ |
| 03 | [VOF: Boiling](03_VOF_Boiling.md) | Multiphase | ebulição com interface resolvida (VOF), 2D, parede a temperatura fixa | ✅ |
| 04 | [Conjugate Heat Transfer: Heated Fin Introduction](04_CHT_Heated_Fin.md) | Heat Transfer | CHT multi-região + convecção natural, interface não conforme | ✅ |
| 05 | [Parts-Based Shells: Exhaust Pipe](05_Parts_Based_Shells_Exhaust.md) | Heat Transfer | parede fina como shell, limpeza de CAD no 3D-CAD, wrappers e interfaces (mapped, hub) | ✅ |
| 06 | [Porous Resistance: Isotropic Media](06_Porous_Resistance_Isotropic.md) | Incompressible Flow | região porosa, coeficientes inercial/viscoso | 🟡 seções recebidas |
| 07 | [Eulerian Multiple Flow Regimes: PWR](07_Eulerian_Multiple_Flow_Regimes_PWR.md) | Multiphase | bolhas + superfície livre + gotas num só modelo (MFR), contracorrente ar–água | ✅ |
| 08 | [Eulerian: Aeration Tank Degassing](08_Eulerian_Aeration_Tank_Degassing.md) | Multiphase | contorno de degaseificação (parede permeável só ao gás), placa perfurada, Mixture Turbulence | 🟡 seções 1–5 |

**Lote 1 completo (13/10/2026).** **Lote 2, por prioridade:** (1) meio poroso ✅ (06) ·
(2) Eulerian Multiple Flow Regimes (PWR) ✅ (07) · (3) Eulerian: Aeration Tank Degassing 🟡 (08). Natural Convection: Concentric Cylinders — dispensável.

## Ferramentas

| arquivo | o que faz |
|---|---|
| [`coef_poroso.py`](coef_poroso.py) | Coeficientes de resistência porosa do STAR (P_i, P_v): ajuste a pontos Δp × v de catálogo/ensaio ou cálculo por Ergun. |
| [`props_agua_saturada.py`](props_agua_saturada.py) | Tabela de água/vapor saturados no formato do STAR (EMP com *Heat of Formation* para o calor latente), em qualquer pressão. Com `--tin` (e `--G`) aplica a receita do líquido sub-resfriado do tutorial 02: cp secante, ρ/μ/k na T média, velocidade de entrada. Requer `pip install CoolProp`. |

## Tutoriais já estudados em outros projetos
- **Ciclone (Valgroup):** tutoriais de ciclone, Lagrangeano, CHT com FE Solid Energy — ver
  `valgroup_ciclone/simulacao/aprendizado_tutorial_ciclone.md`.
- **Camada limite atmosférica:** boas práticas (COST 732, perfis de Richards & Hoxey, teste do
  domínio vazio, rugosidade) — ver `ld_celulose_dispersao_o3/02_metodo_e_analise_previa.md` §9.
