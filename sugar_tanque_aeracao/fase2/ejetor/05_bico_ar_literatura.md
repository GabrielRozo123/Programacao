# 05 — Proposta do bico de ar: o que a LITERATURA justifica (velocidade → bolha)

> Revisão multi-fonte (4 ângulos, busca web) do que o Ito pediu: *"justificado pela literatura"*. Responde
> **qual velocidade/geometria do bico de ar** gera bolha <200–300 µm no xarope viscoso (6,5 Pa·s).

## 🎯 Achado nº 1 (o mais importante) — a "1,3–2 m/s" mede a variável ERRADA para bolha
A regra de **1,3–2 m/s é dimensionamento do TUBO de ar** (perda de carga/ruído/erosão — padrão de tubulação de
gás ~5–10 m/s). **Está DESACOPLADA do tamanho de bolha.** O tamanho da bolha é definido **no ORIFÍCIO** (a jusante),
pela velocidade do **JATO**, não no tubo. *(Fonte: regras de projeto de sparger/aeração.)*

## 🎯 Achado nº 2 — o regime de BORBULHAMENTO nunca chega a <300 µm neste xarope
Lei de Tate (`d_bolha ≈ (6·d_furo·σ/(Δρ·g))^⅓`): furo Ø1 mm → bolha **~3 mm**; furo Ø0,1 mm → **~1,4 mm**; para
bolha 0,3 mm precisaria de furo **~1 µm** (impraticável). **A viscosidade PIORA** (bolha cresce com µ). → **furo
pequeno "borbulhando" é beco sem saída.** *(Tate; Davidson & Schuler; formação de bolha em orifício viscoso.)*

## 🎯 Achado nº 3 — o alvo <300 µm EXIGE o regime de JATEAMENTO (atomização), e o CAD já está nele
Transição borbulhamento→jateamento pelo **Weber do orifício:** `We_furo = ρ_gás·u²·d/σ`. Crítico:
`We_crit ≈ 10,5·(ρ_gás/ρ_líq)^(−½)` → com ρ*≈9×10⁻⁴, **We_crit ≈ 350**. Com o **jato sônico** (u~340 m/s) num
furo Ø1 mm e ρ_gás pressurizado: `We_furo ≈ 5.000 ≫ 350` → **bem dentro do jateamento.** → **O ar supersônico do
projeto do Ito JÁ coloca a injeção no regime certo** (não borbulha — jateia). *(Gutwald & Mersmann; Mori et al.)*

## 🎯 Achado nº 4 — bolha menor = jato mais rápido (d ∝ 1/U), e o mecanismo é EXTENSÃO/atomização (não cisalhamento simples)
- **`d ∝ U^(−1)`** (via `We^(−½)`, correlação de Lubanska). Comprimento de onda de Kelvin-Helmholtz: **6,1 mm a
  1 m/s → 0,38 mm a 4 m/s** (~U^(−2)). Atomização a gás: pó fino de **44,9 → 29,1 µm** quando Mach 1,0 → 2,5.
- **λ→0 CONFIRMADO:** em **cisalhamento simples** a bolha (λ~3×10⁻⁶) **não quebra** (Ca_crit diverge; curva de
  Grace). Em **EXTENSÃO** o Ca_crit é **até ~1000× menor e sem limite de λ** → é o único regime que quebra. O jato
  de gás de alta velocidade entrega isso (atomização por KH na interface). *(Grace; De Bruijn; Lubanska.)*
- **"Prompt atomization":** acima de uma velocidade de gás crítica, o efeito da **viscosidade (Ohnesorge) some** →
  o jato sônico/supersônico **vence a penalidade da viscosidade** do xarope. *(Lefebvre, airblast de alta velocidade.)*

## ⚠️ A ressalva honesta (viscosidade 7× acima do testado)
As correlações de atomização fina (SMD ~25 µm) foram validadas até **~900–1000 cP**; o xarope tem **~6.500 cP**
(~7×). Para líquido tão viscoso, o **termo VISCOSO** de Rizkalla-Lefebvre (`SMD ~ µ^0,85·(1+1/ALR)²`) domina → só
aumentar a velocidade tem retorno decrescente; o outro lever é a **razão ar/líquido (ALR)**. Então **o número
absoluto de bolha a 6.500 cP é extrapolação** — o CFD (Trilho 2) e/ou ensaio confirmam. Mas a **direção** é sólida.

## ✅ Proposta do bico (o que recomendar pro Ito, justificado)
1. **Operar em JATEAMENTO, não borbulhamento** → **furo de ar pequeno com jato sônico/supersônico** (o projeto já
   faz). Garantir `We_furo ≫ 350`.
2. **Bolha menor = MAXIMIZAR a velocidade do JATO no furo** (`d ∝ 1/U`) — furo menor / maior pressão de suprimento.
   **É AQUI que "aumentar a velocidade" vale** (não no tubo de 1,3–2 m/s). ✔ **Justificado pela literatura.**
3. **Contração convergente (de Laval)** no bico de ar → acelera a Mach → maximiza `We` e o cisalhamento **extensional**.
4. **Ajustar a ALR** (mais ar por líquido localmente) se <300 µm não for atingido — o lever do regime viscoso.

## 📣 A frase pro Ito
> *"A regra de 1,3–2 m/s dimensiona o **tubo** de ar, não a bolha. A literatura é clara: neste xarope, borbulhar
> dá bolha de ~mm em qualquer furo; para <300 µm é preciso o regime de **jateamento** — e o **ar supersônico já
> coloca vocês nele**. A bolha encolhe com a **velocidade do jato no furo** (d ∝ 1/U) — então **furo menor / jato
> mais rápido / bico convergente** é o caminho justificado. O número exato a 6.500 cP a gente crava no CFD."*

## Fontes-chave
- **Rizkalla & Lefebvre (1975)** — airblast SMD (termo inercial + viscoso). **Jasuja (1982)** — SMD~D0^0,5, ar até 180 m/s.
- **Sovani, Sojka & Lefebvre (2001)** — efervescente (mistura interna) p/ viscosos. **Lund/Chin/Lefebvre (1991)**.
- **Tate's law**; **Davidson & Schuler**; **Gutwald & Mersmann** (We_furo~2); **Mori et al.** (We_crit=10,5·ρ*^−½).
- **Grace** (Ca_crit×λ); **De Bruijn**; **Lubanska** (d~We^−½). **KH** na interface; gas atomization Mach→pó.
