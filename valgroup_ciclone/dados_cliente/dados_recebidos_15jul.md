# Dados recebidos da Valgroup (15/07/2026) — análise e reconciliação

> Lote de dados: **cromatografia do gás (GC-MS)**, **planilha Lapple dos colegas**, **relatório de
> biomassa** (já tínhamos), e **dados de temperatura de processo** (SCADA). Análise + o que muda.

## 1. Composição do gás — GC-MS do "Óleo de Pirólise" (AFK0948/25)
GC-MS **head space** (Afinko). O gás é **óleo de pirólise de r-PET vaporizado** — mistura de
**hidrocarbonetos C7–C15**, por área relativa: **alcenos > alcanos > aromáticos > cíclicos > alcinos** + álcoois.
- Picos dominantes: **1-Octeno 12,9% · 1-Noneno 12,7% · 2,4-dimetil-hexano 10,4% · o-Xileno ~10,5% ·
  2,4-dimetil-1-hepteno 5,8% · Nonano 5,4% · 1-Deceno 4,0%** … cauda pesada: undecano, dodecano,
  **naftaleno**, tetradeceno, pentadeceno (C12–C15, dilutos ~0,1–0,6% cada).
- **Massa molar média (área-ponderada, head-space) ≈ 124 g/mol** — mas o head-space (incubação 70°C)
  **subamostra os pesados**; o gás quente real é mais pesado.
- **Reconciliação com ρ:** o ρ=3,946 do cliente implica **MW≈168 (a 340°C) / 184 (a 400°C)**. O GC dá 124.
  → **MW real entre ~124 e ~184** (o gás carrega pesados que o head-space perde). Densidade fica
  **incerta: ρ ~2,7–4,0 kg/m³**. *(Menor ρ → menor ΔP → mais margem no ciclone.)*

### Implicação térmica — **ponto de orvalho** (o pedido do Lucas)
Mistura C7–C15 centrada em ~C9. A **cauda pesada (naftaleno bp 218°C; C12–C15 bp 216–268°C)** governa a
**primeira condensação**. Estimativa (a **confirmar por VLE** — DWSIM/Aspen com esses componentes):
**T_orvalho ~180–250°C a 1,2 bar** (os pesados dilutos começam ~230–250°C; o grosso condensa <150°C —
coerente com os condensadores downstream a 71/30/20°C).
- **→ Alvo de projeto:** manter a **parede do ciclone acima de ~230–250°C** (não deixar depositar os tars pesados).
- **Isso refina a discussão do Humberto:** a operação é ~340°C (item 3), o orvalho dos pesados ~230–250°C →
  **margem ~90–110°C no bulk**. Confortável, MAS os **pontos frios** (ápice do cone, parede sem isolamento)
  podem se aproximar do orvalho → o **check térmico continua valendo**, agora com **alvo numérico** (>~250°C).

## 2. Temperaturas de processo (SCADA) — a operação é ~340°C, não 400–450
Estatística dos sensores (chart TT-209):
| Sensor | Local | Média (°C) |
|---|---|---|
| **TT-209** | **Caixa de Dragagem (saída)** — provável local do ciclone | **~343** |
| TT-205 | Reator (Wi-Fi intermediária) | ~338 |
| TT-214 | Entrada do Buffer | ~312 |
| TT-213 | Saída do Buffer | ~230 |
| TT-303 | entre condensadores E-302/E-303 | ~71 |
| TT-226 | entre E-304/E-305 | ~30 |
| TT-305 | saída E-306 | ~20 |

> **Achado:** a temperatura no ponto relevante (**TT-209 ≈ 343°C**, com oscilação ~330–378°C) é **menor**
> que os 400–450°C do kick-off. Isso: (a) **aumenta ρ** um pouco (mais denso a 340 que a 400), (b) **aumenta
> a margem** ao orvalho. **Confirmar ONDE entra o ciclone** (antes/depois da caixa de dragagem) → fixa a T de projeto.

## 3. ⚠️ Reconciliação com a planilha Lapple dos colegas (análise preliminar deles)
Os colegas fizeram um dimensionamento **pelo mesmo método (Peçanha, modelo LN)** — **método igual, INPUTS
diferentes**. As discrepâncias (importantes, a resolver antes de cravar):

