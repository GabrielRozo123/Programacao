# STAR-CCM+ — Fase 1: Hidrodinâmica a Frio (Checklist Operacional)
**Projeto Mestrado Gabriel Rozo | FEQ/UNICAMP | 2025–2027**

> Objetivo: validar escoamento de Poiseuille no canal 2D (L=50 mm, Dh=1,1 mm).
> Critério de sucesso: u_max_CFD ≈ 1,500 mm/s e ΔP_CFD ≈ 2,975 Pa (desvio < 1%).

---

## ETAPA 1 — Criar nova simulação 2D

```
File → New Simulation
  → Space: Two Dimensional   ← CRÍTICO — não criar 3D por engano
  → OK
```

Salvar imediatamente:
```
File → Save As → "biodiesel_canal2D_fase1.sim"
```

---

## ETAPA 2 — Importar a geometria

```
File → Import → Import Surface Mesh... → selecionar: geometry/canal_2d.step

  (ou)

File → Import → CAD Model... → selecionar: geometry/canal_2d.step
  → Confirmar: "Import as Surface Geometry"
```

Após importação, a árvore deve mostrar:
```
[Simulation]
└── Geometry
    └── Parts
        └── canal_2d
            └── Surfaces: 4 arestas (Inlet, Outlet, Top_Wall, Bottom_Wall)
```

> Se as 4 arestas tiverem nomes genéricos (Surface 1, Surface 2…), renomear
> manualmente usando as coordenadas:
>   - x=0     → renomear para "Inlet"
>   - x=50mm  → renomear para "Outlet"
>   - y=0     → renomear para "Bottom_Wall"
>   - y=1.1mm → renomear para "Top_Wall"

---

## ETAPA 3 — Gerar a região de escoamento

```
Geometry → Parts → canal_2d → botão direito → "Assign Parts to Regions"
  → New Region: "Fluid"
  → Boundary Mode: "Create a Boundary for Each Part Surface"
  → OK
```

Resultado na árvore:
```
[Simulation]
└── Regions
    └── Fluid
        └── Boundaries
            ├── Inlet
            ├── Outlet
            ├── Top_Wall
            └── Bottom_Wall
```

---

## ETAPA 4 — Modelos de física

```
Regions → Fluid → Physics (ou Continuum → Physics)
  → botão direito → "Edit Models..."
```

Selecionar **exatamente** estes modelos (na ordem sugerida):

| Categoria | Modelo | Valor |
|---|---|---|
| Space | **Two Dimensional** | — |
| Time | **Steady** | — |
| Material | **Liquid** | — |
| Flow | **Segregated Flow** | — |
| Equation of State | **Constant Density** | — |
| Viscous Regime | **Laminar** | — |

> ❌ NÃO ativar: Energy, Multi-Component, Turbulence, Reaction (Fase 1 = frio)

---

## ETAPA 5 — Propriedades do fluido

```
Regions → Fluid → Physics Values → Material: Liquid
  → clicar duas vezes no fluido (nome padrão: "Water")
  → Material Properties:
       Density:           870,0  kg/m³
       Dynamic Viscosity:   6,0×10⁻³  Pa·s   (mistura óleo/MeOH a 120°C)
```

> Renomear o fluido de "Water" para "OilMeOH_120C" para clareza:
> botão direito no nome → Rename

---

## ETAPA 6 — Condições de contorno

### Inlet (Velocity Inlet)
```
Regions → Fluid → Boundaries → Inlet
  → Physics Conditions → Velocity Specification: Magnitude + Direction
  → Physics Values:
       Velocity Magnitude:  1,0×10⁻³  m/s   (1 mm/s)
       Flow Direction: [1, 0, 0]  (direção +x)
```

### Outlet (Pressure Outlet)
```
Regions → Fluid → Boundaries → Outlet
  → Physics Conditions → (padrão: Pressure Outlet)
  → Physics Values:
       Gauge Pressure:  0,0  Pa
```

### Top_Wall (No-Slip — parede catalítica, sem reação na Fase 1)
```
Regions → Fluid → Boundaries → Top_Wall
  → Physics Conditions: No-Slip Wall   (padrão — nada a mudar)
```

### Bottom_Wall (No-Slip ou Symmetry)
```
Opção A — Canal completo (sem simetria):
  → Physics Conditions: No-Slip Wall

Opção B — Metade do canal (simetria no eixo central y=0):
  → Physics Conditions: Symmetry Plane
```

> **Recomendação:** usar o canal completo (Opção A) na Fase 1. A Fase 2 tem reação
> apenas na Top_Wall → simetria deixa de ser válida.

---

## ETAPA 7 — Geração da malha

```
Mesh → Models:
  ☑ Surface Remesher    (necessário para 2D)
  ☑ Trimmer Mesher      (malha quadrada — mais simples para canal retangular)
     ou
  ☑ Polygonal Mesher    (alternativa)
```

