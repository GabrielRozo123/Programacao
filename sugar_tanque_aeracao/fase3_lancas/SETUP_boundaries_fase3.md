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

| boundary | tipo | valores |
|---|---|---|
| `aerador.injetores` | **Stagnation Inlet** | Total Pressure 1 kgf/cm² = **98 066,5 Pa** · VF xarope 0,765 / ar 0,235 |
| `aerador.topo` | Pressure Outlet | 0 Pa · backflow VF ar = 1 |
| `aerador.lancas` | Wall | no-slip |
| `aerador.parede` | Wall | no-slip |

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

Com 130 m³/h divididos em 16 lanças: **v = 0,73 m/s** por lança, ΔP de 2,58 bar
(interno) e 2,27 bar (externo) — contra os ~30 bar do arranjo de 4 lanças, e com
tensão de cisalhamento ~4× menor na parede da lança.