| Input | **Nosso** | **Colegas** | Comentário |
|---|---|---|---|
| **Vazão mássica de gás** | 720 kg/h (=800−80) | **1900 kg/h** | 🔴 **2,6× — a discrepância nº1.** Muda Q, D_c, tudo. **Confirmar!** |
| Massa específica ρ_gás | 3,946 | 3,946 | ✅ igual |
| **Viscosidade µ** | 2,5e-5 (estimativa) | **9,5e-5** | 🟡 a deles é ~4× maior; **alta** p/ vapor de HC a 400°C (típico 1,5–3e-5). Reconciliar a fonte |
| **ρ_s (partícula)** | 1500 (estimativa) | **776,8 (BULK!)** | 🟡 eles usaram a densidade **aparente/bulk** como ρ_s — **inclui vazios** → subestima a inércia. O certo é a densidade **da partícula** (>bulk; minerais ↑) |
| Alvo de projeto | v_i=15,2 → d* fino | **η=0,92 → d*=24,6µm** | filosofia diferente (eles miram 92%, corte grosso) |

### Impacto no dimensionamento (mesmo método, inputs de cada um)
| Cenário | Q (m³/h) | **D_c (mm)** | **d* (µm)** | ΔP (mbar) |
|---|---|---|---|---|
| **Nosso** (720, 2,5e-5, 1500) | 182,5 | **163** | 3,6 | 36,5 |
| **Colegas** (1900, 9,5e-5, 776,8) | 481,5 | **265** | 12,4 | 36,5* |
| só mudando a vazão → 1900 | 481,5 | 265 | 4,6 | — |
| só mudando µ → 9,5e-5 | 182,5 | 163 | 7,0 | — |

\* colegas reportam ΔP≈12,45 mbar (usam velocidade de projeto menor). A vazão (720 vs 1900) domina o **D_c**;
µ e ρ_s mexem no **d***. **Métodos convergem quando os inputs forem reconciliados.**

## 4. O que travava, agora resolvido / a confirmar
- ✅ **Composição do gás** (GC-MS) → base p/ µ, cp, k e **orvalho** (VLE offline).
- ⚠️ **Vazão mássica de gás: 800 vs 1900 kg/h** — **a confirmar (crítico)**. Muda D_c 163→265mm.
- ⚠️ **µ do gás:** reconciliar 2,5e-5 vs 9,5e-5 (calcular da composição por Wilke/Chung).
- ⚠️ **ρ_s da partícula:** não usar o bulk 776,8; medir/estimar a densidade real (minerais Ti/Si/Fe ↑; ~1500–2200?).
- ⚠️ **T de operação:** ~343°C (TT-209) vs 400°C assumido — confirmar o local do ciclone.
- ⏳ **PSD do char CARREADO** (mais fino) — ainda pendente (Marcus).
- ⏳ **T_orvalho por VLE** com a composição GC — calcular (DWSIM/Aspen/CoolProp).

## Fontes (não commitadas — só os fatos)
Cromatografia AFK0948/25 Rev.01 (Afinko, GC-MS) · Planilha "Dimensionamento de Ciclone Lapple" (colegas) ·
Relatório biomassa ComBio 3072-1/2025.0 · SCADA (TT-205/209/213/214/226/303/305).


---

# 5. ÁUDIO VALGROUP (04/08/2026) — resposta sobre a PSD do carreado

## 5.1 O que foi dito
1. A DT está na **planilha do projeto do ciclone** que eles já enviaram (~1 ano atrás),
   **primeira ou segunda aba**. ⇒ ver §3: é a "planilha Lapple dos colegas" que **já temos**.
2. Ajustaram **3 modelos de DT** e escolheram o de **maior R²**.
3. A amostra é de **dados reais do char COLETADO** — o que ficou para trás. Distribuição
   deslocada para **partículas mais grossas** que o que efetivamente passa adiante.
4. O sistema **não opera com parâmetros estacionários** o tempo todo ⇒ há variação real na PSD.
5. ⛔ **O carreado NÃO é amostrável:** só se recupera em manutenção, e vem **contaminado de
   parafina**. Só o char separado/coletado é analisável de forma confiável.
