# Geometria — Tanque TAG 3.500 L

## Arquivos
| Arquivo | O que é |
|---|---|
| `gen_tank_parametrico.py` | Script cadquery que gera o domínio de fluido (cone + cilindro) parametrizado. Todas as cotas ficam no topo do arquivo. |
| `tank_chiller_base_DRAFT.step` | STEP gerado pelo script — domínio de fluido base (**sem bocais** ainda). Unidades em mm. |
| `tank_chiller_esquematico.png` | Corte r-z com o mapa de bocais (posições confirmadas vs pendentes). |

## Estado atual
- **Geometria-base validada:** cilindro Ø1.659 mm + cone de fundo, líquido a 1,53 m →
  **3.510 L** (fecha com os 3.500 L do cliente).
- **Bocais:** ainda **não** desenhados como stubs — dependem de DN e alturas (perguntas 2, 3 e 4
  em `../05_pendencias_e_perguntas.md`).

## Como gerar o `.step` final (quando as cotas chegarem)
1. Editar as variáveis no topo de `gen_tank_parametrico.py`:
   - `H_CONE`, `R_APEX` (geometria do fundo, se o desenho der o valor real);
   - alturas dos bocais (`Z_SUC_CHILLER`, `Z_RET_CHILLER`, e adicionar os da recirc);
   - DN de cada bocal (para o raio dos stubs).
2. Rodar: `python3 gen_tank_parametrico.py`
3. Conferir o volume impresso (deve bater com 3.500 L) e o esquemático.
4. Importar o `.step` no STAR-CCM+.

## Nota de método
Para um estudo de **estratificação térmica**, um domínio de fluido **limpo e paramétrico**
(cilindro + cone + stubs de bocal) é preferível ao STEP de fabricação (cheio de flanges e
acessórios que só poluem a malha).

## Referência: medição do tanque grande (preliminar)
`../referencias/v3_1_medido_69m3.png` mostra o que foi medido no `chiller_tank_fluid_v3_1.step`
(Ø4,21 m, ~69 m³) — o tanque do **preliminar**, que é outro vaso (ver `../01_contexto.md`).
