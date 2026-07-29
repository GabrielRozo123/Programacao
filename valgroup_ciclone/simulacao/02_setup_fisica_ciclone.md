# Setup da FÍSICA — Ciclone Valgroup (steady, só gás)

> Após estudar o tutorial Siemens "Anisotropic Flow: Cyclone Separator". Malha validada:
> **486.990 células · Face Validity 100% em 1,0 · Volume Change mín. 1,1e-2** (sem células ruins).

## 1. ⚖️ Turbulência: o tutorial usa K-Omega; eu recomendo RSM. Por quê.

**O que o tutorial faz:** `K-Omega SST` — e ele **declara o motivo**:
> *"the K-Omega turbulence model is used **to limit the simulation run time**"*
> *"first run in steady state **without curvature correction**, then run as **unsteady for 0.5 s with
> curvature correction activated**"*

**Leitura honesta:** o tutorial é **didático** (malha grosseira, foco em ensinar o fluxo de trabalho).
K-Omega SST é **isotrópico** — assume viscosidade turbulenta igual em todas as direções, o que é
justamente **falso** num vórtice. A **Curvature Correction** compensa *parte* disso, mas não tudo.
Para **entregar eficiência de coleta a cliente**, o padrão da literatura de ciclones é **RSM**
(resolve as tensões de Reynolds anisotrópicas diretamente).

### 🛠️ O caminho prático (o melhor dos dois)
| # | Modelo | Objetivo |
|---|---|---|
| 1 | **K-Omega SST steady** (sem CC) | robusto: estabelece o escoamento, 1ª estimativa de ΔP |
| 2 | **RSM steady**, inicializando do (1) | precisão: o campo do K-Omega serve de chute inicial |
| 3 | comparar ΔP e perfil de velocidade tangencial | se baterem, temos confiança dupla |
| 4 | **Unsteady + Curvature Correction** | PVC (vórtice precessante) — afeta a captura dos finos |

> RSM em ciclone **frequentemente não converge bem em steady** (o escoamento é intrinsecamente
> transiente pelo PVC). Se travar, o passo 1 já dá o campo para partir direto ao transiente.

## 2. Modelos do Continuum
```
Three Dimensional · Steady · Gas · Segregated Flow · Constant Density
Viscous Regime: Turbulent → RANS
  ├─ (passo 1) K-Omega Turbulence → SST (Menter) → All y+ Wall Treatment
  └─ (passo 2) Reynolds Stress Turbulence (RSM)
```

## 3. Propriedades do gás
| | valor |
|---|---|
| Densidade | **3,946 kg/m³** (constante — @400°C, 1,2 bar) |
| Viscosidade dinâmica | **9,5e-5 Pa·s** |

## 4. Condições de contorno

| Boundary | Tipo | **100%** | **50%** |
|---|---|---|---|
| **`inlet`** | Velocity Inlet | **15,23 m/s** | **7,62 m/s** |
| | *(ou Mass Flow Inlet)* | *0,50556 kg/s* | *0,25278 kg/s* |
| | Turbulence: **Intensity + Length Scale** | I = **0,041** · L = **0,0058 m** | I = **0,045** · L = **0,0058 m** |
| **`outlet_gas`** | Pressure Outlet | 0 Pa | 0 Pa |
| **`outlet_dust`** | ⚠️ **Wall** (ver §5) | — | — |
| **`walls`** | Wall, no-slip | — | — |

*Intensidade calculada por I = 0,16·Re^(−1/8) com Re_duto = 52.430 (100%) / 26.215 (50%);
comprimento L = 0,07·D_h com D_h = 82,9 mm.*

## 5. ⚠️ A sutileza da saída de pó
Na planta a saída de pó vai para **moega com válvula rotativa (airlock)** — é **selada**.
Se virar Pressure Outlet, **o gás foge pelo fundo**, o vórtice não fecha e a eficiência sai errada.

| Para o GÁS | Para as PARTÍCULAS (fase Lagrangeana) |
|---|---|
| **Wall** | **Escape** (partícula que chega ali = CAPTURADA) |

## 6. Solver e parada
- Under-relaxation: **Velocity 0,6 · Pressure 0,3** (RSM: 0,5)
- Rodar **1ª ordem** ~200 iterações, depois **2ª ordem**
- **Maximum Steps ≈ 1500** (o tutorial usa 1500 e é suficiente para o steady)
- Parada real: **ΔP estabilizado** + resíduos

## 7. Monitores
1. **ΔP** (`inlet` → `outlet_gas`) → **validar contra os 29,3 mbar do analítico** ⭐
2. Velocidade tangencial máxima (perfil no plano horizontal)
3. Balanço de massa

