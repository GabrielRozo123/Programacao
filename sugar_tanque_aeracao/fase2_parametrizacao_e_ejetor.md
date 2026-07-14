# Fase 2 (Ito) — Estudo paramétrico (Design Manager) + Ejetor

> Aberta após a **apresentação ao Ito (14/07/2026)** — feedback **positivo**. O Ito pediu:
> (1) variar **diâmetro da pá, ângulo das pás e rotação**; (2) estudar também o **ejetor**.

## A. Estudo paramétrico via Design Manager (STAR-CCM+)
Automatizar "muda aqui, muda ali, roda sozinho". As três variáveis **não têm a mesma dificuldade**:

| Variável | Tipo | Dificuldade | Nota |
|---|---|---|---|
| **Rotação (rpm)** | operação | 🟢 trivial | Global parameter (como o *mass flow* do tutorial Static Mixer). Sem remalhar. |
| **Diâmetro da pá** | geometria | 🟡 média | Exige **3D-CAD paramétrico** (dimensão dirigível) → remalha a cada design. |
| **Ângulo das pás** | geometria | 🟡 média | Idem — parâmetro de sketch no 3D-CAD. |

### Requisito-chave
Pra varrer **diâmetro e ângulo automaticamente**, o **impelidor precisa ser um modelo paramétrico
no 3D-CAD do STAR** (não um STEP "burro" importado). Rotação não precisa disso.

### Plano de estudo (ordem: rápido → completo)
1. **Tutorial "Design Sweep of a Static Mixer"** — o fluxo base: global parameter → faixa de
   valores → Design Manager roda o solver em cada um. Aplicar já na **rotação** (ganho rápido).
2. **Parametrizar o impelidor** no 3D-CAD (diâmetro + ângulo como parâmetros) → entram no sweep.
3. **"Pareto Optimization: Static Mixer"** — só se o Ito quiser o **ótimo** (melhor combinação),
   não só a varredura.

### Custo — regra de ouro
Rodar o sweep **só no REATOR** (MRF permanente, minutos/design). Diâmetro/ângulo/rotação são
parâmetros do **agitador** → reator. **NÃO** colocar o aerador transiente no sweep (dias/design).

### Responses a monitorar no Design Manager
Potência do agitador (meta < 25 kW), **Np**, **Nq**, Reynolds do impelidor, torque. (Os mesmos da
Tabela 1 do deck.)

## B. Achado da apresentação — o "fabricante sobrenatural" (5 µm)
O fabricante das lanças alega bolha de **5 µm no nascimento**; o CFD dá **~1,2 mm** (~240×).
**Não é erro do CFD — é física de formação:**
- O tamanho de nascimento é propriedade do **fluido + escoamento**, não da lança.
- Os 5 µm são quase certamente o **tamanho do poro** do difusor OU medidos **em água** (baixa μ).
- Em xarope de **6,5 Pa·s**, o desprendimento é dominado pela viscosidade → bolha sai ~mm.
- **Reforça a conclusão:** a alavanca é a **viscosidade do meio**, não a lança nem a pressão.

> **Oportunidade de validação:** se o Ito medir tamanho de bolha **no xarope real** (não em água),
> comparar com o CFD. Expectativa: longe dos 5 µm.

## C. Ejetor (sugestão do Ito)
O ejetor ataca a **alavanca real** (cisalhamento na formação) — ao contrário das lanças (baixo
cisalhamento). Garganta de alto cisalhamento = onde a bolha *pode* ser quebrada.

**Escopo inicial proposto:**
1. **Monofásico:** CFD do venturi — jato motriz → baixa pressão na garganta → arraste do ar (razão
   de arraste), mapear o **campo de cisalhamento** na garganta e o difusor (recuperação de pressão).
2. **Multifásico (S-Gamma):** ar + xarope → prever o **tamanho da bolha na saída** do ejetor.
3. **Critério:** se o cisalhamento levar a bolha rumo aos **200 µm**, o ejetor é o caminho da solução.

**Pendências:** geometria/desenho do ejetor (garganta, bocal, difusor), condição motriz (vazão/pressão
do líquido motriz), ponto de injeção do ar.

## Log
- **2026-07-14** — Apresentação ao Ito entregue (feedback positivo). Fase 2 aberta: paramétrico
  (D/ângulo/rpm via Design Manager) + ejetor. Registrado o achado do 5 µm do fabricante.
