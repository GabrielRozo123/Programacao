# biokin — discriminação de mecanismos cinéticos para biodiesel em monolitos

Ferramenta computacional para **inferir o mecanismo e a equação de
velocidade** da transesterificação heterogênea (produção de biodiesel) a
partir de dados experimentais, com atenção específica a reatores de
monolito.

O problema que resolve: quando uma reação não é elementar, a equação de
velocidade não sai da estequiometria. É preciso postular um mecanismo,
derivar a lei que ele implica, e confrontá-la com os dados — repetindo
para cada mecanismo plausível. Feito à mão, isso limita a análise a três
ou quatro candidatos. Aqui a derivação é simbólica e automática, e a
varredura cobre **41 leis de velocidade distintas** vindas de 5 famílias
mecanísticas combinadas com escolhas de etapa determinante e conjuntos de
inibidores.

## O que o pacote faz

```
etapas elementares postuladas
        │
        ▼  derivação simbólica (quase-equilíbrio + balanço de sítios
        │                       + consistência termodinâmica)
equação de velocidade em forma fechada
        │
        ▼  regressão sobre os dados (diferencial → integral)
parâmetros com intervalos de confiança e diagnóstico de identificabilidade
        │
        ▼  filtros: parcimônia (AICc) + termodinâmica (Boudart-Vannice)
                    + estrutura dos resíduos
mecanismo mais provável — ou a constatação de que os dados não decidem
        │
        ▼  planejamento de experimentos (Box-Hill)
os próximos ensaios que resolveriam o empate
```

## Instalação

```bash
git clone https://github.com/GabrielRozo123/Programacao.git
cd Programacao
pip install numpy scipy sympy matplotlib      # pytest para rodar os testes
```

Sem dependências pesadas: a rede neural é implementada em numpy no próprio
pacote, para que a reprodutibilidade não dependa da versão de um framework
de aprendizado profundo.

## Uso imediato

Validar a ferramenta contra um mecanismo conhecido (dados sintéticos):

```bash
python -m biokin demo --keq 3.0 2.0 5.0 --figures figuras/
```

Rodar sobre dados próprios:

```bash
python -m biokin screen meus_dados.csv --keq 3.0 2.0 5.0 --figures figuras/
```

Ver o catálogo de mecanismos e as leis derivadas de cada um:

```bash
python -m biokin mechanisms --detail
```

Descobrir os próximos experimentos de maior poder discriminatório:

```bash
python -m biokin design meus_dados.csv
```

Avaliar transporte de massa na sua geometria de monolito:

```bash
python -m biokin transport --cpsi 400 --washcoat 30 --velocity 0.005
```

## Formato dos dados

CSV com uma linha por ponto amostrado. Células vazias significam "não
medido" — o pacote simplesmente não as usa nos resíduos, então serve tanto
a quem mede só o teor de éster quanto a quem tem o perfil completo de
glicerídeos.

| coluna | significado |
|---|---|
| `experimento` | rótulo da corrida |
| `reator` | `batch` ou `monolith` |
| `T_K` | temperatura [K] |
| `catalisador_g_L` | massa de catalisador por litro de meio |
| `C0_TG`, `C0_M`, … | composição de **alimentação** [mol/L] |
| `tempo_min` | tempo (batelada) ou tempo espacial (monolito) [min] |
| `C_TG`, `C_DG`, `C_MG`, `C_M`, `C_E`, `C_G` | concentrações medidas [mol/L] |

A alimentação vai em colunas próprias porque quase sempre se conhece o que
foi carregado mesmo sem titular — tipicamente o metanol, que está em
excesso.

Gerar um modelo de arquivo:

```python
from biokin.synthetic import generate_dataset
from biokin.data import write_csv
write_csv(generate_dataset(), "modelo.csv")
```

## Estrutura

