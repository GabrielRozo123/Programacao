# 03 — Setup STAR-CCM+ (scaffold do tutorial adaptado)

> Todos os passos do tutorial VOF "Boiler" (9 páginas), com os pontos que **mudam** para
> condensação marcados com ⇒. Sem colar a doc proprietária — só os parâmetros do nosso setup.

## 1. Fases e materiais
- Fase 1: **H2O** (Liquid, Constant Density). Fase 2: **H2O (G)** (Gas) — substituir o Ar padrão
  por **H2O (Water)** da base Standard > Gases.
- ⇒ **Industrial:** trocar Constant Density por propriedades reais (água/vapor dependentes de T,
  ou IAPWS) no ponto de operação. `06_pendencias.md`.

## 2. Modelos de física (continuum)
Two Dimensional · Implicit Unsteady · Multiphase → VOF · Segregated Flow · Turbulent → k-ε
Realizable Two-Layer · **Segregated Multiphase Temperature** · **Gravity**.

## 3. Malha 2D
- Converter malha 3D → 2D (grid alinhado ao plano X-Y, fronteira em Z=0; Mesh > Convert to 2D).
- ⇒ A geometria é a **nossa** (tubo frio no campo de vapor, `05_geometria.md`), não a caixa do
  tutorial. Escala conforme a construção (o tutorial usa fator 0,1).

## 4. Interação de fases (mudança de fase)
- Tutorial: Phase Interaction (H2O → H2O (G)) → **VOF Boiling → Rohsenow Boiling**
  (C_qw = 0,0128, n_p = 1,7 para cobre polido).
- ⇒ **Nosso:** trocar por o **modelo de condensação** (a definir — `06_pendencias.md`), com o
  parâmetro equivalente calibrado pela validação vs Nusselt.

## 5. Condições iniciais
- Tutorial: VF [1,0] (líquido), T = 350 K.
- ⇒ **Nosso:** VF **[0,1] (vapor)**, T inicial = **T_sat** (ou ligeiramente acima).

## 6. Condições de contorno
- Tutorial: Bottom = Wall T=540 K (quente); Left = Velocity Inlet (1 m/s, 350 K, líquido);
  Right = Pressure Outlet (370 K); demais = Wall.
- ⇒ **Nosso:**
  - **Tubo = Wall com T = T_parede < T_sat** (parede fria; ou fluxo/HTC do lado da água de
    resfriamento, se formos conjugados).
  - **Entrada de vapor** (Velocity/Mass Flow Inlet, VF vapor [0,1], T = T_sat).
  - **Saída** (Pressure Outlet) para o condensado/vapor.

## 7. Solver e critérios de parada
- Implicit Unsteady: **Δt = 0,01 s** (revisar para a nossa escala/malha).
- Under-Relaxation: Velocity 0,8 · **Segregated VOF 0,1**.
- Max Inner Iterations = 1 (time-marching, 1 iteração por passo).
- Tempo físico: tutorial 3 s ⇒ **nosso:** rodar até o filme e o `h` estabilizarem.
- ⇒ Se o modelo de condensação tiver termo de parede não-linear (como o Rohsenow tinha URF de
  fluxo), reduzir a **under-relaxation do fluxo de mudança de fase** para convergir.

## 8. Pós-processamento do `h` (ver `02_fisica_e_metodo.md`)
- Field function **"Heat Transfer Coefficient"** com **T_ref = T_sat** → `h` local no tubo.
- Reports: fluxo de calor integral no tubo, `h(θ)`, `h_méd`, espessura do filme.
- Verificação de malha: **Specified y+ HTC**.
