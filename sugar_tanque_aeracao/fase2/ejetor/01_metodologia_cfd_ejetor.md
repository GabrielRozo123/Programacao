# Metodologia CFD do Ejetor Venturi — como simular e prever o tamanho da microbolha

> Projeto Sugar/Ito · Fase 2. Objetivo: prever o **tamanho da microbolha gerada** pelo ejetor no
> **xarope viscoso (6,5 Pa·s)** e responder se a garganta de alto cisalhamento leva a bolha à faixa
> de flotação (**<200–300 µm**) — a alavanca que a Fase 1 identificou (pressão não era).
>
> Metodologia construída por análise multi-abordagem (4 filosofias independentes de CFD) + revisão
> de literatura. Geometria/medidas em [`../../geometria/dimensoes_ejetor_medidas.md`](../../geometria/dimensoes_ejetor_medidas.md);
> domínio fluido `../../geometria/eductor_dominio_fluido_v1.step`.

## 0. O ACHADO QUE MUDA TUDO — o ejetor é LAMINAR
Checagem de Reynolds (com vazão motriz plausível 7–22 m³/h, 7 bicos Ø9 mm):
- **Re_bico ≈ 18–90**, **Re_câmara/lança ≈ 37** — mesmo a 20 m/s. **Escoamento inteiramente laminar.**
- Venturis de microbolha da literatura são **turbulentos** (Re 10⁴–10⁵) — a quebra lá é por turbulência.
  **Aqui não existe quebra turbulenta** (ε_turb ≈ 0).

**Consequências (decidem a modelagem):**
1. **NÃO usar modelo de turbulência.** k-ε/k-ω fabricariam ε e μ_t espúrios em zonas de alto strain →
   **microbolha FALSA** (falso-positivo otimista que enganaria o cliente). Rodar **laminar** (com μ enorme,
   as menores escalas são grandes → malha fina transiente é quase-DNS).
2. **Os kernels de quebra padrão são inválidos.** Luo, Lehr, S-Gamma turbulento dependem de ε≈0 →
   preveem **quebra ≈ zero pelo motivo ERRADO** (mascaram se há quebra viscosa real). A quebra tem de
   ser dirigida pela **taxa de deformação resolvida** e pelo **número de capilaridade** (abaixo).
3. **A viscosidade que ATRAPALHOU na lança pode AJUDAR na garganta:** a tensão viscosa
   `τ = μ·γ̇ ≈ 29 kPa` supera a pressão de Laplace `2σ/a ≈ 280 Pa` em ~100× → **Ca ≈ 200–700 ≫ Ca_crit**
   → quebra é termodinamicamente favorável.

**Mas há dois "poréns" que tornam o desfecho genuinamente incerto (entre ~5 µm e ~mm):**
- **Tempo:** tempo de quebra capilar `t_cap = μ·a/σ` (≈1 ms p/ 10 µm, ≈19 ms p/ 200 µm, ≈90 ms p/ 1 mm)
  vs residência na zona de alto cisalhamento (~2–6 ms). **Pode não haver TEMPO de quebrar.**
- **Tipo de escoamento:** razão de viscosidade `λ = μ_ar/μ_xarope ≈ 3×10⁻⁶ → 0`. A bolha **resiste à
  quebra em cisalhamento SIMPLES** (Ca_crit→∞, vira tip-streaming) e **só quebra em zonas EXTENSIONAIS**
  (contração dos bicos, saída do jato), onde Ca_crit ~0,1–1.

> **É exatamente a pergunta que o CFD existe para responder** (venturi funciona 6500× mais viscoso?).
> A resposta pode ser "sim, gera microbolha" OU "não, trava em ~mm como as lanças" — **ambos são achados
> valiosos** para o Ito. A metodologia foi desenhada para responder isso **honestamente**, sem embutir o desfecho.

## 1. Abordagem recomendada — DOIS PASSOS + âncora VOF
Das 4 filosofias avaliadas, a vencedora (maior confiança + escalável + testa a hipótese sem pressupor)
é a de **dois passos com uma âncora de interface resolvida**. Ela separa as duas perguntas
("o ar entra?" vs "quão fina fica a bolha?") e triangula o tamanho por **3 estimativas independentes**.

```
PASSO 1  Monofásico laminar (STEADY, barato)  ──►  o ar entra? onde a quebra é possível? d_max analítico
   │
   ├─ ÂNCORA VOF (1 bico + furos 1mm, transiente, AMR)  ──►  tamanho de NASCIMENTO real + mecanismo
   │
PASSO 2  EMP Euler-Euler + S-Gamma (TRANSIENTE, subdomínio reduzido)  ──►  distribuição/SMD na saída
```

