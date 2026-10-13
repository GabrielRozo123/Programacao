# Tutorial 04 — Conjugate Heat Transfer: Heated Fin Introduction

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Heat Transfer*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: ✅ tutorial completo lido (seções 1–15: visão geral, importação, conversão 2D, nomes, escala,
> malha interna, modelos, materiais, condições iniciais e referência, interfaces, contornos, cena,
> relatórios, inicialização e execução, linhas de corrente — 13/10/2026).

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

## 6. Ver a malha interna

`Scenes > Geometry Scene 1 > Surface 1` → marcar **Mesh**. Para ver uma região de cada vez, selecionar
o nó da região (`Regions > Fluid`) — ela fica destacada na cena.

## 7. Modelos — um contínuo por região

A conversão para 2D já cria `Physics 1 2D` e `Physics 2 2D`: renomear para **Air** e **Aluminum Alloy**.

### Air (fluido)
| grupo | modelo |
|---|---|
| Espaço / Tempo | Two Dimensional · **Steady** |
| Material | Gas |
| Escoamento | **Coupled Flow** (+ Gradients) |
| Equação de estado | **Ideal Gas** — ar **compressível**: a densidade varia com T, e é isso que gera o empuxo |
| Regime | Turbulent → RANS → **Realizable K-Epsilon Two-Layer**, **Two-Layer All y+** |
| Opcionais | **Gravity** |

*(A energia do gás entra junto com Ideal Gas + Coupled Flow — conferir no nó `Models` que aparece
**Coupled Energy**.)*

### Aluminum Alloy (sólido)
| grupo | modelo |
|---|---|
| Material | Solid |
| Energia | **Coupled Solid Energy** (+ Gradients) |
| Equação de estado | Constant Density |
| Tempo | Steady |

> 💡 **Par de solvers:** fluido com **Coupled Flow** ↔ sólido com **Coupled Solid Energy**; fluido
> com **Segregated Flow** ↔ sólido com **Segregated Solid Energy** (tutorial 01 e nosso ciclone).
> Manter o par coerente entre regiões acopladas por interface.

> 💡 **Coupled × Segregated.** O acoplado resolve continuidade, quantidade de movimento e energia
> **juntas**: mais robusto quando densidade, velocidade e temperatura estão fortemente ligadas
> (compressível, **convecção natural**), ao custo de mais memória por célula. O segregado é o padrão
> para escoamento forçado incompressível e para multifásico.

> ⚠️ **Régua do regime — é mesmo turbulento?** Número de Rayleigh com ΔT ≈ 50 K (aleta ~343 K, ar
> 293 K): `Ra = gβΔT·L³/(να)` ≈ **5×10⁵ (L = 5 cm) a 4×10⁶ (L = 10 cm)**. Convecção natural só
> transiciona perto de **Ra ~ 10⁹** → o regime físico é **laminar**. O k-ε aqui é escolha didática. Em
> caso real: **calcular Ra antes** e preferir laminar abaixo de ~10⁸.

## 8. Propriedades

| material | ρ [kg/m³] | cp [J/kg·K] | k [W/m·K] | μ [Pa·s] |
|---|---|---|---|---|
| **Al** (aleta) — editar | **2 800** | **880** | **180** | — |
| Ar (default, Ideal Gas) | variável | 1 003,62 | 0,0260305 | 1,85508×10⁻⁵ |

Massa molar do ar (default): 28,9664 kg/kmol.

> ⚠️ **Ideal Gas só vale longe da saturação.** Para o ar, perfeito. Para **vapor d'água a 30–40 bar
> na saturação**, o fator de compressibilidade é Z ≈ 0,83–0,86: Ideal Gas erra a densidade em
> **−14 a −17 %** (−6 a −8 % com 90 K de superaquecimento). Para vapor em pressão alta: densidade
> constante na condição de operação ou equação de estado de vapor real.

## 9. Condições iniciais e valores de referência

