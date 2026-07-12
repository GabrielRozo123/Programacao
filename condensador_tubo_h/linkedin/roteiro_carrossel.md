# Roteiro do carrossel LinkedIn — "Prever o h em mudança de fase é difícil"

**Público:** engenheiros projetistas (trocadores, mudança de fase, CFD).
**Tese:** projetos de mudança de fase esbarram na dificuldade de prever o coeficiente `h` com
precisão — e o CFD, feito com honestidade, mostra exatamente onde.
**Tom:** técnico, honesto, sem venda. O herói é o *problema*, não a ferramenta.
**Formato:** 10 slides, 1080×1080. Figuras prontas em `linkedin/fig1..3`.

> Dica de design: fundo claro `#FBFBFD`, título Sora/Inter bold `#1A1A2E`, corpo cinza `#6B7280`.
> Um destaque por slide na cor da história (azul teoria `#35618F`, vermelho o problema `#B23A48`).

---

### Slide 1 — CAPA (gancho)
**Título:** Quantos projetos de mudança de fase simplesmente **chutam** o coeficiente `h`?
**Sub:** Um estudo CFD honesto de condensação — e as 3 armadilhas que entregam um número
*confiante e errado*.
**Visual:** só texto grande + um ícone/silhueta de tubo com gota. Sem figura de dado (o gancho é a pergunta).

---

### Slide 2 — POR QUE O `h` IMPORTA
**Título:** O `h` decide o tamanho do equipamento.
**Corpo:**
- Na condensação, `h = q″ / (T_sat − T_parede)`.
- Ele define a **área de troca** — logo o **custo e o volume** do trocador/condensador.
- É o número que mais gente **copia de tabela** sem checar. E mudança de fase é onde a tabela
  mais engana.
**Visual:** a fórmula grande e centralizada.

---

### Slide 3 — O CASO E O ALVO
**Título:** Um caso limpo, com resposta conhecida.
**Corpo:**
- Tubo horizontal Ø25,4 mm, parede a 75 °C, vapor saturado a 100 °C (ΔT = 25 K).
- Teoria de **Nusselt (1916)** → `h ≈ 9,7 kW/m²·K`. Bancada real → `~5,5` (já abaixo — sinal de ar).
- Se o CFD é bom, o tubo limpo tem que **reproduzir Nusselt**. É o teste.
**Visual:** esquema do tubo no vapor (`geometria/condenser_esquema.png`) ou desenho simples.

---

### Slide 4 — ARMADILHA 1: o modelo "óbvio" não condensa
**Título:** Armadilha 1 — o modelo certo pelo nome, errado pelo regime.
**Corpo:**
- Liguei o **VOF Evaporation/Condensation** (o padrão). Ele é **limitado por difusão**.
- Em **vapor puro** não há gradiente de espécie → **não condensa**. Só sobra **condução**
  (q″ caindo com ~1/√t). Nenhum erro na tela.
- Solução: o modelo **térmico** (Fluid Film + *Thermal Limitation*), certo para vapor saturado.
**Destaque:** *"Rodar dias e entregar condução achando que é condensação."*

---

### Slide 5 — ARMADILHA 2: modelo certo, `h` 4× abaixo
**Título:** Armadilha 2 — condensou… e mesmo assim errou por 4×.
**Corpo:** Com o modelo térmico correto, o `h` médio saiu **2,29 kW/m²·K** — **~4× abaixo** de
Nusselt. O modelo não estava errado: o **filme estava acumulando** (~4× mais grosso que o teórico).
**Visual:** **`fig1_gap_h.png`** (Nusselt 9,7 × Experimental 5,5 × CFD 2D 2,29).

---

### Slide 6 — O ACHADO: o `h` está preso ao dreno (que é 3D)
**Título:** O `h` está amarrado ao **dreno** — e o dreno não cabe em 2D.
**Corpo:**
- O filme só engrossa se o condensado **não escorre**. E ele não escorre porque:
- **Gotejar é 3D** (tensão superficial; a gota sai *no eixo do tubo*, que o corte 2D não tem).
- **Edge stripping** precisa de uma **quina** — o tubo é liso.
- `h = k/δ`: filme grosso ⇒ `h` baixo. **A física do `h` é a física do dreno.**
**Destaque:** *"Não existe caminho de drenagem para o condensado num tubo liso em 2D."*

---

### Slide 7 — A VALIDAÇÃO HONESTA
**Título:** A **forma** está certa. A **média**, não.
**Corpo:**
- O perfil `h(θ)` reproduz Nusselt: **alto no topo** (filme fino), **baixo na base** (acumulado).
- **No topo, o `h` local (~9–12 kW/m²·K) enquadra Nusselt** — onde o filme é fino, o número bate.
- A **média** é puxada pela base inundada — **artefato do 2D**, não da física local.
**Visual:** **`fig2_htheta.png`**.

---

### Slide 8 — AS 3 ARMADILHAS
**Título:** Três formas de errar o `h` — cada uma sozinha basta.
**Corpo:** (1) modelo difusivo × térmico · (2) resolução do filme (µm) · (3) dimensionalidade do dreno.
**Visual:** **`fig3_armadilhas.png`** (o slide inteiro é a figura).

---

### Slide 9 — A LIÇÃO DE PROJETO
**Título:** O que isso significa para quem projeta.
**Corpo:**
- O `h` "de tabela" **esconde** essas três armadilhas. Ele pode estar **certo por sorte** — ou
  errado por um fator que muda o tamanho do equipamento.
- CFD **prevê o `h`** — mas exige a **física certa** (modelo térmico), a **malha certa** (resolver o
  filme) e a **dimensão certa** (3D para o dreno). Pular qualquer uma = número confiante e errado.
- O caminho para o número: **fatia 3D** (o dreno acontece → média converge a Nusselt) e depois
  **NCG** (a queda rumo aos ~5,5 reais — a assinatura industrial do ar).
**Destaque:** *"Não confie num `h` que você não conseguiu reproduzir."*

---

### Slide 10 — FECHAMENTO / CTA
**Título:** Prever o `h` em mudança de fase é difícil — e é por isso que importa fazer direito.
**Corpo:**
- Se seu projeto de condensação/evaporação depende de um `h`, pergunte: ele foi **validado**?
  Contra o quê? Em **2D ou 3D**? Com ou **sem** gás não-condensável?
- Comenta aí: qual `h` você já viu ser chutado num projeto de mudança de fase?
**Assinatura:** Gabriel Rozo · CFD / CAEXPERTS.

---

## Checklist de produção
- [ ] Slides 5, 7, 8 usam `fig1`, `fig2`, `fig3` (já geradas em 1080×1080).
- [ ] Slide 3 pode usar `geometria/condenser_esquema.png` (ou redesenhar limpo).
- [ ] Manter 1 ideia por slide; número grande (2,29 / 4× / 9,7) sempre em destaque.
- [ ] Revisar: nada de doc proprietária Siemens; só resultados e método próprios.
