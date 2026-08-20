# Slides — Bloco térmico e condensação (Valgroup · ciclone)

> Dois slides, para substituir o slide único de "Temperatura de parede" do deck atual.
> Figuras em `relatorio/fig_temperatura_medida.svg` e `relatorio/fig_matriz_orvalho.svg`.

---

## Slide A — O que foi medido

**Título:** Temperatura de parede
**Faixa azul:** O ciclone tem duas temperaturas, e é a mais baixa que decide

**Visual:** `fig_temperatura_medida.svg` ocupando a área principal.

**Texto de apoio (2 bullets):**

- A simulação térmica foi resolvida com **h externo = 10 W/m²·K**, ambiente a 25 °C e gás a
  400 °C, nas duas cargas do turndown. Foram extraídos a **média** e o **mínimo** da parede.

- O mínimo está no **trecho inferior** — saída de pó e últimos 150 mm do cone, 8 % da área.
  Abaixo do fim do vórtice o gás fica quiescente e a troca interna cai a 26 % da do corpo.
  Essa região não aparece na média, mas é a que governa a condensação.

**Frase de destaque:**
> O corpo do ciclone não condensa em nenhuma das hipóteses de orvalho, nas duas vazões.
> O único ponto em risco é o trecho inferior.

**Rodapé:** ⚠️ O critério de comparação — o ponto de orvalho — depende da composição real da
corrente (C1–C40), ainda pendente.

---

## Slide B — O que fazer a respeito

**Título:** Condensação — matriz de decisão
**Faixa azul:** Existe uma configuração que cobre as duas hipóteses de orvalho

**Visual:** `fig_matriz_orvalho.svg` ocupando a área principal.

**Texto de apoio (2 bullets):**

- Cinco configurações de acabamento externo, avaliadas na condição governante (50 % de vazão)
  e nos dois pontos que importam. A **configuração D** — revestimento refletivo no corpo mais
  isolamento apenas nos 8 % inferiores — é a única que cobre as duas hipóteses sem isolar o
  ciclone inteiro.

- **A decisão não precisa esperar a composição.** Adotando D, o resultado é seguro tanto com
  orvalho de 250 °C quanto de 343 °C.

**Frase de destaque:**
> Isolar 8 % da área resolve o ponto crítico. O refletivo resolve o resto — e custa menos que
> isolamento.

---

## Como as temperaturas de cada acabamento foram obtidas

*(bloco de método — pode ir como caixa lateral no slide B, ou como slide de backup)*

O procedimento tem três passos e **não exige nova simulação** para cada acabamento.

**1. A simulação mede a parede com uma condição externa conhecida.**
O CFD foi resolvido com `h_e` = 10 W/m²·K prescrito. Dele saem as quatro temperaturas medidas
do Slide A.

**2. Dessas medições extrai-se o coeficiente interno.**
O balanço na parede é uma associação de duas resistências em série:

```
T_parede = (h_i · T_gás + h_e · T_amb) / (h_i + h_e)
```

Conhecendo `T_parede`, `h_e`, `T_gás` e `T_amb`, inverte-se para `h_i`:

| carga | região | T medida | **h_i extraído** |
|---|---|---|---|
| 100 % | corpo | 378,6 °C | 165,3 W/m²·K |
| 100 % | trecho inferior | 334,9 °C | 47,6 W/m²·K |
| 50 % | corpo | 363,7 °C | 93,4 W/m²·K |
| 50 % | trecho inferior | 290,5 °C | 24,3 W/m²·K |

O `h_i` é **propriedade do escoamento interno** — depende da vazão e da geometria, não do que
existe do lado de fora. Por isso pode ser reaproveitado.

*Validação:* a razão dos `h_i` do corpo entre as duas cargas é 0,565, contra `Re^0,8` = 0,574
previsto pela teoria de camada limite. **Erro de 1,6 %** — o modelo está calibrado.

**3. Troca-se o `h_e` pelo acabamento desejado.**
Do lado externo há dois mecanismos em paralelo, e nenhum depende da condutividade do metal:

```
h_e = h_radiação + h_convecção natural

h_radiação  = ε · σ · (T_par² + T_amb²) · (T_par + T_amb)      ← depende da EMISSIVIDADE
h_convecção = 1,31 · (T_par − T_amb)^(1/3)                     ← igual para qualquer superfície
```

Como o `h_radiação` depende da própria `T_parede`, a solução é **iterativa**: arbitra-se `T_par`,
calcula-se `h_e`, recalcula-se `T_par`, e repete-se até convergir.

Resultado no corpo, a 50 % de vazão:

| acabamento | ε | h_radiação | h_convecção | **h_e** | **T parede** |
|---|---|---|---|---|---|
| revestimento refletivo | 0,05 | 1,3 | 9,1 | **10,4** | **362 °C** |
| aço carbono oxidado | 0,80 | 17,6 | 8,7 | **26,3** | **317 °C** |
| isolado (lã de rocha) | — | — | — | **1,5** | **394 °C** |

**A conclusão que costuma surpreender:** o material da chapa é irrelevante do ponto de vista
térmico. O que muda a temperatura de parede é a **emissividade da superfície externa**. Uma
superfície refletiva irradia 13 vezes menos que aço oxidado, e por isso mantém a parede
**45 °C mais quente sem qualquer isolamento**.
