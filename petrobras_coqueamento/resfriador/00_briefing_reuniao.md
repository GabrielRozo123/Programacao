# Briefing — Reunião Petrobras 13h (resfriador do coqueamento)

> Objetivo da reunião: **entender o processo** e alinhar o que o CFD entrega. Não é vender solução
> ainda — é mostrar que sabemos onde está a física e o que precisamos deles pra atacar.

## 1. O problema em uma frase
Os tubos do **resfriador** do processo de coqueamento estão **empenando** (bowing/warping). Queremos
achar a **causa-raiz** da falha. Nosso pedaço: o **CFD** que prevê o **campo de temperatura no metal**
do tubo — é essa distribuição de temperatura que, entregue ao FEA, vira tensão/deformação/fadiga.

## 2. A física do empenamento (o que causa um tubo a torcer)
Um tubo empena quando **um lado fica mais quente que o outro** e quer dilatar mais — a diferença de
dilatação curva o tubo (efeito "banana"). Três motores possíveis, todos térmicos:

1. **Gradiente circunferencial** (topo × base, ou lado × lado): dilatação diferencial → **arqueamento**.
2. **Gradiente axial** (entrada × saída) + **restrição dos suportes**: → **tensão axial** (empuxo/flambagem).
3. **Ciclagem** (coqueamento é batelada — enche/resfria/decoque): o ΔT **oscila** → **fadiga térmica
   de baixo ciclo** (o item "análise de fadiga" do cronograma).

**A pegadinha:** o empenamento é dirigido pelo **gradiente** (ΔT espacial), não pela temperatura
absoluta. Um balanço térmico 0D (só entra/sai) **não vê** o gradiente. **Só o CFD dá o mapa**.

### Suspeitos de causa-raiz (hipóteses a testar no CFD)
- **Má-distribuição de escoamento** (um passe/tubo recebe mais vazão → esquenta/esfria diferente).
- **Incrustação/coque interno** (deposição isola local → aquele lado corre mais quente → arqueia).
- **Resfriamento desigual** (lado do refrigerante mal distribuído, zonas mortas, recirculação).
- **Mudança de fase** (se condensa/vaporiza no tubo → HTC muda muito ao longo do tubo → gradiente axial forte).

## 3. Como o STAR-CCM+ ajuda (o valor do nosso CFD)
- **Conjugate Heat Transfer (CHT):** resolve **fluido + parede metálica (+ refrigerante) juntos** →
  entrega o **campo 3D de temperatura no metal** (circunferencial e axial). Esse campo **é a carga**
  que o FEA precisa.
- **Diagnóstico de escoamento:** revela má-distribuição, recirculação, zonas mortas, pontos quentes.
- **Teste de hipótese:** rodar cenários (com/sem incrustação, com/sem má-distribuição) e ver qual
  reproduz o gradiente que empena → **causa-raiz por eliminação**.
- **Exporta pro FEA:** mapeia **T (e q″/HTC, pressão)** da malha CFD pra malha estrutural (mapeamento
  por arquivo / co-simulação). O FEA faz tensão/deformação/fadiga.
- **Valida melhoria:** depois que o FEA propõe modificação, o CFD **re-simula** e confirma que o
  gradiente térmico caiu (fecha o ciclo do cronograma).

## 4. Álgebra inicial (ordem de grandeza — leva pra reunião)
Empenamento por gradiente circunferencial ΔT ao longo do diâmetro D, tubo de vão L:

```
Arqueamento:      δ ≈ α · ΔT · L² / (8·D)      (viga biapoiada, gradiente linear no diâmetro)
Tensão axial:     σ ≈ E · α · ΔT               (se o tubo estiver axialmente restrito)
```
Aço, α=12e-6/K, E=200 GPa, **premissas** L=6 m, D=0,114 m (4,5"):

| ΔT circunf. | Arqueamento δ | Tensão axial σ |
|---|---|---|
| 25 K | **11,8 mm** | 60 MPa |
| 50 K | **23,7 mm** | 120 MPa |
| 100 K | **47,4 mm** | 240 MPa (≈ escoamento do aço carbono) |

**O recado:** basta **~25 K de diferença** entre lados pra empenar ~1 cm. Gradientes assim são
**invisíveis** num cálculo médio — e é exatamente o que o CFD (CHT) prevê. *(L e D são premissas;
ajusto quando tivermos o desenho.)*

## 5. O que precisamos da Petrobras (perguntas p/ a reunião)
**Geometria & material**
- Arranjo do resfriador: casco-e-tubo? serpentina? tubo-em-tubo? Nº de tubos/passes.
- Dimensões (OD, espessura, comprimento, vão entre suportes), material dos tubos.
- Como os tubos são **apoiados/fixados** (define se ΔT vira tensão ou dilatação livre).

**Processo & fluidos**
- O que está sendo resfriado (vapor de topo do coque? gasóleo pesado? água de quench?) e o refrigerante.
- Vazões, T e P de entrada/saída de cada lado, propriedades.
- **Tem mudança de fase** (condensação/vaporização) dentro do resfriador? (muda tudo no HTC).

**Operação & falha**
- Regime **contínuo ou cíclico**? Tempos de ciclo (o coqueamento é batelada).
- O empenamento é **progressivo** (creep/ratcheting) ou **súbito**? Há histórico/medição?
- **Onde** e em que **direção** os tubos empenam? Fotos, termografia, relatório de inspeção.
- Há **incrustação/coque** medido dentro dos tubos? Espessura?

**Dados & entregáveis**
- Têm P&ID, folha de dados do trocador, desenhos 3D/CAD? (precisamos p/ simplificar a geometria).
- Formato esperado do **campo térmico** pro time de FEA (malha, software: Abaqus/Ansys?).

## 6. Escopo — o que é e o que NÃO é nosso
- ✅ **Nosso:** CFD do resfriador (escoamento + transf. de calor), campo térmico, diagnóstico de
  causa, exportação pro FEA, re-validação da melhoria no CFD.
- ❌ **Não nosso (outro setor):** FEA estrutural/térmico/modal, fadiga, tensões e deformações.
- 🔗 **Interface crítica:** a **qualidade do campo térmico CFD** define a qualidade do FEA. Alinhar
  malha, formato e frequência de troca com o time estrutural desde já.
