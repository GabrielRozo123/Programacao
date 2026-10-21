# 09 — Surface Wrapper (referência): quando usar, quando NÃO usar

> Notas de leitura da documentação do STAR-CCM+ (páginas *Surface Wrapper*, *Surface Wrapper Properties*, *Gap Closure*,
> *Contact Prevention*, *Leak Detection*), em palavras nossas, + a lição do projeto de dispersão atmosférica (21/10/2026).

---

## 1. O que o wrapper é

Uma operação que "embrulha" a geometria de entrada e devolve uma **superfície triangulada fechada, manifold e sem
interseções**. Ele constrói uma árvore de células (octree) com o tamanho de superfície pedido e projeta a pele de fora
para dentro — por isso **fecha tudo que for menor que a célula**.

**Foi feito para CAD ruim:** peças que se interceptam, furos e frestas, faces desencontradas, superfícies duplicadas e
internas, detalhe demais. Ele fecha furos, "veste" duplicatas, remove o que é interno e simplifica o detalhe.

Se a entrada **já é** fechada, manifold e sem interseções, o wrapper não tem o que consertar — só perde fidelidade.
Nesse caso o caminho é **Surface Remesher** (melhora os triângulos mantendo a forma) → volume mesher.

## 2. Propriedades que importam

| propriedade | o que faz | quando ligar |
|---|---|---|
| *Per-Part Meshing* | embrulha cada part separado (nova descrição por part, sem part novo; interfaces ignoradas → malha não conforme entre parts) | quando trimmer/thin mesher não fecham a interface |
| *Perform Curvature Refinement* | mais faces onde a curvatura é alta | cilindros, bocais |
| *Perform Proximity Refinement* | mais faces onde duas superfícies estão próximas | **frestas** que precisam continuar abertas |
| *Perform Gap Closure* | fecha furos menores que um tamanho, ou a partir de *seed points*, ou ambos | separar volumes (ex.: fechar uma folga indesejada) |
| *Create Weak Contacts With Input Parts* | contatos que viram interfaces ao atribuir regiões | multi-região |
| *Perform Partial Wrapping* / *Local Surface Wrapping* | embrulha só parte das faces | exige **Legacy Wrapper** |
| *Link Output Part Name* | o part de saída leva o nome da operação | sempre (organização) |
| *Legacy Wrapper* | algoritmo antigo, memória compartilhada | só para wrap parcial ou local |

O wrapper padrão (desde 2306) roda em paralelo com memória distribuída; o *Mesher Execution Mode* é ignorado, exceto
*Concurrent* (que força serial). Herança de nomes: se shell e sólido se sobrepõem, a face herda do shell; entre dois
sólidos sobrepostos a escolha é **arbitrária** → nomes de faces coincidentes podem trocar.

## 3. Gap Closure × Contact Prevention × Proximity — não confundir

| ferramenta | objetivo | detalhe |
|---|---|---|
| **Gap Closure** | **fechar** uma abertura (para separar dois volumes) | fecha furos < *Size*, desde que exista parte do volume mais longe da parede que esse tamanho; ou por *seed point*. Resultado do padrão ≠ legacy |
| **Contact Prevention** | **impedir** que duas superfícies próximas se fundam | conjuntos de 1 grupo (todas contra todas) ou 2 grupos (grupo A contra grupo B); *Minimum Size* ≈ a **maior** distância que se quer manter separada — abaixo disso não é garantido; pode ser limitado a um *Volume of Influence* |
| **Proximity Refinement** | refinar a superfície onde há proximidade | ajuda a fresta a sobreviver, mas sem garantia |

**Leak Detection:** traça um caminho de um ponto fonte a um ponto alvo na octree **antes** de embrulhar; se achar, mostra
onde a superfície tem furo (na geometria original). Consertos feitos dentro da ferramenta valem só para a representação
de importação — consertar de verdade no part (*Surface Repair*), senão somem ao reinicializar a malha.

## 4. Lição do projeto atmosférico (domínio de 1,2 km + 65 obstáculos)

- Com o domínio importado separado e *Subtract* + wrapper no STAR, uma fresta de **5 cm** entre um tanque e uma laje
  (CSV com altura incluindo os bocais) virou "cola" — o wrapper com 0,25 m não a enxerga. Também havia uma fresta de
  **2 mm** entre a placa de descarga e o exaustor.
- Correção na origem: alturas pelo costado/teto (bocais são acessórios) e placas encostadas; **a subtração foi feita fora
  do STAR** (OpenCascade, primitivas exatas) gerando um **STL único do volume de ar**, estanque (0 arestas livres, 0
  não-manifold), com cada superfície nomeada (`ld_celulose_dispersao_o3/geometria/gen_volume_fluido.py`).
- No STAR: *Import Surface Mesh* → **Surface Remesher + Trimmed + Prism Layer**, sem 3D-CAD, sem Subtract, **sem
  wrapper**. O wrapper fica de plano B (se o remesher reclamar), com *Proximity Refinement* + *Contact Prevention* nas
  frestas reais (tanque × laje, pilares × tanques).

**Regra geral:** geometria por primitivas, gerada por script → volume de fluido subtraído no script → remesher.
CAD de cliente sujo (milhares de peças, frestas) → wrapper, com contact prevention onde a fresta é física.