| nó | valor |
|---|---|
| Air → Gravity | `[0,0; −9,81]` m/s² (−y) |
| Air → **Reference Density** | **1,27588 kg/m³** |
| Air → Initial Static Temperature | **293 K** |
| Aluminum Alloy → Initial Static Temperature | **343 K** — "perto da temperatura final esperada do sólido" |

> 💡 **Inicializar o sólido perto da resposta.** Em regime permanente, o sólido não tem convecção para
> "carregar" informação: a temperatura dele converge devagar, por difusão. Um chute inicial próximo
> do resultado economiza muitas iterações. Em caso real, usar a **régua** (balanço 1D) para o chute,
> até por Field Function se a temperatura variar por zona.

> 📌 **Reference Density 1,27588 não é o ar a 293 K** (1,2048 kg/m³ — 1,27588 corresponde a ~277 K).
> Com Ideal Gas a densidade de referência só define a **pressão piezométrica** (p − ρ_ref·g·h) e o
> termo de empuxo (ρ − ρ_ref)·g; o resultado físico não depende dela. Boa prática: usar a densidade
> do fluido **frio/ambiente**, que tira a hidrostática do campo resolvido (mesma lógica do líquido
> nos tutoriais 01–02).

## 10. Interfaces

**Sem interface, as regiões não trocam nada** — massa e energia só passam entre regiões por uma
interface.

1. Selecionar (multi-seleção) `Fluid > Boundaries > Air-Interface` **e** `Solid > Boundaries >
   Fin-Interface`.
2. Botão direito → **Create Interface** → cria a interface *in-place*.
   - Surgem `Air-Interface [Interface 1]` e `Fin-Interface [Interface 1]` nas fronteiras: na
     inicialização, **substituem** as paredes originais.
   - Surge a pasta `Interfaces` com `Interface 1`.
3. `Interfaces > Interface 1`: **Type = Contact Interface**, **Topology = In-place**.

> 💡 **Contact Interface** é o tipo para troca de calor **fluido–sólido** (e sólido–sólido). É nela
> que entra a **resistência de contato** do tutorial 01 (folga, incrustação).

> ⚠️ **Conferência pós-inicialização:** a interface só "existe" depois de inicializar. Conferir que as
> fronteiras originais (`Air-Interface`, `Fin-Interface`) ficaram **vazias** (ou só com faces sem par)
> e que as `[Interface 1]` têm a área esperada. Área que sobrou na parede original = calor que não
> passa (§1).

## 11. Condições de contorno

A aleta é um **"T" invertido** numa caixa fechada. Só há condições térmicas de parede:

| região | fronteira | condição |
|---|---|---|
| Fluid | **Vertical-Walls** | Thermal Specification = Temperature → **293 K** (paredes frias) |
| Fluid | Horizontal-Walls | adiabática (default) |
| Solid | **Fin-Bottom** | Thermal Specification = Temperature → **343 K** (fonte de calor) |
| Fluid ↔ Solid | Interface 1 | Contact Interface (condutora) — §10 |

**Caminho do calor:** base da aleta (343 K) → condução na aleta → interface → convecção natural no ar
→ paredes verticais (293 K).

> 💡 **Temperatura imposta na base = Dirichlet.** Fixa a resposta naquele ponto. Quando a fonte de
> calor é **outro fluido** (trocador), o certo é **convecção (Robin)**: temperatura do fluido + h.
> Impor a temperatura da parede seria impor justamente o que se quer calcular.

## 12. Cena da solução

1. Nova **Scalar Scene** (inclui as duas regiões) → `Scalar 1 > Scalar Field > Function = Temperature`.
2. Botão direito na cena → `New Displayer > Vector` → em `Vector 1 > Parts` selecionar **só o
   fluido**.

Temperatura nas duas regiões + vetores de velocidade no ar, atualizando durante a solução.

## 13. Relatório, monitor e gráfico

Lógica do STAR em três camadas: **Report** (o que medir e onde) → **Monitor** (frequência,
normalização) → **Plot** (gráfico X-Y).

1. `Reports > New > Flow / Energy > Heat Transfer` → *Parts* = `Solid > Fin-Interface [Interface 1]`.
2. *Create Monitor and Plot from Report*.

