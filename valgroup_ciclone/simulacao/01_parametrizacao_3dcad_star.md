# Como deixar o ciclone PARAMÉTRICO no 3D-CAD do STAR (por Dc)

> Baseado no tutorial "3D-CAD: Cyclone Separator" (Siemens). A ideia: **um único Design Parameter (Dc)**
> comanda todas as cotas — muda Dc e o ciclone inteiro se redimensiona.
> Geometria de referência já gerada: `ciclone_stairmand_Dc290_fluido.step` (Dc = 290 mm).

## 0. As proporções (Stairmand alta eficiência)
| Cota | Expressão | @Dc=290 |
|---|---|---|
| a — altura da entrada | `0.5*$Dc` | 145,0 mm |
| b — largura da entrada | `0.2*$Dc` | 58,0 mm |
| De — Ø saída de gás | `0.5*$Dc` | 145,0 mm |
| S — mergulho do vortex finder | `0.5*$Dc` | 145,0 mm |
| h — altura cilíndrica | `1.5*$Dc` | 435,0 mm |
| H — altura total | `4.0*$Dc` | 1160,0 mm |
| cone (H−h) | `2.5*$Dc` | 725,0 mm |
| B — Ø saída de pó | `0.375*$Dc` | 108,75 mm |

## 1. Criar o Design Parameter
1. `Geometry → 3D-CAD Models → New` (ou abrir o modelo existente)
2. Dentro do 3D-CAD: **`Design Parameters → New Scalar Parameter`**
3. Renomeie para **`Dc`** · **Value = 0.29 m** (o STAR trabalha em **metros**)

> ⚠️ Em expressões, **sempre `$` antes do nome**: `$Dc`, `0.5*$Dc`.
> ⚠️ Cuide da **unidade**: se o parâmetro está em m, todas as expressões saem em m.

## 2. Corpo (cilindro + cone) — usar **LOFT**
**Sketch 1 (teto, plano XY, z=0):** círculo centrado na origem, Ø = `$Dc`
**Sketch 2 (z = −h):** círculo Ø = `$Dc` → *extrude* do sketch 1 até `−1.5*$Dc` já resolve o cilindro.
**Cone:** crie um plano em `z = −1.5*$Dc` (círculo `$Dc`) e outro em `z = −4.0*$Dc` (círculo `0.375*$Dc`),
e aplique **Loft** entre os dois.

*(No tutorial da Siemens é exatamente isso: dois sketches + Loft para a seção cônica.)*

## 3. Vortex finder (saída de gás)
- Sketch no teto (z=0): círculo Ø = `0.5*$Dc`
- **Extrude para BAIXO** até `−0.5*$Dc` (o mergulho S) e **para CIMA** o quanto quiser de tubo (ex.: `1.0*$Dc`)
- **A parede do vortex finder**: faça um segundo círculo Ø = `0.5*$Dc + 2*t` e **subtraia o anel**
  (t = espessura, ex.: 0,004 m). *No domínio de fluido, o anel é metal → tem de sair.*

## 4. Entrada tangencial
- Crie um **plano de transformação** deslocado em Y (o tutorial usa `Transform Sketch Plane`)
- Sketch **retangular**: largura = `0.2*$Dc`, altura = `0.5*$Dc`
- Posicione de modo que a **face externa fique tangente** ao corpo → o centro do retângulo fica a
  `x = 0.5*$Dc − 0.1*$Dc` = `0.4*$Dc`
- **Extrude** o comprimento do duto (ex.: `1.5*$Dc`) e **una (Unite)** ao corpo

## 5. Saída de pó
- Sketch no ápice (`z = −4.0*$Dc`): círculo Ø = `0.375*$Dc`
- Extrude para baixo `0.5*$Dc` (só para acomodar a BC)

## 6. Nomear as faces (Named Faces) — faça ANTES de gerar a Part
| Nome | Face |
|---|---|
| `inlet` | face retangular na ponta do duto de entrada |
| `outlet_gas` | face circular no topo do tubo de saída |
| `outlet_dust` | face circular na base da saída de pó |
| `walls` | todo o resto |

## 7. Testar a parametrização
Mude **`Dc` de 0.29 → 0.35 m** e clique **`Update 3D-CAD`**.
Se tudo estiver por expressão, o ciclone inteiro se redimensiona. **Se alguma cota ficar fixa, ela não
foi escrita como expressão** — volte nela.

---

## 💡 Por que parametrizar (o argumento pro Humberto/Lucas)
O Humberto notou que o ciclone **não ficou grande** (~1,16 m de corpo; 1,59 m com os stubs de CFD) — e o
Lucas já esperava isso. **Com Dc parametrizado, isso deixa de ser opinião e vira estudo:**

| Dc | v_i @100% | d\* | ΔP | |
|---|---|---|---|---|
| 0,22 m | 26,5 m/s | 6,98 µm | 88,5 mbar | ❌ |
| 0,25 m | 20,5 m/s | 8,46 µm | 53,1 mbar | ❌ |
| **0,29 m** | **15,2 m/s** | **10,57 µm** | **29,3 mbar** | ✅ **escolhido** |
| 0,32 m | 12,5 m/s | 12,25 µm | 19,8 mbar | ✅ |
| 0,35 m | 10,5 m/s | 14,02 µm | 13,8 mbar | ✅ |
| 0,40 m | 8,0 m/s | 17,12 µm | 8,1 mbar | ✅ |

**Menor Dc → corta mais fino, mas ΔP explode** (∝ 1/Dc⁴). O **Dc = 0,29 m** é o ponto que respeita o
limite de 40 mbar com folga. Com o parâmetro pronto, dá para rodar um **sweep** e entregar a curva
**d\* × ΔP × Dc** — a justificativa numérica do tamanho escolhido.

> **Nota:** o STAR também permite ligar o Design Parameter ao **Design Manager** e varrer Dc
> automaticamente. Se quisermos entregar a curva, é o caminho.
