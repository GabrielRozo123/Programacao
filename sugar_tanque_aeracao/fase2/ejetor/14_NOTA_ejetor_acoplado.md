# Ejetor acoplado ao aerador — verificação da entrada de ar

**Projeto:** Sugar · Aerador + Reator · Ejetor CSA01-300-000
**Análise:** CFD 3D — Simcenter STAR-CCM+
**Data:** 4 de agosto de 2026

---

## 1. O que foi feito

O ejetor foi **acoplado geometricamente** ao aerador e ao reator num único domínio de
simulação, eliminando a separação entre os dois modelos anteriores.

**Geometria.** O perfil interno do ejetor foi levantado cota a cota no CAD nativo e conferido
contra a lista de peças do desenho de conjunto: coletor 8" Sch40, ramais 4" Sch40, garganta
2" **Sch160** (Ø int. 42,8 mm) e bico de 7 furos Ø9 mm em PCD Ø27. A linha de ar é de **1/2"**
(Ø int. 15,8 mm), conforme as válvulas esfera 1/2" BSP da lista.

As três lanças anteriores foram removidas e substituídas por **quatro conjuntos ejetor+lança**,
mantida a mesma cota de descarga no aerador (6,47 m de submergência) e as proporções do CAD.
Domínio resultante: **169,4 m³**, malha de **5,16 milhões de células**, com refino local de
1,0 mm nos bicos.

**Método.** A pergunta central — *o ar consegue entrar?* — é decidida pela comparação entre a
pressão do xarope na cota da porta de ar e a pressão de suprimento do ar. Essa comparação **não
depende da modelagem de bolhas**. A análise foi portanto conduzida em regime **monofásico,
laminar e estacionário**, o que elimina as incertezas do modelo multifásico e permite verificação
cruzada com solução analítica.

O regime laminar não é uma simplificação: com µ = 6,5 Pa·s, o número de Reynolds é **37 na lança
e 36 nos furos do bico**. Não há turbulência a modelar.

---

## 2. Verificação do modelo

Quatro verificações independentes, cada uma habilitando a seguinte:

| # | Verificação | Resultado |
|---|---|---|
| 1 | Vazão imposta na entrada de xarope | **130,3 m³/h** — confere com a vazão da bomba informada |
| 2 | Velocidade nos furos do bico | **20,55 m/s** — confere com o valor geométrico (20,3 m/s) |
| 3 | Pressão na face da porta × pressão no ramal | diferença de **0,02 %** — coerência interna |
| 4 | Comparação com solução analítica de Poiseuille | CFD **13 % acima** do previsto |

A verificação **4** é a mais relevante: a solução analítica, calculada de forma totalmente
independente do CFD, prevê 23,8 bar na porta de ar. O CFD 3D devolveu 26,9 bar. A diferença de
13 % está na direção esperada — a conta analítica não inclui os efeitos de entrada, a perda na
contração 4"→2" nem a distribuição do escoamento no coletor de 7 furos.

**Dois métodos independentes convergem para o mesmo resultado.**

---

## 3. Resultados

### 3.1 O ar não entra no ponto de projeto

| | bar (man.) |
|---|---|
| Pressão do xarope na porta de ar | **26,9** |
| Pressão de suprimento do ar (1 kgf/cm²) | **0,98** |
| **Déficit** | **26,0** |

A pressão do xarope na porta é **14 vezes** a pressão do ar disponível. Nessa condição, o
escoamento na linha de ar seria no sentido inverso — xarope para dentro da tubulação de ar.

### 3.2 Reposicionar a porta de ar não resolve

A porta de ar está hoje **318 mm a montante** da contração, no trecho de 4" — onde a pressão é
máxima. Num eductor convencional ela ficaria na garganta, onde a pressão é mínima.

A simulação quantifica o ganho dessa correção:

| | bar |
|---|---|
| Pressão na porta (posição atual) | 26,9 |
| Pressão na garganta (posição correta) | 26,4 |
| **Ganho de reposicionar a porta** | **0,49** |
| Déficit a vencer | 26,0 |
| **Recuperação** | **1,9 %** |

> **A posição da porta está incorreta, mas não é a causa raiz.** A causa é a **viscosidade do
> xarope**: a 6,5 Pa·s o escoamento é laminar em todo o ejetor, a perda por atrito domina, e o
> efeito de Bernoulli — que é o princípio de funcionamento de um eductor — não se estabelece.

### 3.3 Pressão de descarga requerida da bomba

Para entregar os 130 m³/h através deste ejetor, a bomba precisa desenvolver
**26,9 bar** na descarga.

Repartição da perda:

| trecho | bar |
|---|---|
| bico — 7 furos Ø9 mm | 12,9 |
| lança — Ø62,7 mm × 7,1 m | 11,0 |
| demais trechos e hidrostática | 3,0 |

---

## 4. Interpretação

O resultado define **duas condições de operação mutuamente exclusivas**:

**(a)** A bomba desenvolve ~27 bar e entrega 130 m³/h. Nesse caso o ar **não entra**, e não há
aeração pelo ejetor.

**(b)** A bomba desenvolve uma pressão usual de processo (4 a 6 bar). Nesse caso a vazão real
é **substancialmente menor** que 130 m³/h, e a pressão na porta cai proporcionalmente.

A condição **(b)** é compatível com a observação de vácuo na linha de ar relatada pela Ito.
Vácuo na porta requer pressão local abaixo da atmosférica — o que, segundo este modelo, só
ocorre a vazões muito inferiores à de projeto.

**As duas informações não são contraditórias: elas indicam que a vazão real de operação é menor
que a de projeto.**

---

## 5. Informações necessárias para fechar a análise

| # | Informação | Por quê |
|---|---|---|
| 1 | **Curva ou pressão de descarga da bomba** (modelo/fabricante) | Define em que ponto o sistema realmente opera. A vazão foi imposta no modelo; na planta quem manda é a bomba. |
| 2 | **Vazão medida de xarope**, se houver instrumento | Confirma diretamente qual das duas condições acima é a real. |
| 3 | **Vazão de ar medida**, se houver | Permite calibrar o modelo em vez de prescrever pressão. |
| 4 | **Pressão medida na linha de ar** junto à válvula | Confirma ou refuta o vácuo observado, com número. |

---

## 6. Premissas e limitações

- Vazão de xarope **imposta** em 130 m³/h (informação Ito, 15/07). A bomba não está modelada.
- Propriedades do xarope: µ = 6,5 Pa·s, ρ = 1350 kg/m³, isotérmico. *A pressão calculada é
  independente da densidade — em regime laminar `Δp = 32µLv/D²` depende apenas da viscosidade.*
- Posição radial das quatro lanças no aerador: fileira centrada no eixo, alinhada com o maior
  eixo do tanque. O CAD de conjunto não define a orientação.
- Superfícies livres tratadas como tampa rígida (*rigid lid*); a sucção da bomba não integra o
  domínio. Não afeta os resultados apresentados, que são governados pela cabeça do ejetor e
  pela lança.
- Análise monofásica: quantifica **se** o ar entra, não o tamanho de bolha resultante. O estudo
  de bolha requer a etapa multifásica, que só faz sentido em condição na qual haja ar entrando.