> 💡 **Fechar o balanço, não só monitorar um número.** Em regime permanente, com paredes horizontais
> adiabáticas:
> `Q(Fin-Bottom) = Q(Fin-Interface) = −Q(Vertical-Walls)`.
> Criar os três relatórios e um quarto com a **soma** (deve → 0). É o mesmo critério que usamos no
> ciclone (Q da interface × Q externo). Monitor plano + balanço fechado = convergido. No 2D os valores
> saem por metro de profundidade.

> 📌 Reportar sempre na fronteira **`[Interface 1]`** (a que substituiu a parede original). A
> fronteira original fica vazia depois da inicialização e daria zero.

## 14. Inicializar, conferir, rodar

1. **Initialize** (sem rodar) → olhar a cena: aleta a 343 K, ar a 293 K, velocidade zero em todas as
   células.
2. **Run** → acompanhar a cena e o monitor.
3. Salvar ao final.

> 💡 **Inicializar e olhar antes de rodar** é a conferência mais barata de condições iniciais,
> regiões e interfaces. Pega região sem contínuo, valor inicial errado e interface que não foi criada.

## 15. Linhas de corrente

Linhas de corrente são uma **derived part** (como planos e isosuperfícies) e podem entrar em qualquer
cena.

1. Com a *Geometry Scene* ativa: nova **Streamline** derived part → *Input parts* = **só Fluid**.
2. **Seed Mode = Line Seed**, ferramenta de exibição ligada, **resolução 15** (15 pontos de partida).
3. Arrastar as esferas das pontas: linha **horizontal**, **meia célula acima do topo da aleta** →
   *Create*.
4. Nova *Scalar Scene 2* → Function = Temperature → em *Parts* **desmarcar as regiões e marcar só a
   streamline** → escala **fixa: Min 300 K, Max 343 K**.

Resultado: linhas de corrente coloridas pela temperatura local — mostra a **pluma** subindo da aleta
e o ar descendo junto das paredes frias.

> 💡 **Onde semear importa.** A semente logo acima da aleta pega a pluma. Para achar
> **recirculação, estagnação e curto-circuito**, semear também nas entradas e nas regiões suspeitas.

> 💡 **Escala de cor fixa** (Min/Max manuais) é obrigatória quando as figuras vão ser **comparadas**
> entre si (cenários, malhas, alternativas). Escala automática muda a cada figura e engana o leitor.

---

## Checklist reaproveitável
- [ ] Ler a extensão da malha na *Output* logo após importar; escalar **todas** as regiões juntas.
- [ ] 2D multi-região: selecionar todas as regiões na conversão e apagar todos os contínuos 3D.
- [ ] Renomear regiões, contornos **e contínuos** antes do setup, no padrão `<região>-<função>`.
- [ ] Um contínuo por material; par de solvers coerente (Coupled ↔ Coupled Solid Energy).
- [ ] **Calcular Ra** (natural) ou Re (forçada) antes de escolher laminar × turbulento.
- [ ] Ideal Gas só longe da saturação; vapor em pressão alta → densidade constante ou vapor real.
- [ ] Gravidade + Reference Density do fluido frio.
- [ ] Inicializar o sólido **perto da resposta** (régua).
- [ ] Interface *in-place* do tipo **Contact** entre cada par de regiões; conferir a área casada depois
      de inicializar.
- [ ] Fonte de calor vinda de fluido = **convecção (Robin)**, não temperatura imposta.
- [ ] Relatórios de calor em **todas** as fronteiras térmicas + soma → 0 (balanço).
- [ ] Reportar na fronteira `[Interface]`, não na parede original.
- [ ] **Initialize** e olhar a cena antes de rodar.
- [ ] Streamlines semeadas onde está a pergunta (pluma, entradas, zonas suspeitas).
- [ ] Escala de cor **fixa** em figuras que serão comparadas.
- [ ] Radiação: estimar `h_rad` e comparar com a convecção antes de decidir desligá-la.
