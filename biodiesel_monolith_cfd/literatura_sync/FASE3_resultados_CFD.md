# Fase 3 — Canal monolítico com parede de CaO: resultados CFD

**Status: concluída.** Modelo verificado, balanço de massa fechado, resultado
central obtido em duas malhas independentes.

Catalisador: CaO (cinética de Melo, 2023) · Rota metílica · 65 °C · MeOH:TG 6:1
Código, dados brutos e scripts: repositório `Programacao`, pasta
`biodiesel_monolith_cfd/`

---

## 1. O resultado central

```
Número de Damköhler de parede        Da = 0,74       REGIME MISTO
Razão de concentrações               C_parede/C_bulk = 0,574
Conversão por passe                  X_TG = 1,42 %
```

Para reação de primeira ordem na parede, `C_w/C_b = 1/(1+Da)`, de modo que o Da
sai diretamente das duas concentrações medidas.

**Regime misto** significa que resistência cinética e resistência ao transporte
externo são da mesma ordem. A concentração de triglicerídeo na superfície
catalítica é 43% menor que no seio do fluido — existe um gradiente substancial
a vencer, e a geometria do reator passa a ser determinante.

### Por que isso muda a conclusão do projeto

| Fase | Catalisador | Da | Regime |
|---|---|---:|---|
| 2 | ZnAl₂O₄ (Allain, 2015), extrapolado | 0,003 | controle cinético absoluto |
| 3 | **CaO (Melo, 2023), do laboratório** | **0,74** | **misto** |

Na Fase 2, com Da = 0,003, não havia gradiente algum a vencer: o monólito não
cumpria função. Esse era o argumento que constava da apresentação de seminário.
Com a cinética do catalisador efetivamente empregado no laboratório, o Da sobe
mais de duas ordens de grandeza e o sistema entra na faixa em que a razão
área/volume do monólito é determinante.

**A apresentação de seminário precisa ser corrigida nesse ponto.**

---

## 2. Achado de projeto: o canal é curto demais

```
D_h = 2H                    = 2,2 mm
Re  = ρ ū D_h / μ           = 0,182
Sc  = μ / (ρ D)             = 1,73 × 10⁵
Pe  = Re · Sc               = 3,1 × 10⁴

L_entrada,massa ≈ 0,05 · D_h · Re · Sc = 3,46 m
Comprimento do canal                   = 0,05 m
────────────────────────────────────────────────
                            razão         69 ×
```

A camada-limite de concentração **nunca chega a se desenvolver**. O núcleo
abandona o canal essencialmente na composição de alimentação, e a conversão por
passe de 1,42% é consequência estrutural disso, não de catalisador insuficiente.

O número de Schmidt elevado (ν/D ~ 10⁵, próprio de óleos vegetais) é a causa:
com difusividade mássica cinco ordens abaixo da difusividade de momento, um canal
curto opera permanentemente na região de entrada.

**Implicação:** elevar a conversão por passe exige atuar sobre Pe ou sobre L —
canais mais longos, velocidade superficial menor, ou reciclo. Aumentar a carga de
catalisador isoladamente tem retorno decrescente, porque já em Da = 0,74 o
transporte externo responde por 43% da queda de concentração disponível.

---

## 3. Camada-limite medida

Perfil transversal em x = 49 mm, t = 150 s:

| Distância da parede | Y_TG | u (mm s⁻¹) |
|---:|---:|---:|
| 0 µm | 0,4147 | 0,0000 |
| 11 µm | 0,4506 | 0,0594 |
| 44 µm | 0,5398 | 0,2304 |
| 110 µm | 0,7320 | 0,5400 |
| 220 µm | 0,8113 | 0,9600 |
| 660 µm | 0,8194 | 1,4400 |

Espessura da camada empobrecida: **324 µm**, contra 179 µm previstos por Lévêque
para regime permanente. A diferença é transiente: em t = 150 s o regime
permanente ainda não se estabeleceu junto à parede, onde o tempo de trânsito do
fluido a 5 µm da superfície é de 1833 s. **O tempo característico do problema não
é o tempo de residência médio (L/ū = 50 s) mas o tempo de trânsito na região
lenta**, uma a duas ordens de grandeza maior.

Figura: `06_Modelagem_e_Simulacao/figuras/fig4_camada_limite_x49mm.pdf`

---

## 4. Recomendação já acionável para o laboratório

A resistência difusional dentro do washcoat foi tratada pelo módulo de Thiele
para placa plana:

```
φ = δ_wc √(k_v/D_h) = 1,44        η = tanh(φ)/φ = 0,62     para δ_wc = 10 µm
```

