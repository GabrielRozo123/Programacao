# NOTA TÉCNICA PARCIAL — Ciclone de separação gás-sólido
### Projeto Valgroup · CAEXPERTS · *documento de acompanhamento, não é relatório final*

---

## 1. Escopo

Dimensionamento e verificação por CFD de ciclone para separação de particulado (char) de corrente
gasosa de pirólise.

| Condição de processo | valor |
|---|---|
| Vazão total | 1.900 kg/h (1.820 gás + 80 particulado) |
| Temperatura | 400 °C |
| Pressão | 1,2 bar |
| Densidade do gás | 3,946 kg/m³ · µ = 9,5e-5 Pa·s · M = 184 kg/kmol |
| Turndown exigido | 100 % e 50 % |
| **Limite de perda de carga (cliente)** | **40 mbar** |

---

## 2. Geometria dimensionada

**Ciclone Stairmand de alta eficiência**, proporções da referência [1]:

| Dimensão | Símbolo | Valor |
|---|---|---|
| Diâmetro do corpo | Dc | **290 mm** |
| Entrada (altura × largura) | a × b | 145 × 58 mm |
| Ø saída de gás (vortex finder) | De | 145 mm |
| Mergulho do vortex finder | S | 145 mm |
| Altura cilíndrica | h | 435 mm |
| **Altura total** | H | **1.160 mm** |
| Ø saída de pó | B | 108,75 mm |
| Velocidade de entrada | v_i | **15,23 m/s** |

Geometria gerada de forma **paramétrica em Dc** — qualquer redimensionamento é imediato.

---

## 3. Resultados obtidos

### 3.1 Perda de carga

| Método | ΔP (100 %) | ΔP (50 %) |
|---|---|---|
| Correlação empírica (Stairmand, ξ = 6,40) | **29,3 mbar** | 7,3 mbar |
| CFD k-ω SST (isotrópico) | 27,9 – 30,9 mbar | 6,5 mbar |
| **CFD RST anisotrópico** *(em curso)* | **~35 mbar** | — |

**Fator de perda ξ medido no CFD: 6,09 – 6,32** contra **6,40 tabelado** para Stairmand HE →
**a geometria se comporta como um Stairmand de referência.**

**Incerteza numérica medida:** ±3,8 % (três rodadas convergidas do mesmo caso).

### 3.2 Temperatura de parede — verificação de condensação

| Carga | T_parede (CFD) | Ponto de orvalho (C12–C15) | Margem |
|---|---|---|---|
| **100 %** | **381,0 °C** | ~250 °C | **+131 °C** |
| **50 %** | **367,1 °C** | ~250 °C | **+117 °C** |

> ✅ **Não há condensação em nenhum ponto do turndown, mesmo sem isolamento térmico.**
> O isolamento passa a ser decisão de eficiência energética, não de integridade do equipamento.
> *(O caso de 50 % é o governante: a residência dobra e o coeficiente de troca interno cai —
> a parede esfria. Ambos foram simulados.)*

### 3.3 Verificações físicas independentes

| Verificação | Critério | Resultado |
|---|---|---|
| Velocidade de entrada | 50–90 ft/s (faixa de projeto usual) | **15,23 m/s = 50 ft/s** — extremo conservador |
| Comprimento natural do vórtice [2] | l < altura do ciclone | **0,719 m < 1,160 m** → 296 mm de zona quiescente ✅ |
| Diâmetro de corte × PSD | d\* ≪ menor fração | **d\* = 7,6 µm** vs PSD > 20 µm |
| Velocidade tangencial máxima | v_max/v_i = 1,5–2,5 | **2,02** ✅ |
| Frequência do vórtice precessante | St = 0,3–0,6 | **St = 0,32 e 0,48** (duas medições) ✅ |
| Balanço de massa | < 1 % | **2,4e-5 %** ✅ |

---

## 4. ⚠️ Achado técnico relevante

**O modelo de turbulência isotrópico (k-ω) subestima a perda de carga.**

A literatura [3] e as boas práticas do fornecedor do software [4] estabelecem que modelos de
viscosidade turbulenta **não são adequados** para escoamento fortemente rotativo — eles
superestimam a viscosidade turbulenta e amortecem o vórtice.

Verificado neste estudo:

| Modelo | ξ | Leitura |
|---|---|---|
| k-ω transiente | 2,5 | vórtice amortecido (o modelo elimina a precessão) |
| k-ω estacionário | 6,09–6,32 | próximo do tabelado |
| **RST anisotrópico** | **~7,7** | **prevê ΔP ~20 % acima da correlação** |

