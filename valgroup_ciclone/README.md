# Valgroup — Separação Gás-Sólido (Ciclone)

**Cliente:** Daniel Bacellar Souza Vozza — Valgroup Brasil  
**Engenheiro:** Gabriel Hernandez Rozo — CAExperts  
**Objetivo:** Avaliar e dimensionar sistema de separação de partículas de char de gás quente de hidrocarbonetos

---

## Status Atual

**KICKOFF REALIZADO — aguardando dados do cliente**

---

## Dados Conhecidos (da reunião)

| Dado | Valor | Status |
|---|---|---|
| Temperatura do gás | 400–450°C | confirmado |
| Pressão do gás | 1.2 bar | confirmado |
| Vazão mássica total | ~800 kg/h | confirmado |
| Teor de char | ~10% → ~80 kg/h | confirmado |
| Perda de carga máxima | 16 pol H₂O (~40 mbar) | confirmado |
| Sólido a separar | Char (biomassa) | confirmado |
| Downstream finos | Condensador casco-tubo | confirmado |
| Downstream pesados | Tanque buffer → óleo | confirmado |
| Segunda opção | Quench tower (kuenti) | mencionado |
| "Dor" principal | Estimar massa específica do gás | confirmado |

### Granulometria do Char (amostra biomassa 3072-1/2025.0, coleta 17/07/2025)

| Peneira | % Massa Retida |
|---|---|
| 12,5 mm | 2,78% |
| 4,75 mm | 3,77% |
| 1 mm | 9,51% |
| 0,425 mm | 12,10% |
| 0,150 mm | 25,79% |
| 0,075 mm | 36,91% |
| Fundo (< 0,075 mm) | 9,41% |

> **Atenção:** este é o char EXTRAÍDO na saída. O char CARREADO (o que interessa separar) tende a ser **mais fino** — concentrado principalmente abaixo de 150 μm.

---

## Dados Pendentes (solicitar à Valgroup)

### CRÍTICO
- [ ] Planilha de composição do gás (vista na reunião — Marcus vai enviar)
- [ ] Granulometria do char CARREADO (fração fina — distinta da amostra acima)
- [ ] Vazão volumétrica do gás (m³/h) ou densidade para converter da mássica
- [ ] Temperatura exata de entrada no separador (400°C ou 450°C?)

### IMPORTANTE
- [ ] Espaço físico disponível para o separador
- [ ] Material da rosca/tubulação (para seleção de material do ciclone a 450°C)
- [ ] Pressão downstream (saída do separador)
- [ ] Frequência de limpeza esperada

### COMPLEMENTAR
- [ ] Fotos do processo / layout atual
- [ ] Qualquer relatório de análise do gás
- [ ] Especificação dos condensadores downstream

---

## Escopo do Projeto

```
Fase 1: Literatura + Mapeamento de tecnologias
  → Revisão: ciclone, quench tower, filtro cerâmico, scrubber, ESP, settler
  → Tabela comparativa por critérios técnicos

Fase 2: Matriz de Decisão (formato Marcus)
  → Critérios com pesos (1=positivo, 0=neutro, -1=negativo)
  → Recomendação fundamentada da(s) melhor(es) tecnologia(s)

Fase 3: Dimensionamento
  → Propriedades do gás: ρ(T=450°C, P=1.2bar) via Peng-Robinson
  → Ciclone: método Lapple ou Stairmand
  → Validação: eficiência por faixa granulométrica

Fase 4: Simulação CFD
  → Star-CCM+ ou ANSYS Fluent
  → Fase discreta (partículas de char)
  → Eficiência de coleta por tamanho de partícula
  → Campo de velocidades e pressão

Fase 5: Apresentação à Valgroup
  → Resultados + recomendação final
```

---

## Arquivos

| Pasta | Conteúdo |
|---|---|
| `dados_cliente/` | planilha de gás, granulometria do char (quando chegar) |
| `literatura/` | revisão de tecnologias de separação gás-sólido |
| `matriz_decisao/` | planilha/script da matriz com pesos |
| `dimensionamento/` | cálculos do ciclone, propriedades do gás |
| `simulacao/` | geometria CFD, setup Star-CCM+ |

---

## Notas Técnicas

- **Massa específica do gás:** calcular com Peng-Robinson para mistura HC a 450°C/1.2bar. Essa é a "dor" que o Daniel mencionou — varia com composição e temperatura.
- **Baixa vazão + alta temperatura:** desfavorável para ciclone simples (Re baixo = eficiência menor para finos). Pode ser necessário ciclone de alta eficiência (tipo Stairmand) ou conjunto em série.
- **Risco de entupimento no buffer tank:** chars pegajosos a alta temperatura podem aglomerar. Considerar na matriz.
- **Finos abaixo de 75 μm (~9.41% + a fração carreada):** são os mais difíceis de capturar em ciclone convencional — podem precisar de estágio secundário (filtro cerâmico ou ESP).
