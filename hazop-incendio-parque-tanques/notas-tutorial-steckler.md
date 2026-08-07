# Notas — Tutorial "Fire and Smoke Wizard: Steckler Room"

Leitura crítica da documentação do Simcenter STAR-CCM+ (versão 21.02.007-R8), com foco em
**o que o assistente configura automaticamente** e em **o que transfere para o caso do parque de
tanques** descrito no `README.md`.

> **Status: em construção.** Baseado nas páginas de documentação recebidas até agora
> (visão geral, atribuição de regiões, geração de malha, propriedades do fogo, revisão de modelos).
> Faltam as páginas de condições iniciais/de contorno, solver/passo de tempo e pós-processamento.

---

## 1. Configuração do assistente

O Fire and Smoke Wizard **não está na barra de ferramentas por padrão**. Para habilitar:
`Window > Toolbars > Customize`, localizar *Fire and Smoke Wizard* e arrastar o ícone para uma barra.

### Convenções do assistente

| Item | Valor |
|---|---|
| Gravidade | direção −z (z para cima) |
| Densidade de referência | 1,2 kg/m³ |
| Altitude de referência | (0, 0, 0) m |

### Aba *Fire Dynamics*

| Propriedade | Valor |
|---|---|
| Turn On Fire Regions | `Fire` |
| Select Pressure Boundary | `Room: Outlet` |
| Max Simulation Time | 200 s |
| alpha | 3 |
| p | 2 |
| Limit Q | **Ativado — 0,0629 MW** |
| Set Graph Parameters → End X Range | 50 |

Ao aplicar, o assistente cria automaticamente:

1. a **fonte de fogo** (fonte volumétrica de calor na região `Fire`);
2. um **contorno de pressão variando com a altura** (perfil hidrostático no `Outlet`);
3. uma **fonte escalar** (escalar passivo usado como "fumaça" para visualização).

---

## 2. Decodificação dos parâmetros

### 2.1 Q = 62,9 kW

`Limit Q = 0,0629 MW` corresponde ao ponto de ensaio de **62,9 kW**, que é o caso do Steckler mais
usado como referência em validação de CFD de incêndio.

### 2.2 alpha = 3, p = 2 — partida suave, não curva de crescimento

A forma é `Q̇ = α · t^p`, ou seja, um **incêndio t-quadrado**. Porém:

| Classificação t² (NFPA/SFPE) | α aproximado [kW/s²] |
|---|---|
| Slow | 0,0029 |
| Medium | 0,0117 |
| Fast | 0,0469 |
| Ultra-fast | 0,1876 |
| **Tutorial** | **3** |

O valor está ordens de grandeza acima de *ultra-fast*. Consequência: o patamar de 62,9 kW é atingido
em **menos de 5 s** se α estiver em kW/s², e em fração de segundo se estiver em MW/s² — **confirmar a
unidade no diálogo do assistente**. Em qualquer das leituras, o tempo de rampa é desprezível frente
aos 200 s de simulação.

**Interpretação:** o experimento de Steckler usava queimador a gás em **regime permanente**. O t² aqui
não modela crescimento de incêndio — é apenas uma **partida suave numérica** para evitar choque em
t = 0. Os ~195 s restantes rodam a potência constante, buscando o quase-permanente para comparar com
o dado experimental estacionário.

> ⚠️ **Não reaproveitar α = 3 no caso da poça** supondo que seja um parâmetro físico de crescimento.

---

## 3. Malha

### 3.1 Receita do tutorial

- Operação: **Automated Mesh** sobre as parts `Fire` e `Room`
- Meshers: **Surface Remesher** + **Polyhedral Mesher** + **Prism Layer Mesher**
- **Base Size = 0,1 m**
- **Minimum Surface Size = 50 % da base** (evita células muito pequenas dentro da part `Fire`)
- **Surface Control**: prism layers **desativados** em `Fire.Interface` e `Room.Interface`
- **Part Control** sobre `Fire`: `Volume Growth Rate = Custom = 1.0`
  (força células dentro da part de fogo com tamanho semelhante ao restante da malha)

### 3.2 Verificação de resolução — a malha do tutorial é grosseira

Aplicando o critério de diâmetro característico de fogo:

```
D* = ( Q̇ / (ρ∞ · c_p · T∞ · √g) )^(2/5)
   = ( 62,9 / (1,2 × 1,005 × 293 × 3,132) )^0,4
   ≈ 0,32 m
```

Com δx = 0,1 m (base size do tutorial):

```
D*/δx ≈ 3,2
```

