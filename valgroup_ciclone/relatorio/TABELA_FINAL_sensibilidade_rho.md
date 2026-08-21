# Sensibilidade a ±5 % na massa específica do gás — RESULTADO

> Pedido do cliente (Marcus): impacto na eficiência de coleta.
> Método e memória de cálculo em `NOTA_sensibilidade_rho_gas.md`.
> Execução em `simulacao/09_RODADA_sensibilidade_rho.md`.

**Condição:** vazão mássica de gás **fixa em 1 820 kg/h**. A densidade foi variada
pela massa molar (174,8 / 184,0 / 193,2 kg/kmol), mantendo temperatura e
viscosidade — assim a variação é de composição pura e o Reynolds não muda.

**Legenda:** 🟢 medido em CFD · ⚪ projetado pela lei de escala validada.

---

## 1. Escoamento

| | **−5 %** | **base** | **+5 %** |
|---|---|---|---|
| massa específica (kg/m³) | 3,7487 | 3,9460 | 4,1433 |
| velocidade de entrada · 100 % | 14,31 m/s | 13,59 m/s | 12,95 m/s |
| velocidade de entrada · 50 % | 7,16 m/s | 6,80 m/s | 6,47 m/s |
| **queda de pressão · 100 %** | 🟢 **2 057 Pa** | 🟢 1 956 Pa | ⚪ **1 862 Pa** |
| **queda de pressão · 50 %** | ⚪ 495 Pa | 🟢 470 Pa | ⚪ 448 Pa |
| **folga contra o limite de 40 mbar** | **48,5 %** | 51,1 % | 53,4 % |
| Reynolds | 173 343 | 173 343 | 173 343 |

**O pior caso de perda de carga é o gás mais leve** — e ainda assim sobram 48,5 %
de folga. Nenhum cenário se aproxima do limite.

---

## 2. Eficiência

| | **−5 %** | **base** | **+5 %** |
|---|---|---|---|
| diâmetro de corte · 100 % | 6,67 µm | 6,84 µm | 7,01 µm |
| diâmetro de corte · 50 % | 9,65 µm | 9,90 µm | 10,14 µm |
| η da classe de 10 µm · 100 % | 🟢 **80,53 %** | 🟢 79,14 % | ⚪ 77,24 % |
| η da classe de 10 µm · 50 % | ⚪ 52,43 % | 🟢 50,49 % | ⚪ 49,30 % |
| **η GLOBAL · 100 %** | **92,9 – 100,0 %** | **92,9 – 100,0 %** | **92,9 – 100,0 %** |
| **η GLOBAL · 50 %** | **93,2 – 100,0 %** | **93,2 – 100,0 %** | **93,2 – 100,0 %** |

### A resposta ao cliente

> **A eficiência global não é sensível a ±5 % na massa específica do gás.**
> A variação máxima é de **0,2 ponto percentual** — cerca de 0,15 kg/h sobre os
> 80 kg/h de particulado.
>
> A razão: **90,9 % da massa do char está acima de 61 µm**, faixa em que o ciclone
> coleta 100 % nos três cenários. Só os 9,1 % de fundo de peneira reagem a ρ, e
> mesmo neles o efeito é pequeno porque o corte se desloca apenas **±2,5 %**
> (a dependência é de raiz quadrada: `d* ∝ √ρ`).
>
> Para comparação, a incerteza da **granulometria dos finos** vale **7 pontos** —
> trinta e cinco vezes mais. A massa específica não é variável crítica deste
> projeto; a distribuição abaixo de 61 µm é.

---

## 3. Como o resultado foi obtido, e por que é confiável

A vazão mássica é fixa, então `v_i ∝ 1/ρ` e `Re = ṁD/(Aµ)` **não depende de ρ**.
Com o Reynolds invariante, o campo adimensional é o mesmo nos três cenários — muda
só a escala de velocidade. A curva de eficiência não muda de forma: **desliza em
diâmetro**, pela equivalência do número de Stokes.

Isso foi **verificado em CFD**, não assumido:

| verificação | previsto | medido | erro |
|---|---|---|---|
| **ΔP a 100 %, cenário −5 %** | 2 058,5 Pa | **2 057,19 Pa** | **0,06 %** |
| **coeficiente de perda ξ** | 5,364 *(da base)* | **5,360** | **0,07 %** |
| **η(10 µm), cenário −5 %** | 80,31 % | **80,53 ± 0,22 %** | **1 σ** |

O ξ concordar em 0,07 % é a prova direta da similaridade de Reynolds — é o que
autoriza projetar o cenário +5 % em vez de rodá-lo.

A medição de η é a média de **três rastreamentos independentes** (80,97 · 80,30 ·
80,32 %), cada um com 5 082 parcelas e **zero parcelas ativas ao final** — sem
truncamento. O espalhamento medido (σ = 0,38 pt) confere com a estatística de
contagem prevista (0,55 pt).

---

## 4. Ressalvas

**a) A especificação vale a conclusão.** Todo o resultado pressupõe **vazão mássica
fixa**. Se a variação de ρ for imposta a vazão *volumétrica* constante, a
eficiência não muda absolutamente nada (o número de Stokes fica igual), mas o
`ΔP` passa a ser proporcional a ρ e o pior caso inverte para **+5 %**. Qualquer
verificação futura precisa ser especificada em **kg/h**.

**b) Variação por temperatura é ainda menos sensível.** Aqui a densidade foi
variada por composição (massa molar), com µ constante. Se ela variar por
temperatura, µ sobe junto (~T^0,7) e os dois efeitos se opõem: `d* ∝ √(ρ·µ)`, e
o corte se move **−0,8 %** em vez de −2,5 %.

**c) Só ρ foi variado.** Numa mudança real de composição, calor específico e
condutividade térmica também se moveriam. Isolar ρ é o correto para responder à
pergunta feita, mas é uma fronteira do estudo, não uma descrição completa de uma
troca de combustível.
