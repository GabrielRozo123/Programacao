# 00 — RESUMO / ÍNDICE do estudo do ejetor (leia primeiro)

> Amarra tudo num quadro só. Projeto Ito / Fase 2. Atualizado: 2026-07-21 (pós-reunião, feedback positivo).

## 🎯 O objetivo do Ito
Gerar **microbolha < 200–300 µm** (para flotar impurezas) no **xarope de cana viscoso** (6,5 Pa·s). Na reunião
ele focou a pergunta certa: **"quais condições favorecem o cisalhamento?"** (a alavanca da quebra) — e topou
**gastar mais potência/velocidade para cisalhar mais**, dentro do que a **literatura** justificar.

## 🗺️ Onde estamos (o quadro completo)
| Peça | Estado | Doc |
|---|---|---|
| Metodologia CFD do ejetor (2 passos + VOF) | ✅ fechada + verificada | `01` |
| σ ar-xarope | ✅ literatura → **0,058 N/m** (sweep 0,045–0,072) | `02` |
| Álgebra do cisalhamento (geral, impelidor) | ✅ (respondeu "**onde**": é o ejetor, não o reator) | `../estudo_cisalhamento` |
| Álgebra fina do cisalhamento no bico | ✅ | `03` |
| Dados da reunião 21/07 + plano 2 trilhos | ✅ | `04` |
| Literatura velocidade→bolha (proposta do bico) | ✅ **justificada** | `05` |
| Geometria v2 (STEP paramétrico) | ✅ topologia (7 bicos hex); **falta cotas finas** | `../geometria/eductor_v2_notas` |
| Impelidor do reator (Np/Nq/potência) | ✅ **FECHADO** (9,9 kW, +37% bombeamento) | `../impelidor_parametrico/tabela_final_impelidor` |

## 🔑 As 6 conclusões consolidadas (o núcleo do estudo)
1. **O ejetor é LAMINAR** (Re~40) → **sem quebra turbulenta** (não usar k-ε; kernels turbulentos são inválidos).
2. **λ = µ_ar/µ_xarope → 0** → em **cisalhamento SIMPLES a bolha NÃO quebra** (Ca_crit diverge, Grace). **Só
   EXTENSÃO / atomização por jato** quebra (Ca_crit até ~1000× menor, sem limite de λ).
3. **A "1,3–2 m/s" é o TUBO de ar** (dimensionamento/perda de carga) — **desacoplada** do tamanho de bolha.
4. **Borbulhar → bolha de ~mm** (Tate) em qualquer furo prático. **<300 µm EXIGE JATEAMENTO** (`We_furo ≫ 350`) —
   e o **ar supersônico do projeto do Ito JÁ está nesse regime** ✅.
5. **Bolha menor = jato mais rápido** (`d ∝ 1/U`, KH/Lubanska). Lever = **furo menor / bico convergente (de Laval)** —
   é aqui que "aumentar a velocidade" vale, **justificado pela literatura**.
6. **Ressalva honesta:** 6.500 cP é ~7× acima do validado na literatura → **direção sólida, número absoluto é
   extrapolação** → o CFD (Trilho 2) crava.

## 🛤️ O plano em 2 trilhos
- **Trilho 1 — ANALÍTICO (literatura + matemática):** ✅ **feito.** A **proposta do bico está justificada** (`05`):
  jateamento + jato rápido + bico convergente + ajustar ALR. Pode ir pro Ito / colega dele modelar.
- **Trilho 2 — CFD:** ⏳ quando a geometria nova fechar → valida/crava o número (Passo 1 monofásico → VOF → EMP).

## ⏳ Pendências (o que falta)
| O quê | De quem |
|---|---|
| **STEP/Parasolid (.x_t) nativo** ou desenho cotado (DWG→IGES degradou as cotas finas) | cadista do Ito |
| Confirmar: **o que contrai** (tubo de ar × bico de xarope), **Ø exatos** do bico/furos, o **alvo** | Ito |
| **Geometria nova do bico** (proposta nossa → o colega do Ito modela) | Ito + nós |
| Fechar a **matemática do dimensionamento** do furo (Ø p/ velocidade/We alvo com 30 m³/h) | nós (rápido) |
| Novo diagrama detalhado do ejetor (conferir vs v2) | Ito |

## 📊 Dados-chave (referência rápida)
- Ar **~30 m³/h/ejetor** (120/4, 4 ejetores) · motriz **~130 m³/h** · µ=6,5 Pa·s · ρ~1300 · σ=0,058 N/m.
- Geometria (medida no CAD): 7 bicos Ø9 hex · câmara **~Ø45** (corrige v2) · lança 2½" ID62,7 · furos Ø7 = fixação.
- Contração existente no bico: razão entrada:saída **2:1** (Ito quer aumentar).

## 📣 A mensagem pro cliente (uma linha)
> *Já entregue: a proposta do bico está justificada por literatura (**jateamento + jato rápido + bico convergente**);
> o número exato de bolha a 6.500 cP o **CFD crava** quando a geometria fechar.*
