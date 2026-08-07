# Estudo de Segurança de Processos — Incêndio em Parque de Tanques de Solventes

**Simulação CFD (Simcenter STAR-CCM+) acoplada a HAZOP / LOPA**

Estudo técnico-acadêmico motivado pelo incêndio industrial de 04/08/2026 em Itaquaquecetuba (SP).

---

## 0. Ressalva importante sobre escopo e uso

Este estudo usa o incidente de Itaquaquecetuba **apenas como motivação e como referência de ordem de
grandeza do inventário** (planta de solventes e resinas poliéster, ~24 tanques de ~31 m³). Ele **não é**
e **não deve ser apresentado como**:

- uma investigação de causa raiz do evento real;
- uma reconstituição da planta, do layout ou dos procedimentos da empresa envolvida;
- qualquer afirmação sobre conformidade ou não-conformidade normativa daquela instalação.

A apuração oficial cabe ao Corpo de Bombeiros da PMESP, à CETESB e aos órgãos de fiscalização do
trabalho. Todo o modelo aqui descrito deve ser construído sobre um **parque de tanques genérico e
representativo**, com geometria fictícia e propriedades de fluidos tabeladas de literatura aberta.
Sempre que resultados forem divulgados (TCC, artigo, apresentação), essa distinção deve estar
explícita na primeira página.

---

## 1. Por que este cenário, e por que CFD

### 1.1 O gancho de segurança de processos

O que aparece no noticiário — "24 tanques de solvente, fogo difícil de controlar, empresas vizinhas
evacuadas" — é a descrição jornalística de um fenômeno que a segurança de processos chama de
**escalonamento (efeito dominó)**: um evento inicial em um equipamento gera um fluxo de calor
radiante sobre equipamentos vizinhos, que falham por sua vez, multiplicando o inventário envolvido.

É exatamente aqui que HAZOP, LOPA e CFD se conectam:

| Etapa | Pergunta | Ferramenta |
|---|---|---|
| HAZOP | O que pode dar errado no nó "parque de tanques"? | IEC 61882 / NBR IEC 61882 |
| Modelagem de consequência | Qual o fluxo radiante sobre o tanque vizinho? | **CFD — STAR-CCM+** |
| Vulnerabilidade | Em quanto tempo esse tanque falha? | Correlações de *time-to-failure* |
| LOPA | As camadas de proteção dão tempo suficiente? | IEC 61511 / NBR IEC 61511 |
| Projeto | O dilúvio/afastamento especificado é suficiente? | NFPA 15, NBR 17505, IT do CBPMESP |

O CFD entra para responder **uma pergunta que os modelos integrais não respondem bem**, e essa
delimitação é o que dá valor ao trabalho. Ver seção 2.

### 1.2 Honestidade sobre a ferramenta

O STAR-CCM+ **não é** a ferramenta padrão da indústria para modelagem de consequências. O padrão é:

- **PHAST / Safeti (DNV)** e **modelos integrais** (chama sólida, fonte pontual) — o que a CETESB
  espera ver em um Estudo de Análise de Riscos submetido no âmbito da norma P4.261;
- **FLACS-CFD (Gexcon)** — referência para dispersão e explosão em ambiente congestionado;
- **FDS (NIST)** — referência aberta para incêndio, com validação extensa;
- **KFX (Kongsberg)** — referência para jet fire e resposta térmica em offshore.

O STAR-CCM+ se justifica quando a resposta depende de **geometria e de acoplamento multifísico**, que
é onde os modelos integrais e os códigos de incêndio de propósito geral ficam fracos:

1. Parque de tanques **congestionado**, onde o modelo de chama sólida com fator de visão analítico
   erra por não enxergar sombreamento entre tanques, diques e prédios.
2. **Interação chama–spray de dilúvio** (Lagrangiano + filme líquido + radiação): quanto o sistema de
   resfriamento realmente derruba o fluxo na parede do tanque-alvo.
3. **Resposta térmica conjugada** do costado (CHT: aço + líquido + vapor) para estimar tempo até a
   falha, em vez de aplicar um critério binário de kW/m².
4. Ventilação e **posicionamento de detectores de gás** em prédio de manuseio de solventes.

