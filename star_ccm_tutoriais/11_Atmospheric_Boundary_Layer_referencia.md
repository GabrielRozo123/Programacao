# 11 — Atmospheric Boundary Layer (ABL) no STAR-CCM+ (referência)

> Notas de leitura das páginas *Atmospheric Boundary Layers* (teoria), *Atmospheric Boundary Layer Model Reference*,
> *Setting Up Atmospheric Boundary Layers* e *Wall Treatment Models Reference* (versão 21.02 / 2602), em palavras nossas,
> + como se encaixa no estudo de dispersão da LD (16/11/2026).

## O que o modelo faz
- Modelo **opcional** do continuum que fornece nas entradas os perfis de **Richards & Hoxey** (U, k, ε em função da altura).
  A parede do solo é uma parede rugosa comum (*Rough*), com a rugosidade escolhida para casar com o z₀ do perfil.
- Premissas de R&H: velocidade vertical nula, pressão constante, tensão de cisalhamento constante, k-ε em equilíbrio.
- Ativa a field function *Wall Direction*: a altura nos perfis é a **distância à parede** (no domínio vazio, = z).

## Exige
Desmarcar *Auto-select recommended physics models* · Steady · Gas · Segregated ou Coupled · **Constant Density** · Turbulent ·
RANS · **K-Epsilon → Standard K-Epsilon** · **High y+ Wall Treatment** · Optional Models → **Atmospheric Boundary Layer**.
Com outros modelos de turbulência o modelo não serve: perfis de entrada por field function.

## Propriedades do modelo
| propriedade | o que é | padrão |
|---|---|---|
| Reference Speed | velocidade na altura de referência | 10 m/s |
| Reference Height | altura de referência | 6 m |
| Roughness Length | z₀ do terreno | 0,01 m |
| von Karman Constant | κ | 0,42 |

## Receita do manual (*Setting Up Atmospheric Boundary Layers*)
1. **Constantes do Standard K-Epsilon:** Cμ "conforme o perfil de entrada, típico **0,03 a 0,11**"; C1e pela condição de
   equilíbrio **C1e = C2e − κ²/(√Cμ·σε)**. É a mesma condição que usamos ajustando σε em vez de C1e
   (Cμ 0,09, C1e 1,44 → σε = 1,225). Os 0,013 de Richards & Hoxey ficam fora da faixa que o manual sugere.
   - No equilíbrio, νt = Cμ·k²/ε = **κ·u*·z, independente de Cμ**: o Cμ só muda o nível de k, não a difusão do perfil
     não perturbado. Panofsky (σu, σv, σw = 2,5 / 1,9 / 1,3 u*) dá k ≈ 5,8 u*² → Cμ ≈ 0,03.
2. **Condição inicial:** *Initial Conditions → Turbulent Viscosity Ratio*: Constant, **1E10**. Nossa leitura: no ABL a
   razão νt/ν é enorme (no domínio da LD, κ·u*·z/ν ≈ 1,3 milhão no topo de 350 m) e não pode ser podada.
   Conferir também o limite máximo da razão de viscosidade no solver do k-ε e o *Output* ("viscosity limited").
3. **Solo** (*Wall*): *Wall Surface Specification* = **Rough**; *Standard Wall Function* E (exemplo 8,75) e κ;
   *Roughness Model Parameters* C (exemplo 0,25) e RplusRough ≥ 90; **Roughness Height r = E·z₀/C**
   (exemplo: 8,75 × 0,01 / 0,25 = 0,35 m). Vem de casar a lei de parede rugosa, u⁺ = (1/κ)·ln(E·y/(C·r)), com o perfil
   (1/κ)·ln(y/z₀).
4. **Entradas** (*Velocity Inlet*): *Turbulence Specification* = **K+Epsilon**; *Velocity Magnitude*, *Turbulent Kinetic
   Energy* e *Turbulent Dissipation Rate* com Method **Atmospheric Boundary Layer** (a direção vai em *Flow Direction*).
5. **Malha:** **y > 0,2·r** e **y ≥ 10·z₀** (y = distância do centro da 1ª célula ao solo) e **y⁺ ≥ 30**.

## Roughness Limiter: a chave não existe mais
- O guia do ABL ainda diz para desativar o *Roughness Limiter* em *Wall Roughness Parameters*, mas na versão 21.02 o nó se
  chama *Roughness Model Parameters* e só tem **B, C, RplusSmooth, RplusRough** (padrões 0 · 0,253 · 2,25 · 90).
- A *Wall Treatment Models Reference* da mesma versão explica: o método **Rough sempre limita** a rugosidade pela
  distância à parede da célula junto à parede, e o *Output* informa em quantas faces cortou ("Roughness limited on N
  faces"). O método **Rough Displaced Origin** (RDO) não limita, e a Siemens o recomenda quando os dois existem
  (Standard k-ε + High y⁺ tem os dois). Só que o RDO tem só RplusSmooth/RplusRough, sem B e C: a relação r ↔ z₀ da receita
  acima não vale para ele, e precisaria da equação do RDO para casar com o perfil.
- **Consequência prática:** com *Rough*, o limitador fica inativo se o **centro da 1ª célula estiver acima de r**. Com
  r = E·z₀/C, isso pede prisma único de espessura > 2·r.
- Por que importa: com r cortado, a rugosidade efetiva cai, u* na parede cai e o k junto ao solo fica abaixo do perfil.
  É a assinatura que vimos no domínio vazio da LD (k 15–25 % baixo, maior perto do chão).

## Uso no estudo da LD
- z₀ 0,03 m, E 9,0 (padrão do STAR), C 0,253 → **r = 9 × 0,03 / 0,253 = 1,07 m**. (Antes usamos 9,793·z₀/C = 1,16 m, que é
  a fórmula de Blocken para o E do Fluent.) Prisma único de 2,5 m → centro a 1,25 m > r; y ≥ 10·z₀ = 0,3 m; y⁺ ~ 10⁴.
- Rodada 4 do domínio vazio: modelo ABL nas entradas e no Topo, **Cμ 0,09 / σε 1,225 (iguais à rodada 3)**, r = 1,07 m,
  e conferir no *Output* que nenhuma face teve a rugosidade limitada. Muda só o que é suspeito, para isolar o efeito.
- Cμ: sensibilidade depois (0,03, coerente com Panofsky). Não muda νt no perfil não perturbado; muda k e a mistura junto
  aos prédios.