### Passo 1 — Mapa monofásico laminar do xarope  (STEADY · rápido · 1ª entrega)
Justificativa física: o holdup da Fase 1 foi **~0,005–0,007%** → a fase gasosa quase não altera a
hidrodinâmica do líquido. Logo o campo monofásico **é fielmente** o que o gás vai "ver" — não é
aproximação grosseira.
- **Modelo:** Segregated Flow **steady, LAMINAR**, xarope Newtoniano incompressível (μ=6,5 Pa·s,
  ρ≈1300 kg/m³ — confirmar). Ar só como BC (não transportado).
- **Entrega (em horas, sem run multifásico):**
  - **(a) Campo de pressão** → a garganta/câmara cai abaixo da pressão de suprimento do ar? (viabilidade do arraste)
  - **(b) Tensor taxa-de-deformação CLASSIFICADO** em rotacional vs **extensional** (não só |γ̇|) — porque
    só o extensional quebra (λ→0). *Classificar o tensor é obrigatório, não opcional.*
  - **(c) Razão de arraste de ar** via equação de orifício `Q_ar = Cd·A·√(2ΔP/ρ_ar)`, ΔP = P_suprimento − P_câmara(CFD), Cd~0,6–0,8.
  - **(d) Tempo de residência** na zona de alta deformação → confrontar com `t_cap`.
  - **PREDITOR ANALÍTICO de tamanho** (antes de qualquer multifásico!): `d_max(x) = 2·Ca_crit·σ / (μ·γ̇(x))`.
    Nas zonas extensionais (γ̇~160–490 /s) dá **d_max ~10–70 µm — DENTRO da faixa de flotação**; nas de
    cisalhamento de parede o d_max formal é sub-µm mas **fisicamente inválido** (λ→0). Filtro de viabilidade:
    quebra só se `t_res > ~2–3·t_cap`. Os números dão `t_res ~2–6 ms` vs `t_cap ~1–3 ms` → **corda bamba**
    (é a pergunta aberta, já quantificada na 1ª semana).

### Âncora VOF — interface resolvida de 1 bico + furos de 1 mm  (transiente · AMR)
O elo mais forte cientificamente: **não usa nenhuma constante calibrada em água**. Resolve a interface
do ar nascendo e o 1º evento de quebra → dá o **tamanho de nascimento real** e diz se a quebra extensional
de fato ocorre no tempo disponível. Serve para **calibrar o coeficiente de quebra do S-Gamma** do Passo 2.
- **Modelo:** VOF (HRIC sharp, Interface CFL ≤0,3–0,5), CSF (σ≈0,07 N/m — confirmar), **ar como gás ideal
  compressível** (captura expansão no difusor), **laminar**, Implicit Unsteady. **AMR** grudado na interface.
- **Domínio:** micro-subdomínio de **1 bico** (simetria hexagonal — cunha/célula-unitária, não "1/7 de setor"),
  malha ~50–100 µm + AMR 2–3 níveis → pega a interface de 1 mm quebrando em ~10–70 µm. **Não** aplicar VOF ao domínio todo (proibitivo).
- **Medição do tamanho:** threshold α_ar>0,5 → rotular blobs conexos → d_i=(6V_i/π)^(1/3) → SMD/D10/D50/D90.
- ⚠️ Vigiar **coalescência numérica espúria** (VOF funde bolhas a ~1 célula — viés p/ bolha grande, justo
  contra a física de coalescência-inibida do xarope). Mitigar com HRIC sharp, AMR e **convergência de malha do d32**.

### Passo 2 — EMP + S-Gamma transiente (o workhorse da distribuição)  (subdomínio reduzido)
Mesma família **já validada no tanque** (EMP Xarope+Ar + S-Gamma) → comparabilidade direta lança-passiva
vs ejetor, no mesmo formato de histograma/SMD. Bolhas são sub-grid → malha moderada, custo aceitável.
- **Modelo:** EMP Euler-Euler, 2 fases, **LAMINAR**, Implicit Unsteady. Arrasto **Tomiyama** (regime viscoso/baixo
  Re_bolha), **massa virtual ON** (forte aceleração nos bicos, ρ_c/ρ_d~1000), lift e dispersão turbulenta **OFF**.