**Recomendação metodológica:** rodar o modelo integral (chama sólida de Mudan/Thomas ou fonte
pontual) **primeiro**, como baseline, e usar o CFD para quantificar o desvio. Um trabalho que mostra
"o modelo integral dá X, o CFD dá Y, e a diferença vem do sombreamento/inclinação da chama" é muito
mais forte do que um que só mostra figuras coloridas.

---

## 2. Cenários candidatos e recomendação

Quatro recortes viáveis, do incidente para a simulação:

### A. Poça em bacia de contenção → radiação sobre tanque vizinho → escalonamento — **RECOMENDADO**

Perda de contenção em um tanque, formação de poça confinada no dique, ignição, e fluxo radiante sobre
o tanque adjacente. Entrega diretamente um número utilizável em LOPA: **tempo até a falha do
tanque-alvo, com e sem dilúvio**, comparado ao tempo de resposta da brigada e do Corpo de Bombeiros.

*Por que este:* mapeia 1-para-1 num nó de HAZOP, tem critério normativo claro, tem dado de validação
disponível, e o resultado é uma decisão de engenharia (afastamento, dilúvio, fireproofing) — não só
uma figura.

### B. Dispersão de nuvem de vapor inflamável (pré-ignição)

Vazamento de solvente volátil, evaporação e deriva da nuvem até fonte de ignição. Entrega os contornos
de **LII e ½ LII** (LFL / ½ LFL). Útil para classificação de áreas (NBR IEC 60079-10-1) e para
locação de detectores. Mais barato computacionalmente que A, mas depende fortemente de condições
meteorológicas assumidas.

### C. Eficácia do sistema de resfriamento por dilúvio

Sub-caso de A, mas com o spray como protagonista: multifásico Lagrangiano, evaporação das gotas,
filme líquido na parede, e verificação da densidade de aplicação da NFPA 15 (10,2 L/min·m² para
proteção de exposição de vasos) contra o que de fato chega à parede sob vento e sob arrasto térmico
da pluma. Bom recorte se você quiser algo mais "de projeto" e menos "de consequência".

### D. Pluma de fumaça e produtos de combustão sobre a vizinhança

Itaquaquecetuba tem ocupação urbana densa colada à área industrial, e houve evacuação de vizinhos.
Modelagem da pluma flutuante com camada limite atmosférica e terreno. Cientificamente interessante,
mas é o mais difícil de validar e o mais fácil de ser lido como acusação contra a empresa real —
tratar com cuidado extra, se for adiante.

**Sugestão de escopo para um trabalho único:** fazer **A** como caso central, com **C** como caso de
mitigação, e deixar **B** como estudo complementar se sobrar fôlego.

---

## 3. Amarração com o HAZOP

O CFD não substitui o HAZOP — ele quantifica um cenário que o HAZOP levantou. A tabela abaixo é o
formato de entrada sugerido; o nó é o parque de tanques atmosféricos de solvente.

| Palavra-guia | Desvio | Causas | Consequência | Salvaguardas existentes | Onde o CFD entra |
|---|---|---|---|---|---|
| MAIS | Nível alto no tanque | Falha do LT, erro de operação, transferência simultânea | Transbordo, poça no dique, nuvem inflamável | LAH/LAHH, medição redundante, procedimento | B (extensão da nuvem), A (poça resultante) |
| MENOS | Perda de contenção (costado/flange/dreno) | Corrosão, falha de junta, impacto de veículo | Poça no dique, incêndio de poça | Dique, inspeção NR-13, sistema de espuma | **A (fluxo radiante, tempo até falha)** |
| OUTRO QUE | Fonte de ignição em área classificada | Equipamento não Ex, eletricidade estática, serviço a quente | Ignição da nuvem, flash fire / incêndio de poça | Classificação de áreas, permissão de trabalho, aterramento | B (contorno de LII vs. zona classificada) |
| MAIS | Fogo externo sobre tanque adjacente | Escalonamento a partir do tanque vizinho | Falha do tanque-alvo, ampliação do inventário | Afastamento, dilúvio, alívio de emergência | **A + C (com e sem mitigação)** |
| NÃO | Sem água de resfriamento | Falha da bomba de incêndio, válvula fechada, dilúvio subdimensionado | Falha acelerada do tanque-alvo | Bomba redundante, teste periódico, ronda | C (densidade de aplicação efetiva) |

