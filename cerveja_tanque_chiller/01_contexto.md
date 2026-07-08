# 01 — Contexto e histórico

## Cliente e partes envolvidas
- **Cliente final:** GreyLogix (indústria; solução hidroalcoólica).
- **Contato do cliente:** Gustavo de Oliveira Gonçalves.
- **Interlocutor interno (CAEXPERTS):** Pedro Costa (alinhamento técnico com o cliente).
- **Equipe CAEXPERTS/GreyLogix no e-mail:** Marcus Castro Neves, Ricardo Barros, Humberto Junior,
  José Octávio Fernandez, José Eduardo Pauluk, Thomas Philip Starucka, Gabriel Rozo.

## O sistema físico
Tanque de **solução hidroalcoólica (70% água / 30% etanol, m/m)** resfriado por um **chiller
externo**. A solução sai do tanque, passa pelo chiller e retorna mais fria. O objetivo de
processo é manter a solução fria e **homogênea em temperatura**.

## Estudo preliminar (as-built) — JÁ ENTREGUE
- Rodado sobre a geometria **`chiller_tank_fluid_v3_1`** — tanque **grande**: cilindro
  **Ø ≈ 4,21 m**, altura ~5,5 m, **~69 m³** de fluido (medido no CAD; bocais DN150 a
  z ≈ 1,12 m e 1,64 m). Ver `referencias/v3_1_medido_69m3.png`.
- Física: transiente (Implicit Unsteady, Δt=1 s), k-ε Realizable, densidade polinomial em T,
  gravidade, paredes adiabáticas. (Detalhes em `04_metodo_cfd.md`.)
- **Resultado:** caracterizou o fenômeno — **estratificação térmica significativa** no tanque.
- **Entregue e aceito pelo cliente.** Serviu como avaliação **qualitativa** do fenômeno.

## Novo pedido do cliente (e-mail Gustavo)
Com base no preliminar (onde a estratificação foi observada), o cliente solicita um **novo
cenário**, pedindo primeiro **confirmar** que o tanque opera com:
- **3.500 L de solução** → **altura de líquido ≈ 1,53 m** (em relação ao **início da parede
  cilíndrica**).

E então avaliar:
1. **Sucção do chiller a 1,35 m** (≈ +50 cm acima da posição original) — verificar comportamento
   e se há redução da estratificação.
2. **(Se possível) Mesmo sistema + recirculação adicional** — bocal a 1,35 m **+ bomba de
   recirculação de 12 m³/h** acoplada ao tanque — verificar impacto na homogeneização.

## A questão dos DOIS tanques (importante)
O preliminar foi no tanque **grande (~69 m³, Ø4,21 m)**. O novo cenário, pela descrição
(**3.500 L ↔ 1,53 m**), corresponde a um tanque **muito menor** — o **TAG 3.500 L** (Ø ≈ 1,66 m)
do desenho da EGISA (`referencias/`). **Não são o mesmo vaso**, em nenhum nível de enchimento:

| No tanque grande v3_1 (Ø4,21 m) | Resultado |
|---|---|
| Líquido a 1,53 m | ≈ **21.300 L** (não 3.500) |
| Enchendo com 3.500 L | coluna de só **~25 cm** (não 1,53 m) |

Para **3.500 L ↔ 1,53 m**, o diâmetro tem de ser **Ø ≈ 1,66–1,71 m** → o TAG 3.500 L.

### Consequência prática
O novo estudo roda **no tanque de 3.500 L**, com **baseline próprio** (sucção a 0,85 m nesse
tanque). O resultado do v3_1 **não** serve como baseline quantitativo — é outro vaso, e a
estratificação (espessura da termoclina, tempo para estabelecer, ΔT) é bem diferente entre
69 m³ e 3,5 m³. O v3_1 permanece como o **preliminar qualitativo** que provou o fenômeno.

> **A confirmar com o cliente (via Pedro):** o novo estudo é de fato no TAG 3.500 L, e o baseline
> será refeito nesse tanque? Ver `05_pendencias_e_perguntas.md`, pergunta 1.
