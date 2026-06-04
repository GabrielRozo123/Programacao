# STAR-CCM+ — Surface Reaction LHHW para Transesterificação Heterogênea
**Projeto Mestrado Gabriel Rozo | FEQ/UNICAMP**

> Este guia cobre EXATAMENTE como implementar a cinética LHHW em um canal 2D
> com escoamento laminar monofásico líquido. É diferente do tutorial
> "Methane on Platinum" (que usa Chemkin para química de gás complexa).
> Para o nosso caso líquido-sólido com LHHW, o caminho é mais simples.

---

## Por que o tutorial de Metano no Pt NÃO é o nosso caminho

| Tutorial Siemens (CH₄/Pt) | Nosso caso (TG/MeOH/LHHW) |
|---|---|
| Fase gás | Fase líquida |
| Química complexa (20+ reações elementares) | 1 reação global LHHW |
| Arquivo Chemkin (chem.inp + surf.inp) | Field Function customizada |
| Surface coverage (θ_Pt, θ_CO, etc.) | Não necessário (global) |
| Temperatura > 500°C | 120°C |

**Nosso caminho:** Multi-Component Liquid + Surface Reaction com taxa definida por User Field Function.

---

## FASE 1 — Hidrodinâmica a Frio

### Passo a passo STAR-CCM+ (caminho exato na árvore)

**1. Criar geometria 2D**
```
File → New Simulation → 2D
Geometry → 3D-CAD (ou importar STEP de build123d)
Canal: largura = Dh = 1,1 mm | comprimento = 50 mm
```

**2. Gerar malha estruturada**
```
Mesh → Directed Meshing → 2D Extruder (ou Trimmer 2D)
  ├── Tamanho base: 0,05 mm (22 células na largura → Ny ≥ 20 é o mínimo)
  ├── Direção axial: progressão 1.0 (uniforme) para Fase 1
  └── SEM prism layers (escoamento laminar: refinar malha volumétrica)

Malha mínima aceitável: 20 (y) × 200 (x) = 4.000 células
Malha refinada: 40 × 500 = 20.000 células
```

**3. Modelos de física**
```
Continuum → Physics Models → Select Physics:
  ✅ Space: Two Dimensional
  ✅ Time: Steady
  ✅ Material: Liquid
     └── Fluid: criar "OilMeOH_mix" (constante, por ora)
  ✅ Flow: Segregated Flow
  ✅ Equation of State: Constant Density
  ✅ Viscous Regime: Laminar
  ❌ NÃO ativar: Turbulence, Energy, Species (Fase 1 = frio sem reação)
```

**4. Propriedades do fluido (Fase 1 — mistura homogênea)**
```
Continuum → Physics → Models → Liquid → OilMeOH_mix:
  Density:   870 kg/m³
  Viscosity: 6.0×10⁻³ Pa·s   (óleo canola a 120°C — dinâmica)
```

**5. Condições de contorno**
```
Boundaries:
  Inlet  → Velocity Inlet
             └── Velocity: 1.0×10⁻³ m/s  (ajustar conforme Re desejado)

  Outlet → Pressure Outlet
             └── Gauge Pressure: 0 Pa

  Top Wall   → No-Slip Wall (parede com catalisador — sem reação ainda)
  Bottom Wall → No-Slip Wall (ou Symmetry se canal for simétrico)
  Front/Back  → (2D — não existe)
```

> **Nota:** Se o canal for modelado como canal completo (sem simetria), use duas paredes.
> Se usar metade do canal (simetria no eixo central), a parede inferior vira Symmetry Plane.

**6. Reports e critério de parada**
```
Reports:
  → Surface Average: Velocity Magnitude na saída (deve ser ~1.5 × u_entrada = 1.5 mm/s)
  → Surface Average: Static Pressure no Inlet e Outlet
  → ΔP = P_inlet − P_outlet  (deve ser ≈ 3 Pa para os parâmetros acima)

Convergência:
  → Residuals: Continuity + X-Momentum + Y-Momentum < 1×10⁻⁶
  → Normalmente converge em < 200 iterações
```