Cada linha marcada vira um caso de simulação. O resultado do CFD alimenta a coluna de consequência
com um número, e a LOPA subsequente compara o **tempo até a falha** com o **tempo de atuação** de cada
camada independente de proteção (IPL).

---

## 4. Definição do caso recomendado (A)

### 4.1 Geometria de referência (genérica)

- Parque com 6 a 8 tanques verticais cilíndricos, **V ≈ 31 m³** cada (ex.: D = 3,0 m, H = 4,4 m),
  agrupados em 2 bacias.
- Bacia de contenção dimensionada conforme NBR 17505 (verificar o critério de volume da edição
  vigente — tipicamente o maior tanque + margem). Para o caso base, poça confinada de **~15 × 15 m**.
- Afastamento entre costados como **variável paramétrica**: 1,5 m / 3 m / 6 m, para produzir uma curva
  de fluxo radiante vs. afastamento. Essa curva é o entregável mais útil do trabalho inteiro.

### 4.2 Fluido de trabalho

Usar um solvente aromático representativo do setor de tintas/resinas — **tolueno** ou **xileno** —
com propriedades de literatura aberta:

| Propriedade | Tolueno (ordem de grandeza) |
|---|---|
| Calor de combustão ΔH_c | ~40,6 MJ/kg |
| Taxa de queima assintótica ṁ"_∞ | ~0,06 kg/m²·s |
| Coeficiente kβ (Burgess–Zabetakis) | ~2,5 m⁻¹ |
| Fração radiativa χ_r | 0,20–0,35 em poça pequena; cai com o diâmetro por bloqueio de fuligem |

Taxa de queima por Burgess–Zabetakis: `ṁ" = ṁ"_∞ · (1 − e^(−kβ·D))`. Para D equivalente > 5 m, o termo
exponencial satura e `ṁ" ≈ ṁ"_∞`.

**Ordem de grandeza do caso base:** poça de 225 m² × 0,06 kg/m²·s ≈ 13,5 kg/s × 40,6 MJ/kg
≈ **550 MW** de taxa de liberação de calor teórica (HRR).

> **Cuidado técnico:** 550 MW é o valor de queima livre. Uma poça confinada em dique com paredes
> altas fica **sub-ventilada**, e a taxa real de queima cai. Se o modelo entregar 550 MW sem
> restrição de oxigênio, ele está superestimando. Vale rodar uma variante com dique alto para
> capturar isso, e discutir explicitamente.

### 4.3 Configuração de física no STAR-CCM+

**Escoamento e turbulência**
- Segregated Flow (ou Coupled Flow com AMG bem ajustado), gás ideal, **Gravity** ligado.
- RANS: Realizable k-ε Two-Layer ou SST k-ω para o caso base.
- Se houver orçamento computacional: **DES/LES** para a pluma — o *puffing* da chama de poça é
  intrinsecamente transiente, e RANS suaviza demais a intermitência. Estratégia prática: RANS para o
  estudo paramétrico de afastamento, LES para 1–2 casos de referência.
- Transiente, implícito, com passo de tempo controlado por CFL na região da chama.

**Combustão**
- *Etapa 1 (recomendada para começar)*: **fonte volumétrica de calor prescrita**, com HRR calibrado
  por Burgess–Zabetakis e distribuição espacial baseada na correlação de altura de chama de Heskestad.
  Barato, estável, e suficiente para o campo de radiação — que é o que interessa aqui.
- *Etapa 2*: combustão reativa com **FGM (Flamelet Generated Manifold)** ou PPDF/steady laminar
  flamelet para chama não pré-misturada. Eddy Break-Up é uma alternativa mais simples e mais robusta,
  porém menos fiel.

**Radiação — o ponto crítico do estudo**
- **Participating Media Radiation** com **DOM (Discrete Ordinates Method)**, ordem S4 no
  desenvolvimento e S8 nos casos finais.
