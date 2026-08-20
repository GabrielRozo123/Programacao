# 📌 ESTADO DO PROJETO — Ciclone Valgroup

> Documento de retomada. Última atualização: sexta, com o transiente RST rodando na workstation.
> Detalhes em `simulacao/05_RESULTADOS.md` e `simulacao/06_GUIA_lagrangeano_passo_a_passo.md`.

---

# 1. ✅ O QUE JÁ ESTÁ ENTREGUE E VALIDADO

## 1.1 Dimensionamento e geometria
| | |
|---|---|
| Tipo | **Stairmand HE**, **Dc = 290 mm** |
| Proporções | a=145 · b=58 · De=145 · S=145 · h=435 · **H=1160** · B=108,75 mm |
| Geometria | `ciclone_stairmand_Dc290_fluido.step` — **paramétrica em Dc**, 1 sólido, válida, 61,77 L |
| Malha | **486.990 células** · Face Validity **100 % em 1,0** · Volume Change mín 1,1e-2 |

## 1.2 ⭐ QUEDA DE PRESSÃO — **ENTREGÁVEL FECHADO**
Condição: gás **1.820 kg/h** a 400 °C / 1,2 bar · ρ=3,946 · µ=9,5e-5 · **M = 184 kg/kmol**

| Rodada | Carga | Modelo | **ΔP** | analítico | erro | **ξ** |
|---|---|---|---|---|---|---|
| R1 | 100 % | ρ const | **2.823,9 Pa** | 2.928,9 | −3,6 % | 6,17 |
| R2 | 50 % | ρ const | **642,8 Pa** | 733,2 | −12,3 % | 5,61 |
| R3 | 100 % | **+ energia** | **2.893,98 Pa** | 2.928,9 | **−1,2 %** | 6,32 |
| R4 | 50 % | **+ energia** | **652,58 Pa** | 733,2 | −11,0 % | 5,70 |
| R5 | 100 % | + energia, BC verificada | **2.787,38 Pa** | 2.928,9 | −4,8 % | 6,09 |

> **PARA O CLIENTE:**
> **ΔP(100 %) = 28,4 ± 0,6 mbar** · **ΔP(50 %) = 6,5 mbar**
> Limite Valgroup: **40 mbar** → **folga de 29 % a 100 %** e **84 % a 50 %** ✅
> **ξ medido 6,09–6,32 contra 6,40 tabelado para Stairmand HE** → a geometria se comporta como um
> Stairmand de verdade.
> **Incerteza numérica MEDIDA: ±3,8 %** (3 rodadas convergidas do mesmo caso).

## 1.3 ⭐ TEMPERATURA DE PAREDE — **ENTREGÁVEL FECHADO** (pergunta do Lucas)
| Carga | T_parede | Ponto de orvalho | **Margem** |
|---|---|---|---|
| **100 %** | **654,142 K = 381,0 °C** | ~250 °C | **+131 °C** ✅ |
| **50 %** | **640,238 K = 367,1 °C** | ~250 °C | **+117 °C** ✅ |

> ⚠️ **REVISADO.** Os valores acima são a temperatura **média** de parede. A medição do
> **mínimo** (rodada de 50 %, `Minimum of Temperature` em `Walls`) deu **290,5 °C** — 73,2 °C
> abaixo da média, no **ápice do cone**, na zona quiescente abaixo do fim do vórtice.
>
> Com a parede **nua e oxidada** (ε = 0,8) esse ponto cai a **230 °C** e **condensa** mesmo na
> hipótese otimista de orvalho (250 °C).
>
> **O isolamento voltou a ser decisão de integridade** — mas só no cone inferior, ~15 % da área
> lateral. Isolando esse trecho o ponto frio sobe a **378 °C**, cobrindo inclusive o C20 (343 °C).
> Ver `relatorio/RELATORIO_FINAL_ciclone.md` §6.1.1 e §6.3.1.
> *(O caso de 50 % é o governante: residência dobra e h_int cai — a parede esfria. Testado.)*

## 1.4 Números analíticos de apoio
| | 100 % | 50 % |
|---|---|---|
| v_i | 15,23 m/s | 7,62 m/s |
| **d\* (corte, ρ_p=1500)** | **7,6 µm** | **10,8 µm** |
| η_global estimada (convolução) | 99,3 % | 98,6 % |
| Residência do gás | **0,48 s** | 0,96 s |

## 1.5 Verificações físicas independentes feitas
| Verificação | Resultado |
|---|---|
| **Comprimento natural do vórtice** (Alexander) | 0,719 m → termina **296 mm ACIMA** da saída de pó → **`Wall` no fundo está correto**, e sobra zona quiescente (bom, reduz re-entrainment) |
| **Frequência do PVC** | f ≈ **25 Hz** → **St = 0,48** (literatura: ~0,5) ✅ |
| **Teto de vórtice livre** | **v_max ≤ 25,6 m/s** — usado para detectar spin-up |
| **Momento angular alimentado** | v·r = 1,767 m²/s (fixado pela BC) |

---

# 2. 🔄 O QUE ESTÁ RODANDO AGORA
**Transiente RST (Elliptic Blending)** na workstation da CAE, **reinicializado do zero**.

| | |
|---|---|
| Modelo | Reynolds Stress Transport · **Elliptic Blending** · Implicit Unsteady |
| Δt | 2,0e-4 s |
| Inner iterations | 10–15 |
| Estado ao sair | 0,0018 s (**9 passos**), ΔP ~11.500 Pa = **choque de inicialização** |

