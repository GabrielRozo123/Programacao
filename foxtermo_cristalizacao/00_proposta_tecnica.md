# Proposta Técnica — CFD do Tanque de Cristalização de Óleo de Palma (FOXTERMO)

> Rascunho técnico (CAEXPERTS). **A parte comercial (prazo, valor, condições) é da CAEXPERTS/Marcus** —
> aqui está o escopo técnico que fundamenta a proposta. Base: e-mail do Álvaro Salla (16/07).

## 1. Contexto e objetivo
A FOXTERMO desenvolve um **tanque de cristalização de óleo de palma**: o óleo é resfriado sob agitação
para **cristalizar a fração de maior ponto de fusão** (estearina) e separá-la da líquida (oleína) —
fracionamento por cristalização. O resfriamento é feito por uma **serpentina de imersão** (água de torre
por dentro; óleo por fora) e um **agitador** mantém a mistura homogênea.

**Objetivo do CFD:** prever o **campo de velocidades e a transferência de calor** no tanque, com foco nas
**velocidades na região da serpentina** — informação que governa a **uniformidade do resfriamento** e,
portanto, a **qualidade e o controle da cristalização** (zonas mortas → cristalização desigual / incrustação
na serpentina).

## 2. Escopo do estudo
Modelar o tanque com **agitador (rotativo)** e **serpentina helicoidal**, com **óleo de palma** no lado do
tanque e **água de resfriamento** dentro dos tubos, em regime de **transferência de calor conjugada**:
- Campo de velocidade do óleo (dirigido pelo agitador) e do escoamento na serpentina.
- Distribuição de temperatura no óleo e na parede da serpentina.
- **Velocidades na serpentina** (entregável central pedido pelo cliente).
- Efeito da **rotação do agitador** e das **propriedades dependentes da T** (4 cenários).

## 3. Metodologia (STAR-CCM+)
1. **Agitador:** **MRF** (Moving Reference Frame) — região rotativa em torno do agitador. *(Já validado no
   projeto Ito; se houver forte interação agitador-serpentina, avaliar malha deslizante.)*
2. **Transferência de calor conjugada (CHT):** três meios acoplados — **óleo (tanque) ↔ parede da serpentina
   (metal) ↔ água (interior dos tubos)**. Resolve o fluxo de calor real óleo→água.
3. **Propriedades dependentes da T (crítico):** o óleo de palma tem **viscosidade que dispara ao resfriar**
   (e vira não-newtoniano/pastoso ao cristalizar). Modelar **ρ(T) e μ(T)** por tabela/polinômio. *(Mesma
   classe de desafio do xarope viscoso do Ito.)*
4. **Cristalização (fase avançada, a alinhar no escopo):** a solidificação libera **calor latente** e gera
   **fração sólida (slurry)** que muda a reologia. Duas rotas:
   - **(A) Base:** resfriamento + CHT com μ(T) forte, **sem** cinética de cristalização (mais barato, já
     entrega as velocidades e o campo térmico).
   - **(B) Avançada:** modelo de **solidificação/melting** (calor latente + fração sólida) — mais caro;
     recomendado só se o cliente precisar da própria cinética de cristalização.
5. **Turbulência/regime:** definir pelo Reynolds do agitador (o óleo viscoso pode dar **laminar/transição**,
   como o xarope). Sem turbulência espúria em alto strain.
6. **Malha:** poliédrica + prism; refino na **serpentina** (resolver a camada limite térmica óleo/tubo) e na
   ponta do agitador. Independência de malha.

## 4. Os 4 cenários (a confirmar com o cliente)
Variando **propriedades (T)** e **rotação do agitador**. Proposta de matriz:
| # | Temperatura / propriedades | Rotação do agitador |
|---|---|---|
| 1 | Óleo quente (início, μ baixa) | rotação nominal |
| 2 | Óleo resfriado (μ alta, perto da cristalização) | rotação nominal |
| 3 | Óleo resfriado (μ alta) | rotação **reduzida** |
| 4 | Óleo resfriado (μ alta) | rotação **aumentada** |
*(A definir com o Álvaro: os pontos exatos de T e as rotações de interesse.)*

## 5. Entregáveis
- Campo de **velocidade** (óleo e serpentina) por cenário — com destaque nas **velocidades na serpentina**.
- Campo de **temperatura** (óleo, parede, água) e **fluxo de calor** óleo→água.
- **Zonas mortas / de baixa velocidade** (risco de cristalização desigual / incrustação).
- Efeito da **rotação** e da **viscosidade (T)** no resfriamento e na uniformidade.
- Relatório técnico + figuras/cenas. *(Formato a combinar.)*

## 6. Dados necessários do cliente (para fechar o escopo e cotar)
**Geometria**
- Dimensões do **tanque** (Ø, altura, fundo) e desenho/CAD.
- **Serpentina:** Ø do tubo, passo da hélice, nº de voltas, Ø da hélice, material e espessura.
- **Agitador:** tipo (âncora? hélice? turbina?), diâmetro, nº de pás, posição, e **rotação(ões)**.

**Processo / fluidos**
- **Óleo de palma:** ρ(T) e **μ(T)** (curva!), faixa de T (entrada→cristalização), e — se rota B —
  temperatura de cristalização, calor latente, curva de fração sólida.
- **Água de resfriamento:** vazão, T de entrada/saída, DN dos tubos.
- **Ponto de operação:** T inicial do óleo, meta de resfriamento, tempo de batelada.

**Escopo**
- Confirmar as **4 combinações** (T × rotação) de interesse.
- Precisa da **cinética de cristalização** (rota B) ou basta o resfriamento + velocidades (rota A)?
- Regime: **transiente** (batelada de resfriamento) ou **permanente** (ponto de operação)?

## 7. Premissas (a validar)
- MRF para o agitador (frozen-rotor) — adequado se a interação agitador-serpentina não for dominante.
- Água da serpentina como escoamento interno (pode ser 1D/rede acoplada se o cliente só quer o lado do óleo).
- Rota **A (sem cinética de cristalização)** como base, salvo pedido explícito da rota B.

## 8. Comercial
> **A preencher pela CAEXPERTS/Marcus:** prazo, valor, cronograma (nos moldes dos cronogramas Petrobras/Ito),
> e a rota (A ou B) conforme o escopo fechado com o Álvaro.