A faixa de prática consagrada vai de **4 (grosseiro) a 16 (refinado)**. O tutorial roda **abaixo do
limite inferior** — proposital, para o caso rodar rápido. Isso significa que **o resultado padrão do
tutorial não é independente de malha**, e essa limitação precisa ser declarada em qualquer divulgação
dos perfis comparados com o Steckler.

### 3.3 Estudo de malha sugerido (barato)

Sala de 2,8 × 2,8 × 2,18 m ≈ **17 m³** — refinar custa pouco:

| Base Size | D*/δx | Células (ordem de grandeza) |
|---|---|---|
| 0,1 m (tutorial) | 3,2 | ~2–4 × 10⁴ |
| 0,05 m | 6,4 | ~2–3 × 10⁵ |
| 0,033 m | ~10 | ~0,5–1 × 10⁶ |

**Entregável de maior valor deste tutorial:** um único gráfico com o perfil de temperatura e
velocidade no vão da porta para as **três malhas + dado experimental de Steckler**. Demonstra a
distinção entre **verificação** (convergência de malha) e **validação** (comparação com experimento) —
distinção que raramente aparece em divulgação de CFD.

A página de visão geral informa que o **line-probe já está posicionado na stack de medição
experimental**, ou seja, o ponto de comparação vem pronto.

---

## 4. Regiões e contornos

- `Geometry > Parts` → multi-seleção de `Fire` e `Room` → **Assign Parts to Regions**
  - *Create a Region for Each Part*
  - *Create a Boundary for Each Part Surface*
- Resultado: **duas regiões** com interface entre elas, mais o contorno de saída
- `Regions > Room > Boundaries > Outlet` → **Type = Pressure Outlet**

A arquitetura de **região separada para o volume de chama** é o padrão a replicar no caso do parque
de tanques.

---

## 5. Modelos de física

Configurados automaticamente pelo assistente:

- Transiente (unsteady), malha tridimensional
- **Gás ideal levemente compressível** (ar)
- Escoamento **turbulento e não-isotérmico**
- Modelo de turbulência **low-Re** *(o nome completo não consta na página recebida — verificar)*
- **Segregated Flow Solver**
- **Gravidade** ativada

Inspecionar em `Continua > Physics 1 > Models`.

### 5.1 Observação central: não há modelo de combustão

A lista de modelos **não inclui combustão**. O fogo é representado por **fonte volumétrica de calor +
escalar passivo**. Isso confirma a abordagem recomendada na seção 4.3 do `README.md` (etapa 1 —
fonte prescrita em vez de química reativa): é a mesma estratégia adotada pela própria Siemens no
tutorial de incêndio.

### 5.2 Pendências de verificação

| Item | Por quê |
|---|---|
| **Modelo de radiação e coeficiente de absorção** | A visão geral afirma que o caso inclui "radiation and wall heat absorption", mas a página de modelos não lista radiação. É o dado mais importante para transpor ao caso dos tanques — localizar e registrar. |
| **Nome do modelo low-Re e y+ resultante** | Formulação low-Re exige resolver a camada próxima à parede (y+ ~ 1) para que a absorção de calor pela parede esteja correta. Os prism layers foram desativados **apenas** nas interfaces `Fire`/`Room`, permanecendo ativos nas paredes — verificar o y+ obtido. |
| **Modelo de fuligem** | Aparentemente ausente. Aceitável para queimador a gás de pequeno porte; **inaceitável** para poça de solvente aromático, onde a fuligem domina a emissão radiante. |

---

## 6. Transposição para o caso do parque de tanques

### Transfere bem

- **Arquitetura de duas regiões**: part dedicada ao volume de chama, com `Volume Growth Rate = 1.0` e
  prism layers desativados na interface. Receita direta para construir a poça.
- **Contorno de pressão com perfil hidrostático** — essencial em escoamento dirigido por empuxo.
- **Filosofia de fonte volumétrica prescrita** em vez de combustão reativa.
- **Metodologia de verificação por D\*/δx.**

### Não transfere

| Item | Motivo |
|---|---|
| α = 3 | Partida suave numérica, não crescimento físico |
| Ausência de fuligem | Fuligem domina a radiação em solvente aromático |
| Base Size = 0,1 m | Para Q̇ ≈ 48 MW tem-se D\* ≈ 4,5 m → δx ≈ 0,3 m |
| Domínio confinado | O caso dos tanques é externo, com camada limite atmosférica e vento |

---

## 7. Próximas páginas a analisar

- Condições iniciais e de contorno (paredes, absorção de calor)
- Configuração do solver e do passo de tempo
- Pós-processamento e comparação com o dado experimental (line-probe)