**7. Validação analítica (Poiseuille)**
```
Na linha central (y = 0):
  u_max_CFD deve ser ≈ (3/2) × u_média = 1.5 × 1.0 mm/s = 1.5 mm/s

Exportar perfil de velocidade na saída:
  Reports → Line Probe → posição x = L_saída → exportar u(y)
  Comparar com: u(y) = u_max × [1 - (2y/H)²]
```

---

## FASE 2 — Reação de Superfície LHHW + CHT

### Visão geral do que será adicionado

```
Fase 1 (convergida)
    │
    ├── + Multi-Component Liquid  → TG, MeOH, FAME, GL como espécies
    ├── + Fluid Temperature       → equação de energia
    ├── + Surface Reaction (LHHW) → taxa na parede washcoat
    └── + Coupled Wall BC         → balanço térmico na parede
```

### Passo 1 — Adicionar espécies (Multi-Component Liquid)

```
Continuum → Physics Models → Edit...
  ✅ Adicionar: Multi-Component Liquid
               └── Species: TG, MeOH, DG, MG, FAME, GL

ATENÇÃO: a ordem de adição importa para o modelo de difusão.
O componente "solvente" (MeOH, que está em excesso 6:1) deve ser declarado
como componente primário (base) ou usar "Fickian Diffusion" para cada espécie.
```

**Propriedades por espécie (inserir em cada componente):**

| Espécie | M (g/mol) | D em MeOH a 120°C (m²/s) | Notas |
|---|---|---|---|
| TG (triolein) | 885 | ~1×10⁻¹⁰ | Estimado Wilke-Chang |
| MeOH | 32 | ~5×10⁻⁹ | Solvente (base) |
| DG | 621 | ~2×10⁻¹⁰ | Interpolado |
| MG | 357 | ~4×10⁻¹⁰ | Interpolado |
| FAME (oleate) | 297 | ~3×10⁻¹⁰ | Estimado |
| GL (glicerol) | 92 | ~8×10⁻¹⁰ | Menor → mais móvel |

> **Simplificação aceitável na dissertação (Fase 2 inicial):** usar apenas TG e FAME
> (reação global: TG + 3MeOH → 3FAME + GL) e tratar MeOH como solvente (excesso).

### Passo 2 — Adicionar equação de energia

```
Continuum → Physics Models → Edit...
  ✅ Adicionar: Fluid Temperature

Propriedades térmicas do fluido (OilMeOH_mix):
  Thermal Conductivity:  0,17 W/(m·K)
  Specific Heat:         2000 J/(kg·K)
```

### Passo 3 — Surface Reaction LHHW (o coração da Fase 2)

**3a. Criar a Field Function da taxa de reação**

```
Tools → Field Functions → New → User Field Function

Nome: r_LHHW
Unidade: mol/(m²·s)
Definição (expressão):

$$ r = \frac{k \cdot C_{TG} \cdot C_{MeOH}}{(1 + Ka \cdot C_{TG} + Kb \cdot C_{MeOH})^2} $$

Em notação STAR-CCM+ (Field Function syntax):

( A_pre * exp(-Ea / (8.314 * $$Temperature)) 
  * $$MassFraction_TG * rho / M_TG
  * $$MassFraction_MeOH * rho / M_MeOH )
/ pow( 1.0 
       + Ka * $$MassFraction_TG * rho / M_TG 
       + Kb * $$MassFraction_MeOH * rho / M_MeOH 
     , 2.0)

Onde:
  A_pre = fator pré-exponencial [m⁴/(mol·s)] — da literatura cinética
  Ea    = energia de ativação [J/mol]
  Ka    = constante de adsorção do TG [m³/mol]
  Kb    = constante de adsorção do MeOH [m³/mol]
  rho   = $$Density  (densidade local, kg/m³)
  M_TG  = 0.885  (kg/mol)
  M_MeOH = 0.032 (kg/mol)
```

> **Importante:** Adicionar um limitador `max(r, 0.0)` para evitar taxa negativa
> em regiões de alta conversão (instabilidade numérica).

**3b. Ativar Surface Reaction na parede washcoat**

