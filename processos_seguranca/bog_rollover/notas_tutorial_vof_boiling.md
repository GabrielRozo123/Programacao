# Notas — Tutorial Star-CCM+ "VOF: Boiling" → adaptação caso LN₂

> Registro do passo a passo do tutorial oficial (Star-CCM+ 20.06.007) e como adaptar
> para o estudo de BOG/rollover criogênico (caso de validação Seo & Jeong, LN₂, 201×213 mm).
> Atualizado: 2026-06-27 — PDFs recebidos: 5 de 10 (faltam BCs, modelo de ebulição,
> solver, stopping criteria, run/pós-proc).

---

## Visão geral do tutorial original
- **Problema:** água fervendo ao escoar sobre superfície aquecida (phase change).
- **Malha:** reaproveitada do tutorial "VOF: Gravity-Driven Flow", **escalada ÷10**
  (fator 0.1) → bocal ~50 mm.
- **Condições originais:**
  - Entrada (esquerda): água, **v = 1 m/s**, **T = 350 K**
  - Saída (direita): **T = 370 K**, pressão atmosférica
  - Fundo: **parede com T fixa = 540 K** (superfície aquecida)
  - Demais contornos: paredes sólidas **adiabáticas**
- **Objetivo didático:** mostrar impacto dos parâmetros do modelo de ebulição na
  transferência de calor.

---

## Passos cobertos pelos 5 PDFs recebidos

### 1. Converting to a Two-Dimensional Mesh
- Requisitos p/ conversão 2D: malha alinhada ao plano **X-Y**, com boundary em **Z = 0**.
- `Scenes > New > Mesh`; menu `Mesh > Convert to 2D...`; ativar "Delete 3D Regions After
  Conversion".
- Depois deletar `Continua > Physics 1` (recriado como "Physics 1 2D").

### 2. Scaling the Mesh
- `Mesh > Scale Mesh`, região `Default_Fluid 2D`, **Scale Factor = 0.1**.
- Extensão resultante: x[-0.40, 0.50] m, y[0, 0.40] m, z=0 (2D).
- `Mesh > Diagnostics` p/ checar.

### 3. Selecting the Physics Models  (continuum renomeado "Boiler")
Ordem de seleção:
- **Two Dimensional** (pré-selecionado)
- Time: **Implicit Unsteady**
- Material: **Multiphase** → Multiphase Interaction (auto)
- Multiphase Model: **Volume of Fluid (VOF)** → Segregated Flow (auto), Gradients (auto)
- Viscous Regime: **Turbulent** → RANS (auto) → **K-Epsilon** → Realizable K-Eps Two-Layer
  (auto) → Wall Distance (auto) → Two-Layer All y+ Wall Treatment (auto)
- Optional: **Segregated Multiphase Temperature**, **Gravity**

### 4. Setting the Material Properties (node "Phases")
- Fase 1 → renomear **H2O**: Material = **Liquid**, EOS = **Constant Density**
- Fase 2 → renomear **H2O (G)**: Material = **Gas**, EOS = **Constant Density**
- Substituir o Air padrão: `H2O (G) > Models > Gas > Air` → "Replace with" →
  Material Databases > Standard > Gases > **H2O (Water)**.
- Propriedades default servem ao tutorial.

---

## ADAPTAÇÕES para o nosso caso (LN₂, Seo & Jeong)

| Item | Tutorial (água) | Nosso caso (LN₂) |
|---|---|---|
| Geometria | placa/bocal 2D escalado | cilindro **201 mm × 213 mm, 6,75 L** |
| Dimensionalidade | 2D plano | **2D-axissimétrico** (cilindro vertical) |
| Fluido | H₂O líq. + H₂O(G) | **N₂ líquido + N₂ gasoso** (banco Standard) |
| Densidade | constante | avaliar densidade f(T) p/ empuxo (ou Boussinesq) |
| Parede de calor | T fixa 540 K | **fluxo de calor** (heat leak) — Seo & Jeong testam vários |
| Entrada/saída | inlet 1 m/s / outlet atm | **tanque fechado** (sem inlet/outlet); ullage pressuriza |
| Turbulência | K-ε turbulento | provável **laminar** (convecção natural fraca em LN₂) — avaliar Ra |
| Estado inicial | preenchido | **estratificado**: 2 camadas (Δρ/ΔT) p/ rollover, OU fill ~uniforme p/ self-press |
| Validação | qualitativa | comparar **P(t)** com curvas de Seo & Jeong |

### Pontos de atenção
- O tutorial usa **densidade constante** nas duas fases — para rollover/estratificação
  precisamos de **empuxo** (densidade f(T) ou Boussinesq), senão não há overturn.
- "Segregated Multiphase Temperature" é essencial (resolve energia por fase).
- Gravity ON é obrigatório.
- Falta ver (próximos PDFs): qual **modelo de ebulição/phase change** (Lee? Saturation?),
  parâmetros de troca de massa, stopping criteria e setup do solver.

---

## Pendente
- [ ] Receber os 5 PDFs restantes (BCs, modelo de ebulição, solver, run, pós-proc)
- [ ] Definir modelo de phase change (provável Lee/Schrage) e parâmetros
- [ ] Montar geometria LN₂ 2D-axissimétrica (201×213 mm)
- [ ] Trocar materiais para N₂ líq/gás
- [ ] Inicialização estratificada + parede com heat flux
- [ ] Validar P(t) vs Seo & Jeong