## 8. Cena (dica do tutorial)
Scalar Scene com **Total Pressure** no plano de corte, color map **blue-red balanced** — mostra
muito bem o núcleo de baixa pressão do vórtice. (Tutorial "Preparing a Scalar Scene".)

## 9. O que o tutorial NÃO cobre e nós precisamos
| Item | Situação |
|---|---|
| **Fase Lagrangeana** (a eficiência de coleta) | ⏳ próximos tutoriais |
| **CHT** (parede > orvalho ~250°C) | ⏳ requisito do e-mail do Lucas |
| **Erosão** (char com 21% de minerais) | ⏳ desejável |
| **Turndown 50%** | nosso escopo, não do tutorial |

---

## 10. Transiente + Curvature Correction (tutoriais "Running Unsteady" e "Streamlines")

### O que o tutorial faz
1. Desativa `Steady` → ativa **`Implicit Unsteady`**
2. No nó **`SST (Menter) K-Omega`** → **`Curvature Correction = On`**
3. Solvers: **Time-Step 5,0e-4 s** · Under-Relaxation **Velocity 0,9 · Pressure 0,4**
   *(note: MAIORES que no steady — o transiente é mais estável)*
4. Stopping: `Maximum Steps` **desativado** · **Max Inner Iterations = 8** · **Max Physical Time = 0,5 s**
5. Compara steady × transiente com **Solution History + Linked Views** (layout 1 Left / 1 Right)

### ⚠️ Ajuste para a NOSSA geometria (maior que a do tutorial)
| | tutorial | **nosso** |
|---|---|---|
| Time-step | 5,0e-4 s | **2,0e-4 s** (célula 5 mm no núcleo, v ~30 m/s no vórtice → CFL ~1) |
| Inner iterations | 8 | 5–8 |
| Tempo físico | 0,5 s | **≥ 1,5 s** |

**Por que ≥1,5 s:** o **tempo de residência** do nosso ciclone é **V/Q = 61,8 L / 128,1 L/s ≈ 0,48 s**.
0,5 s = apenas **1 residência** — insuficiente para estatística. **3 residências ≈ 1,5 s.**

### Streamlines (ótimo para o relatório ao cliente)
- `Derived Parts → New → Streamline` · **Seed Parts = boundary `inlet`** · U-Res 2 · V-Res 8
- `Streamline Stream 1 → Mode = **Ribbons**` · Scalar Field = **Velocity Magnitude**
- `2nd Order Integrator → Maximum Propagation = **15**` (senão a linha não chega à saída)
- Animação: `Animation Mode = Tracers` · delay 6 · head 0,01 · tail 1
- Superfície do corpo com **Opacity 0,3** para ver por dentro

> A cena de streamlines em fita, colorida por velocidade, é **o visual que vende o resultado** —
> mostra a dupla hélice (vórtice externo descendo, interno subindo). Vale para a apresentação à Valgroup.

---

# ✅ 11. VALIDAÇÃO DA BASE — CFD × analítico (RODADO)

**Rodada:** 100% da vazão · K-Omega SST steady · convergido (~6.400 iterações, ΔP plano).

| | valor |
|---|---|
| **ΔP do CFD** | **2.823,9 Pa = 28,24 mbar** |
| ΔP analítico (Stairmand, ξ=6,4) | 2.928,9 Pa = 29,29 mbar |
| **ERRO** | **3,6 %** ✅ |

### Checagem cruzada: o fator de perda ξ
Extraindo do CFD: `ξ = ΔP/(½ρv_i²) = ` **6,17**
Tabelado para Stairmand HE: **6,40**
→ **A geometria se comporta como um Stairmand de verdade.** Confirma proporções + malha + BCs.

### Margem de projeto
Limite do cliente: **40 mbar**. Obtido: **28,24 mbar** → **folga de 29%**. ✅

### Campo de pressão (Scalar Scene)
A cena de Total Pressure mostra o padrão clássico e correto:
- **Alta pressão no anel externo** (onde o vórtice desce, junto à parede)
- **Núcleo de baixa pressão no eixo** e dentro do vortex finder (mín. −251 Pa)
- Gradiente radial forte = swirl bem resolvido

> **O que isso valida de uma vez:** geometria · malha · condições de contorno · modelo físico ·
> **e o próprio dimensionamento analítico**. A base está confiável para receber as partículas.

### Próximo ponto de validação
Rodar **50%** (v_i = 7,62 m/s). Previsão: **733 Pa (7,33 mbar)**.
Se o CFD cair em **650–800 Pa**, temos **dois pontos** validados — muito mais forte que um.
