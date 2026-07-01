# Contexto — Apresentação Sinatub 2026 (enviada por Marcus Ito)

> "Otimização das Etapas de Clarificação - Fosfatação — Caldo e Xarope" (71 slides).
> Da Sinatub (fornecedor da tecnologia). Dá o processo, a química e um estudo CFD prévio.
> Extraído: 2026-07-01.

## Processo (confirma e detalha o kick-off)
Objetivo: **otimizar a clarificação por fosfatação** de caldo e xarope de açúcar
(redução de custos, recuperação de açúcar, qualidade).
- **Química:** Ca²⁺ + PO₄³⁻ → floco de **fosfato de cálcio Ca₃(PO₄)₂** ("ponte iônica")
  → precipita compostos colorantes (fenóis, flavonoides, proteínas, aminas) por oxi-redução.
- **Floculação primária** (micro-flocos) → **secundária** (macro-flocos + polímero aniônico
  poliacrilamida) + polímeros descolorantes catiônicos (DXD, alquil dimetil, epicloridrina).
- **Caldo → DECANTAÇÃO** ; **Xarope → FLOTAÇÃO / AERAÇÃO** (energia térmica + cinética).
- **4 variáveis-chave:** Tempo, Temperatura, Agitação, pH.

## ⭐ CFD PRÉVIO do TANQUE AGITADO (slide 21) — dá dimensões reais!
Já existe CFD do tanque agitado (reator). Resultados:
| Ø impelidor (m) | D/T | RPM | Potência (kW) | Torque (Nm) | F axial (N) | F radial (N) |
|---|---|---|---|---|---|---|
| 1,52 | 0,35 | 100 | 22,3 | 2.115 | 5.962 | 31 |
| 1,80 | 0,42 | 78 | 25,2 | 3.055 | 7.120 | 71 |
| 2,15 | 0,50 | 58 | 25,1 | 4.090 | 8.291 | 89 |
- Objetivo: potência máx **25 kW**. Quantificaram forças hidrodinâmicas no impelidor.
- **→ Diâmetro do TANQUE T ≈ 4,3 m** (de D/T: 1,52/0,35 ≈ 2,15/0,50 ≈ 4,3 m). Número real!
  (Coerente com o ÷10 do CAD ~5,4 m — mesma ordem; usar ~4,3 m como referência.)

## Escopo de simulação declarado (slide 52)
"Simulações das condições de **Agitação, Aeração, Dosagens, Princípios Ativos, pH e
Floculações** primária e secundária."

## Nota sobre RPM (a esclarecer)
- Apresentação (reator agitado): **58–100 RPM**.
- Kick-off Marcus Ito (tanque aerador/flotação): **10–15 RPM** (agitação gentil p/ não
  quebrar floco na flotação).
- Provável: reatores A/B = alto RPM (formar floco) ; aerador = baixo RPM (flotar). Confirmar.

## Implicação para NOSSO escopo (afiar a proposta)
Eles JÁ têm CFD do **tanque agitado** (impelidor: potência, forças, vazões). Nosso
diferencial/valor está na **AERAÇÃO-FLOTAÇÃO**: o **ejetor venturi** gerando micro-bolhas +
a flotação no **meio viscoso (65 poise)** — a parte mais difícil e menos coberta. É onde o
CFD multifásico agrega. (Confirmar com Marcus Ito se querem a aeração, o agitador, ou ambos.)
