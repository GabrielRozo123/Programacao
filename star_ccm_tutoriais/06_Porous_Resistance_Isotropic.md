# Tutorial 06 — Porous Resistance: Isotropic Media

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Incompressible Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: ✅ material recebido lido (13/10/2026): visão geral, Scaling the Mesh, Setting Up the Models,
> Specifying Porosity Coefficients, Setting Boundary Conditions and Values.

---

## 0. Por que este tutorial

Meio poroso = representar uma peça cheia de pequenos canais (catalisador, filtro, **demister**,
colmeia, leito, **feixe de tubos**) **sem malhar os canais**. A peça vira uma região com uma
**resistência distribuída** ao escoamento, calibrada para dar a perda de carga certa. É o que permite
pôr um elemento com milhares de passagens num modelo de equipamento inteiro.

## 1. O caso

| item | valor |
|---|---|
| Geometria | duto com um **catalisador cilíndrico** no meio (região porosa) |
| Região porosa | **comprimento 0,03 m**, **diâmetro 0,1 m** (0,1 × 0,03 × 0,1 m após escala) |
| Escoamento | ar, turbulento, **incompressível** (densidade constante), regime permanente |
| Entrada | **20 m/s** |
| Resistência | **isotrópica**: P_i = **25 kg/m⁴**, P_v = **1 500 kg/m³·s** (valores típicos de catalisador) |

### A lei de perda de carga

```
Δp / L = P_i·|v|·v + P_v·v        v = velocidade SUPERFICIAL (a do duto vazio)
```

| termo | coeficiente | física |
|---|---|---|
| **inercial** P_i·v² | *Porous Inertial Resistance* [kg/m⁴] | perdas de forma/expansão — dominam em velocidade alta |
| **viscoso** P_v·v | *Porous Viscous Resistance* [kg/m³·s] | atrito em canais finos (Darcy) — domina em velocidade baixa |

Os coeficientes vêm de **ensaio ou catálogo** (Δp × v) ou de **correlações** (Ergun para leitos,
correlações de feixe de tubos etc.).

### Régua deste caso
Os dois termos se igualam em `v = P_v/P_i = 60 m/s`: abaixo disso **domina o viscoso**.

| v superficial [m/s] | Δp na camada de 0,03 m [Pa] | parcela viscosa |
|---|---|---|
| 1 | 46 | 98 % |
| 5 | 244 | 92 % |
| 10 | 525 | 86 % |
| 20 | 1 200 | 75 % |

> ⚠️ A velocidade **no catalisador** não é necessariamente os 20 m/s da entrada: se a área da entrada
> for menor que a do catalisador, a velocidade superficial cai na razão das áreas. **Conferir a
> velocidade superficial média na região porosa** (relatório) antes de comparar com a régua.

**Ferramenta:** [`coef_poroso.py`](coef_poroso.py) faz o caminho inverso — ajusta P_i e P_v a pontos
(v, Δp) de catálogo ou ensaio, ou calcula por Ergun. Conferido: recupera 25 / 1 500 a partir da
tabela acima.

## 2. Escala da malha

`Mesh > Diagnostics` **só na região porosa** (desmarcar Fluid) → extensão ≈ x [−0,5; 0,5], y [0,435;
0,735], z [−0,5; 0,5] → está **10× grande**. `Mesh > Scale Mesh` → **Fluid e Porous** juntos →
**0,1** → *Apply*. Diagnóstico de novo para conferir.

> 💡 Terceiro tutorial com malha fora de escala. **Diagnóstico por região** (só a peça cuja dimensão
> se conhece) é o jeito mais rápido de descobrir o fator.

## 3. Modelos

Contínuo `Physics 1` → renomear **Air**.

| grupo | modelo |
|---|---|
| Espaço / Tempo | 3D · Steady |
| Material | Gas · **Constant Density** |
| Escoamento | **Segregated Flow** |
| Regime | Turbulent → RANS |
| Turbulência | **desligar auto-select** → K-Epsilon → **Standard K-Epsilon** + **High y+ Wall Treatment** |

O tutorial usa o k-ε **padrão** em vez do default do STAR (Realizable Two-Layer) — por isso desliga a
seleção automática.

> 💡 **Um contínuo só** para o fluido livre e a região porosa: o meio poroso é o **mesmo fluido**
> com uma resistência a mais. Não é região sólida.

## 4. A região porosa e os coeficientes

1. `Regions > Porous > Type = Porous Region`.
2. **Turbulência dentro do poroso:** *Turbulence Specification* = **Intensity + Length Scale** →
   intensidade **0,1**, comprimento **0,01 m** (default). Dentro do poroso a turbulência é
   **especificada** pelo usuário (por isso o tutorial a define na região) — a escala de comprimento é
   da ordem do tamanho dos poros/canais.
3. *Porous Inertial Resistance* → **Isotropic Tensor** → **25 kg/m⁴**.
4. *Porous Viscous Resistance* → **Isotropic Tensor** → **1 500 kg/m³·s**.

> 💡 **Isotrópico × direcional.** *Isotropic Tensor* = mesma resistência em todas as direções
> (catalisador granular, espuma). Peças com direção preferencial — **colmeia, demister de tela,
> feixe de tubos** — pedem resistência **diferente por direção**: baixa na direção de passagem,
> alta na transversal (que "endireita" o escoamento como os canais reais fazem).

## 5. Contornos

Parede e saída ficam no default. Só a **entrada**:

| grandeza | valor |
|---|---|
| Turbulence Specification | Intensity + Length Scale |
| Turbulence Intensity | 0,05 |
| Turbulence Length Scale | 0,005 m |
| Velocity Magnitude | **20 m/s** |

---

## Checklist reaproveitável
- [ ] Meio poroso = **mesmo contínuo** do fluido, região do tipo *Porous Region*.
- [ ] Coeficientes P_i, P_v a partir de **dados Δp × v** (`coef_poroso.py dados`) ou correlação
      (`coef_poroso.py ergun`); **v é a velocidade superficial**.
- [ ] Saber **qual termo domina** na faixa de operação (`v = P_v/P_i`).
- [ ] Isotrópico só se a peça não tiver direção preferencial; senão, resistência por direção.
- [ ] Turbulência **especificada** dentro do poroso, com escala de comprimento ~ tamanho do canal.
- [ ] Diagnóstico de malha **por região** para descobrir o fator de escala.
- [ ] Relatório de **velocidade superficial média** e **Δp através da região porosa** para conferir
      contra a régua.

> O material recebido termina nos contornos. Ao rodar, conferir a velocidade superficial média e o Δp
> através da região porosa contra a régua da §1.
