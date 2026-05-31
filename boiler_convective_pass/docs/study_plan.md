# Study Plan — CFD Progression for Boiler Convective Pass

Ordered from simplest to most complex. Each step builds on the previous.
All cases implementable in STAR-CCM+.

---

## Step 1 — Escoamento ao redor de 1 cilindro (Re = 100, laminar, 2D)

**O que é:** Benchmark clássico de derramamento de vórtices (von Kármán).
Nenhum modelo de turbulência necessário — Navier-Stokes laminar puro.

**O que se valida:**

| Grandeza | Valor esperado | Referência |
|----------|---------------|-----------|
| Número de Strouhal St | 0.164 – 0.167 | Williamson (1996) |
| Coef. de arrasto médio C_D | 1.33 – 1.36 | Braza et al. (1986) |
| Coef. de sustentação RMS C_L′ | 0.22 – 0.35 | varia por autor |

**Referências:**
- Braza, M., Chassaing, P., Ha Minh, H. (1986). *Journal of Fluid Mechanics*, 165, 79–130.
  DNS 2D clássico; C_D ≈ 1.364, St ≈ 0.160 a Re = 100.
- Williamson, C.H.K. (1996). "Vortex Dynamics in the Cylinder Wake."
  *Annual Review of Fluid Mechanics*, 28, 477–539. DOI: 10.1146/annurev.fl.28.010196.002401
  Banco de dados experimental definitivo; St × Re sobre toda a faixa laminar.
- Zdravkovich, M.M. (1997). *Flow Around Circular Cylinders, Vol. 1.* Oxford University Press.
  Compêndio de todos os regimes; tabelas de C_D, C_L, St.

**Domínio e malha:**
- Retangular: ~20D montante, 40–50D jusante, 10–15D metade lateral
- Malha 2D estruturada/híbrida; ~50–80 células ao redor do cilindro; 30k–80k células total
- Passo de tempo: Δt ≈ 0.005–0.01 D/U∞
- Solver: transitório laminar (não-estacionário)

**Por que começar aqui:** Ensina o workflow completo de aerodinâmica não-estacionária no
STAR-CCM+ (monitores de força, FFT para Strouhal, refinamento de malha) sem nenhum
modelo de turbulência. Conexão com caldeiras: derramamento de vórtices é o mecanismo
de vibração induzida por escoamento (VIE) nos tubos.

---

## Step 2 — Banco de tubos 2D periódico: transferência de calor (RANS estacionário)

**O que é:** Domínio de uma célula unitária com condições de contorno periódicas
translacionais (direção do escoamento) e simétricas (direção transversal).
Paredes dos tubos isotérmicas. Turbulento (Re = 10³–10⁵). k-ω SST.

**O que se valida:**
- Nu_D vs. Re_D → correlação de Žukauskas (1972, 1987)
- ΔP por fileira → número de Euler de Žukauskas

**Correlação alvo:**
```
Nu_D = C · Re_D^m · Pr^0.36 · (Pr/Pr_w)^0.25
```
Escalonado (Re = 10³–2×10⁵): C = 0.35, m = 0.60
Alinhado  (Re = 10³–2×10⁵): C = 0.27, m = 0.63

**Referências:**
- Žukauskas, A. (1972, 1987). *Advances in Heat Transfer*, 8 e 18. Academic Press.
  Base de dados experimental universal; tabelas C, m, Eu para ambas as configurações.
- Kim, T.W. et al. (2013). "Effect of longitudinal pitch on convective heat transfer
  in crossflow over in-line tube banks." *Nuclear Engineering and Design*, 260, 199–214.
  DOI: 10.1016/j.nucengdes.2013.02.011 — k-ω SST periódico validado; mostra que
  Žukauskas pode sobrepredizer Nu em ~37% para SL/D baixo.
- FHMT (TechScience, **open access**, 2023). "Cross Flow Characteristics and Heat Transfer
  of Staggered Tubes Bundle: A Numerical Study." Vol. 21, pp. 367–383.
  DOI: 10.32604/fhmt.2023.042639. SL/D = 1.3–2.4, Re = 10k–19k.

**Domínio e malha:**
- 1 célula unitária: largura = ST, 1 tubo ao centro; periódico na direção do escoamento
- O-grid ao redor do tubo (~80–120 células na circunferência); y+ < 1 (k-ω SST)
- Total: ~50k–150k células (2D)
- Custo: minutos por caso no STAR-CCM+

**Por que este step:** Ensina o setup de domínio periódico — o truque mais reutilizável
para estudos paramétricos de banco de tubos. Resultado direto: h_gas necessário para
o balanço térmico da caldeira.

---

## Step 3 — Estudo paramétrico de razão de passo (ST/D e SL/D)

**O que é:** Variação sistemática de ST/D (1.25–3) e SL/D (1.25–3) no Step 2.
Saída: curvas Nu × Re e Eu × Re para cada combinação de passo.

