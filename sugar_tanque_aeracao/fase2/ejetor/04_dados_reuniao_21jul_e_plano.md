# 04 — Dados da reunião (21/07) + plano do ejetor (organizar o pensamento)

> Registro fiel do que o Ito passou na reunião — **nunca esquecer**. + o plano em 2 trilhos.

## 📌 Dados NOVOS do Ito (anotar tudo)
1. **O ar entra SUPERSÔNICO** na injeção (região que o Gabriel marcou no bico). → confirma o **choked/compressível**
   que a metodologia (`01`, refinamento 6) já previa. Mais forte ainda: **supersônico** = jato subexpandido com choque.
2. **Já existe uma CONTRAÇÃO** — razão diâmetro entrada:saída = **2:1** (ex.: entrada Ø20 → saída Ø10). → **CONFIRMA
   a álgebra do §5 do `03`** (bocal convergente é o que gera extensão/quebra). O cliente e a física estão alinhados.
3. **Ito quer MELHORAR a razão** (mais contração) → mais velocidade → mais cisalhamento/quebra.
4. **Alvo: velocidade de AR ≈ 1,3–2 m/s NO EJETOR** (na figura, no **tubo/lança de ar** — não no aerador). É o
   **critério de projeto baseline** do Ito. **Podemos PROPOR maior — só se justificado pela LITERATURA** (mais
   velocidade → mais cisalhamento → bolha menor). *(CLARIFICADO 21/07 — era m/s no tubo, não Mach.)*
   - **Reconcilia com o "supersônico":** 30 m³/h num tubo ~Ø63 → **~2–3 m/s** (bate com 1,3–2). Nos **furos de
     injeção** (pequenos, ~Ø1,3), o mesmo ar acelera a **~300 m/s ≈ sônico/supersônico**. Os dois são verdade,
     em locais diferentes: **1,3–2 m/s no tubo · supersônico na injeção.** ✔
5. **4 ejetores** justamente pra **dividir o ar** (120 m³/h total → 30/ejetor) e manter a velocidade no tubo na faixa.
6. **Tarefa AGORA:** **propor a geometria do BICO na lança de AR** (justificada por literatura+matemática) — **não**
   é simular o ejetor mostrado (esse simula quando a geometria nova fechar). O colega do Ito modela a proposta.
7. **Ar ≈ 30 m³/h/ejetor** (120/4) · motriz ≈ 130 m³/h.

## ⚠️ Confirmar (decidem o modelo)
- **O que contrai — o TUBO DE AR ou o BICO DE XAROPE?** ("diminuir o diâmetro do tubo" → provável **ar** (acelerar
  a Mach); mas pode ser o xarope. Muda o mecanismo — ver abaixo.)
- Alvo "1,3–2" = **Mach** (ar) ou **m/s** (líquido)? E onde?
- Ø exato do bico e dos furos de ar (leitura ampliada do PDF nativo `CSA01-300`).

## 🔬 O mecanismo (com o ar supersônico — atualização importante)
Com **ar supersônico**, entra em cena um mecanismo forte que a análise anterior subestimava: **atomização
assistida por gás.** O jato de ar de alta quantidade de movimento penetra o xarope e **cisalha a interface
ar-xarope** (Kelvin-Helmholtz/atomização), gerando bolhas finas. **Quanto maior o Mach do ar → mais cisalhamento
na interface → bolha menor.** É provavelmente a lógica do Ito ("mais velocidade de ar = mais quebra").
→ **Isso é boa notícia:** o supersônico é uma **alavanca de quebra potente** (diferente do cisalhamento viscoso
simples do xarope, que em λ→0 quase não quebra). Dois mecanismos possíveis coexistem:
- **(a) Jato de ar supersônico** → atomização na interface (lever = **Mach do ar** = contração do bocal de ar).
- **(b) Contração do xarope** → extensão no bico (lever = razão de contração do xarope).

## 🛤️ PLANO EM 2 TRILHOS

### TRILHO 1 — Estudo ANALÍTICO (AGORA, sem CFD) → propor a geometria
Objetivo: recomendar a **razão de contração** (e Ø do bico/ar) que maximiza a quebra — com matemática +
fenômenos de transporte. **É onde entra o "estudo matemático fino".** Blocos:
1. **Gás compressível (ar supersônico):** bocal (de Laval se supersônico) → **Mach de saída = f(razão de área)**;
   vazão choked `ṁ = Cd·A*·P₀·√(γ/RT₀)·(2/(γ+1))^((γ+1)/2(γ-1))`; jato subexpandido.
2. **Atomização do jato de ar:** Weber aerodinâmico `We = ρ_xarope·(ΔV)²·d/σ`; tamanho de bolha por
   correlação de atomização (∝ We^−a). → **d_bolha = f(Mach do ar)**.
3. **Contração do xarope (extensão):** `ε̇ = V/L`, `ε_H = 2·ln(D/d)`, `Ca_ext > Ca_crit,ext`.
4. **Balanços:** tempo de residência vs tempo visco-capilar; energia (ΔP) vs cisalhamento (`γ̇ ∝ 1/d³`, `ΔP ∝ 1/d⁴`).
5. **Entrega:** razão de contração recomendada + **tamanho de bolha estimado (analítico)**, sem CFD — para o
   colega do Ito construir a geometria.

### TRILHO 2 — Simulação CFD do ejetor (DEPOIS, quando a geometria fechar)
(Metodologia `01`, agora com o ar supersônico:)
1. **Passo 1 — monofásico laminar (xarope):** campo de deformação → **classificar EXTENSÃO vs cisalhamento**;
   pressão/velocidade na garganta; tempo de residência. Ar como BC compressível.
2. **Âncora VOF (1 bico):** ar como **gás ideal compressível** (captura o **jato supersônico subexpandido + choque**)
   + a contração → **tamanho de nascimento + 1ª quebra** (aqui o supersônico atomiza).
3. **Passo 2 — EMP + S-Gamma transiente:** distribuição/SMD/%<200 µm na saída.
4. **Validação:** reproduzir a lança passiva da Fase 1.

## 🎯 A ordem prática
**Agora:** Trilho 1 (analítico) → propõe a geometria → colega do Ito modela. **Depois:** Trilho 2 (CFD) valida/refina.
O analítico **destrava sem esperar** a geometria nova — e já entrega número/recomendação pro Ito.
