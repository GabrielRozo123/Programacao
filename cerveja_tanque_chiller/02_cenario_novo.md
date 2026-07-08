# 02 — Especificação do novo cenário

## Tanque
**TAG 3.500 L** (linha Brewery Systems / EGISA, desenho 055.2254) — vertical, cilíndrico com
fundo cônico:
- Diâmetro do cilindro: **Ø 1.659 mm** (do desenho)
- Altura total: ~2.991 mm (do desenho)
- Volume de operação: **3.500 L** → altura de líquido **≈ 1,53 m** (datum = início da parede
  cilíndrica)
- Geometria do fundo (cone): **[SUPOSTO]** altura ~0,27 m — ajustado para fechar 3.500 L ↔ 1,53 m
  (o modelo paramétrico dá **3.510 L** com essa hipótese). Confirmar com o desenho/cliente.

## Os três casos a rodar
Para responder "a modificação reduz a estratificação?", os três precisam rodar **no mesmo tanque
de 3.500 L**, com as mesmas condições de processo (`03_dados_processo.md`):

| Caso | Configuração | Objetivo |
|---|---|---|
| **Baseline** | Sucção ao chiller na posição **original (0,85 m)** | Referência de estratificação neste tanque |
| **Cenário 1** | Sucção ao chiller a **1,35 m** (+50 cm) | Reposicionamento resolve? |
| **Cenário 2** | Sucção a 1,35 m **+ bomba de recirc 12 m³/h** | Recirculação homogeneíza? |

> **Nota:** o cliente citou o baseline a 0,85 m ("posição original"). No as-built (v3_1) os
> bocais estavam em outras alturas e em outro tanque — por isso o baseline é **refeito** aqui.

## Leitura física esperada (hipótese a confirmar no CFD)
- A **−5 °C o fluido é mais denso** (~935 kg/m³) do que a **+5 °C** (~930) → o frio afunda.
- **Cenário 1 (só subir a sucção):** puxa a camada mais quente do topo para o chiller e devolve
  frio embaixo. Isso pode **reorganizar / até afiar** a termoclina em vez de homogeneizar —
  sozinho, pode **não** reduzir a estratificação.
- **Cenário 2 (+ recirc):** a bomba de recirculação é a **alavanca real de homogeneização** —
  injeta momentum para quebrar a termoclina.
- Por isso rodar os três é o que blinda a resposta contra "e se piorar?".

## Objetivo declarado pelo cliente
- Cenário 1: "verificar como o sistema se comporta com essa nova geometria e se há **redução da
  estratificação** observada."
- Cenário 2: "verificar o impacto dessa recirculação adicional na **homogeneização da
  temperatura** do tanque."

## Entregável / métrica
**[A CONFIRMAR]** qual métrica o cliente quer ver (pergunta 6 em `05_...`). Candidatas:
- **ΔT topo–fundo** ao longo do tempo (índice direto de estratificação);
- **tempo até homogeneizar** (ΔT abaixo de um limite);
- **perfil vertical de temperatura** em instantes-chave.