**O que se valida:**
- Nu vs. tabelas de Žukauskas (1972, 1987)
- Modelo analítico de Khan-Culham-Yovanovich (2006) — expressões em forma fechada

**Referências:**
- Khan, W.A., Culham, J.R., Yovanovich, M.M. (2006). "Convection heat transfer from tube
  banks in crossflow: Analytical approach." *Int. J. Heat Mass Transfer*, 49(25–26), 4831–4838.
  DOI: 10.1016/j.ijheatmasstransfer.2006.05.038
  Preprint (livre): https://www.mhtlab.uwaterloo.ca/pdf_papers/mhtl06-20.pdf
  Melhor comparação analítica para dados paramétricos de CFD.
- FHMT (2023), mesma referência do Step 2. SL/D = 1.3–2.4; Nu diminui ~9% quando
  SL/D aumenta 44%.

**Custo:** ~30 min por caso RANS estacionário → 20–30 casos em uma sessão.

**Por que este step:** Ensina pensamento de Projeto de Experimentos em CFD.
Conexão com caldeira: a razão de passo é a principal variável geométrica de projeto
— afeta acesso de sopradores de fuligem, taxa de erosão e queda de pressão.

---

## Step 4 — Comparação alinhado vs. escalonado

**O que é:** Comparação direta de transferência de calor e queda de pressão para as
duas configurações em Re, razão de passo e número de fileiras idênticos.

**Resultado clássico:** Configuração escalonada tem Nu 15–30% maior, mas ΔP também
maior que a alinhada para o mesmo Re.

**O que se valida:**
- Razão Nu (escalonado/alinhado): constante C ~35% maior p/ escalonado (Žukauskas)
- Número de Euler: gráficos de Žukauskas para ambas as configurações
- Campo de velocidade: literatura confirma zona de "sombra" estagnada na alinhada vs.
  impingement na escalonada

**Referências:**
- Sharma, A. et al. (2021). "CFD Analysis of Flow Patterns, Pressure Drop, and HTC in
  Staggered and Inline Heat Exchangers." *Mathematical Problems in Engineering*, 2021,
  Art. ID 6645128. DOI: 10.1155/2021/6645128. **Open access (Hindawi/Wiley).**
  Fluent k-ε, 21 vs. 24 tubos; validação dentro de 15% para h, 8% para ΔP.
- Mandhani, V.K., Chhabra, R.P., Eswaran, V. (2002). "Forced convection heat transfer
  in tube banks in crossflow." *Chemical Engineering Science*, 57(3), 379–391.
  DOI: 10.1016/S0009-2509(01)00390-6 — 2D numérico, Re = 1–300; mostra que
  Nu_escalonado > Nu_alinhado se deve principalmente à mistura.

**Domínio e malha:**
- 2 células periódicas (alinhada e escalonada) no mesmo passo
- Ou seção de 5 fileiras com perfil de entrada
- ~50k–200k células (2D); ×5–10 para 3D com span periódico

**Por que este step:** Ligação mais direta com a decisão de projeto da caldeira.
Permite visualizar a razão física da diferença de Nu: efeito de "jato de impingement"
nas fileiras escalonadas.

---

## Step 5 — CHT simples: gás–parede–água (estado estacionário)

**O que é:** Simulação de três regiões: gás quente fora dos tubos (fluido 1), parede
sólida de aço (sólido, λ ≈ 50 W/m·K), fluido de trabalho dentro do tubo (fluido 2).
Sem partículas, sem mudança de fase, estado estacionário.

**O que se valida:**
- Nu_externo vs. Žukauskas
- Nu_interno vs. Gnielinski: Nu = (f/8)(Re−1000)Pr / [1 + 12.7(f/8)^0.5(Pr^(2/3)−1)]
- Coeficiente global U: U = Q / (A · ΔT_lm) → comparar com método LMTD
- Temperatura da parede do tubo: dominada por R_parede = ln(D_o/D_i)/(2πλ)

**Referências:**
- STAR-CCM+ Official Training (2023). "Pipe-in-Duct" CHT Case (Siemens).
  https://www.scribd.com/document/670379964/STAR-CCM-Introductory-Training-2023-Pipe-in-Duct-4-4
  Geometria diretamente análoga a um tubo de caldeira em escoamento cruzado.
- STAR-CCM+ YouTube Tutorial Playlist. "Solid-Fluid CHT Step by Step (Advanced)."
  https://www.youtube.com/playlist?list=PL9_xoSgYy7gVyP_T4qD0QryYF2gaWt7Ua
  Cobertura de interface térmica acoplada, k-ω SST, propriedades de aço.

**Domínio e malha:**
- 3 fileiras de tubos (escalonado), largura completa com entrada/saída
- Cada tubo = região sólida com canal interno
- ~500k–2M células (3D slice)
- Simplificação aceitável: BC convectiva interna (h_Gnielinski) em vez de resolver
  o escoamento interno — reduz custo e complexidade como primeiro passo.

