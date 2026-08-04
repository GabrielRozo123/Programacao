# Descritivo da geometria — domínio acoplado ejetor + aerador + reator

> Todas as cotas em **mm**, no sistema do CAD original do cliente
> (`sugar_dominio_fluido_completo.step`). **z = 0** é a referência do CAD;
> a superfície livre do líquido fica em **z = +1220**.
> Arquivo: `ACOPLADO_aerador_reator_ejetor_fluido.step` — 1 sólido, **169,4 m³**.

---

## 1. ⚠️ Sobre a altura: 7 m ou 3 m?

**A coluna de líquido tem 7,1 m no aerador e 7,65 m no reator.** Medido no domínio fluido:

| corpo | z inferior | z superior | **altura de líquido** |
|---|---|---|---|
| **Aerador** | −5892 | +1220 | **7112 mm = 7,11 m** |
| **Reator** | −6431 | +1220 | **7651 mm = 7,65 m** |

**A cota de 3 m vem de outro lugar:** no CAD do ejetor (Brendo), a lança termina em Y = −3000,
ou seja, **3 m de lança**. Como aquele era o único CAD do ejetor disponível, é natural a
associação — mas ali são **3 m de lança**, não a altura do tanque.

No modelo acoplado a lança foi **alongada para 7087 mm**, para alcançar a cota de descarga que
foi determinada a manter (a mesma das 3 lanças antigas).

---

## 2. Os tanques

Medidos sólido a sólido no domínio fluido:

| corpo | volume | Ø | eixo (x, y) | z |
|---|---|---|---|---|
| **Reator** | 139,86 m³ | **5080 mm** | (200, −6282) | −6431 a +1220 |
| **Aerador** | 20,18 m³ | **2032 mm** | (200, −440) | −5892 a +1220 |
| Passagem (fundo) | 4,35 m³ | — | — | −4850 a −250 |
| Canal do topo | 5,31 m³ | — | — | −211 a **+1084** |

- **Distância entre eixos** reator ↔ aerador: **5842 mm**
- As **duas superfícies livres estão na mesma cota, z = +1220**
- ⚠️ O **canal do topo termina em z = +1084**, ou seja, **136 mm abaixo da superfície livre** —
  é um duto submerso, não uma comunicação de superfície

---

## 3. O ejetor — percurso do fluido, de cima para baixo

Perfil interno levantado **cota a cota no CAD nativo** e conferido contra a lista de peças do
desenho de conjunto CSA01-300-000-01.

| # | elemento | Ø interno | z | observação |
|---|---|---|---|---|
| 1 | **Entrada de xarope** — bocal 8" **vertical** | 202,7 | topo em **+2824,5** | item 25, flange solto 8" |
| 2 | **Coletor (header) 8"** horizontal | 202,7 | **+2524,5** | 1400 mm de comprimento |
| 3 | **4 ramais 4"** | 102,3 | +2430,5 → +1890,8 | item 13, Sch40 |
| 4 | ⭐ **4 portas de ar 1/2"** | **15,8** | **+2208,5** | laterais (+Y) · item 18, válvula esfera 1/2" BSP |
| 5 | **Contração 4"→2"** | 102,3 → **42,8** | +1890,8 → +1865,5 | 2" **Sch160** (item 11) · razão **5,71:1** |
| 6 | **Bico — 7 furos Ø9** | 9,0 (×7) | +1865,5 → +1840,8 | PCD Ø27 · comprimento 24,7 mm |
| 7 | **Lança 2½"** | 62,7 (OD 73,0) | +1840,8 → **−5246,5** | **7087 mm** |
| 8 | **Descarga no aerador** | — | **−5246,5** | **6466 mm submersa** |

### ⚠️ O achado geométrico
A porta de ar (item 4, z = +2208,5) está **317,7 mm A MONTANTE** da contração (item 5,
z = +1890,8) — ou seja, no trecho de 4", **onde a pressão é máxima**.

Num eductor convencional a injeção fica **a jusante do bocal**, na zona de baixa pressão do jato.

---

## 4. Arranjo das 4 lanças

| | |
|---|---|
| Quantidade | **4** (substituem as 3 anteriores) |
| Posição | x = **−325 · +25 · +375 · +725** · y = **−440** |
| Passo | **350 mm** |
| Raios ao eixo do aerador (x=200) | 525 · 175 · 175 · 525 mm |
| Raio do aerador | 1016 mm — **cabem com folga** |
| Cota de descarga | **z = −5246,5** (a mesma das lanças antigas) |

### O que foi removido
As **3 lanças antigas** (Ø externo 84,8 mm, de z = −5246,5 a +1865,5), que ficavam em
(464, −288) · (−64, −288) · (200, −745). O volume que elas ocupavam foi **devolvido ao fluido**.

---

## 5. Velocidades no percurso (a 130,3 m³/h)

| seção | Ø | **v (m/s)** | Re |
|---|---|---|---|
| bocal de xarope 8" | 202,7 | 1,12 | 47 |
| ramal 4" | 102,3 | 1,10 | 23 |
| garganta 2" Sch160 | 42,8 | 6,29 | 56 |
| **furos do bico Ø9** | 9,0 | **20,55** | **38** |
| lança 2½" | 62,7 | 2,93 | 38 |

**Máximo do domínio: Re = 56** — contra Re ≈ 2300 de transição. Escoamento **laminar em todo o
circuito** (µ = 6,5 Pa·s).

---

## 6. Decisões incorporadas

| decisão | origem |
|---|---|
| Manter a **cota de descarga** das lanças anteriores | Marcus |
| Manter as **proporções do CAD** do ejetor | Marcus |
| **Remover as 3 lanças antigas**, deixar só os ejetores | Marcus |
| Incluir o **tubo de entrada de ar** (1 kgf/cm²) na geometria | Ito / Brendo |
| Incluir a **entrada de xarope por cima**, que alimenta as lanças | Ito |
| Topo do aerador como **parede** | Marcus |

---

## 7. Premissas declaradas

1. **Posição radial das lanças.** Fileira centrada no eixo do aerador e alinhada com X.
   O CAD de conjunto **não define a orientação** — é a única premissa geométrica restante.
2. **Comprimento da lança.** O CAD do ejetor tem 3 m; foi alongada para 7087 mm para alcançar a
   cota de descarga determinada. A **cabeça do ejetor** (coletor → ar → contração → bico) mantém
   as cotas **exatas** do CAD.
3. **Superfícies livres** tratadas como tampa rígida (*rigid lid*), no plano z = +1220.
4. **Sucção da bomba** não integra o domínio — o retorno global do tanque é aproximado.
   Não afeta os resultados de pressão no ejetor, que são governados pela cabeça e pela lança.