- Coeficiente de absorção por **WSGGM** para CO₂/H₂O, **somado à contribuição de fuligem**.
- **Modelar fuligem** (modelo de momentos de fuligem do STAR-CCM+) ou, no mínimo, prescrever um
  coeficiente de absorção calibrado. Para solvente aromático a fuligem **domina** a emissão — e o
  manto de fumaça frio na periferia da chama **reduz** a SEP efetiva vista pelo alvo. Ignorar isso
  superestima o fluxo radiante e invalida a comparação com dado experimental.
- Superfícies do tanque-alvo com emissividade e absortividade explícitas (aço pintado ≈ 0,8–0,9;
  aço novo refletivo é bem menor — vale como caso de sensibilidade).

**Resposta térmica do alvo (CHT)**
- Região sólida para o costado (aço-carbono, ~5–8 mm) com opção *thin shell*.
- Distinguir **parede molhada** (em contato com o líquido — sumidouro térmico forte, temperatura
  limitada) de **parede seca** (espaço de vapor — aquece rápido, é onde a falha começa). Essa
  distinção é o coração da análise de escalonamento em tanque atmosférico.
- Critério prático de falha da parede seca: temperatura do aço na faixa de ~400 °C, onde a tensão de
  escoamento cai substancialmente. Refinar com ASME/API 579 se o rigor exigir.

**Vento e camada limite atmosférica**
- Entrada de velocidade com perfil logarítmico ou de potência (field function), com k e ε/ω
  consistentes com o perfil.
- **Não rodar só sem vento.** A inclinação e o arrasto da chama (*flame drag*) sob vento aproximam a
  chama do alvo e podem dobrar o fluxo incidente. Matriz mínima: 0, 3 e 6 m/s, com vento apontando do
  tanque em chamas para o alvo (caso conservativo).

**Dilúvio (caso C)**
- **Lagrangian Multiphase** com two-way coupling, injetor tipo cone, distribuição de tamanho de gota
  (Rosin-Rammler), evaporação quasi-steady.
- **Fluid Film** na parede do tanque para capturar o filme de água e o resfriamento evaporativo.
- Comparar a densidade de aplicação *nominal* de projeto com a densidade *efetiva* que chega à parede
  sob vento e sob a corrente ascendente da pluma. A diferença costuma ser o achado mais interessante.

### 4.4 Malha

Critério de resolução por diâmetro característico de fogo (prática consagrada em FDS, transferível):

```
D* = ( Q̇ / (ρ∞ · c_p · T∞ · √g) )^(2/5)
```

Para Q̇ ≈ 550 MW: **D\* ≈ 12 m**. Com o critério D*/δx ≥ 16, isso dá **δx ≈ 0,75 m** na zona de chama.

- Malha poliédrica ou trimmed com refinamento em blocos:
  - zona de chama e pluma: 0,3–0,75 m
  - entorno do tanque-alvo e camada prismática no costado: 0,05–0,10 m
  - campo distante: crescimento gradual até 2–3 m
- Domínio ~120 × 120 × 80 m → **ordem de 3–6 milhões de células** no caso RANS. Viável em workstation.
- **Fazer estudo de independência de malha sobre o fluxo radiante no alvo**, não sobre temperatura de
  chama. O entregável é o fluxo; é ele que precisa convergir.

---

## 5. Critérios normativos

### 5.1 Brasil

| Norma | Aplicação neste estudo |
|---|---|
| **NR-20** (MTE) — Inflamáveis e Combustíveis | Base regulatória do estudo; exige análise de riscos, procedimentos e capacitação para instalação classe III |
| **NR-13** — Vasos, caldeiras e tanques metálicos de armazenamento | Inspeção e integridade dos tanques; entra como salvaguarda no HAZOP |
| **ABNT NBR 17505** (partes 1 a 7) — Armazenamento de líquidos inflamáveis e combustíveis | Afastamentos, diques, e a **parte 7** para proteção contra incêndio em parques de tanques estacionários. *Conferir a edição vigente das partes aplicáveis.* |
| **CETESB P4.261** — Estudos de Análise de Riscos | **A norma-chave em SP.** Define a metodologia e os critérios de aceitabilidade de risco. É contra os critérios de vulnerabilidade dela que os resultados do CFD devem ser confrontados. |
| **IT do CBPMESP** — Instruções Técnicas, incl. líquidos combustíveis e inflamáveis | Exigências prescritivas de proteção ativa e passiva no estado de SP. *Verificar numeração e requisitos na edição vigente.* |
| **ABNT NBR IEC 60079-10-1** | Classificação de áreas (gases) — amarra o cenário B ao layout |
| **ABNT NBR IEC 61511** | SIS/SIL das camadas instrumentadas identificadas na LOPA |
| **ABNT NBR IEC 61882** | Guia de aplicação do próprio HAZOP |

