# Parâmetros da Simulação - Misturador Estático 18''

## Status dos Parâmetros

| Parâmetro | Valor atual | Status | Fonte |
|-----------|-------------|--------|-------|
| Diâmetro tubo | 444,5 mm (18'' Sch.40) | Estimar - CONFIRMAR | - |
| Comp. total | 2399 mm | Confirmado | Desenho técnico |
| Comp. seção misturadora | 1600 mm | Confirmado | Desenho técnico |
| N° de elementos | REV2: 19 corpos / REV4: 16 corpos | Confirmado | IGES |
| Esp. entre elementos | 400 mm | Confirmado | Desenho técnico |

## Fluidos

| Propriedade | Caldo | Polímero (P) | Fluido Auxiliar |
|-------------|-------|-------------|-----------------|
| Densidade | **? kg/m³ - CONFIRMAR** | 35% > caldo | 35% > caldo |
| Viscosidade | 1 cP (0,001 Pa·s) | 40 cP (0,040 Pa·s) | 40 cP (0,040 Pa·s) |
| Nota | "densidade 0,5" - unidade a confirmar | aniônico | - |

> **PENDENTE**: Confirmar unidade/valor da densidade do caldo.
> Estimativa provisória: 1050 kg/m³ (caldo de cana típico).

## Condições de Contorno

| Condição | Valor | Status |
|----------|-------|--------|
| Velocidade de entrada | **? m/s - CONFIRMAR** | Aguardando dados de vazão |
| Pressão de saída | 0 Pa (relativa) | Padrão |
| Temperatura | 25°C | Estimar |
| Ponto de injeção do polímero | dupla corrente / co-corrente | Confirmar configuração |

## Modelos Físicos

- **Escoamento**: Segregated Flow (SIMPLE)
- **Regime**: Permanente (Steady State)
- **Turbulência**: k-ω SST
- **Mistura**: Escalar Passivo (0 = caldo, 1 = polímero)
- **Gravidade**: Verificar se necessário (escoamento vertical?)

## Métricas de Análise

1. **Perda de carga (ΔP)** - diferença de pressão estática ponderada por área: Inlet → Outlet
2. **Coeficiente de Variação (CoV)** - índice de uniformidade da mistura na saída
   - CoV < 5%: mistura excelente
   - CoV < 20%: mistura aceitável
3. **Streamlines** - visualização de trajetórias para verificar contato com todas as aletas

## Malha

| Parâmetro | Valor |
|-----------|-------|
| Tipo | Polyhedral + Prism Layers |
| Tamanho base | 5% do diâmetro ≈ 22 mm |
| Refinamento nas aletas | 25% do base ≈ 5,5 mm |
| Camadas prismáticas | 8 camadas, stretch 1,3 |
| N° células estimado | 2–5 milhões |

## Sequência dos Macros

```
01_ImportarGeometria.java   → Importa IGES, nomear regiões/boundaries
02_ConfigurarMalha.java     → Parâmetros de malha
                            → [Gerar malha: Mesh > Generate Volume Mesh]
03_ConfigurarFisica.java    → Modelos físicos + condições de contorno
                            → [Rodar simulação]
04_ExtrairResultados.java   → Exporta ΔP, CoV, imagens
05_CompararRevisoes.java    → Tabela comparativa REV2 vs REV4
```

## Questões em Aberto

- [ ] Confirmar densidade do caldo (unidade e valor exatos)
- [ ] Confirmar vazão ou velocidade de entrada
- [ ] Confirmar temperatura de operação
- [ ] O IGES inclui o tubo externo ou só as aletas? (impacta criação do domínio fluido)
- [ ] Configuração exata do ponto de injeção do polímero (dupla corrente)
- [ ] O escoamento é vertical (considerar gravidade)?
- [ ] Versão do Star-CCM+ (para compatibilidade das APIs)
