# Impelidor paramétrico (Fase 2 — Ito)

CAD paramétrico do agitador do reator, para o **estudo de sensibilidade** pedido pelo Ito:
variar **diâmetro, ângulo das pás e número de pás** e medir potência/Np/Nq.

Base: **Agimix AGX-PBW800** (hidrofólio duplo, 3 pás/estágio, Ø800 mm, eixo Ø69,85 mm).

## Os 3 parâmetros (o que o Ito pediu)
| Parâmetro | Símbolo no script | Default | Papel |
|---|---|---|---|
| Diâmetro (ponta-a-ponta) | `D_IMPELIDOR` | **800 mm** | raio de ponta = D/2 (mantido fixo p/ qualquer ângulo) |
| Ângulo das pás (passo) | `ANGULO_PA` | **30°** | 0° = disco plano · 90° = pá radial (reta) |
| Número de pás/estágio | `N_PAS` | **3** | arranjadas a 360/N |

## Como gerar
```bash
python3 gen_impelidor_parametrico.py            # default (Ø800, 30°, 3 pás)
python3 gen_impelidor_parametrico.py 700 24 4   # D=700 mm, ângulo=24°, 4 pás
```
Saídas (mm — **importar no STAR em mm**):
- `impelidor_parametrico.step` — **1 estágio** (o que se varre no MRF)
- `impelidor_parametrico_duplo.step` — 2 estágios (igual ao real, p/ conferência)
- `preview_impelidor.png` — render de checagem

## Modelagem — decisão e ressalva
- É um **pitched-blade** (pás planas de passo dirigível). O real é hidrofólio (perfil curvo/torcido),
  mas para **tendências de Np/Nq vs D/ângulo/nº de pás** o pitched-blade é o modelo padrão e robusto —
  e é o único que dá o "ângulo" como **um número varrível**. Refinar para perfil hidrofólio só se a
  validação de Np do caso-base exigir.
- **Passo sobre o eixo radial:** a ponta fica em D/2 para **qualquer** ângulo (o Ø varrido não encolhe
  com o passo). Verificado: raio de ponta = D/2 (±canto retangular ~1-2%).
- Fixos ajustáveis no topo do script: eixo Ø69,85 · cubo Ø130×90 · espessura 10 mm · corda 0,19·D ·
  espaçamento de estágios 3900 mm.

## Uso no Design Manager (STAR-CCM+)
Duas rotas:
1. **Batch de STEPs (rápido, já funciona):** gerar um `.step` por combinação com o CLI acima e usar o
   **Part-Replacement** do Design Manager (tutorial "Part-Replacement Using Design Manager") para trocar
   o impelidor a cada design. Bom para varredura discreta (poucas combinações).
2. **Paramétrico nativo (contínuo):** reconstruir o impelidor no **3D-CAD do STAR** com `D`, `ângulo`,
   `nº de pás` como **Design Parameters** → o Design Manager morfa/remalha sozinho. Este script serve de
   **referência geométrica** (medidas, construção) para replicar os sketches.

**Regra de ouro (custo):** varrer **só no REATOR** (MRF permanente, minutos/design). NÃO colocar o
aerador transiente no sweep.

## Responses a monitorar
Potência do agitador (meta **< 25 kW**), **Np**, **Nq**, Reynolds do impelidor, torque — os mesmos da
Tabela 1 do deck da Fase 1.

## Validação
Rodar o **caso-base (Ø800, 30°, 3 pás)** e conferir contra a Fase 1 (P≈4,07 kW · Nq=0,345 · Np/est=0,76).
Bateu → a parametrização está calibrada e o sweep é confiável.
