# Tutorial 04 — Conjugate Heat Transfer: Heated Fin Introduction

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Heat Transfer*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: 🟡 seções 1–5 lidas (visão geral, Importing the Mesh, Converting to 2D, Renaming Regions and
> Boundaries, Scaling the Mesh — 13/10/2026). Restante a receber.

---

## 0. Por que este tutorial

É o CHT **"puro"**: um sólido aquecido trocando calor com um fluido por **convecção natural**, em
**duas regiões** ligadas por uma **interface**. Sem multifásico, sem mudança de fase. É o esqueleto de
qualquer modelo térmico de parede: **condução no sólido + convecção no fluido + interface entre os
dois**. Os tutoriais 01–03 ensinaram a física da ebulição; este ensina a **montagem multi-região**.

## 1. O caso

| item | valor |
|---|---|
| Geometria | **aleta sólida de alumínio** dentro de uma **cavidade retangular com ar** |
| Malha | hexaédrica, **uma célula de espessura**, feita no pro-STAR, já com os tipos de contorno |
| Interface aleta–ar | **não conforme** (as malhas do sólido e do fluido não coincidem nos nós) |
| Domínio (após escala) | 10 cm × 10 cm, **2D** |
| Modos de troca | condução na aleta · difusão e **convecção natural** no ar |
| Radiação | **não incluída** |
| Solver | **acoplado** (*coupled*) |

> 💡 **Interface não conforme** = sólido e fluido podem ser malhados **separadamente**, cada um com o
> tamanho de célula que precisa, e o STAR faz a intersecção das faces na interface. Útil quando o
> sólido é fino e o fluido precisa de outra resolução. Ao criar a interface, **conferir na janela
> Output** se a área foi casada por completo — face sem par fica no contorno original (parede,
> adiabática por padrão) e o calor simplesmente não passa por ali.

> 💡 **Radiação fora** é uma escolha que tem de ser justificada caso a caso: depende de quanto o
> coeficiente radiativo `h_rad = εσ(T₁² + T₂²)(T₁ + T₂)` pesa frente à convecção. Perto da ambiente,
> `h_rad ≈ 6ε W/m²K`: com alumínio polido (ε ~0,05) é desprezível; com superfície oxidada ou pintada
> (ε ~0,8–0,9) fica **da mesma ordem** da convecção natural no ar (h ~ 5–10 W/m²K).

## 2. Importar a malha

1. `File > Import > Import Volume Mesh` → `fin.ccm`.
2. A *Output* mostra o relatório da importação; aparecem as regiões **AIR** e **AL** e uma cena de
   geometria.
3. Salvar como `heatedFin.sim`.

## 3. Malha 3D → 2D (multi-região)

Mesmos requisitos do tutorial 03 (malha no plano X-Y, fronteira em z = 0), com dois cuidados a mais
por haver **duas regiões**:

1. `Mesh > Convert To 2D` → **selecionar todas as regiões** → *Delete 3D Regions After Conversion* → OK.
2. Apagar **os dois** contínuos 3D antigos (`Physics 1` **e** `Physics 2` — um por região).

> 💡 **"Uma célula de espessura" é a forma padrão de entregar 2D ao STAR**: gera-se a malha 3D com uma
> camada e converte-se. Vale para malha vinda de outro gerador.

## 4. Renomear regiões e contornos

| original | novo nome |
|---|---|
| Região `AIR 2D` | **Fluid** |
| `wall` (Fluid) | **Air-Interface** |
| `wall 2` (Fluid) | **Vertical-Walls** |
| `wall 3` (Fluid) | **Horizontal-Walls** |
| Região `AL 2D` | **Solid** |
| `Default_Boundary_Region` (Solid) | **Fin-Interface** |
| `wall` (Solid) | **Fin-Bottom** |

> 💡 **Nomear antes de qualquer setup.** Nomes que dizem **o que é e onde fica** (`Fin-Bottom`,
> `Air-Interface`) evitam aplicar condição no contorno errado e deixam relatórios, cenas e
> exportações legíveis. Convenção sugerida: `<região>-<função>` — os dois lados de uma interface com
> nomes que se reconhecem como par.

## 5. Escala da malha (cm → m)

A malha foi feita **em centímetros sem fator de escala** no arquivo: a *Output* da importação mostra
x ∈ [0; 10], y ∈ [0; 10], z ∈ [0; 1] — e o STAR lê isso como **metros**.

1. `Mesh > Scale Mesh` → **Scale Factor = 0,01** para **as duas regiões** → *Apply* → *Close*.
2. *Reset View*.
3. `Mesh > Diagnostics` → todas as regiões → conferir a nova extensão (0–0,1 m).

> ⚠️ **Escalar todas as regiões juntas.** Escalar só uma desalinha a interface entre elas.

> 💡 Segundo tutorial seguido com malha na unidade errada (03: ×0,1; 04: ×0,01). **A leitura da
> extensão na Output da importação é o primeiro controle de qualidade** de qualquer simulação.

---

## Checklist reaproveitável (até aqui)
- [ ] Ler a extensão da malha na *Output* logo após importar; escalar **todas** as regiões juntas.
- [ ] 2D multi-região: selecionar todas as regiões na conversão e apagar todos os contínuos 3D.
- [ ] Renomear regiões e contornos **antes** do setup, no padrão `<região>-<função>`.
- [ ] Interface não conforme: conferir na *Output* se a área foi casada por completo.
- [ ] Radiação: estimar `h_rad` e comparar com a convecção antes de decidir desligá-la.

## Seções seguintes
*(a receber)*
