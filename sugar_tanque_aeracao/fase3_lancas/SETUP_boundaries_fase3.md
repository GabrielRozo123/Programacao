# Fase 3 · Aerador com 16 lanças — boundaries no STAR-CCM+

Arquivo: `aerador_16lancas_fluido.step` · 1 sólido · 36 faces · 19,991 m³ · mm.

## 1. Topologia (a mesma do STEP original de 3 lanças)

Cada lança é **um cilindro subtraído do fluido**, com exatamente duas faces:
a lateral (parede) e o disco da ponta (injetor). Não é um tubo — não há parede
interna nem externa, não há face de topo, nada sobressai da superfície livre.
O escoamento *dentro* da lança não é resolvido pelo CFD: o fluido entra pelo
disco da ponta com a pressão total imposta, e o ΔP interno é a álgebra
(`algebra_lancas.py`).

## 2. Inventário de faces — gabarito de seleção

| grupo | faces | como identificar | área de cada |
|---|---|---|---|
| `aerador.injetores` | 16 | discos planos, normal +z, em z = −5450 (5) e z = −4660 (11) | **3 087,6 mm²** |
| `aerador.lancas` | 16 | cilindros R = 31,35 | 1 313 842 (5) / 1 158 230 (11) mm² |
| `aerador.topo` | 1 | plano em z = +1220 | **3 193 526 mm²** |
| `aerador.parede` | 3 | casco R = 1016, cone do fundo, disco em z = −5892 | 35 672 207 / 6 812 461 / 209 117 mm² |

Os injetores são ~1 000× menores que qualquer outra face — não há como confundir.
No STAR: `Parts → Surfaces → Faces` → botão direito → **`Split by Patch`**, e depois
agrupar pelas áreas acima com `Combine`. Em seguida `Assign Parts to Regions` com
**`Create a Boundary for Each Part Surface`**.

## 3. Condições de contorno

> **Conceito confirmado pelo Marcus (14/08):** as lanças sopram **ar puro**, como na
> primeira simulação. A campanha é de três pressões de suprimento — 1, 2 e 3 kgf/cm².
> A rodada de mistura xarope+ar (VF 0,235) foi descartada.

| boundary | tipo | valores |
|---|---|---|
| `aerador.injetores` | **Stagnation Inlet** | Total Pressure **98 066,5 / 196 133 / 294 200 Pa** · **VF ar = 1,0** · xarope = 0 |
| `aerador.topo` | Pressure Outlet | 0 Pa · **Backflow Specification → Scalars = Extrapolated** |
| `aerador.lancas` | Wall | no-slip |
| `aerador.parede` | Wall | no-slip |

`Scalars = Extrapolated` não é detalhe: o `Q_ar_in` é o resultado da campanha, e ele só
fecha contra o `mx_ar_topo` se o refluxo não inventar ar que nunca passou pelas lanças.
Com `Specified`, o ar reflui também com o **Sauter Mean Diameter prescrito** — bolhas
já coalescidas voltariam renascidas no diâmetro de injeção, enviesando o histograma
justamente na cauda que interessa.

**Física:** Laminar (sem k-ε — ver §5), Gravity, EMP, S-Gamma, Ar como **Ideal Gas**
(expande ~1,9× subindo do injetor à superfície).

**Inicialização:** `VF Xarope = 1,0` (tanque cheio de xarope) e `VF Ar = 1e-3` — o
seed de ar é numérico, 0,02 m³ em 20 m³, e existe só para condicionar a equação de
momento da fase ar onde ela some (a fase fantasma que deu 4583 m/s no ejetor).

`aerador.lancas` separado de `aerador.parede` de propósito: é nele que se lê o
`Wall Shear Stress` que sustenta o argumento do arranjo (ver §4).

## 4. Arranjo — o que o novo layout entrega

| | anel interno | anel externo |
|---|---|---|
| nº de lanças | 5 | 11 |
| raio (a partir do eixo do aerador) | 375 mm | 770 mm |
| cota de descarga | z = −5450 | z = −4660 |
| submergência | 6 670 mm | 5 880 mm |
| folga mínima à parede do cone | 72,6 mm | 70,0 mm |

Descarga **escalonada**: o fundo é cônico (r = 1016 em z = −4368,6 caindo para
r = 259,5 em z = −5892), então o anel externo não pode descer tanto quanto o
interno. Cada anel para na cota mais funda que o cone permite, com 50 mm de folga
mais 40 mm de margem, verificado ponto a ponto ao longo de toda a lança.

Diâmetro: **Ø62,7 mm** — o interno de 2½" Sch40. Como a lança é um cilindro único,
esse diâmetro é ao mesmo tempo a área de escoamento no injetor e a obstrução no
domínio; adotar o interno mantém a vazão por lança coerente com a álgebra.
A obstrução total é 16 × 3 087,6 = 49 402 mm², ou 1,5 % da seção do aerador.

