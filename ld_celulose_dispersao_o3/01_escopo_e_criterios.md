# 01 — Escopo, limiares e cronograma

> Fonte: reunião de abertura com a equipe da LD Celulose, 28/09/2026.
> Anotações do Gabriel, transcritas e organizadas. Nada interpretado nesta seção.

## 1. O problema

O prédio/laboratório de geração de O₃ pode liberar ozônio para a atmosfera. O vento carrega a
nuvem **cruzando a planta**, e é preciso saber **até onde** e **em que concentração** — para
delimitar área de isolamento e posicionar sensores.

### Os três caminhos de liberação identificados

| # | caminho | regime | observação |
|---|---|---|---|
| 1 | **Exaustores do prédio** | contínuo | vazamento interno é extraído e expulso para fora |
| 2 | **PSVs** no ponto mais alto do prédio de produção | transiente (sopro) | alívio de pressão |
| 3 | **Off-gás** | contínuo | é o cenário de 3 ppm — *"perde-se o controle"* |

> ⚠️ Os caminhos 1 e 3 são **contínuos** (RANS estacionário serve). O caminho 2 é um **sopro
> transiente** — a grandeza que importa ali é o histórico de concentração (pico e dose), não
> um campo estacionário. **São modelos diferentes e precisam ser tratados separadamente.**

## 2. A escada de limiares

| concentração | o que acontece |
|---|---|
| **0,01 ppm** | limiar em que já "afeta" |
| **0,2 ppm** | isolam a área · **dispara 2 exaustores adicionais** |
| **0,5 ppm** | isolam tudo |
| **3 ppm** | cenário de off-gás — perda de controle |

### Contexto normativo (referência externa, a confirmar com a segurança do cliente)
| | |
|---|---|
| Limiar olfativo do O₃ | ~0,01 a 0,05 ppm |
| OSHA PEL (8 h TWA) | 0,1 ppm |
| ACGIH TLV | 0,05 a 0,1 ppm, conforme esforço físico |
| IDLH (NIOSH) | 5 ppm |

A escada do cliente é coerente com a prática industrial. **[A CONFIRMAR]** se os 0,2 e 0,5 ppm
são instantâneos ou médias em janela de tempo — muda o pós-processamento (campo médio vs
percentil).

## 3. Condições declaradas

| | |
|---|---|
| Temperatura ambiente | **25 °C** |
| Decaimento do O₃ | **desprezar** (conservador) |
| Pressão de operação do sistema | **10 bar** |
| Pressão de dispersão | **ambiente** |
| Dados meteorológicos | disponíveis na planta — velocidade e orientação do vento |

> **Sobre desprezar o decaimento:** a meia-vida do O₃ no ar ambiente é de horas, muito maior
> que o tempo de trânsito da nuvem pela planta (segundos a minutos). Desprezar é conservador
> **e** fisicamente correto nessa escala. Boa premissa.

## 4. Sistema de ventilação do prédio

| | |
|---|---|
| Exaustores contínuos | operam sempre — **modelados como interface de ventilação** (pedido do Marcus) |
| Exaustores de emergência | 2 unidades, disparam a **0,2 ppm** |

> Os exaustores de emergência **não são uma variação** do cenário contínuo: eles mudam a vazão
> **e** o ponto de emissão. São cenário próprio.

## 5. Entregáveis esperados

1. **Caminhos da nuvem de O₃** sob as condições de vento reais
2. **Extensão e nível de concentração** — os contornos de 0,01 / 0,2 / 0,5 / 3 ppm
3. **Delimitação de área** para isolamento
4. **Posicionamento de sensores** — a recomendação técnica que fecha o estudo

## 6. Cronograma acordado — 45 dias

| Etapa | Atividades | Duração |
|---|---|---|
| **1 — Início** | Kick off · recebimento de documentos · revisão de literatura e normas · **geração da geometria (CAD 3D)** | 7 dias |
| **2 — Análise de elegibilidade dos cenários** | Estudo dos dados meteorológicos · **definição das premissas** · análise dos cenários elegíveis · planilha de projeto · apresentação ao cliente | 5 dias |
| **3 — Configuração inicial** | Setup do **caso base (vento típico)** · convergência e independência de malha · pós · apresentação parcial | 7 dias |
| **4 — Simulações dos cenários (26)** | Rodadas · pós · análise · preenchimento da planilha · apresentação parcial | **21 dias** |
| **5 — Finalização** | Refino e consolidação · compilação · relatório final | 5 dias |

### ⚠️ Onde está o risco do cronograma
A Etapa 4 tem **21 dias para 26 cenários** — menos de um dia por cenário, incluindo
pós-processamento. Isso só fecha se duas decisões da Etapa 2 forem tomadas do jeito certo:

1. **Escalar passivo sobre campo congelado** (ver `02_metodo_e_analise_previa.md` §1)
2. **Domínio escopado ao prédio de O₃ + áreas ocupadas**, não à planta inteira (§4)

Se o estudo for montado com uma rodada completa por cenário num domínio de 1 km, 21 dias não
bastam. **Esse é o ponto a defender na apresentação da Etapa 2.**