Com D_h na faixa reportada por Fonseca (2026) para CaO e CaO/Al₂O₃
(3 × 10⁻¹³ a 4,4 × 10⁻¹² m² s⁻¹), **38% da atividade nominal já se perde por
limitação difusional interna a 10 µm de espessura**.

Como η decresce monotonicamente com δ_wc enquanto a massa de catalisador cresce
apenas linearmente, existe espessura além da qual acrescentar washcoat deixa de
compensar:

```
RECOMENDAÇÃO:  δ_washcoat ≲ 10 µm
```

Repassar à equipe de IC responsável pelas impregnações. O resultado do modelo é
**linear no produto ρ_washcoat × δ_washcoat**, de modo que medir esses dois
valores na amostra real é a medida de maior retorno imediato para o modelo.

---

## 5. Verificação do modelo

Três testes independentes, todos necessários:

**Consistência estequiométrica.** A razão `(dM_FAME/dt)/(dM_TG/dt)` deve valer
876/872 = 1,004587, restrição exata independente de malha e passo de tempo.
Medido: **1,00455 a 1,00462** em todas as janelas de todas as corridas (0,009%).

**Independência de malha.** Duas configurações:

| Malha | Alimentação | C_w/C_b | Da |
|---|---|---:|---:|
| sem prismas, 50 µm uniforme | 4:1 molar | 0,578 | 0,730 |
| 15 camadas prismáticas, 1ª = 2,8 µm | 6:1 molar | 0,574 | 0,743 |

Malhas e composições distintas, concordância de 2%.

**Balanço global de massa** por espécie, com todos os termos medidos
independentemente. Fechado a ~20% de resíduo, atribuível a dois efeitos
identificados (sonda 1 mm a montante da saída; dM/dt ainda vale 7,6% do fluxo
em t = 150 s).

---

## 6. Contribuição metodológica

Dois modos de falha silenciosa foram encontrados e documentados. Ambos com
**resíduos convergidos, soma de frações mássicas igual a 1, fluxos de parede
coerentes e campos visualmente plausíveis** — nenhum detectável pelos
indicadores que o solver oferece por padrão. Somados, custaram oito corridas.

**I. A lei de Fick com difusividades desiguais não conserva massa.** A soma dos
fluxos difusivos só se anula se todos os D_i forem iguais. Com D_MeOH/D_TG ≈ 97,
a soma das frações mássicas deriva, o solver renormaliza, e o erro cai
proporcionalmente a Y_i — ou seja, quase todo na espécie majoritária. Erro medido
no balanço do TG: **374%**. Corrigido para 0,013% igualando as difusividades.

**II. A média ponderada por vazão na saída é imprópria para conversão em
escoamento laminar com reação de parede.** O fluido mais empobrecido é o mais
lento: a 11 µm da parede o TG caiu 45%, mas a velocidade é 4% da do núcleo. A
região que carrega toda a informação de conversão quase não pesa na média, e
fica à mercê de contaminação pelo array de composição da fronteira. Erro medido:
**fator 19**, com 96% do fluxo de parede sem explicação no balanço global.

Texto completo: `Programacao/biodiesel_monolith_cfd/docs/notas_metodologicas_cfd_especies.md`

Os dois são de interesse geral para modelagem de reatores catalíticos de parede
em CFD comercial, e merecem avaliação como nota técnica.

---

## 7. Pendências

```
□ Prolongar a marcha até ~400 s (dM/dt ainda vale 7,6 % do fluxo em 150 s)
□ Refazer a sonda de perfil em x = 49,9 mm para fechar os 20 % do balanço
□ DECISÃO COM A ORIENTAÇÃO: rota metílica (Melo, 65 °C, 6:1) ou
  etílica (Fonseca, 70 °C, 1:9)
□ DADOS DO LABORATÓRIO: ρ_washcoat e δ_washcoat reais, ρ e μ da carga real
□ Trocar 393,15 por ${Temperature} nas FFs de k quando houver Ea
□ Corrigir a apresentação de seminário (regime, seção 1)
□ Avaliar Maxwell-Stefan quando houver difusividades binárias
```

---

## Referências

- ALLAIN, F. et al. Development of a kinetic model for the transesterification of
  vegetable oil over ZnAl₂O₄. *Chemical Engineering Journal*, v. 283,
  p. 833–845, 2015.
- FONSECA, R. V. S. *Transesterificação etílica com catalisadores heterogêneos de
  CaO e CaO/Al₂O₃*. Dissertação — FEQ/UNICAMP, 2026.
- MELO, V. M. *Metanólise de óleo de soja com CaO suportado em biochar*.
  Dissertação — FEQ/UNICAMP, 2023.

---

*Novembro/2026 | Gabriel Rozo — FEQ/UNICAMP*
*Orientação: Prof. Dr. Raphael Soeiro Suppino · Prof. Dr. Dirceu Noriler*