```
Boundaries → Top Wall (parede catalítica) → Edit
  ├── Physics Conditions → Thermal Specification: Coupled Wall  (ou Heat Flux)
  │      └── Heat Flux: q = ΔHrxn × r_LHHW  [W/m²]
  │          Expression: 10000 * $$r_LHHW   (ΔH ≈ 10 kJ/mol → positivo = endotérmico → sink)
  │
  └── Physics Conditions → Species: Reaction
         └── Para cada espécie, definir o fluxo de massa na parede:
             TG:   -M_TG   × $$r_LHHW   [kg/(m²·s)]  ← consumido
             MeOH: -3×M_MeOH × $$r_LHHW              ← consumido (3 mol por mol TG)
             FAME: +3×M_FAME × $$r_LHHW               ← produzido
             GL:   +M_GL   × $$r_LHHW                 ← produzido
```

> **Alternativa mais limpa:** usar `Chemistry → Surface Reactions → Add Reaction`
> e definir a taxa como Field Function já criada. O STAR-CCM+ então calcula
> automaticamente os fluxos de espécie a partir da estequiometria.

**Caminho alternativo (mais integrado):**
```
Continuum → Physics → Models → Chemistry → Surface Reactions
  → Add Surface Reaction
       └── Reactants: TG (ν=1), MeOH (ν=3)
           Products:  FAME (ν=3), GL (ν=1)
           Rate Law:  Custom (User-Defined)
                └── Rate Field Function: r_LHHW  [mol/(m²·s)]
```

### Passo 4 — Condições de contorno Fase 2

```
Inlet → adicionar:
  Species: MassFraction_TG  = 0.88  (fração mássica de TG puro)
           MassFraction_MeOH = 0.12 (razão molar 6:1 → fração mássica ~12%)
  Temperature: 393 K (120°C)

Outlet → Pressure Outlet (igual Fase 1)
  + Species: zero-gradient (padrão — não precisar especificar)

Top Wall → Coupled Wall (sem temperatura fixa — o calor vem da reação)
  ou: Temperature Wall → 393 K (isotérmico — simplificação válida se ΔHrxn é pequeno)
```

### Passo 5 — Inicialização e convergência

```
1. Inicializar com solução da Fase 1 (Field Initialization → Load from file)
2. Rampar a taxa de reação gradualmente (URF nas primeiras 100 iterações)
3. Monitorar:
   - Perfil axial de X_TG (conversão ao longo do canal)
   - Perfil axial de T (temperatura — deve cair levemente se endotérmica)
   - Resíduos de espécie: alvo < 1×10⁻⁵

Relatórios cruciais:
  → Line Probe no eixo central: C_TG(x), T(x)
  → Surface Integral na parede: taxa total de reação (mol/s) → conversão global
```

---

## Parâmetros Cinéticos Placeholder (a substituir pelos valores reais)

Enquanto a referência ZnAl₂O₄ não é localizada, usar estes valores estimados
para verificar que a implementação roda:

| Parâmetro | Valor placeholder | Unidade | Fonte |
|---|---|---|---|
| A_pre | 1×10⁴ | m⁴/(mol·s) | Estimativa ordem de magnitude |
| Ea | 60 000 | J/mol | Típico transesterificação heterogênea |
| Ka | 5×10⁻³ | m³/mol | Estimativa |
| Kb | 1×10⁻³ | m³/mol | Estimativa |
| ΔHrxn | +10 000 | J/mol_TG | Literatura (confirmar) |

> **Nunca apresentar estes valores na dissertação sem confirmação bibliográfica.**
> São apenas para depurar a implementação numérica.

---

## Diferença entre o Tutorial CH₄/Pt e Nosso Caso — Resumo Visual

```
Tutorial Siemens (gás/Pt):          Nosso caso (líquido/washcoat):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chemkin files → importar             Field Function manual
chem.inp (mecanismo gás)             r_LHHW = f(C_TG, C_MeOH, T)
surf.inp (cobertura superficial)     Sem surface coverage (θ)
20+ espécies superficiais            4–6 espécies (TG, MeOH, DG, MG, FAME, GL)
T > 500°C                            T = 120°C
Gás ideal                            Líquido incompressível
Surface Coverage Equations           Não necessário
Tolerância numérica: stiff solver    Segregated species (mais simples)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

O tutorial do metano/platina é útil para entender o conceito de Surface Reaction
no STAR-CCM+, mas a implementação concreta para LHHW líquido é via Field Function,
que é mais simples e mais flexível.