Diâmetro **Ø62,7 mm** (interno de 2½" Sch40) em todas as 16. Obstrução total
16 × 3 087,6 = 49 402 mm², ou 1,5 % da seção do aerador.

## 5. Margem de sopro — ⚠️ RETRATADO

Eu havia montado uma tabela de "margem de sopro" comparando o suprimento (1, 2, 3
kgf/cm²) contra a hidrostática no injetor (0,901 kgf/cm² no anel interno, 0,794 no
externo), e concluído que a 1 kgf/cm² o anel interno operaria com 9,9 % de margem e
receberia metade da pressão motriz do externo.

**Está errado.** A `Reference Density` das simulações é **1350 kg/m³** (a do xarope),
não zero. Com ρ_ref igual à densidade da fase contínua, o STAR resolve pressão
**piezométrica**: a coluna hidrostática de xarope já está embutida no campo de
referência. A pressão total imposta no injetor não compete com os 88 334 Pa de
hidrostática — ela está **por cima** deles.

Consequências:
- o ΔP motriz é o valor cheio (~98 000 Pa a 1 kgf/cm²), não 9 732 Pa;
- limite de Bernoulli sobe de ~96 para ~306 m/s, coerente com a vazão medida;
- **os dois anéis recebem praticamente a mesma pressão motriz** — não há o
  desequilíbrio 2,08× que eu havia previsto. A descarga escalonada é neutra.

Fica valendo só a conclusão geral, que a rodada confirmou por outro caminho: com a
ponta aberta de Ø62,7 mm **nada restringe o escoamento**, e a vazão é hipersensível
a qualquer diferença de pressão. Quem fixa a vazão numa planta é o soprador.

## 5b. A rodada antiga de 3 lanças NÃO é comparável — medido

`Mass Flow of Ar` nos injetores da simulação antiga (`Dominio.Aerador`, 3 kgf/cm²):

```
Dominio.Aerador: aerador.injetores    5.169364e-07 kg/s
```

**0,886 L/h.** É 0,002 % do alvo de processo de 40 m³/h — numericamente, zero.
A rodada atual das 16 lanças, a 1 kgf/cm², injeta 2,505 kg/s = 4 295 m³/h.
**Razão de 4,8 milhões de vezes.**

Isso explica por que os histogramas são tão diferentes, e mostra que a diferença
**não é do arranjo de lanças**:

| | rodada antiga (3 lanças) | rodada atual (16 lanças) |
|---|---|---|
| regime | **sistema fechado** | **injeção contínua** |
| ar entrando | 0,886 L/h (≈ 0) | 4 295 m³/h |
| o que o histograma mostra | 1,4 L de ar coalescendo sozinho por 30 s | bolhas de 1 mm repostas mais rápido do que evoluem |
| resultado | espalhado, 1–4,7 mm, SMD 2,53 mm | travado no diâmetro de injeção |

⚠️ **Não colocar os dois histogramas lado a lado.** Qualquer diferença entre eles é do
regime de injeção, não do número de lanças. O tamanho de bolha deve ser reportado pelo
argumento de **formação** (Tate: 11,8 mm numa saída aberta de Ø62,7) somado aos três
argumentos independentes de que ela não diminui depois — Grace (cisalhamento),
Weber-Ohnesorge (inércia) e a medição do próprio ejetor (0,10 mm injetado → 0,705 mm).

## 6. Por que Laminar, e não k-ε

A rodada com k-ε divergiu com `non-finite residual (Tdr of Xarope)` em
`star.keturb.KeTurbSolver`, precedida de `Turbulent viscosity limited on 9.072.257
cells`. Não é ajuste de solver — é o modelo fora do domínio de validade:

| escala | v | L | Re |
|---|---|---|---|
| jato no injetor | 0,956 m/s | 62,7 mm | **12,4** |
| tanque inteiro | 14,8 mm/s | 2,032 m | **6,2** |

Sem produção, k → 0 e ε → 0 juntos, e `ν_t = C_µ k²/ε` vira 0/0 — literalmente a
divisão por zero da mensagem. Com Laminar as duas equações somem e a rodada fica
mais rápida.

Efeito colateral coerente: os kernels de quebra turbulenta do S-Gamma ficam sem
fonte, e o modelo passa a fazer só coalescência. É exatamente o que o argumento de
Grace já dizia (λ = µ_ar/µ_xarope ≈ 2,8e−6 ⇒ Ca crítico diverge, cisalhamento não
quebra bolha nesse xarope).

## 7. Não existe regime permanente — critério de parada

Só entra ar; nada de xarope entra. O ar não sobe (17 h para bolha de 1 mm, 430 h
para 0,2 mm), então acumula. Como o domínio é rígido e o xarope é incompressível,
para o ar caber o xarope sai pelo topo. Na máquina real o **nível sobe** — representar
isso exigiria VOF ou malha móvel.

Monitor obrigatório: `V_xarope` = Volume Integral de `Volume Fraction of Xarope` na
região. Começa em 19,99 m³.

| tempo físico (a Q_ar = 40 m³/h) | xarope deslocado |
|---|---|
| 60 s | 3,3 % |
| 120 s | 6,7 % |
| 600 s | 33 % |

**Pare quando `V_xarope` < 19,0 m³ (perda de 5 %)** — algo entre 1 e 3 min de tempo
físico. É tempo de sobra: a pluma e o histograma amadurecem no primeiro minuto.

⚠️ Não usar `Phase Impermeable` no xarope. Com xarope preso e domínio rígido, o ar
também não poderia acumular — o solver seria forçado a expulsá-lo na mesma taxa em
que entra, atravessando 7 m instantaneamente. Deixar o xarope sair é o artefato
menos errado, e o `V_xarope` diz até quando ele é aceitável.

## 8. Verificação do S-Gamma — o que caiu e o que ficou

Rodada de verificação (16/08) sobre o SMD que parecia congelado em 1,000 mm.

### Medidas decisivas (sobre o Threshold `Ar_real`, VF_ar > 1e-4)

| report | valor |
|---|---|
| Minimum de Sauter Mean Diameter of Ar | **0,7283 mm** |
| Maximum de Sauter Mean Diameter of Ar | 1,000108 mm |
| Volume Average de Turbulent Dissipation Rate of Xarope | **9 644 m²/s³** |

`S-Gamma Breakup` e `S-Gamma Coalescence` estão ambos ativos na Phase Interaction
`Xarope-Ar` (verificado na árvore).

### Conclusões

1. **O SMD nunca esteve congelado.** O campo vai de 0,728 a 1,000 mm. A barra única
   do histograma era **artefato do binning manual** (Min fixado em 0,90, quando o
   mínimo real é 0,728 — a cauda ficava fora do gráfico). Usar Min = 0,70, Max = 1,02.

2. **O mecanismo dominante é QUEBRA, não coalescência.** O mínimo está 27 % abaixo do
   diâmetro de injeção; o máximo excede o valor de entrada em apenas 1e−4 mm.
   Isso inverte o que se vinha afirmando no projeto.

3. **Mas o ε que alimenta a quebra é artificial.** Potência de aeração `P/V = ρ g u_gs`:

   | | u superficial | ε físico | modelo/físico |
   |---|---|---|---|
   | vazão da rodada (13 640 m³/h) | 1,17 m/s | 11,5 W/kg | 841× |
   | vazão de projeto (40 m³/h) | 0,0034 m/s | 0,034 W/kg | 287 000× |

   Com ε = 9 644 a escala de Kolmogorov cai a 1,84 mm e o ramo inercial de quebra
   acorda. Com o ε físico de projeto seria 42,6 mm, e a bolha de 1 mm estaria 42×
   abaixo dela — quebra inercial identicamente nula.

   Duas causas artificiais somadas: vazão de ar 340× acima do projeto (ponta aberta,
   sem restrição) e k-ε operando fora de validade num escoamento laminar.

### Afirmações RETIRADAS

- ❌ *"A bolha só coalesce, nunca quebra."* O modelo mostra quebra dominante.
- ❌ *"Lei de Tate dá 11,8 mm na saída aberta."* Comprimento capilar = 2,09 mm,
  orifício 62,7 mm ⇒ **Bond = 898**. Tate exige Bond ≪ 1. O regime é jato de gás
  (We do orifício 1330–3030), não formação de bolha, e nenhuma correlação de
  formação se aplica.
- ❌ *"We_crit = 7194 por Ohnesorge."* O Oh de quebra usa a viscosidade da fase
  **dispersa** (ar, 1,85e−5), não do líquido. Oh correto ≈ 1,7e−3 e We_crit = 12.
- ❌ *"V_xarope valida alpha_medio."* São o mesmo dado
  (`V_xarope = V_malha − V_ar`). A verificação era circular.

### Afirmações que SOBREVIVEM

- ✅ A bolha não sobe: 0,17 mm/s para 1 mm, 11,6 h para os 7,1 m.
- ✅ Grace: `Ca_crit ≈ 0,054·λ^(−2/3)` ≈ **270** para λ = 2,8e−6 (Hinch & Acrivos).
  Finito, não divergente — mas inatingível. Conclusão mantida, palavra corrigida.
- ✅ Morton = 6,6e4 ⇒ regime *wobbling* inacessível, sem quebra por oscilação de forma.
- ✅ Pressão piezométrica: com ρ_ref = 1350 a hidrostática está embutida (§5).
  A Siemens recomenda a fase **leve** ou zero como Reference Density, não a pesada.
- ✅ A rodada antiga de 3 lanças não é baseline (§5b).

### Afirmação defensável para o cliente

> Na vazão real de operação a bolha **não quebra nem coalesce de forma apreciável**:
> sai do bico com o tamanho que a formação determinar e permanece assim ao longo de
> todo o percurso. Sustentado por medida (coalescência ~1e−4 mm em 0,18 s) e pela
> escala de Kolmogorov de 42,6 mm no ε de projeto, contra bolha de ~1 mm.

### Pendência de setup

A fase Ar está com **Constant Density**, não Ideal Gas. O ar deveria expandir ~1,8×
subindo de 1,825 para 1,013 bar (diâmetro ×1,217). Como está, a fração de vazio no
topo sai subestimada em ~45 %.
