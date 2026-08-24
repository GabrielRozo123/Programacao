# Slide de conclusões — Valgroup · ciclone

> Substitui o slide "Conclusões do Dimensionamento" atual.
> Duas correções de conteúdo em relação à versão anterior, justificadas ao final.

---

**Título:** Conclusões do dimensionamento
**Faixa azul:** O ciclone entrega entre 92,9 % e 100 %. O que decide onde, dentro
dessa faixa, é a granulometria dos finos — e só ela.

---

## Bullets

**1. Eficiência de coleta: 92,9 % a 100 %.**
A largura da faixa vem inteiramente dos **9,14 % de fundo de peneira** (< 61 µm),
cuja distribuição interna não foi medida. **Mesmo no pior caso concebível** — todo
esse fundo em 1 µm — o estágio único entrega **92,9 %**, o equivalente a 5,7 kg/h de
char arrastado sobre 80 kg/h.

**2. A difração a laser fecha a faixa, e é o único ensaio que fecha.**

| se o fundo estiver | η global |
|---|---|
| acima de 20 µm | 100,0 % |
| em 15 µm | 99,8 % |
| em 10 µm | 98,1 % |
| em 5 µm ou abaixo | 92,9 – 93,7 % |

**3. Um segundo ciclone em série está descartado — por perda de carga, não por
eficiência.**
O ganho máximo seria de **2,3 pontos**, porque 90,9 % da massa já é coletada
integralmente no primeiro estágio. O custo inviabiliza: **39,1 mbar** contra o
limite de 40, e **41,1 mbar no cenário de gás 5 % menos denso** — acima do limite.
Se a difração indicar necessidade de coleta adicional, ela terá de vir de um
**equipamento de princípio diferente**, com outro orçamento de pressão.

**4. A massa específica do gás não é variável crítica.**
Variação de ±5 % desloca a eficiência global em **0,2 ponto** e mantém no mínimo
**48,5 % de folga** na perda de carga. Verificado em seis condições de CFD.
*Para comparação: a incerteza da granulometria dos finos vale 7 pontos.*

**5. Condensação: revestimento refletivo no corpo, isolamento apenas no trecho
inferior.**
Não é preciso isolar o ciclone inteiro. A emissividade externa governa a
temperatura de parede — uma superfície refletiva mantém a parede **45 °C mais
quente que aço oxidado, sem qualquer isolamento**. O trecho abaixo do fim do
vórtice (**8 % da área**) opera mais frio e é o único ponto que exige isolamento,
cobrindo as duas hipóteses de ponto de orvalho.

**6. Verificar a temperatura da moega na interface.**
A região abaixo do fim do vórtice mede **290,5 °C a 50 % de vazão**, contra 363,7 °C
no corpo. Se a moega não mantiver esse trecho aquecido, prever isolamento local.

---

## Frase de destaque

> O equipamento está dimensionado e com folga em pressão. A única pergunta em
> aberto é de **caracterização do material**, não de projeto.

---

## Rodapé

*Eficiência obtida por rastreamento Lagrangeano de 20 classes; queda de pressão e
temperatura de parede validadas contra correlação e balanço térmico.*

---
---

# Justificativa das duas correções *(não vai ao slide)*

## a) "Se for menor que 10 µm, a eficiência será muito baixa" — retirado

A convolução da curva medida com a PSD peneirada dá:

| fundo em | η global |
|---|---|
| 10 µm | **98,09 %** |
| 5 µm | 93,72 % |
| 1 µm | **92,93 %** |

O piso absoluto é 92,9 %, não uma eficiência baixa. A afirmação anterior
contradiz a nossa própria tabela de sensibilidade e seria confrontável pelo
cliente. A razão física de o piso ser alto: a curva CFD tem um **patamar de ~22 %
abaixo de 3 µm** (deposição turbulenta) enquanto Lapple tende a zero, e 90,9 % da
massa está acima de 61 µm de qualquer forma.

## b) "A decisão sobre segundo estágio deve vir após a medição" — reformulado

A decisão **não depende da medição**, porque o segundo estágio já está fora pelo
orçamento de pressão:

| | ΔP de 2 em série | folga vs 40 mbar |
|---|---|---|
| caso base | 39,1 mbar | 2,2 % |
| **cenário −5 % de ρ** | **41,1 mbar** | **−2,9 %** |
| envelope de turbulência (RST) | 54,4 mbar | −36 % |

E o ganho é pequeno em toda a faixa: máximo de **+2,3 pontos**, com fundo em 7 µm.

> Foi o estudo de sensibilidade a ρ que fechou este ponto. Sem ele, a folga de
> 2,2 % do caso base pareceria suficiente para manter a opção em aberto.

O que a difração a laser decide é **se é preciso coleta adicional**, e nesse caso
o equipamento terá de ser de outro princípio — não um segundo ciclone deste porte.
