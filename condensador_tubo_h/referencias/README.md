# Referências

> Resumos e âncoras. **Não** versionar PDFs proprietários (documentação Siemens/STAR-CCM+) —
> apenas os parâmetros/fatos que compõem o nosso setup.

## Documentação STAR-CCM+ consultada (tutorial VOF "Boiler" + HTC)
- **Tutorial de ebulição VOF** (9 páginas): fases, modelos de física, malha 2D, interação de fases
  (Rohsenow), condições iniciais/contorno, solver. Base do nosso scaffold — ver `../03_setup_star.md`.
- **"What Methods Are Available for Exchanging Heat Transfer Coefficients?"** — as 4 definições de
  `h` no STAR e suas temperaturas de referência. Base da nossa decisão de método — ver
  `../02_fisica_e_metodo.md`.
- **"Modeling Evaporation and Condensation" + "Setting Up..." + "Model Reference (VOF)"** — o modelo
  **VOF Evaporation/Condensation**: limitado por difusão, interface em equilíbrio (Raoult),
  multicomponente com espécie inerte (= NCG), Antoine/Wagner p/ P_sat, calor latente via Heat of
  Formation. Base do modelo escolhido — ver `../02_fisica_e_metodo.md`.

## Literatura técnica (a consolidar na revisão de literatura)
- **Nusselt (1916)** — teoria de condensação filmwise (tubo horizontal / placa vertical).
- **Rohsenow** — correção de sub-resfriamento do calor latente (`h_fg'`).
- **Gás não-condensável (Fase 2):**
  - Rose — condensação com NCG em tubo horizontal.
  - Dehbi — correlações de degradação por ar.
  - Sparrow & Minkowycz — condensação laminar com gás não-condensável.
- Datasets experimentais de vapor condensando em tubo horizontal (a fixar: D, T_sat, ΔT, h medido).