### 5.2 Internacionais

| Norma | Aplicação |
|---|---|
| **API 521** | Critérios de exposição a radiação térmica (referência mais citada) |
| **API 2218** | Fireproofing de estruturas e suportes |
| **API 2021** | Combate a incêndio em tanques atmosféricos |
| **NFPA 30** | Flammable and Combustible Liquids Code (base da NBR 17505) |
| **NFPA 15** | Sistemas fixos de água nebulizada — **10,2 L/min·m² (0,25 gpm/ft²)** para proteção de exposição de vasos |
| **CCPS** — *Guidelines for Evaluating the Characteristics of VCEs, Flash Fires and BLEVEs* / *Guidelines for Chemical Process Quantitative Risk Analysis* | Metodologia de consequência e de vulnerabilidade |

### 5.3 Critérios de fluxo radiante (para plotar como iso-superfícies)

| Fluxo | Significado |
|---|---|
| **37,5 kW/m²** | Dano a equipamento de processo; letalidade elevada em exposição curta |
| **12,5 kW/m²** | Ignição pilotada de madeira, fusão de tubulação plástica; limiar comumente adotado para escalonamento |
| **~5 kW/m²** | Dor em ~15–20 s; usado como contorno de limite de área/vizinhança |

Para escalonamento em vaso atmosférico, a literatura (Cozzani & Landucci) trabalha com limiar em torno
de **15 kW/m²** e com correlações de tempo até a falha do tipo:

```
ln(ttf) = −1,128 · ln(q")  −  2,667e−5 · V  +  9,877        [q" em kW/m², V em m³, ttf em s]
```

Para q" = 15 kW/m² e V = 31 m³ isso dá **ttf da ordem de 15 minutos**. Use esse número **apenas como
sanidade de ordem de grandeza** contra o resultado do CHT — não como resultado. A correlação foi
ajustada para uma faixa específica de vasos, e o valor do CFD é justamente substituí-la por um cálculo
próprio da geometria em questão.

---

## 6. Validação — não pular esta etapa

Um CFD de incêndio sem validação é uma figura bonita. Plano mínimo:

1. **Contra modelo integral.** Implementar o modelo de chama sólida (Mudan/Thomas: altura de chama,
   inclinação, SEP, fator de visão) e o modelo de fonte pontual em planilha ou Python. Comparar o
   fluxo no alvo. Diferenças esperadas e explicáveis: sombreamento entre tanques, arrasto de chama,
   bloqueio por fuligem.
2. **Contra dado experimental de poça.** Buscar dados de queima de poça de hidrocarboneto/aromático
   (heptano, tolueno) em escala intermediária, com medição de fluxo radiante a distâncias conhecidas.
   Verificar altura de chama contra a correlação de Heskestad e taxa de queima contra
   Burgess–Zabetakis.
3. **Sensibilidade obrigatória** a: modelo de fuligem/coeficiente de absorção, ordem da quadratura DOM,
   modelo de turbulência, e velocidade do vento. Se o ranking dos cenários muda com o modelo de
   fuligem, isso precisa estar no texto.

---

## 7. Entregáveis

1. Planilha de HAZOP do nó "parque de tanques", com as linhas onde o CFD entra marcadas.
2. **Curva de fluxo radiante no tanque-alvo vs. afastamento entre costados**, para 0/3/6 m/s de vento.
3. Mapas de temperatura do costado e **tempo até a falha** (parede seca), com e sem dilúvio.
4. Verificação da densidade de aplicação efetiva do dilúvio contra o critério da NFPA 15.
5. Iso-superfícies de 37,5 / 12,5 / 5 kW/m² sobrepostas ao layout — a figura que conversa direto com
   a P4.261 e com o pessoal de bombeiro industrial.