- **QUEBRA (a correção-chave):** acionar pela **taxa de deformação RESOLVIDA** via `Ca = μ·γ̇·a/σ` com
  `Ca_crit(λ→0)` dependente do **caráter** do escoamento (extensional ~0,1–1; cisalhamento simples → sem quebra).
  No STAR: verificar qual kernel está ativo; usar a formulação de **laminar shear breakup** ou **override por
  field function** (strain-rate resolvido + Ca_crit calibrado no VOF). *Sem isso o modelo é cego ao único
  mecanismo possível.*
- **COALESCÊNCIA:** manter, mas com **escala de drenagem de filme VISCOSA** (t_dren ∝ μ) → eficiência ≈0
  (coerente com o achado da Fase 1: viscosidade inibe coalescência). Kernel de água super-coalesceria (bolha grande falsa).
- **Semente:** ar entra na classe de nascimento do **VOF** (~1 mm confirma a Fase 1), não um chute.
- **Domínio reduzido:** câmara + garganta/difusor + **~0,5–1 m de lança** (não os 3 m — desperdício). A
  coalescência ao longo da lança de 3 m vai num run EMP grosseiro/1D separado, alimentado pela saída do ejetor.

### Upgrade opcional — Population Balance (AMUSIG por classes)
Se a distribuição sair **larga/bimodal** (provável) e o Ito quiser a **fração <200 µm direto** (a métrica de
processo), trocar o S-Gamma de 2 momentos por **classes** (12–15 bins, ~10 µm→4 mm, geométrico) com os
**mesmos kernels viscosos**. Lê o histograma sem premissa de forma. Mais caro; usar só se o S-Gamma indicar cauda relevante.

## 2. Condições de contorno (conjunto bem-posto: 1 vazão + 2 pressões)
Escolhido para que a **razão de arraste de ar seja RESULTADO, não input**:
- **Entrada motriz** (Ø52 / redutor 4"→2"): **Mass-Flow Inlet** de xarope (duty da bomba), VF_ar=0.
  Mass-flow (não pressão) fixa o ponto de operação no meio viscoso; **reportar a pressão de garganta resultante**.
- **Furos de ar** (1 mm): **Pressure/Stagnation Inlet** na pressão de suprimento (atmosférica se auto-aspirante;
  manométrica do compressor se soprado), VF_ar=1 → a **sucção do venturi decide quanto ar entra**. No Passo 2,
  opção estável = impor a razão de arraste do Passo 1 como mass-flow; +1 run com pressure-inlet p/ checar **choking**.
- **Saída** (fim do stub de lança): **Pressure Outlet** = **hidrostática da submersão** (~82 kPa, 6,47 m de xarope)
  **+ ΔP laminar restante da lança** (Poiseuille ~200 kPa em 3 m — **da ordem do próprio suprimento**, fixa o ponto de operação). **Não é atmosférica.**
- **Paredes:** no-slip. **Ângulo de contato** nos furos (xarope molha aço, θ~30–60°) governa o desprendimento (sensibilidade no VOF).

## 3. Como o tamanho é previsto — TRIANGULAÇÃO (3 vias independentes)
| Via | De onde | O que dá |
|---|---|---|
| **d_max analítico** | Passo 1 (Ca) | limite superior de tamanho por zona — sanity-check, 1ª semana |
| **Nascimento VOF** | âncora | tamanho real de formação/quebra, sem constante de água |
| **SMD (d32) EMP** | Passo 2 | distribuição completa, D10/50/90, **%<200 µm**, holdup, área interfacial na saída |
As três convergindo = número **defensável**. Saída no **mesmo formato dos histogramas da Fase 1** →
comparação cabeça-a-cabeça ejetor vs lança passiva.

## 4. Steady vs transiente
- **Passo 1 (monofásico):** STEADY laminar (Re~30, sem desprendimento de vórtice) — apropriado e barato.
- **Passo 2 (multifásico) e VOF:** **TRANSIENTE OBRIGATÓRIO.** A Fase 1 **provou** que steady erra
  (SMD 1,22 mm steady vs 2,53 mm transiente; 8,6% flotável FALSO vs ~0%). Rodar até estacionariedade
  **estatística** do d32 na saída. **Bom:** o ejetor é device de passagem (residência ms–s) → estaciona em
  **segundos** físicos (não nas horas do tanque) → transiente **acessível**.

