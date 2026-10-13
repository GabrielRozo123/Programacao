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
| 05 | Parts-Based Shells: Exhaust Pipe | Heat Transfer | condução em parede fina (shells) | a receber |

**Lote 2 (se necessário):** Eulerian Multiple Flow Regimes (PWR) · **Eulerian: Aeration Tank Degassing**
(saída de vapor por superfície livre) · Natural Convection: Concentric Cylinders · meio poroso
(Incompressible Flow).

## Ferramentas

| arquivo | o que faz |
|---|---|
| [`props_agua_saturada.py`](props_agua_saturada.py) | Tabela de água/vapor saturados no formato do STAR (EMP com *Heat of Formation* para o calor latente), em qualquer pressão. Com `--tin` (e `--G`) aplica a receita do líquido sub-resfriado do tutorial 02: cp secante, ρ/μ/k na T média, velocidade de entrada. Requer `pip install CoolProp`. |

## Tutoriais já estudados em outros projetos
- **Ciclone (Valgroup):** tutoriais de ciclone, Lagrangeano, CHT com FE Solid Energy — ver
  `valgroup_ciclone/simulacao/aprendizado_tutorial_ciclone.md`.
- **Camada limite atmosférica:** boas práticas (COST 732, perfis de Richards & Hoxey, teste do
  domínio vazio, rugosidade) — ver `ld_celulose_dispersao_o3/02_metodo_e_analise_previa.md` §9.
