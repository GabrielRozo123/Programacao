# Seção de recomendação — Aerador com lanças (Fase 3 · Ito)

> Texto no formato do relatório, pronto para colar. Números do instante em que
> `V_xarope` atinge 19,0 m³ (perda de 5 %, critério de parada — ver §7 do setup).
> **Substituir os valores marcados ⟨…⟩ pela leitura do tempo final.**

---

## X. Distribuição do ar no aerador

A simulação com 16 lanças de descarga aberta (Ø 62,7 mm), operando a 1 kgf/cm² de
pressão de suprimento, apresenta a seguinte distribuição de ar no domínio:

| critério | volume | fração do tanque |
|---|---|---|
| xarope alcançado pelo ar (α > 0,01 %) | ⟨2,117⟩ m³ | ⟨10,6⟩ % |
| xarope efetivamente aerado (α > 1 %) | ⟨1,421⟩ m³ | ⟨7,1⟩ % |
| xarope não atingido | ⟨17,876⟩ m³ | ⟨89,4⟩ % |
| fração de vazio média no volume aerado | — | ⟨32,6⟩ % |

A transição entre as duas primeiras faixas ocupa apenas ⟨0,70⟩ m³, ou seja, **67 % do
volume alcançado já se encontra acima de 1 % de fração de vazio**. A frente de ar é
nítida, sem zona de diluição progressiva.

Esse conjunto de números caracteriza um regime de **segregação**, não de dispersão: o
ar permanece confinado em cavidades de alta fração de vazio junto às descargas, e o
restante do volume não é atingido. A visualização em escala logarítmica de fração
volumétrica confirma a leitura — observam-se cavidades coerentes com α → 1 na ponta
de cada lança, e não uma nuvem de bolhas distribuída.

## X+1. Por que o diâmetro de bolha não atinge a meta de 0,2 mm

O diâmetro da bolha neste sistema é fixado **na formação**, junto à descarga, e não
se altera de forma apreciável ao longo do percurso. Três verificações independentes
sustentam a segunda parte dessa afirmação:

| mecanismo | grandeza | valor | consequência |
|---|---|---|---|
| quebra por cisalhamento | Ca crítico (Hinch & Acrivos, λ = 2,8e−6) | ≈ 270 | inatingível |
| quebra por oscilação de forma | número de Morton | 6,6 × 10⁴ | regime *wobbling* inacessível |
| coalescência | variação medida de SMD | ~1e−4 mm | desprezível |

A escala de Kolmogorov na potência de aeração de projeto é de **42,7 mm**, contra
bolha da ordem de 1 mm — o mecanismo inercial de quebra é nulo por construção.

Quanto à formação, a descarga atual de Ø 62,7 mm opera muito acima do comprimento
capilar do xarope (2,09 mm), com **número de Bond igual a 898**. Nessa condição o
destacamento não é governado pelo diâmetro do orifício, e sim pela instabilidade de
Rayleigh-Taylor na interface, cujo comprimento de onda define o tamanho:

| | |
|---|---|
| comprimento de onda crítico `2π√(σ/ρg)` | **13,1 mm** |
| comprimento de onda mais instável `2π√(3σ/ρg)` | **22,8 mm** |

**Diâmetro de bolha esperado na descarga atual: 13 a 23 mm** — cerca de setenta vezes
a meta de 0,2 mm. Alterar a quantidade, a altura ou o arranjo das lanças **não modifica
esse valor**, pois nenhuma dessas variáveis atua sobre a formação.

## X+2. Caminho técnico para reduzir o diâmetro

O único ponto de atuação é o **diâmetro da descarga**, e ele só é eficiente sob duas
condições simultâneas.

**Condição 1 — furo abaixo do comprimento capilar.** Com furo pequeno o destacamento
volta a ser governado pela lei de Tate, `d_b = (6σd_o/ρg)^(1/3)`:

