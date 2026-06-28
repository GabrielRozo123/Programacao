# Plano — Rollover Térmico LN₂ (Caminho A)

> Validação QUALITATIVA do mecanismo de rollover contra o La Spezia (1971).
> Reaproveita o caso de auto-pressurização já validado (Clausius-Clapeyron, 0,1%),
> mudando 4 coisas para habilitar o overturn. Atualizado: 2026-06-28.

---

## Objetivo
Demonstrar o mecanismo de rollover: duas camadas de LN₂ estratificadas (fria/densa
embaixo, quente/leve em cima, inicialmente ESTÁVEL) → a camada inferior aquece pelo
heat flux do fundo → fica menos densa → cruza a densidade da camada superior →
**overturn súbito** → surto de BOG → pico de pressão.

Validação: comportamento qualitativo do La Spezia (atraso longo → inversão repentina →
sobrepressão → venting). NÃO é validação quantitativa (escala/tempo industrial inviável).

---

## Mudanças vs caso de auto-pressurização validado

### 1. Densidade do líquido → dependente de T (Polynomial Density)
- EOS do N2_liquido: Constant Density → **Polynomial Density**
- ρ(T) = **1162.4 − 4.6·T**  [kg/m³, T em K]
  - coef. a0 = 1162.4 ; a1 = −4.6 ; demais = 0
  - confere: T=77,35 K → 806,6 ; T=77 K → 808,2 ; T=78 K → 803,6
  - β ≈ 0,0057 /K (expansão térmica do LN₂ — grande, típica de criogênico)
- Sem isso NÃO há empuxo entre camadas → sem rollover.

### 2. Condição inicial — duas camadas de temperatura
- `Initial Conditions > Static Temperature` → Method = **Field Function**
- Field function (T inicial por altura z):
  `(${Centroid}[2] < 0.085) ? 77.0 : 78.0`
  - z < 85 mm  → **77 K** (camada inferior, densa, estável)
  - z ≥ 85 mm  → **78 K** (camada superior + vapor, mais leve)
- ΔT = 1 K → camada de baixo ~4,6 kg/m³ mais densa (estável no início).
- VOF Wave (nível de líquido em 170 mm) e pressão hidrostática: mantém igual.

### 3. Heat flux — só no fundo, forte
- `Fundo` → Heat Flux = **500 W/m²** (aquece a camada inferior rápido)
- `parede_lateral` e `Topo` → **Adiabatic** (0 W/m²)
- Isola o gatilho do rollover. Estimativa: camada inferior (~2,2 kg) aquece 1 K em
  ~5 min físicos → inverte logo depois.

### 4. Monitores de rollover
- **eixo_z (line probe)** T(z): ver as duas camadas → mistura súbita no overturn
- **P_ullage**: o **surto** de pressão no instante do rollover (assinatura-chave)
- **Velocidade máxima** (novo report: Maximum of Velocity Magnitude no líquido):
  dispara no overturn — marca o evento
- Scene de **Temperatura** + **Velocidade** (vetores): visualizar a inversão

---

## Numérica — manter o que estabilizou
- Accommodation Coefficient = **1e-3**
- Δt máx = **1e-3 s** perto do evento (pode usar maior antes); Adaptive Time-Step liga
- Maximum Inner Iterations = **15**
- Minimum Allowable Temperature = **50 K**
- AMR Free Surface mantido (interface líquido-vapor); a interface entre as duas camadas
  de líquido NÃO é capturada pelo AMR de superfície livre (é gradiente de T, não de VF)
  → contar com a malha base + convecção para resolver.

## Sequência de execução
1. Trocar EOS do líquido p/ Polynomial Density (ρ=1162.4−4.6T)
2. Field function de T inicial (2 camadas) + aplicar em Initial Conditions
3. Heat flux: fundo 500 W/m², laterais/topo adiabáticas
4. Criar report de Velocidade Máxima + monitor
5. Re-inicializar; conferir scene de Temperatura (2 camadas: fria embaixo)
6. Rodar; observar T(z) estratificado → overturn → surto em P_ullage e velocidade

## Resultado esperado (assinatura do rollover)
- Fase 1 (atraso): T(z) com degrau estável, P_ullage subindo devagar (como antes)
- Fase 2 (gatilho): camada inferior cruza a densidade da superior
- Fase 3 (overturn): velocidade dispara, T(z) mistura/homogeneíza subitamente,
  **P_ullage dá um surto** (líquido quente atinge a superfície e evapora)
- = análogo direto do La Spezia: atraso → inversão repentina → sobrepressão