6. Ofereceram: (a) os **dados brutos** do analisador, (b) coletar material novo para análise.

## 5.2 Confirma nossa leitura, por rota independente
`dimensionamento/convolucao_eficiencia.py` já registrava que a amostra era do char extraído,
porque **28 % dela é > 1 mm**, que não pode ser arrastado a 1,03 m/s (v_terminal 1,3–13,4 m/s).
Chegamos por **velocidade terminal**; eles chegam por **procedência da amostra**.
Mesma conclusão, dois caminhos. ✅

⇒ A pendência "PSD amostrada na corrente gasosa" **fecha com um NÃO fundamentado**.
Deixa de ser item aberto e passa a ser **premissa declarada**.

## 5.3 ⚠️ O ACHADO MAIS GRAVE — o dado é PENEIRAMENTO
As faixas da PSD (**150–425 · 75–150 · 20–75 µm**) são **peneiras ASTM padrão**
(40 / 100 / 200 / 635 mesh). ⇒ análise granulométrica **por peneiramento**, que
**não resolve abaixo de ~20 µm**.

E é abaixo de 10 µm que mora **toda** a perda do ciclone (d* = 7,6 µm):

| d (µm) | 250 | 100 | 39 | 20 | **10** | **6** | **3** |
|---|---|---|---|---|---|---|---|
| η | 99,9 % | 99,4 % | 96,3 % | 87,4 % | **63,4 %** | **38,4 %** | **13,5 %** |

Pior: nossa PSD estimada **soma 100 % nas três faixas** ⇒ estamos assumindo **massa ZERO
abaixo de 20 µm**, a hipótese mais otimista possível, embutida sem estar declarada.

### Sensibilidade — `dimensionamento/sensibilidade_finos.py`
| fração < 20 µm | η_global (finos a 6 µm) |
|---|---|
| **0 % (hipótese atual)** | **99,3 %** |
| 5 % | 96,3 % |
| 10 % | 93,2 % |
| 20 % | 87,1 % |

**Amplitude de 17 pontos percentuais**, inteira dentro do que o peneiramento não mede.

> **Ajustar melhor a distribuição não resolve.** Os 3 modelos foram ajustados aos **mesmos
> pontos de peneira**, e R² sobre curva acumulada é quase cego à cauda fina (a curva é monótona
> e suave ali). Os três terão R² > 0,98 e divergirão exatamente onde a resposta mora.
> **Não é problema de ajuste — é ausência de dado.**

## 5.4 O pedido certo (e barato)
⛔ **Não** coletar material novo — é justamente o carreado que está contaminado de parafina.

✅ **Difração a laser (ou equivalente) na amostra de char que eles JÁ TÊM.**
Mesmo material, equipamento que enxerga abaixo de 20 µm. Sem coleta, sem parafina, sem parada.

**Ressalva honesta:** a amostra é o char **capturado**, cuja cauda fina já está depletada — não
entrega a PSD da alimentação. Mas entrega duas coisas de valor real:

1. **Piso para os finos.** Se o capturado tem 5 % < 20 µm, a alimentação tem **mais** (finos
   escapam preferencialmente). Mata a hipótese de zero imediatamente.
2. **Limite SUPERIOR rigoroso para η.** Convoluir com os finos do capturado dá o melhor caso
   possível. Hoje o nosso número não tem limite nenhum — é otimismo sem cota.

E se soubermos o **η(d) do separador atual**, dá para reconstruir a alimentação:
`f(d) = c(d)/η(d)` — retrocálculo clássico de classificação. ⇒ **perguntar o que existe hoje
na linha** (ciclone? cabeceira? nada?).

## 5.5 Ações
- [ ] Abrir as abas 1 e 2 da planilha do ciclone que **já temos** e conferir se é peneiramento
- [ ] Pedir os **dados brutos** do analisador (oferecidos) — e o **método**: peneira ou laser?
- [ ] Pedir **difração a laser na amostra existente** — com a justificativa da §5.3
- [ ] Perguntar **qual separador existe hoje** na linha (para o retrocálculo)
- [ ] **Entregar η(d), não só η_global.** A curva de grade independe da PSD; o número global
      passa a ser reportado como **faixa declarada**, não valor único
