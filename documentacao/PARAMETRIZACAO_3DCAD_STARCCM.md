# Parametrização 3D-CAD no Star-CCM+
## Conhecimento extraído dos tutoriais de Assembly Constraints

---

## Conceito Central

O Star-CCM+ permite criar geometrias **totalmente parametrizadas** via 3D-CAD interno.
O mecanismo é: **Constraint → Expose Parameter → Design Parameter → Update Model To**

Resultado: mudar um número no painel já reconfigura toda a geometria, malha e simulação.

---

## Tipos de Constraints (Assembly Constraints Feature)

| Constraint | O que faz | Aplicação nos projetos |
|---|---|---|
| **Body Anchor** | Fixa um corpo na posição atual | Fixar o corpo do tubo/tanque |
| **Coincident** | Alinha faces, arestas ou pontos | Encostar flanges, alinhar aletas |
| **Concentric** | Alinha eixos de corpos cilíndricos | Alinhar eixo do misturador com o tubo |
| **Mid Point** | Centraliza um corpo entre dois pontos | Centralizar elemento de mistura |
| **Rigid Group** | Agrupa corpos para moverem juntos | Agrupar aletas do mesmo elemento |
| **Distance Dimension** | Mantém distância fixa entre entidades | Espaçamento entre micronizadores |
| **Planar Angle Dimension** | Controla ângulo entre duas arestas | **PRINCIPAL: ângulo das aletas, posição angular dos micronizadores** |

---

## Fluxo de Parametrização (passo a passo)

```
1. Importar geometria
   File > Import > Import CAD Model into 3D-CAD
   Ativar "Import Edge/Vertex Names"

2. Criar referência geométrica (sketch)
   Botão direito na face → Create Sketch > On Face
   Desenhar linha de referência → Apply Fixation Constraint no ponto
   OK → Sketch Imprint nas faces relevantes

3. Criar Assembly Constraint Feature
   Botão direito em Features → Create Assembly Constraint Feature

4. Aplicar Body Anchor no corpo fixo (base/tanque/tubo)

5. Aplicar Coincident/Concentric para posicionar corpos

6. Aplicar Dimension com "Expose Parameter" ativado
   → Nomear o parâmetro (ex: "Angulo", "Raio", "Altura")
   → O parâmetro aparece em: Design Parameters > [nome]

7. Modificar o parâmetro
   Design Parameters > [nome] → botão direito → Edit → novo valor

8. Atualizar a geometria
   Features > [constraint] → botão direito → Update Model To
   → Toda a montagem se reconfigura automaticamente

9. Via macro Java: automatizar varredura de parâmetros
   → Ver macros parametricas nos projetos
```

---

## Aplicação: Projeto 1 — Misturador Estático

### Parâmetros a Expor na Geometria

| Parâmetro | Tipo de Constraint | Faixa de Varredura |
|---|---|---|
| `Angulo_Aleta` | Planar Angle Dimension | 30°, 45°, 60°, 75°, 90° |
| `N_Elementos` | Pattern Count (Linear Pattern) | 2, 3, 4, 5, 6 |
| `Espaco_Elementos` | Distance Dimension | 300, 400, 500 mm |
| `Diametro_Tubo` | Sketch dimension | 14'', 16'', 18'', 20'' |

### Como criar o padrão de elementos (Linear Pattern)
```
Botão direito no corpo da aleta → Create Pattern > Linear Pattern
   Direction: eixo axial do tubo (Z)
   Count: N_Elementos → Expose Parameter como "N_Elementos"
   Spacing: Espaco_Elementos → Expose Parameter como "Espaco_Elementos"
```

### Resultado: varredura CFD automatizada
```
Para cada (Angulo_Aleta × N_Elementos):
   1. Atualizar Design Parameter
   2. Update Model To
   3. Regenerar malha
   4. Rodar simulação
   5. Extrair ΔP e CoV
→ Tabela de otimização completa sem intervenção manual
```

---

## Aplicação: Projeto 2 — Tanque com Micronizador

### Parâmetros a Expor na Geometria

| Parâmetro | Tipo de Constraint | Faixa de Varredura |
|---|---|---|
| `Raio_Micronizador` | Distance Dimension (do eixo central) | 0.2R, 0.4R, 0.6R, 0.8R |
| `Angulo_Micronizador` | Planar Angle Dimension | 0°, 45°, 90°, 120°, 180° |
| `Altura_Injecao` | Distance Dimension (do fundo) | 0.1H, 0.2H, 0.3H |
| `N_Micronizadores` | Pattern Count (Circular Pattern) | 2, 3, 4, 6, 8 |

### Como criar padrão circular (Circular Pattern)
```
Botão direito no corpo do micronizador → Create Pattern > Circular Pattern
   Axis: eixo central do tanque
   Count: N_Micronizadores → Expose Parameter como "N_Micronizadores"
   Angle: 360° / N (automático com padrão completo)
```

### Posicionamento radial parametrizado
```
Criar Sketch no plano de topo do tanque
   Desenhar linha do centro até a posição do micronizador
   Aplicar Distance Dimension = Raio_Micronizador → Expose Parameter
   Aplicar Planar Angle Dimension = Angulo_Micronizador → Expose Parameter
```

### Métrica de saída no CCM+
```
Eficiência de Incorporação = integral(α × dV) / V_tanque
   α = fração volumétrica de ar (campo do S-Gamma)
   Post-processing via Report: Volume Average of Volume Fraction (Air)
```

---

## Macro Java para Varredura Paramétrica

Ver arquivos:
- `projeto1_misturador_estatico/macros/setup/06_VarreduraParametrica.java`
- `projeto2_tanque_micronizador/macros/setup/06_VarreduraParametrica.java`

---

## Notas Importantes

1. **Sempre nomear edges e faces** ao importar (Import Edge/Vertex Names = ON)
   → Sem isso, os constraints não conseguem encontrar as entidades por nome no macro

2. **Expose Parameter ao criar a Dimension** — não depois
   → Cria o parâmetro automaticamente em Design Parameters

3. **Update Model To** é diferente de **Update Model**
   → "Update Model" atualiza para o valor atual
   → "Update Model To" aplica um valor específico passado no diálogo

4. **Para o IGES importado (nosso caso)**:
   → O IGES não tem constraints — precisa recriar as relações no 3D-CAD
   → Alternativa: criar geometria paramétrica do zero no 3D-CAD e subtrair o volume fluido
   → Recomendado: criar o tanque/tubo parametricamente e importar as aletas/micronizadores como corpos fixos

5. **Via macro Java**, o fluxo é:
   ```java
   CadModel model = sim.get(SolidModelManager.class).getObject("3D-CAD Model 1");
   DesignParameter param = model.getDesignParameterManager().getParameter("Angulo_Aleta");
   param.getQuantity().setValue(60.0);  // novo valor
   model.update();                       // recalcula geometria
   ```
