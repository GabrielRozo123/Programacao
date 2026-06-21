# Revisão de Tecnologias de Separação Gás-Sólido
## Contexto: Pirólise de Biomassa, 400–450°C, Char Pegajoso

**Fontes:** Literatura indexada (ACS, ScienceDirect, Oxford, IEA Bioenergy, PMC/NIH)  
**Data da revisão:** Junho 2026

---

## 1. Ciclone (Lapple / Stairmand)

**Papel no processo:** Separador primário padrão em praticamente todos os sistemas de pirólise de biomassa. Primeira linha de separação.

**Temperatura de operação:** Sem limite prático — operado até >1000°C em gasificação. Para pirólise: 400–800°C comum.

**Eficiência de coleta:**
- Partículas >10 μm: 70–95% (depende do d* do ciclone)
- Partículas <10 μm: baixa (finos escapam no vórtice interno)
- Exemplo real: char de casca de coco → 78% de eficiência; com aditivo → 73–74%
- Finos <10 μm: sem solução eficaz documentada para ciclone simples

**Queda de pressão:** Baixa (5–25 mbar para Lapple). Redução do diâmetro do cone bottom aumenta eficiência sem aumentar ΔP significativamente.

**Partículas pegajosas:** Risco moderado de entupimento na saída cônica (hopper) a altas temperaturas. Mitigação: aquecimento do hopper, geometria com ângulo de cone adequado.

**Custo:** Baixo CAPEX e OPEX. Sem partes móveis. Manutenção mínima.

**Maturidade:** Padrão industrial consolidado. Amplamente documentado.

**Downstream:** ✓ Gás seco, quente — compatível com condensador casco-tubo.

**Referências:**
- Aston University CFD study on pyrolysis downer reactor + cyclone separator
- IOP Conference: Effect of inlet velocity on pressure drop in cyclone for pyrolysis
- ResearchGate: Design of cyclone separator for syngas purification

---

## 2. Quench Tower (Torre de Resfriamento / Scrubber a Spray)

**Papel no processo:** Resfriamento rápido do gás para condensação de vapores, com coleta simultânea de partículas. Usa óleo de pirólise recirculado ou solvente imiscível como fluido de quench.

**Temperatura de operação:** Entrada: até 500°C. **Saída: tipicamente <250°C.** O quench reduz drasticamente a temperatura.

**Eficiência de coleta:** Alta para partículas e vapores condensáveis (>99% para mist de bio-óleo). Dissolve/dilui o char no fluido de quench.

**Queda de pressão:** 10–50 mbar (depende do design do spray).

**Partículas pegajosas:** ✓ Char é dissolvido ou diluído no fluido de quench — não causa entupimento.

**Custo:** Médio. Requer bomba de recirculação, sistema de separação do fluido carregado.

**PROBLEMA CRÍTICO PARA VALGROUP:**
> O quench resfria o gás de 450°C para <250°C. O downstream é um **condensador casco-tubo** que precisa receber o gás a temperatura controlada para condensação das frações desejadas. Se o quench já condensar parte das frações, interfere com o processo downstream. Além disso, o gás sai úmido/com vapores de fluido de quench.

**Maturidade:** Alta — muito usado em escala de laboratório e piloto, menos em industrial contínuo para pirólise.

**Downstream:** ✗ Gás frio e úmido — modifica completamente o perfil térmico do condensador.

**Referências:**
- ScienceDirect: Review on condensing system for biomass pyrolysis (2018)
- ScienceDirect: Performance of flue gas quench and its influence on biomass CHP

---

## 3. Filtro Cerâmico (Velas Cerâmicas — Hot Gas Filter)

**Papel no processo:** Filtração de alta eficiência após ciclone primário. Remove partículas finas residuais e parcialmente alcatrões.

**Temperatura de operação:** 350–500°C (pirólise); até 850°C para versões catalíticas (gasificação).

**Eficiência de coleta:** >99% para partículas acima de 0.3 μm. Tamanho de poro típico: 0.3 μm.

**Queda de pressão:** 10–30 mbar (aumenta com acúmulo de char).

**PROBLEMA CRÍTICO — CHAR PEGAJOSO:**
> **"The filter cake is sticky and cannot therefore easily be removed from the surface of the filter by nitrogen pulsing. Controlled oxidation has also been tested for the removal of the char from the filter, but this procedure took up to 6–9 h to complete the regeneration."**
> → Para char de biomassa a 450°C: regeneração impraticável em operação contínua.

**Implementação industrial:** Planta de pirólise em Hokkaido (Japão): 600 velas cerâmicas de 3m de comprimento, área útil de 1.40 m²/vela. Scale-up é caro.

**Custo:** Alto CAPEX (velas cerâmicas custosas) + alto OPEX (regeneração longa, risco de quebra das velas).

**Maturidade:** Alta em gasificação; problemática em pirólise com char pegajoso.

