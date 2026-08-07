# Geometria — parque de tanques de solvente

Geometria CAD do caso de incêndio, gerada parametricamente por `gerar_geometria.py`.

## Base de projeto

Derivada das informações **públicas** do incêndio industrial de 04/08/2026 em Itaquaquecetuba (SP):

| Informação pública | Uso na geometria |
|---|---|
| Planta de **solventes e resinas poliéster** | Combustível de referência: tolueno (aromático, típico do setor de tintas/resinas) |
| **24 tanques de solvente** | Parque com bacias múltiplas; caso reduzido a duas bacias |
| **~31 m³ por tanque** | Tanque D = 3,0 m × H = 4,4 m → **31,1 m³** |

> O **arranjo** (posições, afastamentos, dimensões de bacia) é **representativo**, não uma
> reconstituição: o layout real da planta não é público. O que vem do caso real é a base de projeto —
> tipo de produto, volume unitário e natureza do parque. Ver a ressalva da seção 0 do `README.md`
> principal.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `gerar_geometria.py` | Script paramétrico (cadquery ≥ 2.8). Todos os parâmetros no topo. |
| `parque_tanques_completo.step` | 6 sólidos nomeados separadamente — para inspeção e modificação |
| `parque_tanques_cfd.step` | 2 sólidos: **`Fire`** e **`Air`** — pronto para o fluxo do tutorial |
| `vista_iso.svg`, `vista_lateral.svg`, `vista_planta.svg` | Prévias em wireframe |

O `parque_tanques_cfd.step` reproduz deliberadamente a **arquitetura de duas partes** do tutorial
Steckler Room (`Fire` + `Room`), de modo que o passo *Assign Parts to Regions* funciona sem
adaptação. `Air` já é o domínio com tanques, bacias e volume de fogo subtraídos.

## Sólidos do modelo completo

| Nome | Descrição |
|---|---|
| `Tank_T01_Source` | Tanque de origem do vazamento, 31,1 m³, teto cônico |
| `Tank_T02_Target` | **Tanque-alvo** — onde se mede o fluxo radiante incidente |
| `Bund_A_Fire` | Mureta da bacia de contenção do incêndio (12 × 10 m interno, h = 1,0 m) |
| `Bund_B_Target` | Mureta da bacia do tanque-alvo |
| `Fire` | Região de fonte volumétrica de calor sobre a poça (⌀ 5,0 m × 5,0 m) |
| `Domain` | Caixa do domínio, 60 × 40 × 30 m |

## Arranjo

Vento em **+x**, do tanque em chamas para o tanque-alvo (orientação conservativa).

```
        Bacia A (incêndio)                    Bacia B (alvo)
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │   ▉ T-01        ( poça ) │          │        ▉ T-02            │
   │  x=-10          x=-4,5   │          │        x=+5              │
   └──────────────────────────┘          └──────────────────────────┘
     x: -13 ────────────── -1              x: +2 ─────────────── +14

   ──────────  vento (+x)  ──────────▶
```

Poça deslocada do tanque de origem — representa **derramamento parcial** por falha de flange ou
dreno, não ruptura catastrófica. A poça de ⌀ 5,0 m ocupa parte da bacia, não sua totalidade.

## Memorial de cálculo

Saída do script (tolueno: ṁ"∞ = 0,06 kg/m²·s, kβ = 2,5 m⁻¹, ΔH_c = 40,6 MJ/kg):

| Grandeza | Valor |
|---|---|
| Volume do tanque | 31,1 m³ |
| Capacidade da bacia | 120,0 m³ (≥ maior tanque ✔) |
| Área da poça | 19,63 m² |
| Vazão mássica de combustível | 1,178 kg/s |
| **HRR** | **47,8 MW** |
| **D\*** | **4,51 m** |
| δx para D\*/δx = 10 | 0,451 m |
| δx para D\*/δx = 16 | 0,282 m |
| **Altura de chama (Heskestad)** | **12,40 m** |
| Altura do domínio | 30,0 m (> 2× chama ✔) |
| Distância fonte→alvo | 8,94 m |

### Fluxo radiante no alvo — modelo de fonte pontual

Fonte na meia-altura da chama; alvo na geratriz mais próxima do costado de T-02, à meia-altura.

| χ_r | q" no alvo |
|---|---|
| 0,15 | 7,1 kW/m² |
| 0,25 | **11,9 kW/m²** |
| 0,35 | 16,7 kW/m² |

Referência: 37,5 / 12,5 / 5 kW/m²; limiar de escalonamento em vaso atmosférico ≈ 15 kW/m².

> **O arranjo foi escolhido para que o alvo caia sobre o limiar**, na faixa de 7 a 17 kW/m² conforme a
> fração radiativa adotada. É o que torna o caso bem posto: a resposta não é trivialmente "seguro" nem
> trivialmente "condenado", e a incerteza em χ_r — que é justamente o que o CFD com radiação resolve
> melhor que o modelo integral — decide o resultado.
>
> Esses valores são o **baseline analítico** para a tabela comparativa CFD × modelo integral
> (seção 9 do `README.md` principal).

## Regeneração

```bash
pip install cadquery
python3 gerar_geometria.py
```

Parâmetros mais úteis para variar, no topo do script:

| Parâmetro | Efeito |
|---|---|
| `TANK_TARGET_POS` | Afastamento fonte→alvo — a **curva principal** do estudo |
| `POOL_D` | Tamanho da poça → HRR, D\*, altura de chama |
| `FIRE_H` | Altura da região de fonte de calor (padrão 5,0 m ≈ zona de chama contínua) |
| `BUND_LX`, `BUND_LY`, `BUND_H` | Geometria da bacia; a capacidade é verificada no relatório |

O script recalcula e imprime o memorial a cada execução, incluindo as verificações de capacidade da
bacia e de altura de domínio.

## Nota sobre `FIRE_H`

A altura da região de fogo (5,0 m) é **menor** que a altura de chama de Heskestad (12,4 m)
propositalmente: a fonte volumétrica representa a **zona de chama contínua**, onde ocorre a maior
parte da liberação de calor. A pluma acima desenvolve-se por empuxo na região `Air`, como no tutorial
Steckler. Distribuir os 47,8 MW por toda a altura de 12,4 m superestimaria a liberação de calor no
topo da chama.
