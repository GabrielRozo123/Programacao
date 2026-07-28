# PREP — Reunião com o Ito (com Marcus)

> Objetivo: **entregar o impelidor (fechado, positivo)** e **destravar o ejetor** com 2 números.
> Regra de ouro: **abrir pela vitória**, depois o achado, depois as perguntas. Nunca "o projeto está errado".

---

## 1️⃣ ABRIR PELO QUE ESTÁ PRONTO — o IMPELIDOR ✅

> *"Marcos, o estudo do impelidor está **fechado**. O upgrade que vocês queriam testar
> (Ø800→880, 3→4 pás, 30→31,5°, 109→120 rpm) **é viável** e nós quantificamos o ganho."*

| | Original | **NOVO** | Δ |
|---|---|---|---|
| **Potência** | 4,07 kW | **9,90 kW** | usa **40% dos 25 kW** ✅ |
| **Bombeamento** | 1.158 m³/h | **1.588 m³/h** | **+37%** |
| **Circulação** | 6,5 min | **4,7 min** | −27% |

**As 3 frases:**
1. **"Cabe no motor com folga"** — 9,9 de 25 kW. Zero risco, não precisa trocar acionamento.
2. **"Mistura +37%"** — o reator homogeneíza 27% mais rápido.
3. **"O custo:"** a eficiência de bombeamento por kW cai 18% (Nq/Np 0,45→0,37). Como sobra orçamento,
   é um trade seguro — **mas a decisão "vale +37% de mistura por +143% de potência?" é de processo, é sua.**

*(Nota de escopo, se ele misturar: o impelidor é do **REATOR** — agitação, não aerado. As **bolhas** são
do aerador/ejetor, tanque separado.)*

---

## 2️⃣ O EJETOR — o achado, sem drama

> *"No ejetor achamos algo que precisa da sua ajuda para fechar."*

**O resultado:** na vazão informada (**130 m³/h**, = 1,10 m/s no tubo de 4"), para empurrar o xarope de
6,5 Pa·s pelos **7 furos Ø9** do bico é preciso **23,5 bar** antes do bico. O ar disponível é **1–3 kgf/cm²**.
→ **O ar é ~24× mais fraco: não entra.** E mais: **o xarope reflui pela linha de ar.**

**Confiabilidade (se ele questionar):**
- **3 métodos independentes** concordam (CFD, Hagen-Poiseuille analítico, modelo calibrado) — ~10%
- **2 modelos multifásicos diferentes** (VOF e EMP) dão a mesma conclusão
- Geometria conferida contra o **STEP nativo do Brendo** — o **Marcus verificou por conta própria** ✅

**A lei que resume:** `P_entrada_de_ar = 21,3 × v_xarope` (bar, bico 7×Ø9)
→ **O ar entra se P_ar > P_bomba.** É uma disputa de pressões.

### Se ele falar em VÁCUO (ele já falou)
> *"Vácuo tem teto físico de 1 bar. Contra 23,5 bar, mudaria 4%. Mesmo vácuo perfeito não muda a
> conclusão. **E mais:** se vocês observam vácuo lá, isso indica que a vazão real é bem menor que os
> 130 m³/h nominais — que é justamente o dado que eu preciso confirmar."*

*(Usar a observação dele como evidência a favor, não rebater.)*

---

## 3️⃣ AS PERGUNTAS (por ordem de impacto)

| # | Pergunta | Por que importa |
|---|---|---|
| **1** | **Qual a pressão de descarga da bomba do ejetor?** (bar / modelo / curva) | **Define onde o sistema opera.** Nós impusemos a vazão; quem manda é a bomba. |
| **2** | **Qual a pressão do ar que alimenta o EJETOR?** Soprador ou compressor? | Os 1/2/3 kgf que usamos são da **Fase 1 (aerador)** — pode não ser o do ejetor. |
| **3** | **Qual bico está instalado: 7×Ø9 ou 4×Ø15?** | Muda tudo: 4,4× mais passagem, 23,5 → 5,3 bar. |
| **4** | **Os 130 m³/h são medidos ou nominais de placa?** | Se for nominal, a vazão real é menor e o quadro muda. |
| **5** | **Vocês veem ar entrando na prática? Em que condição?** | ⭐ **A mais valiosa.** Se funciona lá, aponta o que reconciliar. |
| **6** | **Onde o ejetor descarrega no tanque de aeração?** | Dúvida do Marcus — os CADs vieram separados, sem acoplamento. |

---

## 4️⃣ O TRUNFO — a solução já está no acervo dele

No próprio acervo do Ito existe o desenho **CSA01-300-001 — "BICO Ø15mm"**, de **22/07/2023**, carimbado
**"BOM P/ FABRICAÇÃO"**: **4 furos Ø15** em vez de 7×Ø9.

| | 7×Ø9 (instalado) | **4×Ø15 (desenho dele)** |
|---|---|---|
| N·D⁴ (o que manda) | 45.927 | **202.500 → 4,4×** |
| Contrapressão @130 m³/h | 23,5 bar | **5,3 bar** |

> *"Encontramos no acervo de vocês um desenho de bico 4×Ø15, liberado para fabricação em 2023, que passa
> 4,4× mais e resolve boa parte do problema. **Chegou a ser fabricado? Por que não foi adotado?**"*

**Isso é ouro:** você não chega propondo mudança de projeto — você **resgata uma solução que eles mesmos
engenheiram**. E a resposta dele pode revelar uma restrição que a gente não conhece (erosão, custo, já testaram).

---

## 5️⃣ O QUE LEVAR
- `fase2/ejetor/diagrama_explicativo_marcus.png` — a cadeia lógica + objeções respondidas
- `fase2/ejetor/lei_mestra_P_vs_v.png` — o gráfico da lei (ele pode **apontar onde acha que opera**)
- `fase2/ejetor/bico_7x9_vs_4x15.png` — o comparativo dos bicos
- `fase2/impelidor_parametrico/tabela_final_impelidor.md` — a tabela do impelidor

## 6️⃣ FECHAMENTO
> *"Com a pressão da bomba e a pressão do ar do ejetor, eu fecho o diagnóstico **sem rodar mais nada** —
> e digo exatamente em que condição o ejetor aera."*
