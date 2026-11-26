# Redação de Qualificação — projeto LaTeX

Gabriel Hernandez Rozo · FEQ/UNICAMP · Dezembro de 2026

Formatação reproduzindo o padrão da qualificação do Prof. Raphael Suppino
(2008), com citações e referências em ABNT via **biblatex-abnt**
(NBR 6023:2018 e NBR 10520:2002).

---

## Como compilar

**No Overleaf**

1. Compacte a pasta `qualificacao/` inteira e faça upload como novo projeto.
2. Em *Menu → Settings*: compilador **pdfLaTeX**, documento principal `main.tex`.
3. Compile. O Overleaf detecta o `\addbibresource` e roda o **biber** sozinho.

> **Nota sobre a bibliografia.** A primeira versão deste projeto usava
> `abntex2cite` + `abntex2-alf.bst`. O BibTeX rodava e gerava o `.bbl`, mas o
> LaTeX não reconhecia os comandos `\abntrefinfo` e `\abntnextkey` que esse
> `.bbl` contém — ou seja, o estilo `.bst` estava instalado e o pacote `.sty`
> não. Trocou-se por `biblatex-abnt`, que é mantido, independe da classe de
> documento e implementa as normas mais recentes.
>
> Comandos de citação: `\textcite{chave}` para "Autor (ano)" no meio da frase,
> e `\parencite{chave}` para "(AUTOR, ano)" entre parênteses.

Se a Unicamp tiver licença institucional do Overleaf com sincronia de GitHub,
vale conectar o repositório em vez de subir o zip — o texto passa a versionar
junto com o resto do projeto.

**Localmente**

```bash
pdflatex main
biber    main
pdflatex main
pdflatex main
```

---

## Estrutura

```
main.tex                  preâmbulo e inclusões
referencias.bib           bibliografia
figuras/                  figuras em PDF vetorial
tex/
  folharosto.tex          folha de rosto
  nomenclatura.tex        lista de símbolos
  resumo.tex              resumo e palavras-chave
  introducao.tex          introdução e objetivos
  cap1_revisao.tex        Capítulo 1 — Revisão Bibliográfica
  cap2_modelagem.tex      Capítulo 2 — Modelagem Matemática e Métodos Numéricos
  cap3_resultados.tex     Capítulo 3 — Resultados Preliminares
  cap4_cronograma.tex     Capítulo 4 — Resultados Esperados e Cronograma
```

---

## Trechos pendentes

Tudo o que ainda depende de dado experimental, de referência a confirmar ou de
decisão da orientação está marcado no texto com o comando `\pendente{...}`, que
aparece **em vermelho** no PDF compilado. Para localizar todos:

```bash
grep -rn 'pendente{' tex/
```

Para gerar a versão final, sem os marcadores, basta trocar a definição no
`main.tex`:

```latex
\newcommand{\pendente}[1]{}
```

### Lista do que falta

| Onde | O que |
|---|---|
| `folharosto.tex` | área de concentração do programa |
| `cap1_revisao.tex` §1.2 | dados quantitativos de insumos e efluentes da rota homogênea |
| `cap1_revisao.tex` §1.3 | referências sobre lixiviação de cálcio e estabilização do CaO |
| `cap1_revisao.tex` §1.4 | trabalhos que aplicaram monólitos a biodiesel (teses de Bath) |
| `cap1_revisao.tex` §1.8 | trabalhos recentes de CFD em reatores de biodiesel |
| `cap2_modelagem.tex` §2.3 | ρ e δ do washcoat medidos |
| `cap4_cronograma.tex` §4.2 | datas reais de ingresso e previsão de defesa |
| `referencias.bib` | entradas marcadas `VERIFICAR` e a lista no rodapé do arquivo |

O **Capítulo 1 é o mais curto** e é onde está o grosso do trabalho restante. A
estrutura das seções está montada e o fio condutor está escrito; o que falta é
povoar as seções de revisão com o material já reunido no repositório
`Literatura`.

---

## Sobre o texto

Este é um **rascunho para você reescrever na sua voz**, não um texto para
entregar como está. Leia cada parágrafo e ajuste o que não soar como você — a
dissertação é sua e a banca vai conversar com você sobre ela, não com o
documento.

Os números, equações e resultados estão todos verificados contra as simulações
e contra os documentos em `docs/`. O que precisa de revisão crítica é a
redação e, sobretudo, a revisão bibliográfica do Capítulo 1.

---

## Fontes do conteúdo

| Seção do texto | Origem no repositório |
|---|---|
| Cap. 2 inteiro | `docs/dissertacao_fase3_modelagem_canal_catalitico.md` |
| Cap. 3 §3.1–3.5 | idem, mais `docs/starccm_fase3_CaO_procedimento.md` |
| Cap. 3 §3.6 | `docs/notas_metodologicas_cfd_especies.md` |
| Figura 1.1 | `results/fig5_thiele_washcoat.pdf` |
| Figura 2.1 | TikZ, definida no próprio `cap2_modelagem.tex` |
| Figura 3.1 | `results/fig6_poiseuille_fase3.pdf` |
| Figura 3.2 | `results/fig4_camada_limite_x49mm.pdf` |
| Dados do perfil de concentração | `results/perfil_camada_limite_x49mm.csv` |
| Dados do perfil de velocidade | `results/perfil_velocidade_x49mm_raw.csv` |
