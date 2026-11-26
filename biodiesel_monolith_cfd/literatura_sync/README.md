# 📚 Literatura — Mestrado FEQ/UNICAMP

**Projeto:** Modelagem Computacional (CFD) e Avaliação Hidrodinâmica da Produção de Biodiesel via Transesterificação Heterogênea em Reator Monolítico Estruturado

**Autor:** Gabriel Rozo  
**Programa:** Pós-Graduação em Engenharia Química — FEQ/UNICAMP  
**Orientadores:** Prof. Dr. Raphael Soeiro Suppino | Prof. Dr. Dirceu Noriler  
**Período:** 2025–2027  

---

## 🗂️ Estrutura do Repositório

```
Literatura/
├── 01_Reator_Monolitico/           → Geometria, design e aplicações de reatores monolíticos
├── 02_Cinetica_Heterogenea_LHHW/   → Cinética catalítica heterogênea, mecanismos LHHW e Eley-Rideal
├── 03_CFD_Microcanais_e_Monolitos/ → Simulações CFD em microcanais e canais de monólito
├── 04_Transferencia_Calor_e_Massa/ → CHT, difusão, Nusselt, Sherwood em escoamento laminar
├── 05_Biodiesel_e_Transesterificacao/ → Processo, catalisadores heterogêneos, condições de reação
├── 06_Modelagem_e_Simulacao/       → Metodologia CFD geral, validação, Star-CCM+
│   ├── FASE1_resultados_CFD.md
│   ├── FASE2_resultados_CFD.md
│   ├── FASE3_resultados_CFD.md     ← atual
│   ├── figuras/
│   └── dados/
└── references.bib                  → Arquivo BibTeX unificado (LaTeX-ready)
```

---

## 📋 Tabela Geral de Referências