## 5. Plano de validação (âncora obrigatória ANTES de confiar no ejetor)
1. **Reproduzir a LANÇA PASSIVA da Fase 1** com os mesmos kernels: nascimento ~1,2 mm → ~2,4 mm, ~0% <200 µm,
   sweep de pressão sem efeito. **Se os kernels não reproduzem isso, não confiar na previsão do ejetor.**
2. Convergência de malha do **d32 de saída** e do **γ̇ de pico** (termos-fonte de quebra são mesh-sensíveis — alerta herdado da Fase 1).
3. Convergência de Δt. Sensibilidade a σ e ângulo de contato (entram ~linear no tamanho).

## 6. Acoplamento ao tanque aerador
O ejetor entrega a **distribuição de bolha de saída** (SMD, classes, holdup, razão de arraste). Isso vira a
**condição de injeção** das lanças no modelo do tanque (Fase 1): substituir o "nascimento ~1,2 mm" pela
distribuição prevista pelo ejetor → re-rodar o aerador e ver se a flotação melhora. Fecha o ciclo
ejetor → tanque → eficiência de flotação.

## 7. Parametrização (o que varrer)
- **Ø da garganta / bicos** (o parâmetro geométrico mais crítico do venturi — controla γ̇ e a sucção).
- **Vazão motriz** (o sweep de pressão 1/2/3 kgf da Fase 1 vira sweep de vazão comparável).
- **Pressão de suprimento do ar** (arraste).
- (2ª ordem) comprimento/ângulo do difusor, posição dos furos de ar.

## 8. Riscos e mitigações
| Risco | Mitigação |
|---|---|
| Turbulência espúria (ligar k-ε "por hábito") → microbolha FALSA | **Rodar laminar** (Re~30) e verificar |
| Kernel de quebra turbulento (ε≈0) → "sem quebra" pelo motivo errado | Quebra por **strain-rate/Ca resolvido**, ancorada no VOF |
| Confundir cisalhamento com extensão (d_max sub-µm na parede) | **Classificar o tensor**; quebra só nas zonas extensionais |
| Coalescência de água super-estima (bolha grande falsa) | Escala de **drenagem viscosa** (t∝μ) → eficiência≈0 |
| Arraste superestimado (sem acoplamento reverso/choking) | Passo 1 = limite superior; **run 2b com pressure-inlet** |
| VOF caro/instável em 6,5 Pa·s (interface fina) | Plano B: só Passo 1 + EMP com nascimento ~1 mm da Fase 1 |
| d32 mesh/Δt-sensível | Convergência de malha e de Δt **obrigatórias** |

## 9. O que precisamos do cliente (dados que MUDAM o resultado)
- **⚠️ O ar é AUTO-ASPIRADO (Bernoulli) ou SOPRADO sob pressão?** A Fase 1 alimentava as lanças a 1/2/3 kgf/cm²
  → sugere soprado. **É o dado que mais muda o arraste.** Confirmar com Ito/Jadir.
- **Vazão/curva da bomba motriz** de xarope (faixa de escopo 7–22 m³/h).
- **Curva vazão×pressão do ar** (já pedida no kick-off).
- **ρ do xarope concentrado** (~1300 vs 1350) e **σ ar-xarope** (~0,07 N/m) — entram ~linear no tamanho.
- **Geometria exata:** Ø da garganta, posição/nº dos furos de ar, e confirmar se são **7 bicos Ø9** ou um venturi único (o esquema `venturi_o_que_medir.png` mostra garganta única; as medidas citam 7 bicos).

## 10. Roteiro de execução (ordem sugerida)
1. **Passo 1 monofásico** → viabilidade do arraste + d_max analítico + zonas extensionais (1ª semana, número defensável cedo).
2. **VOF âncora** (1 bico) → tamanho de nascimento + calibra o S-Gamma.
3. **Validar** kernels reproduzindo a lança passiva da Fase 1.
4. **Passo 2 EMP+S-Gamma transiente** (subdomínio) → distribuição/SMD/%<200µm na saída.
5. (Se cauda relevante) **upgrade para Population Balance**.
6. **Acoplar** a distribuição de saída ao tanque → eficiência de flotação.
7. **Parametrizar** (garganta, vazão) para otimizar.

---
*Confiança das abordagens avaliadas: VOF-resolvido 0,72 · Dois-passos 0,72 · EMP+S-Gamma 0,60 · Population Balance 0,60.
Recomendação = Dois-passos (0,72) com âncora VOF embutida, por ser a única que separa arraste de finura,
entrega número cedo, e triangula o tamanho por 3 vias independentes.*