6. **Tabela comparativa CFD × modelo integral**, com discussão da diferença.
7. Nota de LOPA: tempo até a falha vs. tempo de atuação de cada IPL, e conclusão sobre suficiência.

---

## 8. Roteiro sugerido

| Fase | Conteúdo | Marco |
|---|---|---|
| 1 | Levantamento normativo, definição do parque genérico, HAZOP do nó | Planilha de HAZOP fechada |
| 2 | Modelo integral em Python/planilha (baseline) | Curva de fluxo vs. distância analítica |
| 3 | Geometria + malha + estudo de independência | Malha convergida em fluxo radiante |
| 4 | Caso base: fonte de calor prescrita + DOM + fuligem, sem vento | Primeiro campo de radiação validado |
| 5 | Matriz paramétrica: afastamento × vento | Curva principal do trabalho |
| 6 | CHT no tanque-alvo → tempo até a falha | Número para a LOPA |
| 7 | Dilúvio (Lagrangiano + fluid film) | Caso de mitigação |
| 8 | Confronto com critérios normativos, redação | Documento final |

Fases 1–4 já constituem um trabalho defensável por si só, caso o cronograma aperte. Fases 7 e 8 são
onde está o diferencial.

---

## 9. Versão enxuta (divulgação técnica / portfólio)

As seções 4 a 8 descrevem um estudo de porte de TCC. Para uma peça curta de divulgação, o escopo
abaixo entrega algo defensável em ordem de grandeza de um fim de semana, sem prometer o que não
foi feito.

### Etapa 1 — Validação: Steckler Room

Rodar o tutorial **Fire and Smoke Wizard: Steckler Room** e reproduzir os perfis de temperatura e
velocidade no vão da porta contra o dado experimental.

Referência: Steckler, K. D.; Quintiere, J. G.; Rinkinen, W. J., *Flow Induced by Fire in a
Compartment*, NBSIR 82-2520, National Bureau of Standards, 1982. Compartimento de
**2,8 × 2,8 × 2,18 m**, abertura (porta ou janela) de largura variável, queimador a gás com potência
e posição variáveis; 55 ensaios. É benchmark consagrado de CFD de incêndio (usado por FDS, FireFOAM
e outros).

O valor aqui é metodológico: **validar antes de aplicar**. Uma figura de incêndio sem essa etapa não
sustenta discussão técnica.

> **Sobre o Fire and Smoke Wizard:** ele configura o caso automaticamente, o que é conveniente e
> perigoso em igual medida. Antes de divulgar qualquer resultado, inspecionar na árvore o que o
> assistente definiu — modelo de radiação, coeficiente de absorção, tratamento de fuligem, rampa de
> HRR — e ser capaz de justificar cada escolha.

### Etapa 2 — Aplicação: poça única com um tanque-alvo

Redução deliberada do caso da seção 4: **uma** poça, **um** alvo, sem CHT, sem dilúvio, sem matriz
paramétrica completa.