> **Implicação de projeto:** o modelo de maior fidelidade indica ΔP em torno de **35 mbar**,
> contra 29 mbar da correlação empírica. **Recomenda-se dimensionar o ventilador para o valor
> superior**, ou avaliar aumento de Dc (ΔP ∝ 1/Dc⁴ — 307 mm devolveria ΔP a ~29 mbar).

---

## 5. Em andamento

| Item | Estado |
|---|---|
| Simulação transiente com modelo RST | rodando |
| **Curva de eficiência de coleta η × d** | setup concluído, aguarda campo final |
| Espessura de parede (corrosão + erosão) | não iniciado |
| Mapa de erosão | previsto |

---

## 6. Pendência com o cliente

> ⚠️ **Distribuição granulométrica (PSD) amostrada NA CORRENTE GASOSA.**
>
> A amostra disponível é do char **extraído pelo fundo** — **28 % dela está acima de 1 mm**, fração
> que **não pode ser arrastada** pela corrente a 1,03 m/s (velocidade terminal de 1,3 a 13,4 m/s).
> A PSD do material efetivamente carreado foi **estimada** aplicando o corte de arraste. A
> eficiência global depende diretamente desse dado.

---

## 7. Referências

**[1]** Stairmand, C.J. (1951). *The design and performance of cyclone separators.*
Transactions of the Institution of Chemical Engineers, 29, 356–383. — proporções de alta eficiência.

**[2]** Alexander, R.McK. (1949). *Fundamentals of cyclone design and operation.*
Proceedings of the Australasian Institute of Mining and Metallurgy, 152–153, 203–228. —
comprimento natural do vórtice.

**[3]** Hoekstra, A.J.; Derksen, J.J.; Van Den Akker, H.E.A. (1999). *An experimental and numerical
study of turbulent swirling flow in gas cyclones.* **Chemical Engineering Science**, 54(13–14),
2055–2065. **DOI: 10.1016/S0009-2509(98)00373-X**
> Comparação com medições LDA: k-ε previu **apenas o vórtice interno**, contradizendo a estrutura de
> dois vórtices medida; RNG k-ε melhorou; **o modelo de tensões de Reynolds apresentou o melhor
> comportamento**. Conclui que **é necessário pelo menos fechamento de segunda ordem**.

**[4]** Siemens Digital Industries Software. *Best Practices for Cyclone Separators.*
Simcenter STAR-CCM+ Knowledge Base, artigo **KB000040310**.
> *"An anisotropic turbulence model is required… models based on assumptions of isotropic turbulence
> are not suitable as they tend to over predict the turbulent viscosity… the Reynolds Stress
> Transport (RST) is most appropriate."*

**[5]** Siemens Digital Industries Software. *How can I calculate the efficiency in a Lagrangian
Cyclone Separator?* Knowledge Base, artigo **KB000033060**. — método de eficiência de coleta.

**[6]** *Comparison of boundary conditions for predicting the collection efficiency of cyclones.*
**Powder Technology** (Elsevier), PII **S0032591006005328**.
https://www.sciencedirect.com/science/article/abs/pii/S0032591006005328
> Compara três convenções de captura (*bottom trap* · *cone and bottom trap* · *tangential lift-off*)
> contra dados experimentais. Base para a decisão de reportar a eficiência como **faixa**.
> *(DOI a confirmar no acesso institucional.)*

**[7]** Hoffmann, A.C.; Stein, L.E. *Gas Cyclones and Swirl Tubes: Principles, Design and Operation.*
Springer. — referência geral de projeto de ciclones.

**[8]** Lapple, C.E. (1951). *Processes use many collector types.* Chemical Engineering, 58, 144–151.
— modelo de eficiência de grade.

---

## 8. Resumo em uma linha

> Ciclone Stairmand Dc = 290 mm dimensionado e verificado por CFD. **Perda de carga entre 29 e
> 35 mbar** (correlação empírica e modelo anisotrópico, respectivamente) contra limite de 40 mbar.
> **Temperatura de parede acima do ponto de orvalho com margem superior a 115 °C nos dois extremos
> de operação.** Curva de eficiência de coleta em desenvolvimento.

---

*Documento parcial de acompanhamento. Resultados sujeitos a revisão até o fechamento da simulação
transiente e da curva de eficiência.*