**Ao voltar, checar nesta ordem:**
1. **Amplitude do dente de serra** encolhendo? *(estava com razão ~0,7/passo = saudável)*
2. **v_max < 25,6 m/s**? *(alarme antecipado de spin-up)*
3. **ΔP** só depois de **0,1–0,2 s** de tempo físico
4. **PVC sustentado** (não decaindo) ⬅️ o teste que o k-ω falhou

**Aceite:** ΔP médio **2.700–3.100 Pa** · v_max **20–26 m/s** · oscilação **persistente**

---

# 3. ⏳ PENDENTE
| # | Item | Estado |
|---|---|---|
| 1 | **Curva η × d (Lagrangeano)** ⭐ *entregável principal* | setup pronto, aguarda campo bom |
| 2 | Transiente RST | rodando |
| 3 | **PSD amostrada na CORRENTE GASOSA** | ⚠️ **pendência com a Valgroup** — a amostra atual é do char extraído do fundo (28 % >1 mm, não pode ser arrastado a 1,03 m/s) |
| 4 | Espessura de parede (corrosão HCl + erosão) | não iniciado |
| 5 | Erosão (char com 21 % de minerais) | é um checkbox na fase Lagrangeana |
| 6 | Estudo de malha Trimmed × Polyhedral | opcional, Best Practices recomenda Trimmed |

## 3.1 Plano do Lagrangeano quando o campo estiver pronto
1. Congelar Flow · Energy · Turbulence · **Lagrangian NÃO congelado**
2. **`Walls → Escape`** (captura na parede) → **limite SUPERIOR**, roda em segundos
3. 8 classes: 1 · 2 · 5 · 10 · 20 · 50 · 75 · 150 µm · **0,002778 kg/s cada**
4. Depois `Walls → Rebound` em 2–3 classes → **limite INFERIOR**
5. **Entregar a FAIXA**, com as duas convenções declaradas
   *(a literatura confirma que ambas são usadas — Powder Technology, "Comparison of boundary
   conditions for predicting the collection efficiency of cyclones")*

---

# 4. 🚨 AS 18 ARMADILHAS ENCONTRADAS (a lista que vale ouro)

## Físicas / de modelagem
| # | Armadilha | Sintoma | Correção |
|---|---|---|---|
| 1 | **`outlet_dust` como Outlet** | η ≈ 1 % | **`Wall`** — o ápice está em pressão negativa; um outlet a 0 Pa **injeta 37–52 % de vazão parasita** |
| 3 | **ρ_s bulk (776,75)** | η baixa | **1.500 kg/m³** (densidade da partícula) |
| 4 | Sem **Turbulent Dispersion** | finos captados demais | ligar |
| 5 | **Ideal Gas sem Molecular Weight** | ΔP 2.824 → 381 Pa | **M = 184 kg/kmol** |
| 14 | **Restituição tangencial 0,9** | parcelas param na parede | **1,0** — a 1.250 impactos/s a perda acumula até parar |
| 15 | **`Walls` e `outlet_dust` são o MESMO TIPO** | pó quica no fundo | `Lagrangian Specification → Specify for Boundary` |
| 17 | **Curvature Correction** | **v_max = 44,3 m/s = 1,73× o vórtice livre** | desligar — cria momento angular |
| 18 | **k-ω puro** | ξ = 2,5 e **PVC morrendo** | → **RST Elliptic Blending** |

## De ferramenta (as que fazem "rodar sem produzir nada")
| # | Armadilha | Sintoma |
|---|---|---|
| 2 | Maximum Residence Time curto | parcela deletada sem aviso |
| 6 | Distribuição com `Parcel Streams = 1` | injeta **um** tamanho |
| 7 | `Track File` sem **`Boundary Sampling`** | vê trajetória, reports em zero |
| 8 | `Maximum Sub-Steps` default (20.000) | voo de 0,1 s; **piora quanto melhor a malha** |
| 10 | Track file **temporário** + `Auto-Load` off | **cena da rodada anterior para sempre** |
| 11 | `Temporary Storage Retained` off | field function sem dado no report |
| 12 | **Dois `.trk` na pasta** | causou 3 diagnósticos errados |
| 13 | **`Frozen` no solver Lagrangeano** ⬅️ o pior | tudo zero, **nenhum aviso** |
| 16 | Recomendação de IA sem verificação | sugeria **494 trilhões de células** |

---

# 5. 🧠 AS LIÇÕES DE MÉTODO
1. **Balanço de massa fechado é NECESSÁRIO, não suficiente.** Ele detecta parcela deletada, não
   física errada. Pergunte também: *"esse número é fisicamente possível?"*
2. **Controle ausente = grau de liberdade inexistente.** Quando um nó não aparece no STAR, a
   pergunta é *"por que não há escolha aqui?"*, não *"como faço aparecer?"*
3. **Mudança de parâmetro sem mudança no resultado ⇒ você não está olhando o resultado novo.**
4. **Nunca troque um componente validado para consertar um problema não diagnosticado.**
5. **Toda recomendação passa por:** conta de ordem de grandeza · confronto com a doc · teste contra
   o que já foi validado.
6. **Leia a mensagem antes de mexer no parâmetro.** Sintomas idênticos, causas diferentes.
7. **Conservação é o melhor detector de artefato.** Momento angular pegou o spin-up da CC em
   30 segundos, sem CFD nenhum.
