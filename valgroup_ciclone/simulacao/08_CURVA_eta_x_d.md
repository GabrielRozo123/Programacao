# 08 — CURVA η × d · Dc = 307 mm · 100 % de vazão

> Campo base: **Rodada 8** (k-ω steady · `Outlet` · parede convectiva · ΔP = 1.955,6 Pa).
> Método: **η = 1 − |mdot_gas| / mdot_inj** (ver `07_EXECUCAO` §8).
> Fase Lagrangeana: **ρ_p = 1500 kg/m³** · classes monodispersas · 5.082 parcels.

---

## 1. Resultados medidos

| d (µm) | sub-steps | ativas no fim | **η c/ dispersão** | **η s/ dispersão** | Lapple (d\*=8,28) |
|---|---|---|---|---|---|
| **1** | 150.000 | 34 (0,67 %) ✅ | **22,70 %** | — | 1,4 % |
| **2** | 50.000 ⚠️ | 1.325 (26,1 %) ⚠️ | *62,0 %* ⚠️ | — | 5,5 % |
| **2** | 150.000 | 968 (19,1 %) | — | **19,9 %** | 5,5 % |
| **5** | 150.000 | 19 (0,37 %) ✅ | **31,34 %** | — | 26,7 % |
| **50** | 20.000 | 5.077 (travadas) ✅ | **100,00 %** | — | 97,3 % |

*(nas classes grossas a fração ativa não cai — travam na parede — mas o η já está determinado
porque `mdot_gas` zera cedo; ver `07_EXECUCAO` §9.4)*

---

## 2. ⚠️ INCONSISTÊNCIA A RESOLVER — o ponto de 2 µm

| d (µm) | η |
|---|---|
| 1 | 22,7 % |
| **2** | **62,0 %** ← |
| 5 | 31,3 % |

**Eficiência de grade tem de ser monotônica** — mais inércia, mais captura. 2 µm acima de 5 µm
é fisicamente impossível.

**Causa:** o 2 µm é o **único que rodou a 50.000 sub-steps** (antes da correção do §9.4), com
**26,1 % das parcelas sem resolver** — todas contadas como retidas.

⇒ **Refazer o 2 µm a 150.000.**
⇒ **Previsão registrada: η(2 µm) entre 22,7 % e 31,3 %** — provavelmente **26 a 28 %**.

Se cair nessa faixa, a curva fecha por **consistência interna**, o que vale tanto quanto a
comparação com Lapple.

---

## 3. A assinatura da dispersão isotrópica

| d (µm) | CFD | Lapple | **razão** |
|---|---|---|---|
| 1 | 22,7 % | 1,4 % | **16,2** |
| 5 | 31,3 % | 26,7 % | **1,17** |
| 50 | 100,0 % | 97,3 % | **1,03** |

A razão **cai monotonicamente com o tamanho**: quanto mais leve a partícula, mais ela obedece ao
chute turbulento radial que o modelo isotrópico exagera. É o mesmo mecanismo que o teste
com/sem dispersão isolou (§10 do `07_EXECUCAO`): 2 µm vai de **62,0 % para 19,9 %** ao desligar
o modelo.

**Formato da curva:** a ponta fina fica **achatada** (22,7 % → ~27 % → 31,3 % entre 1 e 5 µm) —
característico do regime dominado por transporte turbulento, onde a captura deixa de depender da
inércia. O fenômeno é real; aqui está **exagerado pela isotropia** do k-ω.

---

## 4. O que falta

| classe | c/ dispersão | s/ dispersão |
|---|---|---|
| 1 µm | ✅ 22,70 % | ⏳ |
| **2 µm** | ⚠️ **refazer a 150.000** | ✅ 19,9 % |
| 5 µm | ✅ 31,34 % | ⏳ |
| 10 µm | ⏳ 150.000 | — |
| 20 µm | ⏳ 150.000 | — |
| 50 µm | ✅ 100,00 % | — |
| 75 µm | ⏳ 20.000 | — |
| 150 µm | ⏳ 20.000 | — |

Depois: repetir a **50 % de vazão** (v_i = 6,80 m/s · `mdot_inj` = 1,389e-3).

---

## 5. Premissas e limitações — para o entregável

1. **η = 1 − fuga.** Partícula que trava na parede é contada como retida. Fisicamente correto
   (está no strand), mas **não representa reentranhamento** ⇒ viés levemente otimista, maior no
   grosso. Medido: +2,7 pts em 50 µm sobre Lapple.
2. **Dispersão turbulenta isotrópica** (k-ω, Boussinesq) **superestima a captura de finos**. O
   transporte radial real é suprimido pelo gradiente centrífugo. ⇒ **A ponta fina é reportada
   como BANDA**, entre os casos com e sem dispersão.
3. **ρ_p = 1500 kg/m³.** A planilha do cliente usa 776,75 (densidade **aparente do leito**,
   abaixo do mínimo de 1500 que a própria tabela de valores usuais dela declara). Conversão para
   qualquer outra densidade ou viscosidade: `07_EXECUCAO` §9.2 (número de Stokes).
4. **Sensibilidade à malha no bico** não quantificada — item de estudo futuro.
5. A conversão para **eficiência global** exige a PSD, cuja fração abaixo de 61 µm **não é
   medida** (peneiramento) e vale **17 pontos** de η_global —
   `dimensionamento/sensibilidade_finos.py`. **É a maior incerteza do projeto**, maior que a
   banda da dispersão (5,7 pontos).
