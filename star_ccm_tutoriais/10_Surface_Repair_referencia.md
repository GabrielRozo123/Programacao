# 10 — Surface Repair (referência): o que o diagnóstico diz e quando consertar

> Notas de leitura da documentação do STAR-CCM+ (*The Surface Repair Tool*, *Surface Repair User Interface*,
> *The Slide Out Panel*, *Changing the Parts in the Active Model*, *Repair User Settings Reference*), em palavras nossas,
> + a leitura do diagnóstico do volume de ar do projeto atmosférico (21/10/2026).

---

## 1. O que a ferramenta é

- Diagnostica e conserta **superfícies trianguladas** (e part curves). Também **reorganiza** a geometria: busca faces por
  atributo/feature e as atribui a part surfaces novos ou existentes.
- Trabalha na **representação discretizada** — as mudanças **não entram no pipeline** de malha e **se perdem quando o CAD
  de origem muda**. A Siemens recomenda consertar antes, no CAD (Repair Geometry, 3D-CAD, operações de CAD nas parts).
- Dentro da sessão tudo é reversível (undo/redo); **ao sair, as mudanças ficam permanentes**.
- Dois modos de seleção: **individual** (triângulo a triângulo, para o detalhe que não se resolve de outro jeito) e
  **patch** (pelos patches da superfície, para mudanças grandes). Pode alternar e combinar.

## 2. Interface
| onde | o quê |
|---|---|
| painel esquerdo | modos (*Repair*, *Global*, *Query*, *Organize*, *Classify*); opções do tool aparecem embaixo ao clicar nos **três pontos** ao lado do ícone (clicar no ícone executa) |
| janela gráfica | seleção, filtros, display |
| *slide out* à direita | **Surface** (diagnóstico das superfícies) · **Feature** (diagnóstico das part curves) · **Search** (filtros com predicados + tags) · **Shapes** (seleção por formas envolventes) |
| embaixo | *Reset Parts…* (troca o modelo ativo), *Close*, *Repair User Settings* (engrenagem) |

- **Close** fica desativado enquanto uma operação roda (ou até abortar).
- **Reset Parts…** troca as parts/regiões do modelo ativo — útil para diagnosticar por grupos — mas **zera** seleções,
  diagnósticos, sets, undo/redo e listas de imprint/boolean/leak path.
- **Repair User Settings** são da máquina (não da simulação): quebra da seleção inteligente (duplo clique) em feature edges /
  non-manifold / ângulo; cores de origem/destino (imprint, boolean, leak path); cor de **contato entre part surfaces**.

## 3. Diagnóstico — como ler
Os números no slide out são **clicáveis**: clicar seleciona e mostra as faces daquele problema. *Manage…* edita os limiares.

Modos de interação:
| modo | mostra |
|---|---|
| **Combined** (padrão) | per-part + part a part |
| **Per-part / Per-region** | problemas da part sozinha (ex.: part que se intercepta, faces próximas de si mesma) |
| **Part to part** | só o que vem da interação entre parts: **pierced**, **close proximity**, **duplicate faces** |

| diagnóstico | gravidade | o que fazer |
|---|---|---|
| Free edges, non-manifold edges/vertices, pierced faces | **bloqueia** volume fechado | consertar (de preferência na origem) |
| Face quality | aviso | triângulos ruins (finos, longos). Se o **Surface Remesher** vai refazer a superfície, **não consertar** |
| Face proximity | aviso | faces próximas sem estar ligadas: espessura fina, fresta ou triângulo enorme perto de outra face. Ver onde estão; se for geometria real, controlar com tamanho de superfície |
| Duplicate faces | bloqueia | apagar a duplicata |

## 4. Leitura no projeto atmosférico (STL do volume de ar gerado por script)
- 0 free edges, 0 non-manifold, 0 pierced → volume **fechado e válido**.
- *Face quality* ~5 000 → é a **triangulação de CAD**: triângulos de centenas de metros no solo (um polígono com dezenas de
  furos) e lascas de 10–50 m de altura × 0,4 m nos cilindros. É o que o Surface Remesher refaz.
- *Face proximity* ~50 → espessuras e frestas **reais** (laje das prensas 0,85 m, cobertura do terraço 0,6 m, vão
  tanque–laje 0,8 m, vigas sob a laje) somadas a triângulos enormes ao lado delas. Conferir clicando no número; resolver
  com tamanho de superfície (obstáculos 0,25/0,1 m), **não** no Repair.
- **Não consertar nada no Repair:** a "fonte" da geometria é a tabela + script. Qualquer conserto feito aqui se perde na
  próxima regeneração do STL → corrigir na tabela e regerar.
- Teste que fecha a questão: rodar só o **Surface Remesher** e repetir o diagnóstico na superfície remalhada — *face
  quality* deve ir a ~0; o que sobrar de *proximity* é geometria fina real.
