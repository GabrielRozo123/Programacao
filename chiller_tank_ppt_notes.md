# GreyBeer Chiller Tank — Descobertas CFD (Rascunho PPT)
**Projeto:** GreyLogix / GreyBeer 20400100TK  
**Ferramenta:** Star-CCM+ | Transiente Implícito | Δt = 1 s  
**Última atualização:** t = 20.000 s simulados

---

## SLIDE 1 — Contexto e Motivação

- Tanque de resfriamento: solução hidroalcóolica 70/30 (água/etanol) a −5°C
- Capacidade: **69,3 m³** (≈ 69.300 L)
- Vazão chiller: **12 m³/h** (ṁ = 3,11 kg/s)
- Tempo de renovação (τ): **20.772 s ≈ 5,8 horas**
- Pergunta do cliente: *"Quanto tempo leva para o tanque chegar a −5°C após partida? O sensor de controle representa o bulk?"*

---

## SLIDE 2 — Geometria do Domínio Fluido

| Parâmetro | Valor |
|-----------|-------|
| Diâmetro interno | 4.210 mm = 4,21 m |
| Altura cilindro | 4.720 mm = 4,72 m |
| Altura cone de fundo | 780 mm = 0,78 m |
| Altura total do fluido | 5.500 mm = 5,50 m |
| Bocal inlet (teto, DN150) | offset radial 1.200 mm do centro |
| Bocal outlet (ápice do cone, DN150) | centro, direção −Z |

- Entrada do chiller: **TETO** (jato descendente, −5°C)
- Saída para o chiller: **ápice do cone** (ponto mais baixo, drenagem por gravidade)
- Geometria reconstruída em CadQuery → exportada como STEP → importada no Star-CCM+

---

## SLIDE 3 — Modelos Físicos

| Modelo | Escolha | Justificativa |
|--------|---------|---------------|
| Escoamento | Implícito Unsteady, k-ε Realizable | Transiente com convecção forçada + natural |
| Fluido | Single-phase liquid (não VOF) | Composição uniforme; apenas T varia |
| Densidade | Polinomial em T: ρ = 1082,88 − 0,55·T [K] | Âncora: 932,65 kg/m³ @ 0°C (OIML R22) |
| Gravidade | g = −9,81 m/s² (eixo Z) | Convecção natural por gradiente de densidade |
| Discretização temporal | 2ª ordem | Evita difusão numérica da termoclina |
| Δt | 1 s | 9× menor que tempo de atravessamento do plume (9 s) |

**Propriedades do fluido (0°C, 30% m/m etanol):**
- ρ = 932,65 kg/m³ | μ = 1,796×10⁻³ Pa·s | k = 0,2758 W/m·K | cp = 3.652 J/kg·K
- β = 5,9×10⁻⁴ K⁻¹ | Re_inlet = 14.693 (turbulento)

---

## SLIDE 4 — Descoberta #1: Curto-Circuito Imediato

- **Tempo para o jato frio atingir o outlet:** ~85 s (< 2 minutos)
- O jato desce pelo cone, sai pela base — *curto-circuito hidráulico*
- Implicação: o sensor de saída lê −5°C cedo, mas o bulk ainda está quente
- **Risco operacional:** chiller "pensa" que o tanque esfriou → pode desligar prematuramente

> 📌 *Imagem sugerida: Vector Scene / Streamlines a t ≈ 85–115 s mostrando o jato descendo e saindo.*

---

## SLIDE 5 — Descoberta #2: Estratificação Térmica (Filling-Box)

- Teoria de Baines & Turner (1969): plume frio desce, fluido frio acumula de baixo para cima
- Três zonas identificadas no perfil T(z):
  1. **Bulk bem-misturado** (z = 1,0–4,0 m): gradiente suave
  2. **Núcleo do plume** (próximo ao eixo): mais frio
  3. **Tampa quente ("warm lid")** (z > 4,5 m): estratificação estável, resfriamento lento
- Sensor no topo é o **último** a chegar em −5°C

> 📌 *Imagem sugerida: XY Plot T(z) com múltiplas curvas temporais sobrepostas (Solution History).*

---

## SLIDE 6 — Descoberta #3: Comportamento CSTR do Bulk

**Surpreendente:** apesar da estratificação local, o bulk do tanque segue o modelo de tanque bem-misturado:

$$T(t) = -5 + 10 \cdot e^{-t/\tau} \quad [\text{°C}], \quad \tau = 20.772\,\text{s}$$

| Tempo (h) | T_bulk previsto | T_bulk simulado |
|-----------|----------------|-----------------|
| 0 h | +5,0°C | +5,0°C |
| 5,6 h (t=20.000 s) | −1,2°C | **−1,0°C** ✓ |
| 11,5 h (t=41.544 s) | −3,7°C | (extrapolado) |
| 17,3 h (t=62.316 s) | −4,5°C | (extrapolado) |
| **23,1 h (t=83.000 s)** | **−4,8°C** | **≈ regime** |

**Conclusão:** o tanque precisa de ~4 renovações de volume (≈ 23 horas) para atingir −5°C em todo o bulk.

---

## SLIDE 7 — Descoberta #4: Impacto do Sensor no Controle

| Sensor | Localização | Lê −5°C em... | Bulk real em... |
|--------|------------|---------------|-----------------|
| Saída (outlet) | Ápice do cone | ~85 s | +5°C (curto-circuito!) |
| Sensor Baixo | Base do cilindro | ~t ≈ ? h | −5°C apenas localmente |
| Sensor Alto | Meio do cilindro | ~t ≈ ? h | −5°C localmente |
| **Topo** | Tampa do tanque | **último** | Bulk já frio |

> ⚠️ *Se o controle do chiller usa apenas a temperatura de saída, pode desligar em < 2 min enquanto 69 m³ ainda estão a +5°C.*

*(Valores exatos pendentes: exportar CSV dos monitors e da Solution History)*

---

## SLIDE 8 — Recomendações para o Cliente

1. **Não usar temperatura de saída isolada** como critério de desligamento do chiller
2. **Sensor de controle deve estar no topo** (último a esfriar) para garantir que o bulk atingiu a temperatura
3. **Tempo de pré-resfriamento recomendado:** mínimo 6 horas (1τ) para −1°C; **23 horas para −5°C completo**
4. **Alternativa:** lógica AND — chiller liga enquanto T_topo > −4°C E T_saída > −4,5°C
5. Avaliar se a capacidade do chiller (Q = 12 m³/h) é adequada para o tempo de processo do cliente

---

## PENDÊNCIAS (dados ainda necessários)

- [ ] Export CSV: Monitor Sensor Alto, Baixo, Saída, Topo (completo até t=20.000 s)
- [ ] Solution History: perfis T(z) a cada 600 s → figura de evolução
- [ ] Confirmar posição exata dos sensores reais de controle (Otávio/Marcus)
- [ ] Rodar até t = 42.000 s para capturar o "joelho" da curva exponencial
- [ ] Imagem final da Scalar Scene mostrando estratificação completa