| # | Autores | Título (resumido) | Tipo | Tema | Ano | DOI/Link | Status |
|---|---------|-------------------|------|------|-----|----------|--------|
| 1 | Noureddini & Zhu | Kinetics of Transesterification of Soybean Oil | Artigo | Cinética | 1997 | [JAOCS 74:1457](https://doi.org/10.1007/s11746-997-0040-8) | ✅ Lido |
| 2 | Firth (Bath, Tese) | Biodiesel Production in Fixed-Bed Monolithic Reactors | Tese | Reator Monolítico | 2014 | [Bath Research Portal](https://researchportal.bath.ac.uk/en/studentTheses/biodiesel-production-in-fixed-bed-monolithic-reactors) | ✅ Fichado |
| 3 | Asli, Umi Aisah (Bath, Tese PhD) | Catalytic Monoliths for Biodiesel Production | Tese | Reator Monolítico | 2011 | [Bath Research Portal](https://researchportal.bath.ac.uk/en/studentTheses/catalytic-monoliths-for-biodiesel-production) | ✅ Fichado |
| 4 | Omranpour & Larimi | Modeling and Simulation of Biodiesel: FBR vs PBMR (Sci. Rep.) | Artigo | CFD + Biodiesel | 2024 | [10.1038/s41598-024-60757-5](https://doi.org/10.1038/s41598-024-60757-5) | ✅ Fichado |
| 5 | Ezzati et al. | Kinetics Models of Transesterification (Ren. Energy) | Revisão | Cinética | 2021 | [10.1016/j.renene.2020.12.055](https://doi.org/10.1016/j.renene.2020.12.055) | ✅ Fichado |
| 6 | Allain, F.; Portha, J.-F.; Girot, E.; Falk, L.; Dandeu, A.; Coupard, V. | Estimation of Kinetic Parameters and Diffusion Coefficients — Triolein/MeOH/ZnAl₂O₄ | Artigo | Cinética | **2016** | [CEJ 283:833–845](https://doi.org/10.1016/j.cej.2015.07.075) | ⚠️ Superada |
| 7 | Subramaniam, K. et al. | Enhancing Biodiesel Production: A Review of Microchannel Reactor Technologies | Revisão | CFD + Microcanais | 2024 | [10.3390/en17071652](https://doi.org/10.3390/en17071652) | ✅ Fichado |
| 8 | Mohd Laziz, A. et al. | Rapid Production of Biodiesel in a Microchannel Reactor at Room Temperature (CES) | Artigo | CFD | 2020 | [10.1016/j.ces.2020.115532](https://doi.org/10.1016/j.ces.2020.115532) | ✅ Fichado |
| 9 | Melo, V. M. (FEQ, Dissertação) | Metanólise de óleo de soja com CaO suportado em biochar | Dissertação | Cinética CaO | 2023 | — | ⭐ Ref. principal |
| 10 | Fonseca, R. V. S. (FEQ, Dissertação) | Transesterificação etílica com CaO e CaO/Al₂O₃ | Dissertação | Difusividade no poro | 2026 | — | ✅ Lido |

**Legenda de Status:**
- ✅ Lido e fichado
- 📖 Em leitura
- 🔲 Na fila
- ⭐ Referência-chave da dissertação
- ⚠️ Usada em fase anterior, substituída por dado próprio
- ❌ Descartado (justificar no README da pasta)

> **Resolvido para a ref. 6.** Confirmado pelo PDF e pelo Crossref:
> *Chemical Engineering Journal*, **v. 283, p. 833–845, 2016**. Este README
> estava certo quanto a volume e página; o `references.bib` estava errado
> (v. 281, p. 654–664) e trazia ainda título incorreto, o ano como 2015,
> "Girot, Luc" no lugar de **Emilien Girot**, e faltavam dois autores
> (Aurélie Dandeu e Vincent Coupard). Tudo corrigido.
>
> **Resolvido para a ref. 3.** Os anos de 2015 e 2017 que constavam do
> `references.bib` estavam errados. O PDF confirma: Asli, Umi Aisah,
> *Catalytic Monoliths for Biodiesel Production*, PhD, Department of Chemical
> Engineering, University of Bath, fevereiro de 2011. As notas de geometria que
> estavam associadas a "Bath2015" (400 cpsi, SrO) pertencem a este trabalho.
> Falta obter o PDF de Firth (2014).

---

## 🧭 Mapa Conceitual do Projeto

```
REATOR MONOLÍTICO (canal representativo pseudo-2D)
        │
        ├── FASE 1: Hidrodinâmica a frio ✅ CONCLUÍDA
        │       └── Perfil de Poiseuille validado contra solução analítica
        │           Re << 1, escoamento laminar plenamente desenvolvido
        │           Comprimento de entrada hidrodinâmico desprezível
        │
        ├── FASE 2: Reação de parede com cinética de literatura ✅ SUPERADA
        │       └── Cinética de Allain (2015), ZnAl₂O₄, extrapolada
        │           Da = 0,003 → controle CINÉTICO estrito
        │           Conclusão: nesse regime o monólito não cumpre função
        │           Ver: 06_Modelagem_e_Simulacao/FASE2_resultados_CFD.md
        │
        └── FASE 3: Reação de parede com o catalisador do laboratório ✅ CONCLUÍDA
                └── Cinética de Melo (2023), CaO/biochar, 65 °C
                    Difusividade no poro de Fonseca (2026)
                    Washcoat por fator de efetividade (Thiele), η = 0,62

                    Da = 0,76 → REGIME MISTO
                    C_parede/C_bulk = 0,567
                    X_TG = 1,40 % por passe
                    δ_c medido = 324 µm (Lévêque em regime: 179 µm)

                    L_entrada,massa = 3,46 m contra canal de 50 mm → 69×
                    O canal opera permanentemente na região de entrada

                    Ver: 06_Modelagem_e_Simulacao/FASE3_resultados_CFD.md
```

### O que a Fase 3 mudou

Com a cinética do catalisador efetivamente usado no laboratório, o número de
Damköhler sobe de **0,003 para 0,76** — mais de duas ordens de grandeza. O
sistema sai do controle cinético estrito e entra em regime misto, no qual a
razão área/volume do monólito passa a ser determinante.

**É esse resultado que sustenta a escolha da configuração monolítica**, e ele só
apareceu ao substituir a cinética extrapolada da literatura pela medida no
próprio grupo.

---

## 🔧 Correções registradas

Esta seção existe para que conclusões superadas não circulem como válidas.
Três afirmações da Fase 2, que constavam de versões anteriores deste README,
foram **derrubadas** ao longo da Fase 3:

| Afirmação anterior | Situação | Por quê |
|---|---|---|
| `δ_c ≈ 22 µm` | ❌ errada por fator 10 | O valor de Lévêque em x = L é 220 µm. Erro aritmético. |
| `regime MTL` (limitado por transporte) | ❌ invertida | Da = 0,003 é controle **cinético**. Confundiu-se Sc elevado com limitação de transporte. |
| `auto-enriquecimento de MeOH na parede, Y 0,18 → 0,61` | ❌ artefato numérico | Veio de corrida com difusividades desiguais, que violava conservação de massa em 374 %. Ver Nota I. |

A causa raiz do terceiro item está documentada em
`06_Modelagem_e_Simulacao/` e, em detalhe, nas notas metodológicas do
repositório `Programacao`.

---

## 🧪 Contribuições metodológicas

Dois modos de falha silenciosa foram encontrados e documentados durante a
Fase 3. Ambos apresentam **resíduos convergidos, soma de frações mássicas igual
a 1 e fluxos de parede coerentes** — nenhum é detectável pelos indicadores que o
solver oferece por padrão.

**Nota I — Fick com difusividades desiguais não conserva massa.**
A soma dos fluxos difusivos só se anula se todas as difusividades forem iguais.
Com D_MeOH/D_TG ≈ 90, a soma das frações mássicas deriva, o solver renormaliza, e
o erro cai proporcional a Y_i — quase todo na espécie majoritária. Erro medido no
balanço do TG: **374 %**. Corrigido para 0,013 % igualando as difusividades.

**Nota II — Leitura de fração mássica em face de fronteira não é confiável.**
Três relatórios distintos (média ponderada por vazão na saída, média de
superfície na parede e sonda de linha) retornaram a composição de alimentação,
enquanto as grandezas de célula permaneceram corretas. Erro medido: **fator 19**.

Verificação cruzada que detecta os três casos, hoje padrão no projeto:

```
média volumétrica de Y_i  ==  M_i / (ρ·V)      em 5–6 algarismos
```

Texto completo: `Programacao/biodiesel_monolith_cfd/docs/notas_metodologicas_cfd_especies.md`

---

## 📌 Como Contribuir com Novas Referências

1. Adicione o PDF na pasta temática correspondente com o nome: `Autor_Ano_PalavraChave.pdf`
2. Atualize a tabela acima com os metadados
3. Adicione a entrada BibTeX no arquivo `references.bib`
4. Atualize o `README.md` da pasta temática correspondente

---

*Repositório mantido por Gabriel Rozo | FEQ/UNICAMP | 2025–2027*