| furo | Bond | regime de formação | diâmetro de bolha |
|---|---|---|---|
| 0,2 mm | 0,01 | Tate | 1,74 mm |
| 0,5 mm | 0,06 | Tate | 2,36 mm |
| 1,0 mm | 0,23 | Tate | 2,97 mm |
| 2,0 mm | 0,91 | Tate (limite) | 3,75 mm |
| 5,0 mm | 5,7 | Rayleigh-Taylor | — |
| **62,7 mm (atual)** | **898** | **Rayleigh-Taylor** | **13 a 23 mm** |

Note-se a dependência **cúbica**: reduzir o furo de 1,0 para 0,2 mm — cinco vezes —
diminui a bolha apenas de 2,97 para 1,74 mm. Existe um **piso da ordem de 1,7 a 3 mm**
que o diâmetro do furo, isoladamente, não ultrapassa.

**Condição 2 — velocidade de jato.** Para descer abaixo desse piso é necessário sair
do regime de borbulhamento e entrar em **regime de jato**, o que ocorre acima de
`We_gás = ρ_g v² d_o / σ ≈ 2`:

| furo | velocidade de jato | vazão por furo | nº de furos para 40 m³/h |
|---|---|---|---|
| 1,0 mm | 7,4 m/s | 21 L/h | 1 903 (119 por lança) |
| 0,5 mm | 10,5 m/s | 7,4 L/h | 5 384 (336 por lança) |
| 0,2 mm | 16,6 m/s | 1,9 L/h | 21 282 (1 330 por lança) |

Na descarga atual, a velocidade de projeto é de 0,225 m/s e o `We_gás` vale **0,115** —
duas ordens de grandeza abaixo da transição. O sistema opera integralmente em
borbulhamento.

**Conclusão de projeto: furo pequeno não é suficiente; é necessário furo pequeno
associado a velocidade de jato.** Essa é a definição funcional de uma lança de
aeração do tipo *blast*, e é o que justificaria sua adoção.

## X+3. Restrição construtiva a considerar

A pressão capilar que impede a entrada do xarope num furo de 1 mm é `4σ/d` = **232 Pa**.
A pressão hidrostática na cota de descarga é de **88 334 Pa** — **380 vezes maior**.

Com o suprimento de ar interrompido, o xarope penetra nos furos e os obstrui. Qualquer
lança perfurada neste serviço exige **válvula de retenção individual por lança** ou
pressurização permanente da linha de ar. Trata-se de requisito de operação, não de
detalhe construtivo.

## X+4. Observação sobre a interpretação dos resultados

> Os diâmetros médios de Sauter aqui reportados caracterizam o **inventário de bolhas
> presente no domínio** no instante da medição. A vazão de ar efetivamente admitida
> pelas lanças é **resultado** da simulação — decorre da pressão total imposta na
> descarga e da contrapressão local — e não um dado de entrada do modelo. Os valores
> de SMD devem, portanto, ser lidos em conjunto com a vazão de ar correspondente a
> cada caso.

Registra-se ainda que, com descarga aberta, a vazão de ar é **hipersensível à pressão
de suprimento**: por não haver restrição no bocal, variações de poucos por cento na
pressão de linha alteram a vazão em ordens de grandeza. Em operação, a vazão de ar é
determinada pelo soprador, e não pela lança.

---

## Referências das grandezas empregadas

| grandeza | expressão | valor |
|---|---|---|
| comprimento capilar | `√(σ/ρg)` | 2,09 mm |
| número de Bond | `(d_o/l_c)²` | 898 (descarga atual) |
| número de Morton | `gμ⁴/(ρσ³)` | 6,6 × 10⁴ |
| escala de Kolmogorov | `(ν³/ε)^(1/4)` | 42,7 mm (ε de projeto) |
| Ca crítico (Hinch & Acrivos) | `0,054·λ^(−2/3)` | ≈ 270 |
| lei de Tate | `(6σd_o/ρg)^(1/3)` | válida para Bond ≪ 1 |
| transição para jato | `We_g = ρ_g v²d_o/σ ≈ 2` | atual: 0,115 |

Propriedades: ρ_xarope = 1350 kg/m³ · µ = 6,5 Pa·s · σ = 0,058 N/m ·
ρ_ar ≈ 2,1 kg/m³ na cota de descarga.