| Parâmetro | Valor |
|---|---|
| Poça | ~5 m de diâmetro equivalente (≈ 19,6 m²) |
| Combustível | Tolueno (ṁ" ≈ 0,06 kg/m²·s, ΔH_c ≈ 40,6 MJ/kg) |
| HRR | ≈ **48 MW** |
| D\* | ≈ **4,5 m** |
| δx na chama | ≈ **0,3 m** (D\*/δx ≈ 15) |
| Domínio | ~40 × 40 × 25 m com blocos de refino |
| Malha | **1–2 milhões de células** |
| Casos | 2 apenas: sem vento e com vento de 5 m/s |

Física: fonte volumétrica de calor prescrita + **DOM com meio participante e fuligem**. Sem
combustão reativa, sem multifásico.

**Entregáveis (dois, só):**

1. Iso-superfícies de **37,5 / 12,5 / 5 kW/m²** sobre o layout — a figura de capa, que conversa
   direto com os critérios da CETESB P4.261 e com o pessoal de brigada.
2. **Tabela comparativa CFD × modelo de fonte pontual**, com a diferença atribuída a sombreamento e
   inclinação de chama. É este item, e não o render, que carrega o conteúdo técnico.

**O que declarar explicitamente como fora de escopo:** CHT e tempo até a falha, dilúvio,
sub-ventilação em dique, estudo de independência de malha completo. Listar as limitações é parte do
entregável — e é o que separa divulgação técnica de marketing.

---

## 10. Tutoriais do STAR-CCM+ — ordem de estudo

### Prioridade

| # | Tutorial | Conjunto | Por quê |
|---|---|---|---|
| **1** | **Fire and Smoke Wizard: Steckler Room** | Reacting Flow | Caso de incêndio completo com validação experimental disponível. Pluma flutuante, estratificação, radiação e fuligem — mesma física do incêndio de poça, em domínio pequeno e tolerante. **Ponto de partida.** |
| **2** | **Radiação em meio participante (DOM)** | Heat Transfer and Radiation | A peça mais crítica do estudo e **ausente** do conjunto Reacting Flow. É onde está o número que interessa: o fluxo no alvo. |
| **3** | Eddy Break-Up: Coal Combustion | Reacting Flow | EBU montado na mão + radiação em fornalha; mostra o que o Wizard automatizou. Mais pesado. |
| **4** | Spray Combustion: n-Dodecane | Reacting Flow | Somente se for para o caso do dilúvio: injetor, distribuição de tamanho de gota, evaporação. A mecânica transfere para spray de água. |
| — | Transferência de calor conjugada (CHT) | Heat Transfer and Radiation | Necessário apenas na fase 6 (tempo até a falha do costado). |
| — | Lagrangiano + Fluid Film | Multiphase Flow | Necessário apenas na fase 7 (dilúvio). |

### Baixa prioridade ou irrelevantes para este estudo

- **Complex Chemistry: Methane-Air Jet Flame** — chama difusiva é o regime certo, mas química
  detalhada é desproporcional quando o objetivo é o campo radiante.
- **FGM: Perfectly Premixed Combustion with Adaptive Meshing** — FGM é a fase 2 do plano, porém em
  regime **pré-misturado**, que não é o da poça (difusiva). O adaptive meshing é a única parte
  aproveitável.
- **Surface Chemistry: Methane on Platinum Oxidation** — catálise heterogênea. Sem relação.
- **Reacting Channels: Steam Methane Reforming** — reformador. Sem relação.
- **Acoustic Modal Analysis: Annular Combustor** — instabilidade termoacústica de turbina a gás.
  Sem relação.

---

## 11. Referências

### Notícias do evento (contexto)

- [Incêndio em Itaquaquecetuba atinge indústria química — TMC](https://tmc.com.br/brasil/incendio-quema-quimica-itaquaquecetuba-bombeiros/)
- [O que produzia a fábrica química que pegou fogo em Itaquaquecetuba — TMC](https://tmc.com.br/brasil/o-que-produzia-a-fabrica-de-quimica-que-pegou-fogo-em-itaquaquecetuba/)
- [Fábrica de produtos químicos pega fogo com 24 tanques de solventes — NSC Total](https://www.nsctotal.com.br/seguranca/fabrica-de-produtos-quimicos-pega-fogo-com-24-tanques-de-solventes-e-gera-evacuacao-de-empresas-em-sp)
- [SP: Incêndio atinge fábrica de produtos químicos em Itaquaquecetuba — Baixada na Web](https://baixadanaweb.wordpress.com/2026/08/04/sp-incendio-atinge-fabrica-de-produtos-quimicos-em-itaquaquecetuba/)

### Técnicas

- SFPE Handbook of Fire Protection Engineering — capítulos de incêndio de poça e de radiação térmica
- Mudan, K. S. — *Thermal radiation hazards from hydrocarbon pool fires*
- Cozzani, V.; Landucci, G. et al. — modelos de escalonamento e *time-to-failure* em vasos sob fogo
- CCPS — *Guidelines for Chemical Process Quantitative Risk Analysis*
- TNO — *Yellow Book* (Methods for the calculation of physical effects)
- Documentação do Simcenter STAR-CCM+ — Radiation, Reacting Flow, Lagrangian Multiphase

---

*Documento de escopo. Os valores numéricos são estimativas de ordem de grandeza para dimensionamento
do estudo e devem ser recalculados com as propriedades e a geometria efetivamente adotadas.*
