# Braskem PE5 — DEM Screw Conveyor (Embuchamento)

**Cliente:** Jeferson Diefenthaler — Braskem PE5, RS  
**Engenheiro:** Gabriel Hernandez Rozo — CAExperts  
**Software:** Star-CCM+ 2506  
**Objetivo:** Estudar e mitigar o embuchamento (clogging) de pó de PEAD em rosca transportadora

---

## Status Atual

**GEOMETRIA: CONCLUÍDA E VALIDADA NO STAR-CCM+**
- Casing com funil retangular e junção elíptica soldada ✓
- Rotor padrão (pá contínua) ✓
- Rotor cut-flight (cortes a cada 90°) ✓

**PRÓXIMO PASSO: aguardando dados operacionais e geométricos da Braskem**

---

## Dados Confirmados na Reunião (19/06/2026)

| Dado | Valor | Status |
|---|---|---|
| Comprimento total da rosca | ~2000 mm | confirmado |
| Destino após rosca | Secador | confirmado |
| Teor de hexano no PEAD | 2–3% | confirmado |
| Aparência visual do pó | similar a pó de talco | confirmado |
| Problema | embuchamento | confirmado |

---

## Dados Pendentes (solicitar à Braskem)

### CRÍTICO — sem isso não simula
- [ ] Diâmetro externo da pá (D_screw) em mm
- [ ] Diâmetro do eixo (D_shaft) em mm
- [ ] Passo da hélice (pitch) em mm
- [ ] RPM de operação
- [ ] D50 do pó de PEAD (ao menos estimado)
- [ ] Localização típica do embuchamento (início / meio / fim)

### IMPORTANTE — afeta precisão
- [ ] Granulometria completa do PEAD (D10, D50, D90)
- [ ] Densidade aparente (bulk density) em kg/m³
- [ ] Ângulo de repouso ou índice de flowability
- [ ] Tipo exato de rosca (padrão / cut-flight / ribbon)

### COMPLEMENTAR
- [ ] Desenho técnico ou croqui com cotas
- [ ] Fotos do equipamento real
- [ ] Fotos do PEAD pó
- [ ] Fotos de evento de embuchamento
- [ ] RPM e vazão mássica alvo

---

## Geometria Atual (parâmetros preliminares)

```python
D_SHAFT        = 30.0   mm    # *** confirmar
D_SCREW        = 100.0  mm    # *** confirmar
T_BLADE        = 4.0    mm
PITCH          = 100.0  mm    # *** confirmar
N_TURNS        = 6            # seção representativa (rosca real = ~2000mm)
L_SCREW        = 600    mm
CLEARANCE      = 3.0    mm
D_CASING_I     = 106.0  mm
W_HOPPER       = 70.0   mm
L_HOPPER_AX    = 80.0   mm
H_HOPPER       = 90.0   mm
D_RECEIVER     = 130.0  mm
CUTS_PER_TURN  = 4            # cut-flight: cortes a cada 90°
CUT_FRACTION   = 0.45         # 45% da pá removido por corte
```

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `geometria/generate_braskem_auger.py` | Script CadQuery — gera os 3 STEP files |
| `geometria/braskem_auger_casing.step` | Calha + funil + coletor |
| `geometria/braskem_auger_rotor_standard.step` | Eixo + pá helicoidal contínua |
| `geometria/braskem_auger_rotor_cutflight.step` | Eixo + pá com cortes a cada 90° |
| `literatura/braskem_dem_literatura.md` | Revisão bibliográfica DEM |
| `literatura/braskem_dem_guia_projeto.md` | Guia completo Star-CCM+ para este caso |
| `dados_cliente/` | ← dados da Braskem quando chegarem |

---

## Estratégia de Simulação

- **Dois casos:** rosca padrão vs. cut-flight
- **Física:** DEM + Hertz-Mindlin + Liquid Bridge Force (Lian 1993) para coesão hexano-PEAD
- **Malha:** Polyhedral, Base Size = 5× D50
- **Timestep DEM:** ~7.8 μs (E_soft = 10 MPa, D50 = 3 mm estimado)
- **Seção simulada:** 3–4 voltas representativas (rosca de 2m inteira = inviável computacionalmente)
- **Validação:** zonas de velocidade ≈ 0 = embuchamento

---

## Notas Técnicas

- **Granulometria:** se D50 < 100 μm → discutir coarse-graining
- **Distribuição:** usar PSD (Rosin-Rammler) em vez de diâmetro único
- **Proxy para granulometria:** pó de talco pode dar ordem de grandeza do D50, mas forma platelet ≠ PEAD. Alternativa: medição a laser em atmosfera N₂.
