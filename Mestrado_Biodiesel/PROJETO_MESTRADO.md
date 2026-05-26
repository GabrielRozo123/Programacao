# MESTRADO — Reator Monolítico para Biodiesel
## Modelagem CFD em Simcenter STAR-CCM+

**Aluno:** Gabriel Rozo  
**Orientadores:** Prof. Supino + Prof. Dirceu  
**Status:** Aguardando parâmetros da bancada experimental  
**Última atualização:** 2026-05-26

---

## 1. TÍTULO DO PROJETO

> "Modelagem Computacional (CFD) e Avaliação Hidrodinâmica da Produção de
> Biodiesel via Transesterificação Heterogênea em Reator Monolítico Estruturado"

---

## 2. DESCRIÇÃO FÍSICA

### O Equipamento
- Reator monolítico cerâmico (cordierita), tipo "colmeia"
- Catalisador heterogêneo impregnado nas paredes (washcoat): CaO, ZnO ou similar
- Fluido: mistura óleo vegetal + metanol escoando pelos microcanais

### Por que monolítico?
- Elimina lavagem pós-reação (catálise heterogênea)
- Baixa queda de pressão vs. leito fixo empacotado
- Canais paralelos idênticos → simular apenas UM canal representativo

### Reação
```
Triglicerídeo (TG) + 3 Metanol (MeOH) → 3 FAME (biodiesel) + Glicerol
Tipo: Endotérmica | Heterogênea | Superfície catalítica
```

---

## 3. ESCOPO DA SIMULAÇÃO (validado pelo Prof. Dirceu)

### FASE 1 — Validação Hidrodinâmica a Frio ✅ PRÓXIMA ETAPA
- Geometria: **retângulo 2D** (único canal representativo)
- Física: fluxo laminar monofásico, regime permanente, isotérmico, SEM reação
- Objetivo: validar perfil parabólico de Poiseuille + confirmar ΔP ≈ 0
- Software: Simcenter STAR-CCM+

### FASE 2 — Simulação Reativa (tese completa)
- Adicionar: Segregated Species Transport (TG, MeOH, FAME, Glicerol)
- Adicionar: Segregated Fluid Temperature
- Parede: Reaction Wall com taxa de Arrhenius (Caminho B — sem Chemkin)
- Mapear: perfil de conversão X(z) e arrefecimento T(z) ao longo do canal

---

## 4. ABORDAGEM ESCOLHIDA — CAMINHO B (sem Chemkin)

### Justificativa
- Literatura já fornece k₀ e Ea para catalisadores sólidos (CaO, ZnO)
- Mais simples que Chemkin, igualmente publicável
- Adequado para fase líquida (evita problema do Ideal Gas EOS)

### Modelos STAR-CCM+ (Fase 2)
```
✓ Steady-State
✓ Multi-Component Liquid
✓ Segregated Flow
✓ Segregated Species Transport  → espécies: TG, MeOH, FAME, Glycerol
✓ Segregated Fluid Temperature
✓ Laminar
✓ Reaction Wall (Field Function)
✗ Complex Chemistry (NÃO usar — requer Chemkin)
```

### Taxa de reação na parede (Field Function)
```
r_s = k₀ · exp(-Ea/RT) · C_TG · C_MeOH   [mol/m²·s]

Parâmetros cinéticos (Lukić et al., 2016 — CaO washcoat):
  k₀ = 8.4×10⁻³ m⁴/mol·s
  Ea = 62.8 kJ/mol
  R  = 8.314 J/mol·K
```

---

## 5. PARÂMETROS NECESSÁRIOS DA BANCADA ⚠️ PENDENTE

**Email enviado em 2026-05-26 para Prof. Supino e Prof. Dirceu.**
**Aguardando resposta.**

| Parâmetro | Símbolo | Status | Valor típico literatura |
|---|---|---|---|
| Comprimento do canal | L | **PENDENTE** | 50–150 mm |
| Abertura do canal | a | **PENDENTE** | 0.8–1.5 mm |
| Velocidade de entrada | u₀ | **PENDENTE** | 0.01–0.1 m/s |
| Temperatura operação | T | **PENDENTE** | 60–120 °C |
| Razão molar MeOH:óleo | — | **PENDENTE** | 6:1 a 15:1 |

---

## 6. REFERÊNCIAS BIBLIOGRÁFICAS CHAVE

1. **Universidade de Bath** — Tese biodiesel em monólito cerâmico com SrO (cordierita 61 células/cm², dh=1.1mm, T=120°C, 8 bar, razão 6:1)
2. **Lukić et al. (2016)** — Cinética heterogênea CaO washcoat, k₀=8.4×10⁻³, Ea=62.8 kJ/mol
3. **Pinheiro/Larimi (Sci. Rep., 2024)** — Modelagem 2D FBR vs PBMR, ácido tungstofosfórico, conversão 99.94% a 180°C

---

## 7. TUTORIAIS STAR-CCM+ ESTUDADOS

| Tutorial | Relevância | Observação |
|---|---|---|
| Reacting Channels: Steam Methane Reforming | Baixa para uso direto | Usa 1D PFR + 3D firebox — arquitetura diferente |
| Surface Chemistry: Methane on Platinum | Alta para Fase 2 | Ensina Surface Chemistry + Chemkin — usar estrutura, não os arquivos |

### O que aproveitar do tutorial Surface Chemistry:
- Seleção de modelos (trocar Multi-Component Gas → Liquid)
- Estrutura de boundary conditions (inlet, outlet, reactive wall)
- Conceito de Surface Mechanism Option → CATALYST na parede

---

## 8. PRÓXIMOS PASSOS (em ordem)

- [ ] Receber resposta dos professores com parâmetros da bancada
- [ ] Construir geometria 2D retangular no STAR-CCM+ (Fase 1)
- [ ] Gerar malha estruturada quad (~2000 células)
- [ ] Rodar Fase 1: validar Poiseuille e ΔP
- [ ] Adicionar espécies e reação de parede (Fase 2)
- [ ] Validar conversão com dados experimentais da bancada
- [ ] Redigir capítulo de metodologia CFD para dissertação

---

## 9. COMO RETOMAR ESSE PROJETO COM O CLAUDE

Ao iniciar nova sessão, envie:
> "Claude, quero retomar o projeto de mestrado. Aqui está o arquivo de contexto:"
> [Cole o conteúdo deste arquivo ou faça upload do PROJETO_MESTRADO.md]
