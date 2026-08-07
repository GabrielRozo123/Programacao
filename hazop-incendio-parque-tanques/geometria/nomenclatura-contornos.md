# Nomenclatura de contornos e importação no STAR-CCM+

Esquema de nomes e tipos de contorno do caso de incêndio em parque de tanques, e o fluxo de
importação que minimiza trabalho manual.

---

## 1. Duas formas de importar — e por que uma é melhor

A importação de `parque_tanques_cfd.step` funciona (2 bodies, `Air` e `Fire`, com os nomes de sólido
preservados pelo tradutor Siemens), mas todas as faces chegam agrupadas em `Named Faces > Default`:

| Corpo | Faces |
|---|---|
| `Fire` | 3 |
| `Air` | **32** |

Nomear 32 faces manualmente é lento e propenso a erro.

### Caminho recomendado — subtração dentro do STAR-CCM+

Como os nomes de sólido sobrevivem ao STEP, fazer a subtração no STAR-CCM+ (em vez de usar a versão
já subtraída) faz as *part surfaces* herdarem o nome da parte de origem. As faces dos tanques, das
bacias e do fogo chegam já agrupadas e rotuladas.

```
1. Importar  parque_tanques_completo.step        → 6 partes nomeadas

2. Geometry > Operations > New > Boolean > Subtract
       Target = Domain
       Tools  = Tank_T01_Source, Tank_T02_Target,
                Bund_A_Fire, Bund_B_Target, Fire
       → parte  Air , com superfícies separadas por origem

3. Geometry > Operations > New > Imprint
       Partes = Air, Fire
       → garante interface conforme entre as duas regiões

4. Assign Parts to Regions        (Air + Fire)
       Create a Region for Each Part
       Create a Boundary for Each Part Surface
```

Trabalho manual restante: **6 faces** (as do cubo do domínio, que a subtração não distingue) em vez
de 32.

> O passo de **Imprint** não existe no tutorial Steckler porque lá as duas partes já vinham
> conformes. Aqui, com geometria importada, ele evita interface não conforme entre `Air` e `Fire`.

---

## 2. Contornos do domínio — nomear manualmente

Vento em **+x**, do tanque em chamas para o tanque-alvo (orientação conservativa).

| Nome | Localização | Tipo | Observação |
|---|---|---|---|
| `Inlet` | plano **x = −30 m** | Velocity Inlet | Perfil de camada limite atmosférica (log ou potência), com k e ε/ω consistentes. **Caso sem vento: trocar para Pressure Outlet.** |
| `Outlet` | plano **x = +30 m** | Pressure Outlet | Perfil hidrostático |
| `Top` | plano **z = +30 m** | Pressure Outlet | Perfil hidrostático |
| `Side_Y_neg` | plano **y = −20 m** | Pressure Outlet | |
| `Side_Y_pos` | plano **y = +20 m** | Pressure Outlet | |
| `Ground` | plano **z = 0 m** | Wall | Face com furos onde assentam tanques, bacias e poça |

### Por que Pressure Outlet e não Symmetry nas laterais

Pluma de incêndio arrasta ar por **entranhamento** em volume considerável. Contorno de simetria
bloqueia o fluxo normal e restringe artificialmente esse arraste, distorcendo altura de chama e
temperatura da pluma. Pressure Outlet permite entrada e saída conforme a solução exigir.

### Perfil hidrostático nas demais fronteiras

O Fire and Smoke Wizard aceita **um único** `Select Pressure Boundary` e aplica nele o perfil de
pressão variável com a altura. Apontar o `Outlet`.

⚠️ As outras fronteiras de pressão (`Top`, `Side_Y_neg`, `Side_Y_pos` e, no caso sem vento, o
`Inlet`) **não** recebem o perfil automaticamente. Replicar a mesma field function manualmente —
caso contrário o campo de empuxo fica inconsistente nas bordas do domínio.

---

## 3. Contornos herdados da subtração

| Nome | Geometria | Tipo |
|---|---|---|
| `Tank_T01_Source` | Cilindro ⌀ 3,0 m em (−10, 0), h = 4,4 m + teto cônico | Wall |
| **`Tank_T02_Target`** | Cilindro ⌀ 3,0 m em (+5, 0), h = 4,4 m + teto cônico | **Wall — superfície de medição** |
| `Bund_A_Fire` | Mureta, externo x ∈ [−13,3; −0,7], y ∈ [−5,3; 5,3], h = 1,0 m — **9 faces**, 104,0 m² | Wall |
| `Bund_B_Target` | Mureta, externo x ∈ [1,7; 14,3], y ∈ [−5,3; 5,3], h = 1,0 m — **9 faces**, 104,0 m² | Wall |
| `IF_Fire` | Cavidade do fogo: lateral 78,54 m² + disco superior 19,63 m² — **2 faces**, 98,17 m² | Interface com a região `Fire` |

### Corpo `Fire` (3 faces)

| Face | Geometria | Tipo |
|---|---|---|
| `Pool_Surface` | Disco ⌀ 5,0 m em **z = 0** — 19,63 m² | **Wall** — superfície da poça, **não** é interface |
| `IF_Air` | Lateral 78,54 m² + disco superior 19,63 m² — 98,17 m² | Interface com `Air` |

> **A interface precisa ser nomeada dos dois lados.** A cavidade no `Air` e a superfície do
> cilindro no `Fire` são superfícies distintas, encostadas. Nomear apenas um lado deixa o outro em
> `Default`, e o STAR-CCM+ cria **duas** interfaces em vez de uma. Conferência: `IF_Fire` e
> `IF_Air` valem **98,17 m²** cada.
>
> O disco inferior do corpo `Fire` fica coplanar com o `Ground`, mas o ar não existe abaixo de
> z = 0 — ele é contorno externo da região `Fire`, não interface.

---

## 4. `Tank_T02_Target` — o contorno que produz o resultado

É deste contorno que sai o número do estudo. Relatórios a criar:

| Relatório | Campo | Uso |
|---|---|---|
| Surface Maximum | Radiative Heat Flux | Ponto mais exposto do costado |
| Surface Average | Radiative Heat Flux | Comparação com o modelo integral |
| Surface Maximum | Temperature (parede) | Entrada para tempo até a falha (fase CHT) |

Comparar o **Surface Average** com o baseline de fonte pontual (7,1 / 11,9 / 16,7 kW/m² conforme
χ_r = 0,15 / 0,25 / 0,35). Ver `README.md` desta pasta.

Emissividade e absortividade do costado devem ser definidas explicitamente em *Surface Materials* —
aço pintado ≈ 0,8–0,9; aço novo, bem menor. Vale como caso de sensibilidade.

---

## 5. Verificação após a importação

| Item | Esperado |
|---|---|
| Número de corpos | 6 (completo) ou 2 (cfd) |
| Volume de `Fire` | 98,2 m³ |
| Volume de `Air` | 71 811 m³ |
| Volume de cada tanque | 31,1 m³ |
| Interface `Air`/`Fire` | Conforme após o Imprint |
| Faces do domínio nomeadas | 6 |