**Downstream:** ✓ Gás seco e quente — compatível com condensador.

**Referências:**
- ACS Energy & Fuels: Novel Hot Vapor Filter Design for Biomass Pyrolysis (PMC/NIH, 2023)
- ACS Energy & Fuels: Mini-Review on Hot Gas Filtration in Biomass Gasification (2021)
- MDPI Energies: Review of Porous Ceramics for Hot Gas Cleanup

---

## 4. Precipitador Eletrostático (ESP)

**Papel no processo:** Coleta de partículas muito finas (<10 μm) por ionização e atração eletrostática. Usado como estágio secundário ou terciário.

**Temperatura de operação:**
- ESP convencional: <400°C (eletrodos limitados)
- ESP para alta temperatura (wire-cylinder): testado até >500°C em syngas
- **Problema:** "High temperature was harmful to the performance of the ESP, with lower maximum collection efficiency and higher energy consumption"

**Eficiência de coleta:**
- Partículas finas: 96% em syngas >500°C (configuração wire-cylinder otimizada)
- Bio-óleo mist: 97–99.5%
- Carvão/char de alta resistividade: eficiência diminui com temperatura

**Queda de pressão:** Muito baixa (0.5–2 mbar). Ponto fortíssimo.

**Partículas pegajosas:** ⚠ Risco de acúmulo nos eletrodos. Char carbonoso tem alta resistividade elétrica a altas temperaturas → reduz eficiência de coleta (back-corona effect).

**Custo:** Alto CAPEX (eletrodos de alta temperatura, fonte de alta tensão). Médio OPEX.

**Maturidade:** Alta em aplicações convencionais (<250°C). Ainda em desenvolvimento para >400°C em pirólise.

**Downstream:** ✓ Gás seco — compatível com condensador.

**Referências:**
- ScienceDirect: Electrostatic precipitation under coal pyrolysis gas at high temperatures (2019)
- ScienceDirect: Separation of particles from syngas at high temperatures with ESP (2011)
- ACS Energy & Fuels: Experimental study on ESP of low-resistivity high-carbon fly ash (2017)

---

## 5. Scrubber Úmido

**Papel no processo:** Lavagem do gás com líquido (água, óleo) para remoção de partículas e compostos solúveis.

**Temperatura de operação:** Entrada: até 400°C. **Saída: geralmente <250°C** (o líquido de lavagem resfria o gás).

**Eficiência de coleta:** 90–99% para partículas >1 μm. Boa para finos.

**Queda de pressão:** 5–30 mbar.

**Partículas pegajosas:** ✓ Char é lavado e removido continuamente com o líquido.

**PROBLEMA CRÍTICO PARA VALGROUP:**
> Gas de saída resfriado e carregado de vapor (umidade) — incompatível com condensador casco-tubo que precisa receber gás quente para condensação controlada das frações de hidrocarboneto. Wet scrubbing resulta em temperatura geralmente abaixo de 250°C.

**Custo:** Médio. Requer sistema de tratamento do líquido efluente.

**Maturidade:** Alta.

**Downstream:** ✗ Gás úmido e frio.

---

## 6. Settler Gravitacional

**Papel no processo:** Câmara de sedimentação gravitacional. Partículas caem por gravidade enquanto o gás flui lentamente.

**Temperatura de operação:** Qualquer (passivo).

**Eficiência de coleta:** 50–80% apenas para partículas >200–500 μm. Ineficiente para finos.

**Queda de pressão:** <5 mbar.

**Custo:** Muito baixo (apenas uma câmara).

**Limitação para Valgroup:** O char carreado é predominantemente <150 μm — o settler seria ineficaz para a fração de interesse.

---

## 7. Conclusões para a Matriz de Decisão

| Tecnologia | Apto a 450°C? | Char pegajoso? | Downstream OK? | Finos <75μm? | Veredicto |
|---|---|---|---|---|---|
| Ciclone | ✓✓ | ⚠ risco hopper | ✓✓ | ⚠ parcial | **1ª escolha — primário** |
| Quench Tower | ✓ entrada | ✓✓ dissolve | ✗ esfria gás | ✓ | Incompatível (downstream) |
| Filtro Cerâmico | ✓ | ✗✗ 6-9h regen | ✓✓ | ✓✓ | Inviável (char pegajoso) |
| ESP | ⚠ degrada >400°C | ⚠ resistividade | ✓✓ | ✓✓ | Possível 2º estágio |
| Scrubber Úmido | ✓ entrada | ✓✓ | ✗ esfria gás | ✓ | Incompatível (downstream) |
| Settler | ✓✓ | ⚠ | ✓✓ | ✗✗ | Ineficaz (finos) |

**Recomendação preliminar:** Ciclone de alta eficiência (Stairmand ou bateria Lapple) como estágio primário. Se necessário estágio secundário para finos <75 μm: ESP de alta temperatura (não filtro cerâmico, incompatível com char pegajoso).
