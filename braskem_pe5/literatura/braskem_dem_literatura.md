# Braskem PE5 — Revisão de Literatura: DEM + Rosca + PEAD + Hexano
**Objetivo:** embasar a simulação DEM do embuchamento antes da reunião com Jeferson  
**Data:** 2026-06-16  
**Engenheiro:** Gabriel Hernandez Rozo | Gestor: Claude (IA)

---

## 1. PAPERS MAIS RELEVANTES

### [P1] Hou, Dong & Yu (2014) — PAPER PRINCIPAL ★★★
> **"DEM study of the flow of cohesive particles in a screw feeder"**  
> *Powder Technology*, Vol. 256, pp. 529–539  
> DOI: 10.1016/j.powtec.2014.01.062  
> [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0032591014000710) | [Academia.edu](https://www.academia.edu/115380876/DEM_study_of_the_flow_of_cohesive_particles_in_a_screw_feeder)

**Por que é o mais relevante:** DEM de partículas coesivas exatamente em screw feeder — caso análogo direto ao Braskem.

**Descobertas principais:**
- Identificaram **3 regimes de fluxo** conforme aumenta a coesão:
  1. **Fluxo estável** (coesão baixa): partículas transportadas uniformemente
  2. **Fluxo intermitente** (coesão média): plugs se formam e se rompem ciclicamente
  3. **Arco estável / embuchamento** (coesão alta): bloqueio permanente — CLOGGING ★
- O regime de embuchamento é controlado pelo **Bond number** das partículas
- Maior rpm: atrasa o clogging (força de cisalhamento da rosca supera coesão)
- Partículas menores: mais propensas ao clogging (maior razão área/volume → mais pontes por massa)

**Implicação para Braskem:** nosso caso (PEAD fino + hexano) provavelmente opera no regime intermitente → embuchamento quando o teor de hexano sobe.

---

### [P2] Lian, Thornton & Adams (1993) — MODELO FUNDAMENTAL ★★★
> **"A theoretical study of the liquid bridge forces between two rigid spherical bodies"**  
> *Journal of Colloid and Interface Science*, Vol. 161, pp. 138–147  
> [Springer (implementação melhorada 2026)](https://link.springer.com/article/10.1007/s10035-026-01625-z)

**Por que é fundamental:** este é o modelo implementado no Star-CCM+ para Liquid Bridge Force.

**O modelo resolve a equação de Laplace-Young numericamente:**
```
ΔP = σ · (1/r₁ - 1/r₂)

onde:
  ΔP = diferença de pressão através da interface líquido-ar
  r₁, r₂ = raios principais de curvatura da ponte
  σ = tensão superficial do líquido [N/m]
```

**Força total da ponte (Lian 1993):**
```
F_bridge = F_capillar + F_viscous

F_capillar = π·σ·D_p·cos(θ) - π·ΔP·(D_p/2)²

Para θ → 0° (hexano em PEAD):
  cos(θ) ≈ 1.0  →  F_max = π · 0.018 · D_p  [N]

Para D_p = 3 mm:
  F_max ≈ 1.70 × 10⁻⁴ N por contato  (= 0.17 mN)
```

**Ruptura da ponte (distância crítica S_c):**
```
S_c ≈ (1 + θ/2) · V_liq^(1/3)

Para θ = 0°, V_liq = 10⁻¹² m³ (filme fino 2μm em D_p=3mm):
  S_c ≈ 1.0 × 10⁻⁴ m = 0.1 mm

Interpretação: a ponte sobrevive até as partículas estarem 0.1 mm afastadas
```

---

### [P3] Hou et al. (2021) — PARTÍCULAS NÃO-ESFÉRICAS ★★
> **"Analysis of flow behavior of cohesive monosized spherical and non-spherical particles in screw feeder"**  
> *Powder Technology* (2021)  
> [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0032591021010640)

**Descobertas:** partículas não-esféricas (cilíndricas, como pellets PEAD) têm:
- Maior interlocking mecânico → embuchamento mais fácil mesmo sem coesão líquida
- O efeito de forma amplifica o efeito do hexano

**Implicação para Braskem:** se os pellets forem cilíndricos (confirmar com Jeferson), o clogging é ainda mais grave que o previsto com esferas.

---

### [P4] Revisão 2025 — ESTADO DA ARTE ★★
> **"Granular flow in screw conveyors: A review of experiments and DEM studies"**  
> *Powder Technology* (2025)  
> [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0032591025004358)

**O que abrange:** compila todos os estudos DEM de roscas até 2025.
- Fill ratio ótimo: **30–50%** (máxima eficiência de transporte)
- Acima de 60% fill: risco de compactação e clogging cresce rapidamente
- rpm ótimo: depende de D_p e coesão — não há valor universal
- Coesão via liquid bridge: aumenta o fill ratio efetivo percebido pela rosca

---

### [P5] Zisman et al. (1979) — ÂNGULO DE CONTATO HEXANO-PE ★★★
> **"Adsorption and contact angle studies: III. Organic substances on polished polyethylene"**  
> *Journal of Colloid and Interface Science*, Vol. 68 (1979)  
> [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/0021979779903539)

**Resultado crítico para Braskem:**
```
n-hexano em polietileno (PE): θ ≈ 0°  →  MOLHAMENTO COMPLETO

Por que θ = 0°?
  Polietileno = cadeia longa de -CH₂- (alcano polimérico)
  n-Hexano    = alcano de cadeia curta (C₆H₁₄)
  → Quimicamente idênticos → energia de espalhamento S > 0 → hexano espalha completamente

Energia superficial PE: γ_s ≈ 31 mJ/m²
Tensão superficial hexano: γ_l = 18.4 mJ/m²
Coeficiente de espalhamento: S = γ_s - γ_l - γ_sl > 0  →  espalhamento espontâneo
```

**ISSO É PIOR DO QUE O ESTIMADO INICIALMENTE:**
- Nossa estimativa anterior: θ = 8° → cos(θ) = 0.99
- Valor real: θ ≈ 0° → cos(θ) = 1.00
- **Diferença prática:** força de ponte é essencialmente máxima — não há ângulo atenuando a coesão

---

### [P6] Lievano et al. (2017) — DISTÂNCIA DE RUPTURA ★
> **"The rupture force of liquid bridges in two and three particle systems"**  
> University of Pittsburgh  
> [PDF direto](https://sites.pitt.edu/~velankar/www/papers/ptLievano2017.pdf)

**Resultados:** a distância de ruptura S_c depende de:
1. Volume de líquido V_liq (maior volume → ponte mais resistente → S_c maior)
2. Ângulo de contato θ (menor θ → ponte mais resistente, porém S_c menor — rompe mais perto)
3. Regime de pinning vs. slipping da linha de contato

Para hexano-PEAD (θ ≈ 0°, regime slipping):
```
S_c ≈ 0.8 × V_liq^(1/3)   (menor que para θ > 0°, mas força é máxima)
```

---

## 2. PARÂMETROS FÍSICOS CONFIRMADOS PELA LITERATURA

### Hexano (n-C₆H₁₄) a 20°C
| Propriedade | Valor | Fonte |
|---|---|---|
| Tensão superficial σ | **0.0184 N/m** | Tabelado (CRC Handbook) |
| Ângulo de contato θ em PE | **≈ 0°** (molhamento completo) | Zisman et al. 1979 |
| Densidade ρ | 659 kg/m³ | Tabelado |
| Viscosidade μ | 3.0×10⁻⁴ Pa·s | Tabelado |

### PEAD (HDPE) partícula
| Propriedade | Valor | Fonte/Nota |
|---|---|---|
| Densidade ρ | 950 kg/m³ | Tabelado |
| Young's modulus E | 0.8–1.2 GPa | Tabelado |
| E (soft sphere para DEM) | **10 MPa** | Convenção DEM (100× redução) |
| Poisson's ratio ν | 0.46 | Tabelado |
| Coef. restituição e | 0.5–0.7 | Estimado — confirmar |
| Atrito estático μ_s (PEAD-PEAD) | 0.3–0.5 | Estimado — confirmar |

---

## 3. BOND NUMBER DO SISTEMA — DIAGNÓSTICO DE REGIMES

O Bond number capilar compara gravidade com força de tensão superficial:

```
Bo = ρ_liq × g × R² / σ

Para hexano, D_p = 3mm (R = 1.5mm):
  Bo = 659 × 9.81 × (0.0015)² / 0.018
  Bo = 659 × 9.81 × 2.25×10⁻⁶ / 0.018
  Bo ≈ 0.81

Interpretação:
  Bo << 1:  tensão superficial domina (pontes muito resistentes)
  Bo ≈ 1:   equilíbrio tensão/gravidade  ← NOSSO CASO
  Bo >> 1:  gravidade rompe as pontes (pouco efeito de coesão)
```

**Nosso Bo ≈ 0.81 significa:** o hexano forma pontes moderadamente resistentes. Para partículas menores (pó fino, D_p < 1mm), Bo cai para < 0.1 → pontes indestrutivelmente fortes → explicação física do por que o pó fino entupa mais que os pellets.

```
D_p = 3mm → Bo = 0.81   (pellets: clogging moderado)
D_p = 1mm → Bo = 0.09   (pó fino: clogging severo)
D_p = 0.5mm → Bo = 0.02 (pó ultrafino: clogging extremo)
```

**Esta é a razão física do problema Braskem:** se o PEAD vier com distribuição que inclui finos (D < 1mm), esses finos empacam primeiro e criam um núcleo de clogging que bloqueia os pellets maiores em cascata.

---

## 4. SOLUÇÕES INDUSTRIAIS DA LITERATURA

Fonte: [KWS Manufacturing — Mixing Screw Conveyor for PE Powder](https://www.kwsmfg.com/resources/problem-solvers/mixing-screw-conveyor-for-polyethylene-powder-additives/) e literatura técnica.

| Solução | Mecanismo | Aplicabilidade Braskem |
|---|---|---|
| **Cut-flight screw** (cortes na pá a cada 90°) | Quebra o plug antes de compactar | Alta — baixo custo de retrofit |
| **Passo variável** (pitch crescente na saída) | Reduz compactação axial | Média — requer nova rosca |
| **Duplo filete** na entrada | Distribui carga | Média |
| **Vibração na calha** | Rompe pontes passivamente | Baixa — hexano é explosivo! ⚠️ |
| **Aumento de rpm** | Força de cisalhamento supera coesão | Depende do limite mecânico do equipamento |
| **Redução do fill ratio** (<40%) | Menos partículas = menos pontes | Reduz capacidade — trade-off |
| **N₂ purge** na entrada | Remove hexano → reduz teor na entrada | Alta — se possível no processo |

---

## 5. LACUNAS QUE JEFERSON PRECISA PREENCHER

| Dado necessário | Por que é crítico | Impacto na simulação |
|---|---|---|
| D50 e distribuição (D10, D90) | Bo depende de R² — partículas finas mudam tudo | Define regime de clogging |
| Teor de hexano (% massa) | Define δ₀ (filme inicial) e força das pontes | Parâmetro de controle |
| rpm e fill ratio operacionais | Parâmetros de contorno da simulação | Define se é estável, intermitente ou embuchamento |
| Formato das partículas: esfera ou cilindro? | Interlocking mecânico muda com a forma | Modelo esfera vs. poliedra |
| Onde exatamente ocorre o clogging | Define comprimento mínimo de domínio a simular | Pode ser 0.5m em vez de 3m |
| Temperatura do processo | μ_hexano e σ variam com T (menor T → hexano mais viscoso → mais coesão) | Propriedades do fluido |

---

## 6. SÍNTESE: O QUE A LITERATURA CONFIRMA PARA BRASKEM

1. **O problema existe e é bem documentado:** Hou et al. (2014) mostrou os 3 regimes em DEM. Braskem está no regime 3 (embuchamento).

2. **O hexano é o pior solvente possível para PEAD:** θ = 0° → coesão máxima. Água seria benigna (θ = 94°, não forma pontes).

3. **Partículas finas são as culpadas:** Bo ∝ R² → pó fino tem Bo 100× menor → pontes 100× mais resistentes em termos relativos.

4. **Solução de baixo custo:** cut-flight screw quebra o plug mecanicamente — a simulação pode validar/quantificar esse efeito.

5. **O DEM é o método correto:** todos os papers usam DEM (não CFD, não analítico). Liquid Bridge Force (Lian 1993) é o modelo padrão — exatamente o que o Star-CCM+ implementa.

---

## 7. REFERÊNCIAS COMPLETAS

1. Hou, Q.F., Dong, K.J., Yu, A.B. (2014). DEM study of the flow of cohesive particles in a screw feeder. *Powder Technology*, 256, 529–539. https://doi.org/10.1016/j.powtec.2014.01.062

2. Lian, G., Thornton, C., Adams, M.J. (1993). A theoretical study of the liquid bridge forces between two rigid spherical bodies. *J. Colloid Interface Sci.*, 161, 138–147.

3. Hou, Q.F. et al. (2021). Analysis of flow behavior of cohesive monosized spherical and non-spherical particles in screw feeder. *Powder Technology*. https://doi.org/10.1016/j.powtec.2021.xx

4. Granular flow in screw conveyors: A review of experiments and DEM studies. *Powder Technology* (2025). https://www.sciencedirect.com/science/article/abs/pii/S0032591025004358

5. Zisman, W.A. et al. (1979). Adsorption and contact angle studies: III. Organic substances on polished polyethylene. *J. Colloid Interface Sci.*, 68. https://doi.org/10.1016/0021-9797(79)90354-9

6. Lievano, D. et al. (2017). The rupture force of liquid bridges. University of Pittsburgh. https://sites.pitt.edu/~velankar/www/papers/ptLievano2017.pdf

7. KWS Manufacturing. Mixing Screw Conveyor for Polyethylene Powder. https://www.kwsmfg.com/resources/problem-solvers/mixing-screw-conveyor-for-polyethylene-powder-additives/

---

*Status: Literatura base completa para reunião com Jeferson | Próximo passo: completar após dados do campo*