**Parâmetros de malha:**

```
Mesh → Reference Values:
  Base Size:  0,05 mm    (= Dh/22 → ≥ 22 células na direção y)

Mesh → Volumetric Controls → (sem controle adicional para Fase 1)
```

**Malhas para análise de independência de malha (GCI):**

| Malha | Base Size | Células aprox. | Uso |
|---|---|---|---|
| Grossa  | 0,100 mm | 20 × 500 = 10 000 | Teste rápido |
| Média   | 0,050 mm | 22 × 1000 = 22 000 | **Fase 1 principal** |
| Fina    | 0,025 mm | 44 × 2000 = 88 000 | Verificação GCI |

> Para Fase 2 (Sc_TG ≈ 54 000): será necessário refinamento próximo à Top_Wall.
> Na Fase 1 isso não é necessário — malha uniforme é suficiente para Poiseuille.

Gerar malha:
```
Mesh → Generate Volume Mesh   (ou Ctrl+M)
```

---

## ETAPA 8 — Critérios de parada e monitores

### Residuais
```
Stopping Criteria → Maximum Steps: 500
Stopping Criteria → Residuals:
  Continuity:   1×10⁻⁶
  X-Momentum:   1×10⁻⁶
  Y-Momentum:   1×10⁻⁶
```

### Reports de validação
```
Reports → New Report → Surface Average:
  Nome: "u_max_outlet"
  Surface: Outlet
  Field Function: Velocity[i]   (componente x)
  → Esperado: ≈ 1,500×10⁻³ m/s na linha central
  → Como Monitor: Plots → New Plot → Y-Axis: u_max_outlet

Reports → New Report → Surface Average:
  Nome: "P_inlet"
  Surface: Inlet
  Field Function: Pressure

Reports → New Report → Surface Average:
  Nome: "P_outlet"
  Surface: Outlet
  Field Function: Pressure

Reports → New Report → Expression Report:
  Nome: "deltaP"
  Expressão: ${P_inlet} - ${P_outlet}
  → Esperado: ≈ 2,975 Pa
```

---

## ETAPA 9 — Inicialização e execução

```
Solution → Initialize   (ou botão "Initialize" na barra)
  → Aceitar valores padrão (u=0, p=0 em todo o domínio)

Solution → Run   (ou botão "Run" / F5)
  → Monitorar resíduos: devem cair abaixo de 1×10⁻⁶ em < 200 iterações
```

---

## ETAPA 10 — Validação dos resultados

### 10.1 — Perfil de velocidade na saída (comparar com Poiseuille analítico)

```
Derived Parts → New Part → Line Probe:
  Nome: "probe_outlet"
  Posição: Ponto 1 = (50mm, 0mm)   Ponto 2 = (50mm, 1.1mm)
  Resolução: 100 pontos

Reports → Line Probe → exportar u_x vs. y
```

Comparar com:
```
u(y) = u_max × [1 − (2y/Dh − 1)²]     (Poiseuille canal plano)

Para y normalizado η = 2y/Dh − 1 ∈ [−1, +1]:
  u(η) = 1,500 mm/s × (1 − η²)
```

### 10.2 — Queda de pressão

```
ΔP_CFD = P_inlet_médio − P_outlet_médio

Critério: |ΔP_CFD − 2,975 Pa| / 2,975 < 0,01  (desvio < 1%)
```

### 10.3 — Checklist de validação

```
[ ] Residuais < 1×10⁻⁶ (continuidade e momento)
[ ] u_max na saída ≈ 1,500 mm/s (desvio < 1%)
[ ] ΔP ≈ 2,975 Pa (desvio < 1%)
[ ] Perfil de velocidade parabólico (R² > 0,999 vs. Poiseuille analítico)
[ ] Pressão uniforme em cada seção transversal (confirmar visualmente)
[ ] Velocidade nula nas paredes (confirmar no Scene)
```

---

## Referência dos valores analíticos (u_entrada = 1 mm/s)

| Grandeza | Valor analítico | Fórmula |
|---|---|---|
| Re | 0,160 | ρ·u·Dh/μ |
| u_max | 1,500 mm/s | 3/2 × u_média (canal plano 2D) |
| ΔP | 2,975 Pa | 12·μ·L·u/Dh² |
| L_hid | 8,8 µm | 0,05·Re·Dh |
| τ_wall | 0,0327 Pa | 3·μ·u_média/(Dh/2) |

---

## Próximo passo após validação

Com a Fase 1 convergida e validada, salvar o arquivo `.sim` e partir para a Fase 2:
```
File → Save As → "biodiesel_canal2D_fase2_base.sim"
```
→ Seguir guia: `docs/starccm_implementation_fase2.md`
