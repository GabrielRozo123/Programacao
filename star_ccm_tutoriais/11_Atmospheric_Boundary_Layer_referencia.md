# 11 — Atmospheric Boundary Layer (ABL) no STAR-CCM+ (referência)

> Notas de leitura das páginas *Atmospheric Boundary Layers* (teoria) e *Atmospheric Boundary Layer Model Reference*
> (2602), em palavras nossas, + como se encaixa no estudo de dispersão da LD (16/11/2026).

## O que o modelo faz
- Modelo **opcional** do continuum que impõe nas entradas os perfis de **Richards & Hoxey** (U, k, ε em função da altura) e
  **ajusta a função de parede rugosa** para ficar consistente com eles (relação entre a rugosidade do STAR e o comprimento de
  rugosidade z₀, seguindo Martinez). É a mesma lógica que montamos à mão com Field Functions, mas com a parede casada.
- Premissas de R&H: velocidade vertical nula, pressão constante, tensão de cisalhamento constante, k-ε em equilíbrio.

## Exige
Desmarcar *Auto-select recommended physics models* · Steady (ou implícito/PISO) · Gas ou Liquid · Segregated ou Coupled ·
**Constant Density** · Turbulent · RANS · **K-Epsilon → Standard K-Epsilon** (não serve com o Realizable).

## Propriedades
| propriedade | o que é | padrão |
|---|---|---|
| Reference Speed | velocidade na altura de referência | 10 m/s |
| Reference Height | altura de referência | 6 m |
| Roughness Length | z₀ do terreno | 0,01 m |
| von Karman Constant | κ | 0,42 |
Ativa a field function *Wall Direction* (normal à parede mais próxima): a altura nos perfis é a **distância à parede**.

## Cuidados do próprio manual
- Constante do k-ε recomendada pelo modelo: **Cμ = 0,013** (valor original de Richards & Hoxey, ajustado a medições de campo).
  Para o perfil de ε ficar em equilíbrio: **σε = κ² / ((C2ε − C1ε)·√Cμ) = 0,42² / (0,48 × 0,114) ≈ 3,22**.
  (Com Cμ = 0,09 o σε coerente é 1,225 — foi o que usamos na rodada manual.)
- O centro da célula junto à parede tem de ficar **acima de z₀**.
- **Desativar o Roughness Limiter** da parede rugosa. No nosso teste do domínio vazio o *Output* mostrava
  "Roughness limited on 268 738 faces on boundary: Solo" — o limitador estava cortando a rugosidade, candidato a explicar
  a perda de 15–25 % de k junto ao solo.
  - Na nossa versão o nó *Roughness Model Parameters* do contorno mostra só RplusSmooth (2,25), RplusRough (90), B (0) e C
    (0,253), sem chave do limitador; a descrição do nó é "Roughness height is limited by cell height". O método *Rough* usa
    ks efetivo = mín(ks; distância à parede da célula junto à parede). O método *Rough Displaced Origin* não tem esse corte e a
    Siemens o recomenda quando disponível, mas ainda não conferimos se ele é compatível com o modelo ABL.
  - Forma garantida de anular o limitador: **1ª célula com centro acima do ks**, ou seja, prisma único com espessura acima de
    2·ks, com folga (ks = 1,16 m → prisma de 3 m, centro a 1,5 m). Confirmar no *Output*: a linha "Roughness limited on N
    faces" deve sumir.
- Com Cμ = 0,013, os perfis feitos à mão mudam só no k: k = u*²/√0,013 (2,6× o valor com 0,09). U e ε não dependem de Cμ.

## Uso no estudo da LD
1. Repetir o teste do domínio vazio com o modelo ABL (Ref. Speed 1,9 m/s · Ref. Height 10 m · z₀ 0,03 m · κ 0,42), limitador
   desligado, e comparar o k na entrada × centro × saída com as rodadas manuais (`ld_celulose_dispersao_o3/08` §4b).
2. Se passar no critério (U ±3 %, k ±15 %), o V1 usa o modelo ABL no lugar das Field Functions.
3. Cμ: 0,013 (recomendado) dá k ~2,6× maior que com 0,09 — intensidade de turbulência mais realista para campo aberto
   (~17 % a 10 m), porém **menos conservadora** para a concentração. Registrar a escolha e fazer sensibilidade.