**Por que este step:** Equivalente CFD do cálculo do coeficiente global U.
Ensina interfaces fluido-sólido-fluido — habilidade central do STAR-CCM+.
Insight físico: na caldeira, a resistência dominante é usualmente o lado do gás
(h_gas ≈ 50–200 W/m²·K) versus lado da água (h_água ≈ 5k–20k W/m²·K).

---

## Step 6 — Meio poroso: banco de tubos completo (abordagem de sistema)

**O que é:** O banco de tubos inteiro é substituído por uma zona de **meio poroso** com:
- Coeficientes de resistência de Darcy-Forchheimer derivados do número de Euler de Žukauskas
- Fonte de calor volumétrica: Q_vol = h_eff · a_v · (T_gas − T_parede)

**Como derivar os coeficientes no STAR-CCM+:**
1. Calcular Eu de Žukauskas para o passo e Re de operação
2. ΔP_fileira = Eu · ½ ρ U_max²
3. Coeficiente inercial: C₂ = 2 ΔP_fileira / (ρ U_max² · L_fileira)  [1/m]
4. Configurar em: Physics → Continua → Fluid → Porous Media → Inertial Resistance

**O que se valida:**
- ΔP do meio poroso vs. Eu × N_fileiras de Žukauskas (dentro de 5–10%)
- Q_total vs. cálculo NTU-efetividade ou LMTD

**Referências:**
- ANSYS FLUENT 12.0 User's Guide, §7.2.3 "Porous Media Conditions."
  https://www.afs.enea.it/project/neptunius/docs/fluent/html/ug/node233.htm
  Formulação Darcy-Forchheimer; coeficientes viscosos e inerciais.
- *Journal of Fluids Engineering*, 144(8), 081403 (2022). "Validation of the Porous
  Medium Approximation for Compact Heat Exchangers." DOI: 10.1115/1.4054168
  Modelo de meio poroso reproduz ΔP do CFD detalhado dentro de 5%.
- Drosatos, P. et al. (2014). *Fuel*, 117, 633–648. DOI: 10.1016/j.fuel.2013.09.082
  Metodologia desacoplada: meio poroso para a seção convectiva na caldeira de 300 MWe.

**Domínio e malha:**
- Passe convectivo completo (~5 m × 3 m × 1 m)
- Malha grosseira estruturada: ~50k–200k células hexaédricas
- Custo: minutos vs. dias para geometria totalmente resolvida

**Por que este step:** Abordagem industrial para modelagem de sistema de caldeira —
distribuição de escoamento, mal-distribuição, balanço térmico global.
Após validar o modelo resolvido (Steps 2–5), o meio poroso é calibrado contra
ele e usado para simulações de escala completa.

---

## Tabela-Resumo da Progressão

| Step | Tópico | Complexidade | Setup | Validação principal |
|------|--------|-------------|-------|---------------------|
| 1 | Cilindro único, Re=100, laminar | Muito baixa | 2–4 h | Braza (1986): St, C_D |
| 2 | Banco 2D periódico, RANS, Nu × Re | Baixa | 4–6 h | Žukauskas (1972): Nu |
| 3 | Paramétrico ST/D, SL/D (6–12 casos) | Baixa | 6–8 h | Žukauskas + Khan (2006) |
| 4 | Alinhado vs. escalonado | Baixa–Média | 4–6 h | Sharma (2021); Žukauskas |
| 5 | CHT: gás–parede–água | Média | 1–2 dias | U (LMTD); Gnielinski |
| 6 | Meio poroso: passe completo | Média | 1 dia | ΔP, Q_total vs. Žukauskas |
| 7+ | DPM passivo → fouling → erosão | Alta | Dias–semanas | Ver literature_survey.md |

---

## Notas de Setup STAR-CCM+ (transversais a todos os steps)

**Modelo de turbulência:** k-ω SST para todos os casos com transferência de calor.
y+ < 1 (10–15 camadas prismáticas, taxa de crescimento 1.2) para acurácia em Nu.
Wall functions (y+ ~30) aceitáveis para estudos de queda de pressão apenas.

**Domínio periódico:** Usar interface "Fully Developed Flow" com fluxo de massa
especificado — não confundir com periódico cíclico. Requer cuidado especial na
condição de periodicidade térmica (temperatura periódica, não adiabático).

**Independência de malha:** Sempre 3 níveis (grosseiro/médio/fino, razão ~√2 em
contagem de células). Critério: < 2% de variação em Nu e Eu entre médio e fino.
Células circunferenciais mínimas: 80; camadas prismáticas mínimas: 10.

**Tutorial nativo STAR-CCM+:** "Staggered Tube Bank" (Thermal → CHT examples)
é o ponto de partida mais próximo disponível na documentação do Simcenter.
