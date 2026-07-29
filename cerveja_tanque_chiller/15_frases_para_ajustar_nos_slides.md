# 15 — Frases a ajustar no deck (após a correção da recirculação)

> Base: deck `Grey_Logix_nova_rodada_1.pdf`. Motivo: a geometria da recirculação estava errada
> (bocais laterais em vez de **dreno do cone → tampa**). Ver `14_resultado_sim2_CORRIGIDO.md`.
> **Só 4 pontos mudam. O restante do deck continua válido.**

---

## ⛔ 1. Slide 5 — a frase que ficou FALSA (prioridade máxima)

**Está assim:**
> *"Sim 1 revela um resfriamento mais rápido que a mistura perfeita, o frio no fundo empurra o quente
> até a sucção (deslocamento). **A recirculação da Sim 2 mistura o tanque, então o resfriamento volta
> ao ritmo da mistura perfeita.**"*

**Trocar por:**
> *"Sim 1 revela um resfriamento mais rápido que a mistura perfeita: o frio no fundo empurra o quente
> até a sucção (deslocamento). **A recirculação da Sim 2 elimina a estratificação, mas cobra o preço —
> o resfriamento fica ~25 % mais lento que a mistura perfeita (6.140 s contra 4.925 s).**"*

*Por quê:* com a geometria correta o Sim 2 **não** coincide mais com o CSTR — fica **24,7 % acima**.

---

## ⚠️ 2. Onde aparecer "estratificação cai pela metade / 4,7 °C"

**Trocar** o número: com a recirc correta a estratificação **não cai pela metade — ela desaparece**.

| dizer | não dizer |
|---|---|
| *"ΔT topo−fundo → ~0 °C: o tanque fica **térmicamente homogêneo**"* | ~~"pico de 4,7 °C, metade do Sim 1"~~ |

Esse é um **ganho** da correção: o argumento de uniformidade ficou mais forte.

---

## 📐 3. Slide 3 — a descrição do circuito de recirculação

**Está assim:** *"Sim 2: + Recirculação / 1,35 m + 2º circuito fundo→topo"* (e as figuras/legendas
que falam em **bocais laterais**).

**Trocar por:**
> *"Sim 2: chiller a 1,35 m + 2º circuito de recirculação (12 m³/h): **capta pelo dreno central no
> ápice do cone** e **devolve por cima, pela tampa** (fora do eixo, r ≈ 665 mm) — conforme o diagrama
> EGISA 055.2254."*

Trocar também a **figura do domínio** (slide 2 e onde mais aparecer) pela do STEP corrigido.

---

## 🎯 4. A conclusão / recomendação — reforçar, não reescrever

A mensagem central **não muda**, só fica mais nítida:

> **"A recirculação entrega uniformidade, não velocidade."**

Sugestão de fechamento com os dois números nos extremos:

| | Sim 1 (só chiller 1,35 m) | **Sim 2 (+ recirculação)** |
|---|---|---|
| Estratificação (ΔT topo−fundo) | 9,6 °C transitório | **~0 °C** |
| Tempo p/ 99 % resfriado | ~2.500 s | **6.140 s** |
| Regime | deslocamento (mais rápido que CSTR) | homogêneo, ~25 % mais lento que CSTR |

> *"É uma escolha de projeto: **priorizar tempo de batelada → Sim 1**; **priorizar cerveja sem
> gradiente térmico → recirculação**, ao custo de ~2,5× o tempo."*

---

## ✅ O que NÃO precisa mexer
- Todo o diagnóstico do **baseline 0,85 m** (curto-circuito) e a recomendação de subir a sucção p/ 1,35 m.
- O **benchmark CSTR** como régua (só os números do Sim 2 mudam).
- Os resultados do **Sim 1** (a geometria dele estava certa).
- A metodologia, o modelo ρ(T) e as hipóteses.

## 🔎 Ressalva a declarar no deck (uma linha)
> *"Diâmetro da linha de recirculação adotado como DN65 (não cotado no diagrama) — a confirmar."*