| módulo | conteúdo |
|---|---|
| `biokin.mechanism` | etapas elementares e validação do ciclo catalítico |
| `biokin.lhhw` | **derivador simbólico** LHHW / Eley-Rideal |
| `biokin.library` | catálogo de mecanismos candidatos |
| `biokin.network` | rede das três reações consecutivas |
| `biokin.transport` | Sherwood, Thiele, Weisz-Prater, Mears, Carberry |
| `biokin.reactor` | batelada e monolito (ideal / filme / filme + washcoat) |
| `biokin.parameters` | Arrhenius e van 't Hoff reparametrizados |
| `biokin.estimation` | regressão diferencial e integral, covariância, ICs |
| `biokin.discrimination` | AICc, pesos de Akaike, regras de Boudart-Vannice |
| `biokin.ml` | rede neural, extração de taxas, regressão racional esparsa |
| `biokin.doe` | Box-Hill, Hunter-Reiner, D-ótimo |
| `biokin.screening` | orquestração da varredura |
| `biokin.report` | figuras |

## Fundamentação

`docs/metodo.md` explica cada etapa: por que a consistência termodinâmica
não é opcional, o que os critérios de informação medem e o que não medem,
por que o disfarce difusional é o modo de falha mais perigoso deste tipo
de estudo, e onde o aprendizado de máquina ajuda e onde atrapalha.

`docs/guia_experimental.md` traduz isso em decisões de bancada: quantas
corridas, em que faixa, o que medir e por quê.

## Validação

```bash
python -m pytest tests/ -q       # 44 testes, ~2,5 min
```

Os mais importantes verificam que:

- a lei derivada **se anula no equilíbrio químico** para toda família e
  toda escolha de etapa determinante — a propriedade que separa uma lei
  mecanística de um ajuste empírico com aparência de mecanismo;
- a derivação reproduz as leis de livro-texto para Eley-Rideal e
  Langmuir-Hinshelwood;
- a integração conserva os balanços de acila, de esqueleto de glicerol e
  de metanol;
- a varredura recupera o mecanismo que gerou dados sintéticos ruidosos.

### Resultado da validação sintética

`docs/relatorio_demo.txt` traz a saída completa de `python -m biokin demo`
sobre 27 corridas com 3 % de ruído. Em **cerca de 10 minutos** a varredura
percorre 41 candidatos e conclui:

| | |
|---|---|
| mecanismo verdadeiro | `ER-M[G] \| RDS=sr` |
| primeiro colocado | `ER-M[G] \| RDS=sr`, peso de Akaike 1,000 |
| `k₁` recuperado | +1,4 % do valor verdadeiro |
| `Ea₁` recuperada | 50,9 ± 7,6 contra 52 kJ/mol |
| `K_ads,G` recuperada | −2,2 % do valor verdadeiro |
| famílias LH | reprovadas: ΔS_ads de −487 J/(mol·K), impossível |

Vale reparar em três desfechos que mostram os filtros funcionando:

- o modelo com um termo **a mais** de inibição (por éster) ajusta
  igualmente bem — SSE 3,484 contra 3,485 — e é rejeitado pela parcimônia;
- o modelo **sem** inibição por glicerol ajusta visivelmente pior, o que
  estabelece que a inibição é real;
- as famílias Langmuir-Hinshelwood ajustam tão bem quanto a verdadeira e
  são eliminadas pelas regras termodinâmicas, não pela estatística.

O tempo se reparte em ~300 s de triagem diferencial (41 modelos), ~230 s
de regressão integral (5 sobreviventes) e ~35 s no restante.

## Limitações

Estão declaradas com franqueza porque uma banca vai perguntar:

- **O catálogo é finito.** Se o mecanismo real não estiver entre os
  candidatos, o peso de Akaike vai para o menos ruim, não para o
  verdadeiro. Os pesos são probabilidades *relativas ao conjunto
  examinado*.
- **Discriminação não é prova.** Nenhum ajuste de dados macroscópicos
  demonstra um mecanismo. Ele elimina candidatos incompatíveis. Evidência
  espectroscópica (DRIFTS in situ, TPD) e cálculos de estrutura eletrônica
  são o que confirma espécies de superfície.
- **Disfarce difusional.** Se os critérios de Weisz-Prater e Mears
  reprovarem, os parâmetros do modo `ideal` são aparentes, não
  intrínsecos. O relatório avisa; o modo `full` regride através do modelo
  de transporte.
- **Desativação não é modelada.** Lixiviação de fase ativa e envenenamento
  por ácidos graxos livres ou água aparecem como desvio sistemático nos
  resíduos, não como um termo do modelo.
- **Os valores em `biokin.synthetic` são inventados**, para exercitar o
  pipeline. Não são parâmetros de nenhum sistema real e não devem ser
  citados como tal.
